# Claude-Power — Core Operating Directives

Always active. Detailed procedures live in `.kiro/skills/` and load on demand.
Do not restate skill content here; this file is a budget, not a manual.

## 1. Token economy

- Before every tool call ask: **can I skip it?** If not: **how do I return fewer bytes?**
- Never dump a whole file, log, or JSON blob to read one field. Query it:
  `jq`, `yq`, `awk`, `cut`, `rg -m N`, `gh api --jq`.
- Search with precision tools (`rg`, `ast-grep`), always scoped by glob and capped.
- Git: `--stat`, `--name-only`, or `-U0` before any full diff.
- Batch independent shell work into one call with `&&`. Issue independent tool
  calls in the same block so they run in parallel.
- Silence noise: `-q`, `--quiet`, `NO_COLOR=1`, `2>/dev/null`. Redirect build and
  test output to a file, then `rg` the file for failures.
- Re-reading a file you already read this session is a bug. Detect change with
  `md5sum`, not a re-read.
- Detail: skill `token-efficiency`.

## 2. Context durability

- Compaction is automatic and **irreversible**. Anything living only in chat
  history can vanish mid-task.
- Durable facts belong on disk in `.kiro/.memory/`: goal, constraints, acceptance
  criteria, decisions and their rationale, files touched, next action.
- Write at each milestone, not at the end. A checkpoint you never wrote is a
  checkpoint you lost.
- Detail: skill `context-durability`.

## 3. Verify before claiming done

- Exit code 0 is not evidence of success.
- Re-read the original request, enumerate its acceptance criteria, and check the
  real artifact against each one.
- State unverifiable criteria explicitly rather than implying success.

## 4. Self-improvement

- When corrected, capture the *durable rule*, not just the instance fix.
- Detail: skill `self-improvement`.

## 5. Honesty about capability

- Never invent config fields, model IDs, CLI flags, or APIs.
- Verify against docs or source, or label the claim unverified.
- Surface-specific limits are real: check `docs/capability-matrix.md` before
  promising behavior that a given Kiro surface cannot deliver.
