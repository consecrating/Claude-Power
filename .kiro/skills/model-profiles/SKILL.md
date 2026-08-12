---
name: model-profiles
description: Use when choosing which model to run a task on, when the user mentions Claude Opus 5, Opus 4.8, model selection, Auto mode model choice, reasoning effort, or wants the strongest model for hard work and a cheap model for simple work. Also apply when calibrating how much planning, self-checking, and autonomy a task warrants, or when a task is going badly and may be mis-tiered.
metadata:
  version: "1.0"
  part-of: claude-power
---

# Model profiles and routing

## Read this first: what you can and cannot control

Two facts from the Kiro docs that shape everything below:

- **In Kiro Web Autonomous mode, the agent selects the model automatically. You
  cannot pick it.** There is no configuration file that overrides this.
- **Custom agents — the only mechanism with a `model` field — are not read on Web
  or Mobile.** They work in the IDE and CLI.

So a repo cannot force Autonomous mode onto Opus 5 or Opus 4.8. Anyone claiming
otherwise is guessing. What a repo *can* do:

1. Pin models where pinning is supported — IDE and CLI, via `.kiro/agents/`
   (this pack ships two such agents).
2. Make the work model-agnostic and robust, so a strong model excels and a weaker
   one still cannot silently fail — that is the job of the rest of this pack.
3. Give the human a clear routing rule for the surfaces where they *do* choose
   (`/model` in IDE/CLI, model picker in Web default mode).

## Honest limits of per-model claims

Kiro's docs list available models by display name — Claude Opus 5, Opus 4.8, 4.7,
4.6, 4.5, Sonnet 5 / 4.6 / 4.5, Haiku 4.5, and others — but they do **not** publish
per-model capability breakdowns, and model IDs are explicitly not enumerated
(discover them with `/model`).

Therefore this skill does not assert benchmark differences between Opus 5 and
Opus 4.8. It routes by **task difficulty**, which is observable, rather than by
invented model deltas.

## Routing by task shape

Choose the tier from the properties of the work, not from habit.

**Top tier (Claude Opus 5 / Opus 4.8) — use when the cost of a wrong answer
exceeds the cost of the tokens:**

- architecture and design with long-lived consequences
- debugging where the symptom is far from the cause
- concurrency, transactions, cache coherence, distributed state
- security-sensitive logic: auth, authorization, crypto, multi-tenant isolation
- large refactors that must preserve behavior across many call sites
- reconciling conflicting requirements, or deciding what to build
- anything that will run unattended for many steps

**Mid tier (Sonnet class) — well-specified work with a clear shape:**

- implementing an agreed design
- writing tests against a settled interface
- mechanical migrations with a known pattern
- documentation, formatting, straightforward CRUD

**Fast tier (Haiku class) — high volume, low ambiguity:**

- renames, import fixes, lint cleanup
- extracting a value, summarizing a file
- yes/no checks against a known rule

Between Opus 5 and Opus 4.8, prefer whichever is the newer default for genuinely
novel reasoning; treat them as interchangeable top-tier otherwise, and let cost and
availability decide. Do not manufacture a distinction you cannot measure.

## Behavioral calibration

Match your working style to the tier you are on.

**On a top-tier model:** invest in planning before acting. Hold the whole problem
at once rather than solving it piecewise. Consider two or three approaches and
record why you rejected the losers. Longer autonomous runs are justified — but
checkpoint to disk anyway, because capability does not prevent compaction.

**On a mid or fast model:** shrink the step size. Verify more often and after
smaller increments. Prefer explicit, mechanical procedures over judgement calls.
Escalate rather than guess: if a task turns out to need architectural judgement,
say so and recommend re-running on a top-tier model instead of muddling through.

## Mis-tiering: how to notice and respond

Signs the task is on too weak a model: repeated failed fixes to the same defect,
oscillating between two wrong approaches, plausible-looking code that does not
match the actual API, losing track of constraints stated one turn earlier.

Response: stop. Do not thrash — see the `error-recovery` skill. Write current state
to memory, then tell the user the task appears to need a stronger model, with the
specific evidence.

Signs of too strong a model: spending top-tier reasoning on a rename. Wasteful but
harmless; just proceed briskly rather than over-analyzing.

## Where pinning actually works

```bash
# IDE / CLI — discover the real IDs, never guess them
/model
```

Then set `model:` in a `.kiro/agents/*.md` file. This pack ships
`.kiro/agents/opus-deep.md` and `.kiro/agents/opus-lean.md` with the model field
left as a documented placeholder, because **the exact ID strings are not published**
and a wrong ID silently falls back to the default. Fill them in from `/model`.

Detail: `references/routing-policy.md`.
