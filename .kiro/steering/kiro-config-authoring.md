---
inclusion: fileMatch
fileMatchPattern:
  - ".kiro/skills/**/SKILL.md"
  - ".kiro/steering/**/*.md"
  - ".kiro/agents/**/*"
  - ".kiro/hooks/**/*.json"
  - "AGENTS.md"
---

# Authoring Kiro configuration

Loads only when editing Kiro config. Zero cost otherwise — that is the point.

## The token contract

Every file has a load cost and a load trigger. Choose the trigger to match value:

| Mechanism | Loaded | Cost |
|---|---|---|
| `AGENTS.md` | every turn, always | highest — treat as a hard budget |
| steering `inclusion: always` | every turn | highest |
| steering `inclusion: fileMatch` | only when matching files are in play | ~free |
| steering `inclusion: auto` | name + description always; body on match | low |
| steering `inclusion: manual` | only on `#file-name` | ~free |
| skill `SKILL.md` | name + description always; body on activation | low |
| skill `references/*`, `scripts/*` | only when the body points to them | ~free |

Rule: **push detail down the table.** If content is not needed on literally
every turn, it does not belong in an always-loaded file.

## Reserved filenames — do not create

`product.md`, `tech.md`, `structure.md` are foundation steering names that Kiro
loads into every interaction and that the *host* repository owns. This pack must
never ship them or it will overwrite a consumer's own project context. Use
distinct, prefixed names.

## Steering frontmatter

Frontmatter must be the very first bytes of the file — no leading blank line or
comment. Only four fields exist:

- `inclusion` — `always` (default) | `fileMatch` | `auto` | `manual`
- `fileMatchPattern` — required with `fileMatch`; string or array of globs
- `name`, `description` — both **required** with `auto`; `description` is what
  gets matched against the user's request, so write it as trigger conditions

Do not invent other fields. Reference live files with `#[[file:relative/path]]`.

## Skill frontmatter

- `name` — **must equal the folder name**; lowercase, digits, hyphens; max 64 chars
- `description` — max 1024 chars; state *when to use*, not what it is
- optional: `license`, `compatibility`, `metadata`

`SKILL.md` is loaded in full on activation, so keep the body actionable and move
depth into `references/`. Prefer a `scripts/` entry point for anything
deterministic — a script is cheaper and more reliable than prose the model must
re-derive each time.

## Writing descriptions that trigger correctly

The `description` is a router, not a summary. Include the words a user would
actually type and the situations that should activate it.

- Weak: "Best practices for efficient token usage."
- Strong: "Use when a task involves reading files, searching code, inspecting
  git history, running builds, or processing JSON/YAML — anything where output
  size drives cost. Apply for requests mentioning tokens, credits, cost, speed,
  context limits, or large outputs."

## Hooks and agents portability

`.kiro/hooks/` and `.kiro/agents/` are **not read on Kiro Web or Mobile**. Anything
essential to correct behavior must therefore live in skills or steering; hooks and
agents may only *optimize* what already works. Never make a skill depend on a hook
having fired.

Prefer hook `action.type: "command"` over `"agent"` — an agent action starts a new
model loop and consumes credits, a command action does not.
