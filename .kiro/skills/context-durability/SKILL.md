---
name: context-durability
description: Use on any task expected to span many turns, or when the conversation is already long, context is filling up, output was truncated, or you are resuming work already in progress. Also apply when the user says you forgot something, lost track, changed an earlier decision, or repeated work. Defines the on-disk memory protocol that survives Kiro's automatic irreversible context compaction.
metadata:
  version: "1.0"
  part-of: claude-power
---

# Context durability

Kiro compacts long conversations **automatically and irreversibly**. Older turns
are replaced by a summary. Compaction reliably preserves task status, modified file
paths, key decisions, next steps, and stated intent — but individual tool results,
intermediate reasoning, earlier code snippets, and exploratory discussion may be
summarized away or lost.

There is no manual compaction trigger on Kiro Web, and no built-in memory file.
So: **chat history is not storage. The filesystem is storage.**

## The one rule

If losing a fact would force you to redo work or would change a decision, it does
not belong only in the conversation. Write it to `.kiro/.memory/`.

## What to persist

| Persist | Why |
|---|---|
| The goal, in the user's own words | prevents drift; the goal is set at the start, not by the latest turn |
| Hard constraints | "don't touch X", "must use Y", scope limits — expensive to violate |
| Acceptance criteria | what "done" means; needed for final verification |
| Decisions **with rationale** | stops you re-litigating or silently reversing a settled choice |
| Rejected alternatives + why | stops you re-trying a dead end |
| Files changed and why | the change surface; enables review and rollback |
| The single next action | makes any interruption resumable |
| Non-obvious environment facts | the working build command, the real test path, a required env var |

## What NOT to persist

Do not mirror the repo into memory. Skip file contents, full command output, code
snippets you can re-derive, and narration. Store **pointers and conclusions**:
`` `src/auth.ts:88` — token TTL is read here, not from config `` beats pasting the
function. Memory is an index, not a cache.

## Checkpoint triggers

Write at these moments — not at the end:

- immediately after the goal and constraints are understood
- after any decision that closes off alternatives
- after each file is created or meaningfully changed
- before any long or risky operation (large build, migration, bulk edit)
- when you notice context filling or output being truncated
- before handing off to a subagent, and after it reports back
- whenever the next action changes

Persist *before* you spend. A checkpoint written after the expensive step is a
checkpoint you might never write.

## Using the script

```bash
M=.kiro/skills/context-durability/scripts/memory.sh

$M init "Ship OAuth device-code login"        # store the real goal
$M constraint "Do not modify the public SDK surface"
$M criterion "device flow returns a refresh token"
$M criterion "existing password login still passes its tests"
$M note "Rejected implicit flow — no refresh token, blocks criterion 1"
$M file src/auth/device.ts "new device-code grant"
$M next "wire the poll endpoint into the router"

$M status          # compact digest — cheap, safe to re-read any time
$M check "refresh token"   # tick a criterion once verified
$M verify          # report gaps before claiming done
$M render          # write TASK.md, a readable snapshot for humans/PRs
```

Plain `fs_write` into `.kiro/.memory/` is equally valid — the script exists to keep
shape and timestamps consistent and to make `status` cheap to re-read.

`.kiro/.memory/` is gitignored by default. To let reviewers audit the agent's
reasoning, un-ignore it and commit `TASK.md`.

## Recovering after compaction

When you notice history has been summarized, or you are unsure what was already
decided:

1. `memory.sh status` — restores goal, constraints, open criteria, next action
2. `git status --short && git diff --stat` — restores the actual change surface
3. `tail -20 .kiro/.memory/decisions.md` — restores *why* things are as they are

Do this **before** reading source files again. Re-reading the repo to rebuild a
mental model you already wrote down is the most expensive possible recovery.

Never silently reverse a logged decision. If you now disagree with one, say so
explicitly and log the reversal with its reason.

## Before reporting done

Run `memory.sh verify`, then check every criterion in `criteria.md` against the
real artifact. Unticked criteria mean not done — see the `verification-discipline`
steering rules.

Detail on failure modes and drift: `references/compaction-survival.md`.
