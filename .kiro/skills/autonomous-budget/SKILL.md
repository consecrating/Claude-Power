---
name: autonomous-budget
description: Use when working with Claude Opus 5 or Opus 4.8 in Kiro Web or any mode. Enforces token budgets, early termination at 80% quality ("good enough"), burn rate monitoring, and hard budget caps to prevent credit exhaustion. Applies to both interactive and autonomous modes.
metadata:
  version: "1.0"
  part-of: claude-power
---

# Autonomous Budget Execution

**Opus 5 costs $5/MTok in, $25/MTok out.** Even Opus 4.8 ($2/MTok in, $10/MTok out) adds up fast if you don't watch your spending.

This skill is **mandatory** for any task using Opus 5 or Opus 4.8. It enforces:
- **Budget caps** that prevent surprise charges
- **Early termination** at 80% quality ("good enough" threshold)
- **Burn rate monitoring** with hard stop at 90%
- **Model selection** guidance (Opus 4.8 preferred unless explicitly needed)

---

## Phase 0 — Budget Lock (MANDATORY, runs BEFORE any work)

### Step 1: Calculate Hard Budget

```
HARD BUDGET = base_cost + (estimated_iterations × 5,500) + 20% buffer
```

| Task Size | Estimated Iterations | Base | Hard Budget | Max Cost (Opus 4.8) |
|---|---|---|---|---|
| Tiny (<500 tokens) | 1-2 | 2,000 | 5,000 | $0.15 |
| Small (500-2,000) | 2-3 | 3,000 | 7,500 | $0.23 |
| Medium (2,000-5,000) | 3-4 | 6,000 | 14,000 | $0.42 |
| Large (5,000-10,000) | 4-5 | 12,000 | 27,000 | $0.81 |
| XL (10,000+) | 5-6 | 20,000 | 48,000 | $1.44 |

### Step 2: Lock Budget in Constraints

```bash
M=.kiro/skills/context-durability/scripts/memory.sh
$M init "<goal> [BUDGET: $X.XX]"
$M constraint "<BUDGET LIMIT: $X.XX max>"
$M criterion "<80% quality = acceptable>"
```

---

## Phase 1 — Clarify with BUDGET FILTERS

Ask questions, but **filter through budget lens**:

### Budget Emergency Checklist

- [ ] Can I skip this clarification? (Use defaults)
- [ ] Can I answer this myself from context? (Do it)
- [ ] Is this worth >1,000 tokens in question/answer? (Skip or simplify)

### Automatic Defaults (Use if not specified)

| Default | Value | Saves |
|---|---|---|
| Quality target | 80% ("good enough") | ~30% tokens |
| Max iterations | 3 (small) or 5 (large) | Prevents runaway |
| Model | Opus 4.8 (cheapest) | 60% cheaper than Opus 5 |
| Error handling | Fail fast, report | No retry loops |

**If user says "make it perfect" or "full quality":**
- Respond: "Full quality may cost 40-60% more. For interactive work, I'll deliver 80% quality and stop. Want me to continue, or do you want to increase the budget?"

---

## Phase 2 — Plan with CAPPING

### Budget Cap Rules

| Action | Max Cost | Emergency Override |
|---|---|---|
| Reading files | 500 lines | Cap at first 200 |
| API calls | 1 call | Batch or skip |
| Tool schemas | Cached | Always use cache |
| System prompt | Cached | Always use cache |

### Iteration Caps (HARD)

| Task Type | Total Max |
|---|---|
| Tiny | 2 |
| Small | 3 |
| Medium | 4 |
| Large | 5 |
| XL | 6 |

### Budget Emergency Cutoff

If budget calculation shows >$2 estimated:
- **STOP** and ask: "This exceeds recommended budget ($2). Scale down or increase budget?"

---

## Phase 3 — Execute with BURN MONITORING

### Per-Iteration Budget

| Iteration | Max Tokens | Alert |
|---|---|---|
| 1 | 5,000 | Normal |
| 2 | 4,000 | Watch (13% below avg) |
| 3 | 3,000 | Warning (36% below avg) |
| 4 | 2,000 | Critical (55% below avg) |
| 5+ | 1,500 | Emergency (64% below avg) |

### Burn Rate Monitoring (AUTOMATIC)

