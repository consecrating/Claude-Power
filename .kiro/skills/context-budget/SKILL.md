---
name: context-budget
description: Use when a Kiro config feels slow or expensive, when adding or removing skills and steering, when a skill that should have triggered did not, or when asked what the config costs per session. Measures the standing token charge paid before any work happens, and detects skills whose descriptions compete for the same requests.
metadata:
  version: "1.0"
  part-of: claude-power
---

# Context budget

Skill bodies load on demand, so it is tempting to treat installing a skill as
free. It is not. Every skill's **name and description** load at session start,
and `inclusion: always` steering loads **in full**, every session. That is a
standing charge paid before you type anything, and nothing measures it.

Two questions this answers:

1. **What does this config cost before any work happens?**
2. **Can the right skill still be selected?** Skills are chosen by matching a
   request against descriptions. Two skills describing the same territory do not
   give you two options; they give you a coin flip, and the loser silently never
   runs.

```bash
python3 .kiro/scripts/context-budget.py --root .
```

Offline, dependency-free, and free. Add `--exact` for exact counts via the
unbilled `count_tokens` endpoint.

## Reading the output

```
  layer                                   tokens  cost
  per turn (AGENTS.md)                      ~622  $0.0031
  per session (startup)                   ~7,514  $0.0376
  on demand (not paid until triggered)  ~373,484  -
```

| Layer | When you pay | What to do about it |
|---|---|---|
| per turn | **every message** | keep `AGENTS.md` small; this is the most expensive line in the file |
| per session | every session start | prune skills, move always-steering to `fileMatch` |
| on demand | only when triggered | largely free — do not optimise this first |

The monthly projection multiplies the per-session charge by your session rate.
It is the number worth acting on, because the standing charge recurs whether or
not the session does any work.

## What it flags

| Code | Level | Meaning |
|---|---|---|
| `skill-no-description` | error | installed but can never activate — pure dead weight |
| `no-skill-md` | error | directory with no `SKILL.md`; never loads |
| `filematch-no-pattern` | error | `fileMatch` with no pattern, so it can never trigger |
| `reserved-steering` | error | `product.md` / `tech.md` / `structure.md` belong to the project |
| `description-collision` | warn | two skills compete for the same requests |
| `skill-name-mismatch` | warn | directory and declared `name` disagree |
| `desc-too-long` | warn | large description, charged every session |
| `desc-too-short` | warn | too little signal to match requests reliably |
| `fat-always-steering` | warn | large `always` steering; consider `fileMatch` |
| `nearest-descriptions` | info | closest pairs when none crossed the threshold |

Exit codes: `0` clean, `1` an error or the budget exceeded, `2` bad arguments.
`--strict` also fails on warnings.

## Use it as a gate

The point of a budget is that something enforces it. Otherwise the number in the
README drifts from the number on disk, and nobody notices which is real.

```bash
python3 .kiro/scripts/context-budget.py --root . --budget 2500
```

Fails when the per-session charge exceeds 2,500 tokens. Wire it into CI so
adding a skill has to be paid for deliberately.

## When a skill did not trigger

Check for a collision first. `description-collision` means two descriptions
overlap enough that a matching request picks unpredictably — the usual cause of
"why did it use the wrong skill". The fix is to narrow one description so the
two stop competing, not to add words to both.

Also check `skill-name-mismatch`: if the directory says `taste-skill` but the
file declares `name: design-taste-frontend`, the declared name is what Kiro
uses, and referring to the directory name will not find it.

## Interpreting the numbers honestly

- Counts are **estimates** unless `--exact` was passed, and are marked `~`.
  Typically within ~10-15%. Use `--exact` for a number you will act on; it is
  unbilled.
- The collision detector compares **content-word overlap**, not meaning. It will
  miss two differently-worded descriptions covering the same ground, and can
  flag two that merely share vocabulary. Read the pair before deleting anything.
- Pricing comes from `opus5lean` (Claude-Opus5) when installed; otherwise a
  fallback rate is used and the report says so.

## Reducing the charge

In order of payoff:

1. **Delete skills you do not use.** Each costs its description every session,
   forever. This is the only change that scales.
2. **Move `always` steering to `fileMatch`.** A 1,000-token always-on file is
   usually a few hundred tokens of rules that matter plus a reference section
   that could load on demand.
3. **Shorten long descriptions.** Keep the trigger conditions, cut the feature
   list. The body is where detail belongs — it is free until activated.
4. **Trim `AGENTS.md` last but hardest.** It is per *turn*, so it is multiplied
   by conversation length, not session count.
