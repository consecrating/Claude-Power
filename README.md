# Claude-Power

A Kiro configuration pack: **16 skills**, 2 steering rules, 2 custom agents, 4 hooks,
2 validated helper scripts, and 1 MCP server. Built to make Kiro — including **Autonomous (Auto)
mode** — token-frugal, resistant to context loss in long sessions, model-aware, and
able to turn your corrections into durable rules.

Everything here is checked against Kiro's documented schemas by
`.kiro/scripts/validate-config.sh`, which runs clean.

---

## Read this before anything else: what is actually possible

Three of the four things this repo was asked to do are fully achievable. One is not,
and it would be dishonest to ship config that pretends otherwise.

| Goal | Status | Reality |
|---|---|---|
| Minimal tokens / credits | ✅ Done | `opus5-lean` MCP server + `token-efficiency` skill. Real optimization tools. |
| Don't forget things in long chats | ✅ Done | `context-durability` skill + `memory.sh`. Compaction is automatic and **irreversible**, so durable state is written to disk. |
| Self-improve over time | ✅ Done | `self-improvement` skill + `capture-learning.sh`. Human-in-the-loop by design. |
| **Force Auto mode onto Opus 5 / 4.8** | ⚠️ **Not possible** | **In Kiro Web Autonomous mode the agent picks the model automatically — it cannot be pinned.** The only mechanism with a `model` field is custom agents, and `.kiro/agents/` is **not read on Web or Mobile**. |

### So what *was* done about the model requirement

1. **Where pinning works — IDE and CLI —** this pack ships `.kiro/agents/opus-5.md`
   and `.kiro/agents/opus-4-8.md`, ready to pin.
2. Their `model:` field is **deliberately left commented out.** Kiro does not publish
   model ID strings, and an unrecognized ID *silently falls back to the default model*.
   A wrong ID is an invisible failure; an unset one is an obvious no-op. Run `/model`,
   copy the exact ID, paste it in.
3. The `model-profiles` skill gives a routing policy by **task difficulty** — which is
   observable — instead of inventing capability differences between Opus 5 and 4.8
   that Kiro's docs do not publish.
4. Every other skill is written to be **model-agnostic**: correctness is enforced by
   procedure and verification, not by hoping a strong model was selected. A pack that
   only works on the best model is a fragile pack.

See [`docs/capability-matrix.md`](docs/capability-matrix.md) for what works on which
surface.

---

## Install

Kiro Web and Mobile read **only** project-scoped config committed to the repo.

```bash
# From your project root
git clone https://github.com/consecrating/Claude-Power.git /tmp/claude-power
cp -r /tmp/claude-power/.kiro/skills   .kiro/
cp -r /tmp/claude-power/.kiro/steering .kiro/
cp -r /tmp/claude-power/.kiro/scripts  .kiro/
cp -r /tmp/claude-power/.kiro/mcp-servers .kiro/
cp    /tmp/claude-power/AGENTS.md      .        # merge if you already have one

# IDE / CLI only — ignored on Web and Mobile
cp -r /tmp/claude-power/.kiro/agents /tmp/claude-power/.kiro/hooks .kiro/

chmod +x .kiro/skills/*/scripts/*.sh .kiro/scripts/*.sh
bash .kiro/scripts/validate-config.sh          # confirm it loaded cleanly
```

Add to your `.gitignore`:

```
.kiro/.memory/
.kiro/.learnings/
.kiro/.tmp/
```

**This pack deliberately does not ship `product.md`, `tech.md`, or `structure.md`.**
Those are reserved foundation steering filenames that your repo owns — shipping them
would overwrite your own project context. The validator fails if anyone adds them.

---

## The 16 skills

Skills activate automatically when your request matches their description. Only the
name and description are loaded at startup; the body loads on activation, and
`references/` load only when the body points to them.

### Core — the four requirements

| Skill | Use it for |
|---|---|
| `token-efficiency` | Shaping every tool call to return the fewest bytes that answer the question. 3 reference recipe books. |
| `context-durability` | Surviving compaction. On-disk memory protocol + `memory.sh`. |
| `model-profiles` | Routing work to the right model tier; honest limits on pinning. |
| `self-improvement` | Turning corrections into durable rules + `capture-learning.sh`. |
| `autonomous-execution` | The Auto-mode loop: clarify → plan → execute → verify → deliver. |

### Engineering

| Skill | Use it for |
|---|---|
| `codebase-recon` | Mapping an unfamiliar repo cheaply; tracing one thread end to end. |
| `root-cause-debugging` | Reproduce → isolate → hypothesize → fix the cause → prove it. |
| `error-recovery` | Your *own* failures: the two-strike rule, backing out, reporting blocked. |
| `test-strategy` | Tests that can actually fail; killing flakiness; coverage ≠ verification. |
| `safe-refactoring` | Behavior-preserving change across many call sites, with a baseline. |
| `api-contract-design` | Classifying breaking changes; expand/contract migration. |
| `performance-work` | Measure → find the dominant cost → fix → re-measure. |
| `security-review` | Secrets, object-level authz, injection, SSRF, data exposure. |
| `dependency-hygiene` | Adding, upgrading, auditing, and removing dependencies. |
| `pr-craft` | Commits, PR descriptions, review response. On Web the PR *is* the product. |
| `spec-driven-delivery` | Features too large for one conversation; `.kiro/specs/`. |

---

## MCP Servers

### opus5-lean — Real Token Efficiency (Hacker Tools)

**This is the HACKER SOLUTION** to credit exhaustion. Not filters and alerts —
real optimization tools from the `Claude-Opus5` repo.

