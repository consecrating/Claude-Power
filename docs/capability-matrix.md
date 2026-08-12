# Capability matrix

What in this pack actually works on which Kiro surface. Based on Kiro's published
configuration documentation. Anything not confirmed is marked as such rather than
assumed.

## Configuration support by surface

| Config | IDE | CLI | Web | Mobile |
|---|:--:|:--:|:--:|:--:|
| Project steering `.kiro/steering/` | ✓ | ✓ | ✓ | ✓ |
| Project skills `.kiro/skills/` | ✓ | ✓ | ✓ | ✓ |
| Specs `.kiro/specs/` | ✓ | ✓ | ✓ | ✓ |
| `AGENTS.md` | ✓ | ✓ | ✓ | ✓ |
| Custom agents `.kiro/agents/` | ✓ | ✓ | — | — |
| Hooks `.kiro/hooks/` | ✓ | ✓ | — | — |
| Permissions | ✓ | ✓ | — | — |
| Global `~/.kiro/` | ✓ | ✓ | — | — |
| Steering inclusion modes | ✓ | see note | ✓ | ✓ |
| Skill slash commands | ✓ | ✓ | coming soon | — |
| Manual compaction (`/compact`) | — | ✓ | — | — |
| Automatic compaction | ✓ | ✓ | ✓ | ✓ |

**CLI note:** on Kiro CLI, steering inclusion modes are not currently supported —
every file in `.kiro/steering/` loads automatically. This pack keeps only two steering
files, and both are cheap, specifically so that CLI's load-everything behavior does not
blow up the budget.

**Web and Mobile read only project-scope config committed to the repository.** There is
no local filesystem, so `~/.kiro/` does not exist there. Everything in this pack that
matters is therefore project-scoped.

## This pack, component by component

| Component | Works on Web / Auto mode? | Notes |
|---|:--:|---|
| `AGENTS.md` | ✓ | always loaded, every surface |
| 16 skills | ✓ | automatic activation by description match |
| `references/` files | ✓ | loaded on demand from a skill body |
| `scripts/*.sh` | ✓ | run via shell, so they work wherever bash does |
| `verification-discipline` steering | ✓ | `inclusion: auto` |
| `kiro-config-authoring` steering | ✓ | `inclusion: fileMatch` |
| `.kiro/agents/opus-5.md` | ✗ | IDE / CLI only |
| `.kiro/agents/opus-4-8.md` | ✗ | IDE / CLI only |
| `.kiro/hooks/claude-power.json` | ✗ | IDE / CLI only |
| `validate-config.sh` | ✓ | plain bash; also runs in CI |

The design consequence: **nothing essential depends on hooks or agents.** They only
optimize behavior that already works through skills and steering. No skill in this pack
assumes a hook has fired.

## Autonomous mode specifics

Documented facts:

- Autonomous mode is toggled in the chat input bar before submitting; off by default.
- Phases: clarification → planning → execution → completion. It asks clarifying
  questions up front, and **your answers act as the steering for that task.**
- It delegates to sub-agents and can open one or more PRs — though it will not always
  open one.
- **The model is selected automatically and cannot be chosen.**
- If it needs input mid-run, the task enters a *Needs attention* state.
- PR comment commands: `/kiro all`, `/kiro fix`.
- Feedback in PR comments from the task creator becomes learnings applied to future
  work across your repositories.

**Not documented / could not confirm:** whether steering, skills, or context handling
behave any differently in Autonomous mode versus default mode. Nothing in Kiro's docs
states a difference, so this pack assumes they load identically and does not rely on any
mode-specific behavior.

Terminology note: Kiro's current Web docs call the non-autonomous mode "default mode".
"Vibe mode" appears in some Kiro clients but not in the Web documentation.

## Compaction behavior

| | IDE | CLI | Web | Mobile |
|---|:--:|:--:|:--:|:--:|
| Automatic compaction | ✓ | ✓ | ✓ | ✓ |
| Manual `/compact` | — | ✓ | — | — |
| Context usage meter | ✓ | ✓ | ✓ | ✓ |

**Reliably preserved:** task status, paths of modified files, key decisions and
constraints, next steps, your stated intent.

**At risk:** individual tool call results, intermediate reasoning, earlier code
snippets, details of resolved errors, exploratory discussion.

Compaction is **one-way**. This is the entire justification for the
`context-durability` skill: conclusions tend to survive, evidence tends not to, so
evidence and rationale get written to disk.

There is **no documented `.kiro/` memory or session-persistence feature.** The
`.kiro/.memory/` directory used by this pack is a convention implemented by
`memory.sh`, not a Kiro feature. It works because it is just files.

## Model IDs

Kiro's docs list available models by **display name** — including Claude Opus 5 and
Claude Opus 4.8 — but **do not publish the ID strings** used by the `model` field.
They direct you to `/model` to discover them.

An unrecognized ID falls back to the default model with a warning. That is a silent
behavior change, which is why both agent files in this pack ship with `model:`
commented out rather than guessed.

## Verification

Everything in this table that concerns *this pack* is enforced by
`.kiro/scripts/validate-config.sh` and `.kiro/scripts/validate-frontmatter.py`, which
run in CI on every push. Claims about *Kiro's own* behavior come from its published
documentation and are labelled unconfirmed where the docs are silent.
