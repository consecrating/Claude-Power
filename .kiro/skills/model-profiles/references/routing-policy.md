# Routing policy

## Decision table

| Signal in the task | Tier |
|---|---|
| "design", "architect", "should we", "which approach" | top |
| Bug survived one obvious fix attempt | top |
| Touches auth, permissions, crypto, tenancy, money | top |
| Concurrency, locking, ordering, idempotency, retries | top |
| Refactor spanning >10 call sites, behavior must not change | top |
| Requirements conflict or are underspecified | top |
| Unattended run of many steps | top |
| Design is settled, implementation is mechanical | mid |
| Tests for an interface that already exists | mid |
| Migration with an established pattern | mid |
| Docs, comments, formatting | mid |
| Rename, import fix, lint | fast |
| Extract one value, answer one factual question | fast |
| Bulk repetitive edits, no judgement per edit | fast |

When signals conflict, take the highest tier. Under-tiering is far more expensive
than over-tiering: a wrong architectural decision costs days, a wasted top-tier
rename costs cents.

## The economics

Top-tier tokens cost more per token but frequently cost less per *task*, because
the failure modes of under-tiering are expensive:

- rework after a wrong approach
- a subtle defect reaching production
- many turns of thrashing, each of which is also billed
- a human having to intervene and re-explain

Conversely, running a bulk mechanical edit on a top-tier model burns budget for no
gain in correctness.

The economical policy is therefore **not** "always use the cheapest model." It is:
spend on judgement, economize on mechanics.

## Escalation protocol

When mid-tier work turns out to require judgement:

1. Stop before the third failed attempt at the same thing.
2. Persist state: `memory.sh note "escalating: <what>, evidence: <what failed>"`.
3. Report to the user: what the task turned out to require, what was tried, and
   the recommendation to re-run on a top-tier model.

Do not silently keep trying. Repeated failure on the same defect is information —
surface it.

## De-escalation

Once a top-tier model has produced the design and it is written down, the
implementation is mid-tier work. Hand it off:

- record the design in `.kiro/.memory/decisions.md` or a spec under `.kiro/specs/`
- make the remaining steps mechanical enough that they do not need re-derivation

This is the highest-leverage cost optimization available: use the expensive model
to *remove ambiguity*, then execute cheaply. Ambiguity is what costs money.

## Filling in model IDs

Model IDs are not published in Kiro's documentation, and an unrecognized ID falls
back to the default model with a warning — a silent behavior change. Never guess.

```bash
/model                    # IDE or CLI: lists the IDs actually available to you
```

Copy the exact string into the agent file:

```yaml
---
description: Deep reasoning agent
model: <paste-exact-id-from-/model>
---
```

Verify it took effect rather than assuming: switch to the agent and confirm no
fallback warning appeared.

## Autonomous mode reality check

On Kiro Web Autonomous mode the model is chosen for you and cannot be pinned. Design
accordingly:

- do not write instructions that depend on being on a specific model
- make correctness enforced by procedure and verification, not by model strength
- keep step sizes small enough that a mid-tier model would also succeed
- rely on on-disk memory rather than long-range in-context recall

A configuration pack that only works on the strongest model is a fragile pack. The
rest of this repo is written to that standard.
