---
name: self-improvement
description: Use when the user corrects you, expresses frustration, repeats an instruction they already gave, rejects an approach, or says to remember, always, never, or from now on. Also apply after finishing a task that went badly, after PR review feedback, or when you notice you have made the same class of mistake twice. Converts one-off corrections into durable rules stored in steering and skills.
metadata:
  version: "1.0"
  part-of: claude-power
---

# Self-improvement

A correction you only apply once is a correction you will need again. The point of
this skill is to convert feedback into configuration.

## Trigger signals

Act on any of these:

- explicit: "remember", "always", "never", "from now on", "going forward"
- repetition: the user tells you something they already told you
- rejection: an approach is thrown out, or a diff is reverted
- friction: "no", "that's not what I asked", "you did it again"
- review: a PR comment about style, structure, or convention
- self-observed: you catch yourself repeating a mistake

## Classify before capturing

Ask: **would this apply to a different task next month?**

- **No — task-specific.** Belongs in `.kiro/.memory/` for this task only. Do not
  promote it. (`memory.sh constraint "..."`)
- **Yes, and repo-specific.** Belongs in `.kiro/steering/` in this repository.
- **Yes, and applies across repositories.** Belongs in a global learning — on Kiro
  Web, learnings are additionally derived from your PR review comments and applied
  to future work across your repos.

Misclassification is the common failure: a one-off preference promoted to
always-on steering taxes every future turn forever.

## Write rules that actually change behavior

A rule must be specific, testable, and state the trigger condition.

| Weak | Strong |
|---|---|
| "Write better commit messages." | "Commit subject: imperative mood, ≤50 chars, no trailing period." |
| "Be careful with the database." | "Never run a migration without first printing the generated SQL for approval." |
| "Prefer functional style." | "In `src/core/**`, no classes — export pure functions; classes are allowed only in `src/adapters/**`." |
| "Don't waste tokens." | "Never `cat` a file >200 lines; use `rg -n` then read the specific range." |

Include the *why* when it is non-obvious. A rule whose rationale is recorded
survives future pressure to break it; a bare prohibition gets rationalized away.

## Choose the cheapest placement that works

Every promotion has a permanent token cost. Push rules as far down this list as
possible:

1. `.kiro/skills/<relevant-skill>/` — add to an existing skill body or reference.
   Costs nothing until the skill activates. **Prefer this.**
2. `.kiro/steering/*.md` with `inclusion: fileMatch` — costs nothing unless
   matching files are in play. Ideal for language- or directory-specific rules.
3. `.kiro/steering/*.md` with `inclusion: auto` — costs a description always, body
   on match. Good for situational rules.
4. `AGENTS.md` or `inclusion: always` — costs on every single turn. Reserve for
   rules that are genuinely universal and safety-relevant.

Before adding anything, check whether an existing file already covers it. Amending
an existing rule is almost always better than adding a competing one.

## Capture, then promote

Capture immediately (cheap, reversible); promote deliberately.

```bash
L=.kiro/skills/self-improvement/scripts/capture-learning.sh

$L add "Never cat files over 200 lines; rg -n then read the range" token-efficiency
$L add "Migrations require printed SQL before running" repo
$L list                    # review the inbox
$L promote 2               # print placement guidance for entry 2
```

The inbox is `.kiro/.learnings/inbox.md`, gitignored. Promotion is a deliberate
edit to a steering file or skill — the script advises, it does not auto-edit,
because uncontrolled promotion is how configuration rots.

## Keep the config healthy

Self-improvement includes pruning. Periodically:

- delete rules that no longer apply — stale rules actively mislead
- merge duplicates and near-duplicates
- move anything that outgrew its placement further down the cost list
- if two rules conflict, resolve it explicitly rather than leaving both

A skill or steering file that has grown past roughly 150 lines should be split, with
depth moved into `references/`.

## Closing the loop with the user

When you capture a learning, say so in one line: what rule, where it went. This lets
the user correct a bad generalization immediately — much cheaper than discovering
next month that you over-generalized from a single remark.

Do not silently rewrite steering based on ambiguous feedback. If you are unsure
whether a correction is a one-off or a standing rule, ask.
