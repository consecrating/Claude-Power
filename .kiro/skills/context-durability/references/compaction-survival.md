# Compaction survival

## What compaction does

As a conversation approaches the model's context limit, Kiro generates a summary,
replaces older history with it, keeps recent messages verbatim, and continues.
This happens on every surface, automatically. It is **one-way** — the pre-compaction
transcript is not recoverable within the session.

Reliably preserved: task status, paths of modified files, key decisions and
constraints, next steps, your stated intent.

At risk: individual tool call results, intermediate reasoning, code snippets from
earlier turns, details of errors already resolved, exploratory discussion.

The pattern to notice: **conclusions tend to survive, evidence tends not to.** So
persist the evidence you will need again, and the reasoning behind conclusions —
not just the conclusions themselves.

## The four failure modes

### 1. Goal drift

The task slowly becomes "whatever we discussed most recently." The original request
had five requirements; after compaction three are in play, and the summary reflects
the narrowed version. Nothing signals the loss.

Guard: write the goal verbatim at the start and re-read it from disk before
reporting done. Compare against the file, not your memory of it.

### 2. Decision amnesia

A choice was made and its rationale lost. You re-open a settled question, or worse,
silently reverse it and produce a design that contradicts earlier work.

Guard: log decisions with rationale. Rationale is what makes a decision resistant
to re-litigation — "chose X" invites reversal, "chose X because Y ruled out Z" does not.

### 3. Dead-end recycling

An approach was tried and failed. After compaction the failure is gone and the
approach looks attractive again. This can loop indefinitely.

Guard: log rejections as explicitly as decisions. `Rejected: polling — rate limit is
10/min, need sub-second latency.`

### 4. Phantom completion

You report success for work done before compaction, based on the summary saying it
was done, without any surviving evidence that it was verified.

Guard: criteria are ticked only after observing the artifact. Re-verify from disk
and git state, never from the summary.

## Persist pointers, not payloads

The instinct to "save everything" backfires: bloated memory files get pulled back
into context and accelerate the next compaction.

```
Bad:   [400 lines of src/auth.ts pasted into decisions.md]
Good:  - `src/auth.ts:88-104` — token TTL hardcoded here, ignores config. Fix target.
```

Memory should be an index into the repo, not a copy of it.

## Resumption checklist

On any suspicion that history was compacted, or when resuming:

```bash
M=.kiro/skills/context-durability/scripts/memory.sh
$M status                          # goal, constraints, open criteria, next action
git status --short                 # what is actually modified
git diff --stat                    # size and shape of the change
tail -20 .kiro/.memory/decisions.md
```

Four cheap commands rebuild the working state. Do this before re-reading source.

## Interaction with the token budget

These goals cooperate more than they conflict. Persisting a conclusion once is
cheaper than re-deriving it after every compaction. Precise tool use delays
compaction, which reduces how much you lose.

But memory files are not free — they get read back. Keep them terse:

- one line per decision
- no duplicates (the script dedupes constraints, criteria, and files)
- prune criteria that turned out irrelevant rather than accumulating noise
- `status` is designed to be bounded; prefer it over `cat`-ing the whole store

## Committing memory

`.kiro/.memory/` is gitignored by default because it is scratch state for one task.

Commit it when the reasoning trail has review value — a large refactor, a
security-sensitive change, or an autonomous run a human will audit afterwards. In
that case run `memory.sh render` and commit `TASK.md`, which is written for humans.
