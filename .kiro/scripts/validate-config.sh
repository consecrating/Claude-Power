#!/usr/bin/env bash
# validate-config.sh — check this pack's Kiro configuration against the documented
# schemas. Catches the mistakes that make a skill or steering file silently fail to
# load: wrong filename, name/folder mismatch, invalid inclusion mode, missing
# required fields, malformed hook JSON.
#
# Usage:
#   validate-config.sh            validate everything
#   validate-config.sh <file>     validate one steering file or SKILL.md
#
# Exit 0 = clean, 1 = at least one error. Warnings do not fail the run.

set -uo pipefail

ERR=0
WARN=0
err()  { printf 'ERROR  %s\n' "$*" >&2; ERR=$((ERR+1)); }
warn() { printf 'WARN   %s\n' "$*" >&2; WARN=$((WARN+1)); }
ok()   { [ "${VERBOSE:-0}" = "1" ] && printf 'ok     %s\n' "$*"; return 0; }

# Extract a top-level scalar from the leading YAML frontmatter block.
fm_get() {
  awk -v key="$2" '
    NR==1 && $0!="---" { exit }
    NR==1 { next }
    $0=="---" { exit }
    {
      k=$0; sub(/:.*/,"",k); gsub(/^[ \t]+|[ \t]+$/,"",k)
      if (k==key) { v=$0; sub(/^[^:]*:[ \t]*/,"",v); print v; exit }
    }
  ' "$1"
}

has_frontmatter() { [ "$(head -c 4 "$1")" = "---"$'\n' ] || [ "$(head -n1 "$1")" = "---" ]; }

# Does the frontmatter contain this key at top level (any value form)?
fm_has() {
  awk -v key="$2" '
    NR==1 && $0!="---" { exit }
    NR==1 { next }
    $0=="---" { exit }
    { k=$0; sub(/:.*/,"",k); gsub(/^[ \t]+|[ \t]+$/,"",k); if (k==key) { found=1; exit } }
    END { exit(found?0:1) }
  ' "$1"
}

validate_skill() {
  local f="$1" dir folder name desc
  dir=$(dirname "$f"); folder=$(basename "$dir")

  if ! has_frontmatter "$f"; then
    err "$f: frontmatter must be the first bytes of the file (no leading blank line)"
    return
  fi
  name=$(fm_get "$f" name)
  desc=$(fm_get "$f" description)

  [ -n "$name" ] || err "$f: missing required frontmatter field 'name'"
  [ -n "$desc" ] || err "$f: missing required frontmatter field 'description'"

  if [ -n "$name" ]; then
    [ "$name" = "$folder" ] || err "$f: name '$name' must equal folder name '$folder'"
    [ "${#name}" -le 64 ]   || err "$f: name is ${#name} chars (max 64)"
    printf '%s' "$name" | grep -qE '^[a-z0-9-]+$' \
      || err "$f: name '$name' must be lowercase letters, digits, hyphens only"
  fi

  if [ -n "$desc" ]; then
    [ "${#desc}" -le 1024 ] || err "$f: description is ${#desc} chars (max 1024)"
    [ "${#desc}" -ge 40 ]   || warn "$f: description is very short; it is the activation trigger"
  fi

  local lines; lines=$(wc -l <"$f")
  [ "$lines" -le 200 ] || warn "$f: $lines lines; consider moving depth into references/"

  ok "$f"
}

validate_steering() {
  local f="$1" inc
  if ! has_frontmatter "$f"; then
    warn "$f: no frontmatter; defaults to inclusion: always (loaded every turn)"
    return
  fi
  inc=$(fm_get "$f" inclusion)
  [ -n "$inc" ] || inc="always"

  case "$inc" in
    always|manual) ;;
    fileMatch)
      fm_has "$f" fileMatchPattern \
        || err "$f: inclusion: fileMatch requires 'fileMatchPattern'"
      ;;
    auto)
      fm_has "$f" name        || err "$f: inclusion: auto requires 'name'"
      fm_has "$f" description || err "$f: inclusion: auto requires 'description'"
      ;;
    *)
      err "$f: invalid inclusion '$inc' (must be always, fileMatch, auto, or manual)"
      ;;
  esac

  case "$(basename "$f")" in
    product.md|tech.md|structure.md)
      err "$f: reserved foundation filename owned by the host repo — rename it"
      ;;
  esac

  ok "$f ($inc)"
}

