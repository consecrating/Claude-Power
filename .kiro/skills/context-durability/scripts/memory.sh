#!/usr/bin/env bash
# memory.sh — durable working memory for long Kiro sessions.
#
# Chat history is compacted automatically and irreversibly. Anything that must
# survive belongs on disk. This script is the ergonomic path for writing and
# reading that state in a consistent, low-token shape.
#
# Storage: $KIRO_MEMORY_DIR (default .kiro/.memory)
#
#   goal            single statement of what the user actually asked for
#   constraints.md  hard limits: do-not-touch, must-use, style, scope
#   criteria.md     acceptance criteria as checkboxes
#   decisions.md    append-only log of decisions + rationale (timestamped)
#   files.md        files touched and why
#   next            the single next action
#   TASK.md         rendered human-readable snapshot (via `render`)
#
# Usage:
#   memory.sh init "<goal>"          create store, set goal
#   memory.sh goal "<text>"          set/replace goal
#   memory.sh constraint "<text>"    add a hard constraint
#   memory.sh criterion "<text>"     add an acceptance criterion
#   memory.sh check "<substring>"    tick the first matching open criterion
#   memory.sh note "<text>"          log a decision with rationale
#   memory.sh file <path> [why]      record a touched file (deduped)
#   memory.sh next "<text>"          set the next action
#   memory.sh status                 compact digest (cheap; safe to re-read)
#   memory.sh render                 write TASK.md snapshot
#   memory.sh verify [--strict]      report gaps; --strict exits 1 on any gap
#   memory.sh clear                  delete the store

set -uo pipefail

MEM="${KIRO_MEMORY_DIR:-.kiro/.memory}"
G="$MEM/goal"
N="$MEM/next"
C="$MEM/constraints.md"
A="$MEM/criteria.md"
D="$MEM/decisions.md"
F="$MEM/files.md"
SNAP="$MEM/TASK.md"

TAIL_DECISIONS="${KIRO_MEMORY_TAIL:-8}"

ts() { date -u +'%Y-%m-%dT%H:%MZ'; }

ensure() {
  mkdir -p "$MEM" || { echo "memory: cannot create $MEM" >&2; exit 1; }
  local f
  for f in "$G" "$N" "$C" "$A" "$D" "$F"; do
    [ -e "$f" ] || : >"$f"
  done
}

have_store() { [ -d "$MEM" ]; }

# first non-empty line, whitespace-collapsed, capped
oneline() {
  [ -s "$1" ] || { printf '(unset)'; return; }
  tr '\n' ' ' <"$1" | sed 's/[[:space:]]\+/ /g; s/^ //; s/ $//' | cut -c1-300
}

# Count matching lines, always printing exactly one integer.
# `grep -c` prints "0" AND exits 1 when there are no matches, so the naive
# `grep -c ... || echo 0` emits "0\n0" and breaks arithmetic comparisons.
count_lines() {
  local n
  n=$(grep -c -- "$1" "$2" 2>/dev/null) || n=0
  printf '%s' "${n:-0}"
}

nonempty_lines() { count_lines '[^[:space:]]' "$1"; }

