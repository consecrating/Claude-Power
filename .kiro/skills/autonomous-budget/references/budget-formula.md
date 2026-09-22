# Budget Formula Reference

## Token Budget Calculation

```
budget = base_cost + (iterations * per_iteration_cost) + safety_buffer
```

### Base Costs by Task Type

| Task | Base Tokens | Notes |
|---|---|---|
| Bug fix | 2,000 | Read code, understand, fix, test |
| Small feature | 5,000 | Simple addition, no refactor |
| Medium feature | 12,000 | Multiple files, moderate complexity |
| Large feature | 25,000 | Cross-cutting, many integrations |
| Refactor | 8,000 | Plan + execute + verify |
| Documentation | 3,000 | Read code, write docs |

### Per-Iteration Costs

| Phase | Tokens | What's included |
|---|---|---|
| Clarify | 1,000 | Questions, constraints, goals |
| Plan | 2,000 | Strategy, file map, acceptance criteria |
| Execute | 1,500 | Code changes, tool calls |
| Verify | 500 | Check outputs, diff |
| Overhead | 500 | Response parsing, state |

**Total per iteration: ~5,500 tokens**

### Safety Buffer Rules

- Small tasks (<10,000): 20% headroom
- Medium tasks (10,000-50,000): 15% headroom
- Large tasks (>50,000): 10% headroom

### Cost Estimation Examples

#### Example 1: Bug Fix
```
base_cost = 2,000
iterations = 2 (clarify + execute/verify)
per_iteration = 5,500
safety = 20%

budget = 2,000 + (2 × 5,500) + 20% = 13,000 tokens
cost = 13,000 / 1,000,000 × ($5 + $25) = $0.39
```

#### Example 2: Medium Feature
```
base_cost = 5,000
iterations = 3 (clarify + plan + execute/verify)
per_iteration = 5,500
safety = 15%

budget = 5,000 + (3 × 5,500) + 15% = 24,250 tokens
cost = 24,250 / 1,000,000 × ($5 + $25) = $0.73
```

#### Example 3: Large Refactor
```
base_cost = 8,000
iterations = 4 (plan + execute + verify + polish)
per_iteration = 5,500
safety = 10%

budget = 8,000 + (4 × 5,500) + 10% = 30,800 tokens
cost = 30,800 / 1,000,000 × ($5 + $25) = $0.92
```

## Budget Thresholds

| Budget | Model | Action |
|---|---|---|
| <5,000 | Opus 4.8 | Default |
| 5,000-20,000 | Opus 4.8 | Default (good enough) |
| 20,000-50,000 | Opus 4.8 or GPT-4o | Compare quality/cost |
| >50,000 | Opus 5 only | Explicit user approval |

## Early Termination Triggers

Stop if any:

1. **Budget exceeded** — 100% of budget
2. **Quality plateau** — 3 consecutive iterations with <5% improvement
3. **No progress** — 2 iterations with same output
4. **User delay** — waiting >60 seconds for response
5. **Error loop** — repeated failures on same step

## Quick Budget Calculator

```bash
# Save as .kiro/skills/autonomous-budget/scripts/budget-calculator.sh
#!/usr/bin/env bash
base=$1
iterations=$2
safety_pct=${3:-20}

total=$((base + iterations * 5500))
buffer=$((total * safety_pct / 100))
budget=$((total + buffer))
tokens=$budget
cost_in=$((tokens * 5 / 1000000))
cost_out=$((tokens * 25 / 1000000))
total_cost=$(echo "scale=2; ($cost_in + $cost_out) / 100" | bc)

echo "Budget: $tokens tokens"
echo "Estimated cost: \$$total_cost"
echo "Breakdown:"
echo "  Base: $base"
echo "  Iterations ($iterations): $((iterations * 5500))"
echo "  Safety ($safety_pct%): $buffer"
```