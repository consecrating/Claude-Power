---
name: error-recovery
description: Use when your own actions keep failing, when you have retried something more than once, when you are stuck or looping between approaches, when a command fails in an unexpected way, or when you are unsure whether to keep going or stop and ask. Prevents thrashing, defines when to back out versus push on, and governs how to report being blocked.
metadata:
  version: "1.0"
  part-of: claude-power
---

# Error recovery

This skill is about *your* failures, not defects in the code under test. Its purpose
is to stop the most expensive agent failure mode: repeating a failing action with
minor variations until the budget is gone.

## The two-strike rule

**One failure**: read the error properly and correct it. Retrying with a real fix is
fine.

**Two failures at the same thing**: stop. Do not attempt a third variation. Two
failures mean your model of the situation is wrong, and the third attempt is
guessing. Change something structural instead:

- verify an assumption you have not actually checked
- try a different mechanism, not a different spelling
- reduce scope to something you can confirm works, then build up
- ask the user

The distinction that matters: **fixing** is informed by the error; **thrashing**
ignores it. If you cannot say what the error told you, you are thrashing.

## Read the failure before reacting

Most agent retry loops come from skimming. Extract these before acting:

- Is this the error I expected, or a different one? A *changed* error is progress.
- Is it my command that is wrong, or the thing it operates on?
- Is it environmental — missing tool, no network, no permission, wrong directory?
- Does it say what to do? Many tools print the fix; read to the end of the message.

```bash
command -v <tool> || echo "tool not installed"     # rule out environment first
pwd && ls -d ./*/ | head                            # rule out wrong directory
```

Environment failures are not fixed by retrying. Detect them and adapt.

## Diagnose before escalating effort

When stuck, the instinct is to do *more*. Usually the answer is to do *less*, with
more certainty. Shrink to a known-good state and take one small step:

```bash
# Does the smallest possible version work?
npx tsc --noEmit path/to/one/file.ts
npm test -- -t 'the one test'
```

If the small version fails too, you have a much cheaper reproduction. If it passes,
the problem is in what you added — bisect it.

## Backing out

Undo when your changes have made the state harder to reason about. A clean revert
plus one careful attempt beats layered half-fixes.

```bash
git diff --stat                       # what am I carrying?
git stash                             # park it, keep it recoverable
git checkout -- path/to/file          # discard one file's changes
```

Rules: never `reset --hard`, never `clean -fd`, never force-push to recover. Those
destroy work you cannot get back. Prefer `stash` — reversible.

If you revert something the user asked for, say so explicitly.

## When to stop and ask

Stop and ask when continuing means guessing about intent, or when the next step is
irreversible:

- the request is ambiguous in a way that changes the outcome
- two requirements conflict and you would have to pick
- the fix requires a decision the user owns (schema change, dependency, API break)
- you would need to touch production, delete data, or change auth/access control
- credentials or access you do not have
- two failed attempts and no new hypothesis

Asking costs one cheap turn. Guessing wrong costs the whole task, plus the user's
time reviewing something they did not want.

## How to report being blocked

A good blocked report is actionable in one read. Include:

1. **What I was trying to do** — the specific step
2. **What happened** — the actual error, trimmed to the signal
3. **What I ruled out** — so the user does not suggest it
4. **What I think is going on** — best hypothesis, labelled as hypothesis
5. **What I need** — a decision, access, or information; be specific

Bad: "I'm having trouble getting the tests to pass."

Good: "`npm test` fails at `db.connect` with `ECONNREFUSED 5432`. Not a code issue:
`pg_isready` shows no local Postgres and there is no docker-compose service. Ruled
out config — `DATABASE_URL` is set correctly. I need either a running database or
your preference for mocking the repository layer in these tests."

## Persist before you stop

Being blocked is exactly when state is most likely to be lost:

```bash
M=.kiro/skills/context-durability/scripts/memory.sh
$M note "BLOCKED: no local Postgres; ECONNREFUSED at db.connect"
$M note "Ruled out: DATABASE_URL config, node version"
$M next "await user decision: provision DB or mock repo layer"
```

## Never do these

- Do not report success after failures you could not resolve. Say what failed.
- Do not silently drop part of the task because it was hard. Report it.
- Do not disable, skip, or delete a test to make a suite pass. That converts a
  visible failure into an invisible one — the single worst trade available.
- Do not widen permissions, add `|| true`, or suppress errors to get past a failure.
- Do not keep retrying a network or credential failure. It will not fix itself.
