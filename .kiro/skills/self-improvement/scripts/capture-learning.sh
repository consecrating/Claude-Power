#!/usr/bin/env bash
# capture-learning.sh — stage feedback as candidate durable rules.
#
# Capture is cheap and reversible. Promotion into steering or a skill is a
# deliberate edit, because every promoted rule carries a permanent token cost.
# This script therefore stages and advises; it never edits config for you.
#
# Storage: $KIRO_LEARNINGS_DIR (default .kiro/.learnings), gitignored.
#
# Usage:
#   capture-learning.sh add "<rule>" [scope]   stage a rule; scope is free text
#                                              (e.g. token-efficiency, repo, global)
#   capture-learning.sh list                   numbered inbox
#   capture-learning.sh promote <n>            placement guidance for entry n
#   capture-learning.sh rm <n>                 drop entry n
#   capture-learning.sh count                  number of staged entries
#   capture-learning.sh clear                  empty the inbox

set -uo pipefail

DIR="${KIRO_LEARNINGS_DIR:-.kiro/.learnings}"
INBOX="$DIR/inbox.md"

ensure() {
  mkdir -p "$DIR" || { echo "learnings: cannot create $DIR" >&2; exit 1; }
  [ -e "$INBOX" ] || printf '# Learning inbox\n\n' >"$INBOX"
}

entries() { [ -f "$INBOX" ] && grep -n '^- ' "$INBOX" 2>/dev/null || true; }
count()   { entries | wc -l | tr -d ' '; }

nth_line_no() {
  entries | sed -n "${1}p" | cut -d: -f1
}

cmd="${1:-list}"
[ $# -gt 0 ] && shift

case "$cmd" in

  add)
    [ $# -gt 0 ] || { echo 'usage: capture-learning.sh add "<rule>" [scope]' >&2; exit 2; }
    ensure
    rule="$1"; shift
    scope="${1:-unclassified}"
    if grep -qF -- "$rule" "$INBOX" 2>/dev/null; then
      echo 'learnings: already staged (duplicate ignored)'
      exit 0
    fi
    printf -- '- [%s] (%s) %s\n' "$(date -u +'%Y-%m-%d')" "$scope" "$rule" >>"$INBOX"
    printf 'learnings: staged (%s total). Review with: capture-learning.sh list\n' "$(count)"
    ;;

  list)
    if [ ! -s "$INBOX" ] || [ "$(count)" -eq 0 ]; then
      echo 'learnings: inbox empty'
      exit 0
    fi
    echo "=== LEARNING INBOX ($(count)) ==="
    entries | cut -d: -f2- | nl -ba -w2 -s'. '
    echo '=== promote with: capture-learning.sh promote <n> ==='
    ;;

  count)
    count
    ;;

  promote)
    n="${1:-}"
    case "$n" in ''|*[!0-9]*) echo 'usage: capture-learning.sh promote <n>' >&2; exit 2 ;; esac
    ln=$(nth_line_no "$n")
    [ -n "$ln" ] || { echo "learnings: no entry $n" >&2; exit 1; }
    text=$(sed -n "${ln}p" "$INBOX")
    cat <<EOF
Entry $n:
  $text

Choose the CHEAPEST placement that works. Cost is permanent.

  1. .kiro/skills/<skill>/SKILL.md or references/
     Free until the skill activates. PREFER THIS for anything procedural.

  2. .kiro/steering/<name>.md  with  inclusion: fileMatch
     Free unless matching files are in play. Best for rules scoped to a language,
     directory, or file type.
       ---
       inclusion: fileMatch
       fileMatchPattern: ["src/**/*.ts"]
       ---

  3. .kiro/steering/<name>.md  with  inclusion: auto
     Description always loaded, body on match. Best for situational rules.
       ---
       inclusion: auto
       name: <kebab-name>
       description: Use when <explicit trigger conditions>.
       ---

  4. AGENTS.md  or  inclusion: always
     Paid on EVERY turn, forever. Only for universal, safety-relevant rules.

Before writing:
  - grep the existing config: does a rule already cover this?
      rg -n '<keyword>' .kiro/steering .kiro/skills AGENTS.md
  - if yes, AMEND it rather than adding a competing rule
  - make it specific and testable, and state the trigger condition
  - record the rationale if it is not self-evident

After promoting, remove the entry:
  capture-learning.sh rm $n
EOF
    ;;

  rm)
    n="${1:-}"
    case "$n" in ''|*[!0-9]*) echo 'usage: capture-learning.sh rm <n>' >&2; exit 2 ;; esac
    ln=$(nth_line_no "$n")
    [ -n "$ln" ] || { echo "learnings: no entry $n" >&2; exit 1; }
    sed "${ln}d" "$INBOX" >"$INBOX.tmp" && mv "$INBOX.tmp" "$INBOX"
    printf 'learnings: removed entry %s (%s remain)\n' "$n" "$(count)"
    ;;

  clear)
    ensure; printf '# Learning inbox\n\n' >"$INBOX"; echo 'learnings: inbox cleared'
    ;;

  -h|--help|help)
    sed -n '2,22p' "$0" | sed 's/^# \{0,1\}//'
    ;;

  *)
    echo "learnings: unknown command '$cmd' (try: capture-learning.sh help)" >&2
    exit 2
    ;;
esac