cmd="${1:-status}"
[ $# -gt 0 ] && shift

case "$cmd" in

  init)
    ensure
    [ $# -gt 0 ] && printf '%s\n' "$*" >"$G"
    printf 'memory: store ready at %s\n' "$MEM"
    [ -s "$G" ] && printf 'goal: %s\n' "$(oneline "$G")"
    ;;

  goal)
    [ $# -gt 0 ] || { echo 'usage: memory.sh goal "<text>"' >&2; exit 2; }
    ensure; printf '%s\n' "$*" >"$G"; echo 'memory: goal set'
    ;;

  next)
    [ $# -gt 0 ] || { echo 'usage: memory.sh next "<text>"' >&2; exit 2; }
    ensure; printf '%s\n' "$*" >"$N"; echo 'memory: next action set'
    ;;

  constraint)
    [ $# -gt 0 ] || { echo 'usage: memory.sh constraint "<text>"' >&2; exit 2; }
    ensure
    grep -qxF -- "- $*" "$C" 2>/dev/null || printf -- '- %s\n' "$*" >>"$C"
    echo 'memory: constraint recorded'
    ;;

  criterion)
    [ $# -gt 0 ] || { echo 'usage: memory.sh criterion "<text>"' >&2; exit 2; }
    ensure
    if grep -qF -- "$*" "$A" 2>/dev/null; then
      echo 'memory: criterion already present'
    else
      printf -- '- [ ] %s\n' "$*" >>"$A"
      echo 'memory: criterion added'
    fi
    ;;

  check)
    [ $# -gt 0 ] || { echo 'usage: memory.sh check "<substring>"' >&2; exit 2; }
    ensure
    key="$*"
    if awk -v k="$key" '
          BEGIN { done = 0 }
          {
            if (!done && index($0, k) > 0 && $0 ~ /^- \[ \]/) {
              sub(/^- \[ \]/, "- [x]"); done = 1
            }
            print
          }
          END { exit (done ? 0 : 1) }
        ' "$A" >"$A.tmp"; then
      mv "$A.tmp" "$A"
      echo 'memory: criterion checked'
    else
      rm -f "$A.tmp"
      echo "memory: no open criterion matching: $key" >&2
      exit 1
    fi
    ;;

  note)
    [ $# -gt 0 ] || { echo 'usage: memory.sh note "<text>"' >&2; exit 2; }
    ensure; printf -- '- %s — %s\n' "$(ts)" "$*" >>"$D"
    echo 'memory: decision logged'
    ;;

  file)
    [ $# -gt 0 ] || { echo 'usage: memory.sh file <path> [why]' >&2; exit 2; }
    ensure
    p="$1"; shift
    why="${*:-touched}"
    if grep -qF -- "\`$p\`" "$F" 2>/dev/null; then
      echo 'memory: file already recorded'
    else
      # shellcheck disable=SC2016  # backticks are literal markdown, not a subshell
      printf -- '- `%s` — %s\n' "$p" "$why" >>"$F"
      echo 'memory: file recorded'
    fi
    ;;

  status)
    if ! have_store; then
      echo 'memory: no store. start with: memory.sh init "<goal>"'
      exit 0
    fi
    open_n=$(count_lines '^- \[ \]' "$A")
    done_n=$(count_lines '^- \[x\]' "$A")
    echo "=== WORKING MEMORY ($MEM) ==="
    echo "GOAL: $(oneline "$G")"
    echo "NEXT: $(oneline "$N")"
    echo "CRITERIA: $done_n done / $open_n open"
    if [ "$open_n" -gt 0 ]; then
      grep '^- \[ \]' "$A" 2>/dev/null | head -10
    fi
    if [ "$(nonempty_lines "$C")" -gt 0 ]; then
      echo "CONSTRAINTS:"
      head -10 "$C"
    fi
    if [ "$(nonempty_lines "$D")" -gt 0 ]; then
      echo "RECENT DECISIONS (last $TAIL_DECISIONS of $(nonempty_lines "$D")):"
      tail -n "$TAIL_DECISIONS" "$D"
    fi
    if [ "$(nonempty_lines "$F")" -gt 0 ]; then
      echo "FILES TOUCHED ($(nonempty_lines "$F")):"
      head -15 "$F"
    fi
    echo "=== END MEMORY ==="
    ;;

  render)
    ensure
    {
      printf '# Task state\n\n_Rendered %s. Source of truth for this task; survives compaction._\n\n' "$(ts)"
      printf '## Goal\n\n%s\n\n' "$([ -s "$G" ] && cat "$G" || echo '_not set_')"
      printf '## Constraints\n\n%s\n\n' "$([ -s "$C" ] && cat "$C" || echo '_none recorded_')"
      printf '## Acceptance criteria\n\n%s\n\n' "$([ -s "$A" ] && cat "$A" || echo '_none recorded_')"
      printf '## Next action\n\n%s\n\n' "$([ -s "$N" ] && cat "$N" || echo '_not set_')"
      printf '## Files touched\n\n%s\n\n' "$([ -s "$F" ] && cat "$F" || echo '_none recorded_')"
      printf '## Decision log\n\n%s\n' "$([ -s "$D" ] && cat "$D" || echo '_none recorded_')"
    } >"$SNAP"
    printf 'memory: rendered %s\n' "$SNAP"
    ;;

  verify)
    strict=0
    [ "${1:-}" = "--strict" ] && strict=1
    gaps=0
    have_store || { echo 'memory: no store'; [ "$strict" -eq 1 ] && exit 1; exit 0; }
    [ -s "$G" ] || { echo 'gap: goal not recorded'; gaps=$((gaps+1)); }
    [ -s "$A" ] || { echo 'gap: no acceptance criteria recorded'; gaps=$((gaps+1)); }
    [ -s "$N" ] || { echo 'gap: next action not recorded'; gaps=$((gaps+1)); }

    # Files changed in git but never recorded in memory
    if git rev-parse --git-dir >/dev/null 2>&1; then
      unrecorded=""
      while IFS= read -r p; do
        [ -n "$p" ] || continue
        case "$p" in "$MEM"/*) continue ;; esac
        grep -qF -- "\`$p\`" "$F" 2>/dev/null || unrecorded="$unrecorded $p"
      done <<EOF
$(git status --porcelain 2>/dev/null | awk '{print $NF}')
EOF
      if [ -n "${unrecorded# }" ]; then
        echo "gap: changed but not recorded:${unrecorded}" | cut -c1-400
        gaps=$((gaps+1))
      fi
    fi

    if [ "$gaps" -eq 0 ]; then
      echo 'memory: complete'
    else
      echo "memory: $gaps gap(s)"
      [ "$strict" -eq 1 ] && exit 1
    fi
    exit 0
    ;;

  clear)
    rm -rf "$MEM" && echo "memory: cleared $MEM"
    ;;

  -h|--help|help)
    sed -n '2,32p' "$0" | sed 's/^# \{0,1\}//'
    ;;

  *)
    echo "memory: unknown command '$cmd' (try: memory.sh help)" >&2
    exit 2
    ;;
esac
