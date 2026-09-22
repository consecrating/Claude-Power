# Model Selection: Opus 4.8 vs Opus 5 (Hacker's Guide)

## Current Pricing (as of Sep 2026)

| Model | Input | Output | Context | Best For |
|---|---|---|---|---|
| **Opus 4.8** | $2/MTok | $10/MTok | 200k | Everything except complex reasoning |
| **Opus 5** | $5/MTok | $25/MTok | 100k | Complex reasoning, creative writing |
| **GPT-4o** | $5/MTok | $15/MTok | 128k | When quality matters more than cost |
| **Claude 3.5 Sonnet** | $3/MTok | $15/MTok | 200k | Balanced option |

## The Opus 4.8 Advantage (60% Savings)

Opus 4.8 is **the hacker's best friend** for most tasks:

| Metric | Opus 4.8 | Opus 5 | Savings |
|---|---|---|---|
| Input cost | $2 vs $5 | 60% cheaper |
| Output cost | $10 vs $25 | 60% cheaper |
| Context window | 200k vs 100k | 2x more room |
| Response speed | Faster | Slower (more thinking) |

## When to Use Each Model

### ✅ Use Opus 4.8 (Default for 95% of tasks)

| Task | Opus 4.8 | Notes |
|---|---|---|
| Code generation | ✅ | Nearly identical quality |
| Bug fixes | ✅ | Same reliability |
| Refactoring | ✅ | Same correctness |
| Test writing | ✅ | Same coverage |
| Documentation | ✅ | Slightly less verbose |
| Code review | ✅ | Same insight |

### ⚠️ Use Opus 5 (Only when explicitly required)

| Task | Opus 5 | Why |
|---|---|---|
| Complex math/logic | ✅ | Better reasoning chain |
| Creative writing | ✅ | More natural prose |
| Multi-step puzzles | ✅ | Better plan decomposition |
| Ambiguous requirements | ✅ | Better clarification |
| Document analysis | ⚠️ | Compare Opus 4.8 first |

### ❌ Never use Opus 5 for

| Task | Why |
|---|---|
| Simple code edits | 60% overpay for no benefit |
| Bug fixes | Opus 4.8 has same accuracy |
| Routine refactoring | Same quality at 60% cost |
| Testing | Same coverage, lower price |

## Hacker's Model Selection Flow

```
User request received
        ↓
Is Opus 5 explicitly required? (e.g., "use Opus 5")
        ├─ YES → Use Opus 5
        └─ NO → Is task <20,000 tokens?
                  ├─ YES → Use Opus 4.8 (95% of tasks)
                  └─ NO → Is quality CRITICAL?
                            ├─ YES → Use Opus 5 OR GPT-4o
                            └─ NO → Use Opus 4.8 + "good enough"
```

## Cost Comparison Examples

### Example 1: Bug Fix (5,000 tokens)

| Model | Input Cost | Output Cost | Total |
|---|---|---|---|
| Opus 4.8 | $0.01 | $0.05 | **$0.06** |
| Opus 5 | $0.025 | $0.125 | **$0.15** |
| **Savings** | - | - | **60%** |

### Example 2: Medium Feature (25,000 tokens)

| Model | Input Cost | Output Cost | Total |
|---|---|---|---|
| Opus 4.8 | $0.05 | $0.25 | **$0.30** |
| Opus 5 | $0.125 | $0.625 | **$0.75** |
| **Savings** | - | - | **60%** |

### Example 3: Large Feature (100,000 tokens)

| Model | Input Cost | Output Cost | Total |
|---|---|---|---|
| Opus 4.8 | $0.20 | $1.00 | **$1.20** |
| Opus 5 | $0.50 | $2.50 | **$3.00** |
| **Savings** | - | - | **60%** |

## The 60% Rule

**Always prefer Opus 4.8 unless you have a documented reason to use Opus 5.**

Every time you use Opus 5 when Opus 4.8 would work:
- You burn 60% more credits
- You get the same quality (for most tasks)
- You have fewer credits for future work

## Auto Mode Optimization

In Kiro Web's Auto mode, you cannot force the model. But you can:

1. **Use the `model-profiles` skill** to route tasks by difficulty
2. **Design tasks for Opus 4.8** — keep them small, focused
3. **Set budget limits** — if budget requires Opus 4.8, you'll stay under
4. **Document model preference** — "Please use Opus 4.8 for this task"

## Summary: Hacker's Model Checklist

Before starting any Auto task:

- [ ] Can this be done in <20,000 tokens? → **YES = Opus 4.8**
- [ ] Is quality CRITICAL for complex reasoning? → **YES = Opus 5**
- [ ] Otherwise → **Opus 4.8 with "good enough" approach**

Remember: **60% savings isn't optional. It's how hackers survive.**