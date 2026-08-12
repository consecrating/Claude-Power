# Roadmap — what else this repo could add

Prioritized by value per unit of effort. Nothing here is required for the pack to
work today.

---

## Tier 1 — highest value, small effort

### 1. A `LICENSE` file
The repo is public with no license, which technically means nobody may reuse it. MIT
or Apache-2.0. **Blocking for public sharing.**

### 2. An install script
`cp -r` in a README is error-prone: it silently clobbers an existing `AGENTS.md` and
forgets `chmod +x`. A real `install.sh` should:

- detect an existing `AGENTS.md` and offer to merge rather than overwrite
- refuse to overwrite existing steering files without `--force`
- append the three `.gitignore` entries idempotently
- set the executable bits
- run the validator and report
- support `--skills-only` and `--minimal` (core 5 only) for budget-conscious installs

### 3. A tuned `.kiroignore`
Keep the agent out of `node_modules`, `dist`, lockfiles, snapshots, `.min.js`, and
build caches. This is the single cheapest token win available and it is currently
absent — it prevents wasteful reads structurally rather than by asking nicely.

### 4. Language-specific `fileMatch` steering
The cheapest possible steering: zero cost unless matching files are open.
Candidates: `typescript.md`, `python.md`, `go.md`, `rust.md`, `sql.md`,
`terraform.md`, `dockerfile.md`, `react.md`. Each carries local idioms, the project's
lint rules, and the actual test command.

---

## Tier 2 — high value, moderate effort

### 5. A skill scaffolder
`.kiro/scripts/new-skill.sh <name>` that creates the folder, a `SKILL.md` with valid
frontmatter, `references/`, and runs the validator. Removes the most common authoring
mistakes (folder/name mismatch, frontmatter not at byte 0).

### 6. Golden-prompt regression tests
The real gap in this pack: **nothing verifies that skills actually activate.** A test
harness would keep a table of prompts mapped to the skills that should trigger, and
flag descriptions that stop matching after an edit. Descriptions are routers; right
now they are untested routers.

### 7. Spec templates
`.kiro/specs/_templates/` with `requirements.md`, `design.md`, `tasks.md` skeletons
matching the `spec-driven-delivery` skill, so specs start consistent.

### 8. A `docs/` steering example set
A worked example of this pack applied to a real repo — a filled-in `product.md`,
`tech.md`, `structure.md` shown as *examples* (never shipped as live config, since
those names belong to the host repo).

### 9. More reference recipe books
`token-efficiency/references/` currently covers shell, git, and JSON. Worth adding:
Docker/Kubernetes inspection, cloud CLIs (`aws`, `gcloud`) with `--query`/`--format`
projections, and database introspection — all areas where the default output is
enormous.

---

## Tier 3 — valuable, larger effort

### 10. An MCP server bundle
`.kiro/settings/mcp.json` presets for common servers, with a note that Web configures
sandbox MCP through its own settings rather than this file.

### 11. Cost telemetry
A `Stop` hook that appends turn count and elapsed time to a local log, giving a real
before/after measurement of the token discipline instead of an estimate. Must stay a
`command` action so it costs no credits.

### 12. Prompt-injection defense skill
Rules for handling untrusted content — fetched web pages, issue bodies, PR
descriptions, tool output — as data rather than instructions. Increasingly relevant
for autonomous runs that read external input.

### 13. Observability / incident-response skill
Structured logging, useful error context, metrics that answer questions, and a triage
loop for production incidents. Deliberately omitted so far because it overlaps
`root-cause-debugging`; it earns its own skill only if the split is kept clean.

### 14. Data-migration safety skill
Backfills, zero-downtime schema changes, expand/contract at the database level,
reversibility, and dry-run discipline. High-consequence work that the current pack
only touches obliquely.

### 15. Accessibility and frontend-quality skill
Semantic HTML, keyboard navigation, ARIA only where needed, contrast, focus
management. Valuable for any UI repo and genuinely distinct from the current 16.

---

## Deliberately not planned

**Rules restating what the model already does well.** Every always-on line is paid
forever. The pack is intentionally small in its always-on layer, and padding it with
generic advice ("write clean code") would make it worse, not better.

**More `inclusion: always` steering.** Two steering files, neither always-on, is a
feature. New rules should go into skills or `fileMatch` steering.

**A skill per language or framework.** That is what `fileMatch` steering is for, at a
fraction of the cost. Skills are for procedures, not for facts about a syntax.

**Auto-promoting learnings into steering without review.** Uncontrolled promotion is
exactly how a config pack rots into an expensive, self-contradictory prompt.
`capture-learning.sh` advises; a human decides.

---

## Known gaps in the current pack

Stated plainly so they are not discovered as surprises:

1. **Skill activation is unverified.** Descriptions are written to be good routers but
   nothing tests that they route. See item 6.
2. ~~`shellcheck` unavailable.~~ **Closed.** All three scripts pass
   `shellcheck -S warning` with zero findings, pass `bash -n`, and were executed end
   to end. The one info-level `SC2016` in `memory.sh` is a false positive (literal
   markdown backticks in a `printf` format string) and carries a documented
   `disable` directive.
3. **Hook behavior is untested.** Hooks do not run on Kiro Web, so the four in
   `.kiro/hooks/` were validated for schema conformance only — never observed firing.
4. **Model pinning is unproven.** Both agent files intentionally leave `model:` unset
   because the ID strings are not published. Nobody has yet confirmed a working ID.
5. **No CHANGELOG or versioning.** Skills carry a `metadata.version` field, but the
   pack as a whole has no release process.