validate_hooks() {
  local f="$1"
  if ! command -v jq >/dev/null 2>&1; then
    warn "$f: jq not available, skipping hook validation"; return
  fi
  jq -e . "$f" >/dev/null 2>&1 || { err "$f: invalid JSON"; return; }

  [ "$(jq -r '.version // empty' "$f")" = "v1" ] || err "$f: version must be \"v1\""
  jq -e '.hooks | type == "array"' "$f" >/dev/null || { err "$f: 'hooks' must be an array"; return; }

  local valid_triggers='PostFileSave PostFileCreate PostFileDelete PreToolUse PostToolUse UserPromptSubmit SessionStart Stop PreTaskExec PostTaskExec'
  local n i
  n=$(jq '.hooks | length' "$f")
  i=0
  while [ "$i" -lt "$n" ]; do
    local nm tr ty cmd pr
    nm=$(jq -r ".hooks[$i].name // empty" "$f")
    tr=$(jq -r ".hooks[$i].trigger // empty" "$f")
    ty=$(jq -r ".hooks[$i].action.type // empty" "$f")
    cmd=$(jq -r ".hooks[$i].action.command // empty" "$f")
    pr=$(jq -r ".hooks[$i].action.prompt // empty" "$f")

    [ -n "$nm" ] || err "$f hooks[$i]: missing 'name'"
    [ -n "$tr" ] || err "$f hooks[$i]: missing 'trigger'"
    if [ -n "$tr" ]; then
      case " $valid_triggers " in
        *" $tr "*) ;;
        *) err "$f hooks[$i]: invalid trigger '$tr'" ;;
      esac
    fi
    case "$ty" in
      command) [ -n "$cmd" ] || err "$f hooks[$i]: action.type command requires 'command'" ;;
      agent)   [ -n "$pr" ]  || err "$f hooks[$i]: action.type agent requires 'prompt'"
               warn "$f hooks[$i]: agent action starts a new model loop and consumes credits" ;;
      *)       err "$f hooks[$i]: action.type must be 'command' or 'agent' (got '$ty')" ;;
    esac
    i=$((i+1))
  done
  ok "$f ($n hook(s))"
}

validate_script() {
  local f="$1"
  bash -n "$f" 2>/dev/null || err "$f: bash syntax error"
  [ -x "$f" ] || warn "$f: not executable (chmod +x)"
  ok "$f"
}

# ---- single-file mode -------------------------------------------------------
if [ $# -gt 0 ]; then
  t="$1"
  [ -f "$t" ] || { echo "validate-config: no such file: $t" >&2; exit 1; }
  case "$t" in
    */SKILL.md)          validate_skill "$t" ;;
    .kiro/steering/*.md) validate_steering "$t" ;;
    *.json)              validate_hooks "$t" ;;
    *.sh)                validate_script "$t" ;;
    *)                   echo "validate-config: nothing to check for $t"; exit 0 ;;
  esac
  [ "$ERR" -eq 0 ] && { echo "validate-config: OK"; exit 0; }
  exit 1
fi

# ---- full run ---------------------------------------------------------------
echo "validate-config: checking Kiro configuration"

shopt -s nullglob
for d in .kiro/skills/*/; do
  if [ -f "$d/SKILL.md" ]; then
    validate_skill "$d/SKILL.md"
  else
    err "${d}: skill folder has no SKILL.md (filename must be exactly SKILL.md)"
  fi
done

for f in .kiro/steering/*.md; do validate_steering "$f"; done
for f in .kiro/hooks/*.json;  do validate_hooks   "$f"; done
for f in .kiro/skills/*/scripts/*.sh .kiro/scripts/*.sh; do validate_script "$f"; done

# Cross-reference check: skills referenced by name that do not exist.
# Matches both "skill `name`" and "`name` skill". The closing backtick is
# required, so path fragments like `references/*` are not mistaken for names.
if command -v rg >/dev/null 2>&1; then
  for ref in $( { rg -o 'skill `([a-z0-9-]+)`' -r '$1' --no-filename \
                    .kiro/skills .kiro/steering AGENTS.md 2>/dev/null
                  rg -o '`([a-z0-9-]+)` skill' -r '$1' --no-filename \
                    .kiro/skills .kiro/steering AGENTS.md 2>/dev/null
                } | sort -u ); do
    [ -d ".kiro/skills/$ref" ] || warn "referenced skill '$ref' does not exist"
  done
fi

printf '\nvalidate-config: %d error(s), %d warning(s)\n' "$ERR" "$WARN"
[ "$ERR" -eq 0 ] || exit 1
echo "validate-config: OK"
