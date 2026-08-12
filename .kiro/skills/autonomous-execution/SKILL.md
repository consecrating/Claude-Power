---
name: autonomous-execution
description: Use when running in Kiro Autonomous or Auto mode, when working unattended for many steps, when asked to take a task end to end and open a PR, or when the user will not be available to answer mid-run. Defines the clarify, plan, execute, verify, deliver loop and the discipline that keeps a long unattended run from drifting, thrashing, or over-reaching scope.
metadata:
  version: "1.0"
  part-of: claude-power
---

# Autonomous execution

Unattended runs fail differently from interactive ones. Nobody catches a wrong
assumption at step 3, so it compounds until step 40. The countermeasures are:
front-load ambiguity resolution, persist state, keep steps verifiable, and stop
rather than guess.

## Phase 1 — Clarify, before doing anything

In Autonomous mode your clarifying questions are the *only* steering you will get,
and answers act as constraints for the whole task. Ask them up front; there is no
cheap mid-run correction.

Ask when any of these is genuinely unclear and the answer changes the work:

- scope boundaries: which files, services, or behaviors are in and out
- acceptance criteria: what observable result means done
- constraints: what must not change; compatibility requirements
- conflicts: two stated requirements that cannot both hold
- destructive intent: anything touching production, data, auth, or infrastructure

Do not ask about things you can determine yourself from the repo. Reading a config
file is cheaper than a round trip. Ask about *intent*, never about *facts*.

Then persist the answers immediately:

```bash
M=.kiro/skills/context-durability/scripts/memory.sh
$M init "<the goal in the user's own words>"
$M constraint "<each hard limit>"
$M criterion "<each acceptance criterion>"
```

## Phase 2 — Plan

Produce a plan with explicit acceptance criteria before editing anything. A plan is
useful only if it is falsifiable: each step should have an observable outcome.

- order steps so the riskiest assumption is tested earliest and cheapest
- prefer many small verifiable steps over few large ones
- identify the reversal path for anything destructive
- for genuinely large features, use a spec under `.kiro/specs/` instead of an
  in-chat plan — see the `spec-driven-delivery` skill

If planning reveals the task is underspecified in a way that matters, go back to
Phase 1. Discovering this now is cheap; discovering it at step 40 is not.

## Phase 3 — Execute

Work the plan one step at a time, and after each step:

1. verify the step's observable outcome (not just the exit code)
2. record the file touched and why: `$M file <path> "<why>"`
3. update the next action: `$M next "<what follows>"`
4. log any decision that closed off alternatives: `$M note "<decision> — <why>"`

Hold to the token discipline throughout — see `token-efficiency`. Unattended runs
are long, so waste compounds and accelerates compaction.

**Scope control.** You will notice unrelated problems: dead code, weak tests, a
sloppy pattern. Note them for the final report; do not fix them. Scope creep in an
unattended run produces an unreviewable diff, which is worse than the untouched
flaw. The exception is when the task genuinely cannot be completed without the fix —
then log the reason before doing it.

**Blocked?** Do not thrash. Two failed attempts at the same thing means stop and
change approach; see `error-recovery`. Repeatedly retrying the same failing action
burns credits and produces nothing.

## Phase 4 — Verify

Verification is a distinct phase, not a feeling. Apply the `verification-discipline`
rules in full:

```bash
$M verify                       # gaps in recorded state
git status --short              # nothing unintended changed
git diff --stat                 # the diff is the size it should be
```

Then walk `criteria.md` and check each criterion against the real artifact —
reading the file, running the test, hitting the endpoint. Tick each only when
observed: `$M check "<criterion substring>"`.

Any criterion you cannot verify stays unticked and gets reported as unverified.
Never tick a criterion because the plan said it would be done.

## Phase 5 — Deliver

Push to a branch and open a PR — on Web the PR is the human's review surface, and
they cannot see your terminal or filesystem.

```bash
git checkout -b <descriptive-branch>
git add <specific files>          # named files, not -A
git commit -m "<imperative subject>"
git push -u origin <branch>
gh api repos/{owner}/{repo}/pulls \
  -f title="..." -f body="..." -f head="<branch>" -f base="main" --jq '.html_url'
```

Check for an existing PR first; if one is merged or closed, branch anew rather than
reusing it. See the `pr-craft` skill for commit and description standards.

## The final report

State, in this order:

1. what was done, and where to review it (the PR link)
2. each acceptance criterion: verified / failed / **unverified, and why**
3. decisions made on the user's behalf, with rationale — especially any assumption
   filled in without asking
4. problems noticed but deliberately left out of scope
5. what remains, if anything

Never end an unattended run with an unqualified "done" when criteria are unverified.
An honest partial result is actionable; a false completion costs the user their trust
and their time.

## Standing rules for unattended work

- **Never** force-push, hard-reset, delete branches, or rewrite history unasked.
- **Never** push directly to `main`.
- **Never** commit secrets. If you must read one, reference it by key name only.
- Prefer the contained option: project-local over global, additive over destructive,
  backup before overwrite.
- High-risk actions — production changes, data deletion, auth or access-control
  changes, infrastructure edits, anything bulk or recursive — are stop-and-ask, even
  in Autonomous mode. Autonomy is permission to work unsupervised, not permission to
  take irreversible actions the user did not sanction.
