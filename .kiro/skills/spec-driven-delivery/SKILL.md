---
name: spec-driven-delivery
description: Use for features too large to hold in one conversation — multi-file or multi-component work, anything spanning several sessions, or work where requirements need agreement before implementation. Apply when the user asks for a spec, a plan, a design document, or phased delivery, and when a task is too ambiguous to start coding safely.
metadata:
  version: "1.0"
  part-of: claude-power
---

# Spec-driven delivery

Some features are too big to build correctly in one pass. A spec turns them into
reviewable artifacts — requirements, design, tasks — stored in `.kiro/specs/`, so
agreement happens before implementation and progress survives any session boundary.

## When a spec is worth it

Use a spec when two or more hold:

- the work spans several files, modules, or services
- it will not finish in one session
- requirements are ambiguous, or stakeholders disagree
- the design has consequences that are expensive to reverse
- someone else needs to review the approach before code exists
- you want incremental, checkpointed delivery

Do **not** write a spec for a bug fix, a small feature, or anything you can complete
and verify in one sitting. A spec for a small change is pure overhead — and a stale
spec is worse than none.

## The three artifacts

Written and agreed in order. Each answers a different question.

### Requirements — *what and why*

Behavior, not implementation. Every requirement must be testable: if you cannot write
a check that distinguishes met from unmet, it is not a requirement yet.

```markdown
## R1 — Headless login
As a CLI user on a machine with no browser, I can authenticate.

Acceptance criteria:
- [ ] `cli login` prints a user code and verification URL
- [ ] polling returns an access token and a refresh token
- [ ] an expired device code returns a distinguishable error
- [ ] the existing password flow is unaffected

Out of scope: SSO, MFA enrollment.
```

State **out of scope** explicitly. Unstated scope is where autonomous runs go wrong,
and it is the cheapest thing to get agreement on.

### Design — *how*

Only after requirements are agreed. Cover the decisions that are expensive to change:

- components and their responsibilities
- data model and migrations
- interface contracts (see `api-contract-design`)
- error handling and failure modes
- **alternatives considered and why they were rejected** — the most valuable section,
  and the one that stops the design being re-litigated later
- how each requirement will be verified

Reference live files rather than pasting code, so the spec cannot go stale:
`#[[file:src/auth/index.ts]]`.

### Tasks — *in what order*

Decompose into steps that are individually implementable and individually verifiable.

```markdown
- [ ] 1. Add device-code table + migration (R1)
- [ ] 2. Implement code generation and storage (R1)
- [ ] 3. Add polling endpoint with expiry handling (R1, R3)
- [ ] 4. Wire `cli login` to the device flow (R1)
- [ ] 5. Integration test: full flow incl. expiry (R1, R3)
```

Each task: traceable to a requirement, small enough to verify, ordered so the riskiest
assumption is tested earliest. A task nobody can verify is not a task — it is a wish.

## Working a spec

- implement **one task at a time**; do not run ahead
- verify against that task's requirement before ticking it
- tick the box only after observing the result
- if implementation reveals the design is wrong, **update the design** and say so —
  do not silently diverge. A spec that no longer matches the code actively misleads.
- mirror progress into working memory so an interruption is recoverable:
  `memory.sh next "spec task 3: polling endpoint"`

## Requirements traceability

Every task points at a requirement; every requirement is covered by tasks. This makes
two failure modes visible: work with no justification, and requirements nobody is
building. Check both before starting implementation.

## The discipline that makes specs work

**Get agreement at each stage before advancing.** The value of a spec is catching a
wrong assumption while it costs a paragraph to fix, not a rewrite. Skipping straight
to tasks discards most of the benefit.

**Keep it current or delete it.** Specs decay. If the code has moved on, update the
spec in the same change or remove it. Confidently wrong documentation is worse than
none.

**Do not gold-plate.** The spec exists to reduce risk on this feature, not to
document the system. Three tight pages beat thirty vague ones.

## Relationship to autonomous runs

A spec is the ideal input to an unattended run: ambiguity was resolved beforehand, the
task list is explicit, and each step has an acceptance criterion. If a task keeps
going wrong in Autonomous mode, the usual cause is that it needed a spec and was
started from a one-line prompt instead.
