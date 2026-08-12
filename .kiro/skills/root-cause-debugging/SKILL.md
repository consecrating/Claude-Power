---
name: root-cause-debugging
description: Use when something is broken, failing, erroring, crashing, flaky, or behaving unexpectedly, and when a first obvious fix did not work. Apply for stack traces, failing tests, incorrect output, intermittent failures, regressions, and "it works locally but not in CI". Enforces reproduce, isolate, hypothesize, fix the cause, prove it, rather than patching symptoms.
metadata:
  version: "1.0"
  part-of: claude-power
---

# Root-cause debugging

Most failed debugging is a category error: changing code to make a symptom go away
without ever explaining the symptom. If you cannot say *why* the bug happened, you
have not fixed it — you have moved it.

## The loop

### 1. Reproduce deterministically

No reproduction, no debugging. Everything after this step depends on being able to
tell whether the bug is present.

- get the exact failing command and its exact output
- reduce to the smallest input that still fails
- for intermittent bugs, find the condition that makes it reliable (ordering,
  concurrency, cache state, clock, locale, leftover data) before touching code

If it only fails in CI, the difference *is* the bug's habitat: compare env vars,
versions, working directory, parallelism, and whether state leaks between tests.

### 2. Read the actual error

Read the whole trace, not the first line. Specifically identify:

- the deepest frame **in your own code** — usually where to look, not the library frame
- the actual vs expected values, precisely
- whether the error is the *first* error or a downstream consequence of an earlier one

An error swallowed and re-raised elsewhere is a common time sink. Find the origin.

### 3. Bisect the distance between cause and symptom

The symptom's location is rarely the cause's location. Narrow the gap:

```bash
git log --oneline -15 -- path/to/suspect        # did this change recently?
git bisect start <bad> <good>                   # for a genuine regression
```

Or bisect the data path: at what point does the value stop being correct? Check the
midpoint, not every step.

### 4. Form a falsifiable hypothesis

State it out loud, in this shape:

> "X fails because *specific mechanism*. If true, then *specific observable*
> should be true. I will check it by *specific cheap test*."

A hypothesis that cannot be wrong is not a hypothesis. "Something's off with the
config" is not one; "the config loader reads `PORT` before `.env` is loaded, so it
gets the default" is.

### 5. Test the hypothesis, not the fix

Confirm the mechanism before writing a fix. Cheapest first: read the code path,
print one value, check one log line. Do not restructure code to test an idea.

If the hypothesis is wrong, that is progress — you have eliminated a branch. Discard
it explicitly and form the next one. Do not keep a disproven hypothesis alive because
you liked it.

### 6. Fix the cause

Fix at the level where the wrong decision is made — not where it surfaces.

| Symptom fix (wrong) | Cause fix (right) |
|---|---|
| add a null check at the crash site | find why it is null and stop it being null |
| wrap in try/catch and continue | handle the actual failure condition |
| add a retry | fix the race, or make the operation idempotent |
| add a `sleep` | wait on the real condition |
| loosen an assertion | make the behavior match the assertion |
| special-case the failing input | fix the general handling that excludes it |

Defensive checks are legitimate as *defense in depth* — but never as the explanation.
If you add one, you must still be able to say what went wrong.

### 7. Prove it

- the reproduction from step 1 now passes
- add a regression test that **fails without your fix** — verify that by reverting
  the fix, or by writing the test first and watching it fail
- the surrounding suite still passes
- explain the mechanism in one sentence

A test you never saw fail is not known to test anything.

## Stop-and-rethink triggers

- two fixes attempted, symptom unchanged → your model of the system is wrong; go
  back to step 1 and re-verify assumptions rather than trying a third fix
- the fix works but you cannot explain why → not finished; you likely moved the bug
- you are changing more than a few lines to fix a small defect → you may be fixing
  the wrong thing
- you find yourself adding logging everywhere → bisect instead

Thrashing has a real cost and produces nothing. See `error-recovery`.

## Persist the trail

```bash
M=.kiro/skills/context-durability/scripts/memory.sh
$M note "Repro: npm test -- t/order.spec.ts -t 'applies discount'"
$M note "Ruled out: rounding — values are correct until repo/order.ts:88"
$M note "Cause: discount applied before tax; spec requires after"
```

Recording ruled-out hypotheses is what stops you re-testing them after compaction.