| Tool | What it does | Cost |
|---|---|---|
| `opus5_count` | Count tokens and estimate cost (free via `count_tokens` API) | Free |
| `opus5_slim` | Strip wasted tokens (code untouched) | Free, offline |
| `opus5_cache` | Plan cache strategy for 67%+ savings | Free, offline |
| `opus5_cost` | Calculate scale pricing | Free, offline |
| `opus5_sweep` | Find cheapest effort level | Requires API key |

**Example output:**
```
Cache plan  (claude-opus-5, 5m TTL)

  10,300/13,700 tokens cacheable (75%), 1 breakpoint(s), break-even after 1 hit(s)

  At 5,000 requests/day for 30 days (150,000 requests):
    without cache  $10,275.00
    with cache     $3,365.14
    saved          $6,909.86  (67%)
```

**Install:**
```bash
pip install -e /projects/sandbox/Claude-Opus5
```

**Usage:**
```bash
export PATH="/root/.pyenv/versions/3.11.15/bin:$PATH"
opus5-lean count prompt.md          # How much does this cost?
opus5-lean slim prompt.md --stdout  # Strip wasted tokens
opus5-lean cache segments.json --rpd 5000  # Plan cache strategy
```

---

## The token budget, measured

The architecture is **one small always-on file + progressive disclosure for
everything else**. Measured word counts from this repo:

| Layer | Cost | When |
|---|---|---|
| `AGENTS.md` | 335 words (~450 tokens) | every turn |
| 16 skill names + descriptions | 912 words (~1,200 tokens) | every session, at startup |
| 1 `auto` steering description | ~40 words | every session |
| One skill body | 730–930 words | only when that skill activates |
| `kiro-config-authoring` steering | 600 words | only when editing `.kiro/` files |
| 5 reference files | 2,958 words total | only when a skill body points to one |

**Always-on total: roughly 1,300 words (~1,700 tokens).** The remaining ~15,000 words
in this pack cost nothing until relevant.

That is the whole design. Detail lives behind a trigger, never in the always-on layer.
The load-cost table in `.kiro/steering/kiro-config-authoring.md` is the rule the pack
holds itself to.

### Pruning

16 skill descriptions is the one unavoidable per-session cost. If you want it smaller,
delete skill folders you do not need — they are independent. Removing all 11
engineering skills cuts startup cost to about 300 words.

The only caveat: some skills cross-reference others by name (`error-recovery`,
`pr-craft`, `token-efficiency`, `context-durability`). The validator warns about
dangling references after you prune.

---

## Scripts

Both are tested and executable.

```bash
M=.kiro/skills/context-durability/scripts/memory.sh

$M init "<the goal in the user's own words>"
$M constraint "Do not change the public SDK surface"
$M criterion "device flow returns a refresh token"
$M note "Rejected implicit flow — no refresh token"
$M file src/auth/device.ts "new grant"
$M next "wire the poll endpoint"

$M status     # compact digest — this is what survives a compaction
$M check "refresh token"
$M verify     # gaps, incl. files changed in git but never recorded
$M render     # TASK.md snapshot for humans
```

```bash
L=.kiro/skills/self-improvement/scripts/capture-learning.sh
$L add "Never cat files over 200 lines" token-efficiency
$L list
$L promote 1        # prints placement guidance, cheapest option first
```

```bash
bash .kiro/scripts/validate-config.sh          # everything
bash .kiro/scripts/validate-config.sh .kiro/skills/pr-craft/SKILL.md
python3 .kiro/scripts/validate-frontmatter.py  # strict YAML check
```

---

## Layout

```
AGENTS.md                        always-on core directives (the token budget)
.kiro/
  steering/
    kiro-config-authoring.md     fileMatch: only when editing .kiro/ config
    verification-discipline.md   auto: before claiming anything is done
  skills/                        16 skills, progressive disclosure
    <skill>/SKILL.md
    <skill>/references/*.md      loaded on demand only
    <skill>/scripts/*.sh         deterministic work
  mcp-servers/                   MCP servers (opus5-lean for token efficiency)
    opus5-lean/server.json
    opus5-lean/server.py
    opus5-lean/server.sh
  agents/                        IDE + CLI only
    opus-5.md                    deep reasoning
    opus-4-8.md                  delivery / throughput
  hooks/claude-power.json        IDE + CLI only; all command actions (no credits)
  scripts/                       validators
docs/
  capability-matrix.md           what works on which surface
  roadmap.md                     what else to add, prioritized
```

## Hooks

All four use `action.type: "command"` — **`"agent"` actions start a new model loop and
consume credits; command actions do not.** Not available on Web or Mobile.

| Hook | Trigger | Does |
|---|---|---|
| `restore-working-memory` | `SessionStart` | prints task state into context so a new session resumes instantly |
| `snapshot-working-memory` | `Stop` | re-renders `TASK.md` |
| `validate-kiro-config-on-save` | `PostFileSave` | catches a malformed skill that would silently never load |
| `block-secret-commits` | `PreToolUse` | exit 2 blocks a commit containing a credential — **`enabled: false`**, opt in deliberately |

---

## What this pack will not do

- It will not pin the model in Kiro Web Autonomous mode. Nothing can.
- Hooks, agents, and permissions do nothing on Web or Mobile.
- It does not add tests to your project unless you ask.
- It does not guarantee zero forgetting. Compaction is lossy; the memory protocol
  makes the *important* state recoverable, and only if it gets written.

## License

No license file yet — see [`docs/roadmap.md`](docs/roadmap.md). Add one before
sharing publicly.