```
ITERATION 1 COMPLETE:
  Used: 5,000 tokens
  Budget: 10,000
  Remaining: 5,000 (50%)
  Status: HEALTHY

ITERATION 2 COMPLETE:
  Used: 7,500 tokens
  Budget: 10,000
  Remaining: 2,500 (25%)
  Status: WARNING - 75% budget used

ITERATION 3 COMPLETE:
  Used: 9,200 tokens
  Budget: 10,000
  Remaining: 800 (8%)
  Status: EMERGENCY - HARD STOP IN 2%
```

### Hard Stop Triggers (AUTOMATIC)

| Trigger | Action |
|---|---|
| Budget 85% used | Alert: "85% budget used. Final steps must be efficient." |
| Budget 90% used | HARD STOP. Report status. Ask for more. |
| Budget 95% used | DO NOT PROCEED. Emergency stop. |
| Max iterations reached | STOP. Report what's done. |

---

## Phase 4 — Verify with 80% QUALITY BAR

### The 80% Quality Rule

**80% quality is acceptable.** Do not continue for perfection unless budget permits.

| Check | Full Quality | 80% Quality | Saves |
|---|---|---|---|
| Code comments | Detailed | Minimal | 50% |
| Test coverage | 100% | Core paths only | 60% |
| Error handling | All cases | Common cases | 40% |
| Documentation | Full | Key points only | 70% |
| Examples | Many | 1-2 essential | 80% |

### Verification Checklist (80% Edition)

- [ ] Output exists and is valid
- [ ] Core functionality works (not edge cases)
- [ ] No obvious critical bugs
- [ ] Tests pass for main paths (not all)
- [ ] Documentation covers key usage

**If all checked, DELIVER. Do not iterate further.**

---

## Phase 5 — Deliver with BUDGET REPORT

### Budget Report Template (MANDATORY)

```
📊 BUDGET REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INITIAL BUDGET: $X.XX (X,XXX tokens)
QUALITY TARGET: 80% ("good enough")

ACTUAL SPEND:
  Iteration 1: $X.XX (X,XXX tokens)
  Iteration 2: $X.XX (X,XXX tokens)
  Iteration 3: $X.XX (X,XXX tokens)
  ─────────────────────────────
  TOTAL: $X.XX (X,XXX tokens)

REMAINING: $X.XX (X,XXX tokens)
BUDGET UTILIZATION: XX%

MODEL: claude-opus-4-8 (budget mode)
ITERATIONS: X / X (max)

STATUS: ✅ DONE (80% quality, within budget)
```

---

## The Hacker's Budget Survival Rules

### Rule 1: Budget First
> **Calculate and lock budget BEFORE starting work. No exceptions.**

### Rule 2: 80% Quality is Good Enough
> **Stop at 80% quality. Perfection is expensive.**

### Rule 3: Burn Monitoring
> **If budget >85%, alert. If >90%, HARD STOP. No exceptions.**

### Rule 4: Model Selection
> **Use Opus 4.8 unless explicitly requested otherwise. 60% cheaper.**

### Rule 5: Early Termination
> **Stop at 3-5 iterations max. Most tasks are done by iteration 3.**

---

## Model Selection: Opus 4.8 vs Opus 5

| Task Type | Opus 4.8 | Opus 5 | When to use 5 |
|---|---|---|---|
| Code generation | ✅ Yes | ⚠️ No | Complex reasoning only |
| Bug fixes | ✅ Yes | ⚠️ No | Same accuracy |
| Refactoring | ✅ Yes | ⚠️ No | Same correctness |
| Testing | ✅ Yes | ⚠️ No | Same coverage |
| Documentation | ✅ Yes | ⚠️ Maybe | Creative writing only |
| Math/logic | ⚠️ Maybe | ✅ Yes | When accuracy matters |

**Rule of thumb:** Use Opus 4.8 for 95% of coding tasks. Opus 5 is 60% more expensive for similar quality on code.

---

## Pro Tips for Surviving on a Budget

1. **Pre-cache everything** — tool schemas, system prompt, docs
2. **Batch similar calls** — one smart call beats 10 small ones
3. **Use 80% quality as default** — perfection is expensive
4. **Stop at 3 iterations** — most tasks are done by then
5. **Report early** — if budget looks tight, warn immediately

### Hacker's Mantra

> **"80% done is better than 100% bankrupt."**

Budget awareness isn't stingy — it's professional.