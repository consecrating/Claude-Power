# Burn Rate Monitoring: Alert Thresholds

## Token Burn Rate Alerts

Monitor tokens used vs budget at each checkpoint:

| Threshold | Alert | Action |
|---|---|---|
| 50% | Info | "Halfway done, budget looks good" |
| 70% | Warning | "70% budget used. 30% left for remaining steps." |
| 85% | Urgent | "85% budget used. Final steps must be efficient." |
| 90% | Critical | "Budget nearly exhausted. Continue or extend?" |
| 95% | Emergency | "95% budget used. Hard stop in 5%." |
| 100% | Stop | **HARD STOP. Do not proceed.** |

## Burn Rate Calculator

```bash
# .kiro/skills/autonomous-budget/scripts/burn-check.sh
#!/usr/bin/env bash
used=$1
budget=$2

if [ -z "$used" ] || [ -z "$budget" ]; then
    echo "Usage: burn-check.sh <tokens_used> <budget>"
    exit 1
fi

percent=$((used * 100 / budget))

if [ $percent -lt 50 ]; then
    color="32"  # green
    status="HEALTHY"
elif [ $percent -lt 70 ]; then
    color="33"  # yellow
    status="MODERATE"
elif [ $percent -lt 85 ]; then
    color="33"  # yellow
    status="WARNING"
elif [ $percent -lt 90 ]; then
    color="31"  # red
    status="URGENT"
elif [ $percent -lt 95 ]; then
    color="31"  # red
    status="CRITICAL"
else
    color="31"  # red
    status="STOP"
fi

echo -e "\033[${color}m[Burn Rate: ${percent}%] ${status}\033[0m"
echo "  Used: $used / $budget tokens"
echo "  Remaining: $((budget - used)) tokens"

if [ $percent -ge 90 ]; then
    echo -e "\033[31m  >>> BUDGET ALERT: ${percent}% used <<<\033[0m"
fi
```

## Per-Phase Budget Tracking

Track tokens by phase to identify where budget is spent:

| Phase | Budget % | Alert if exceeded |
|---|---|---|
| Clarify | 10% | 15% |
| Plan | 20% | 25% |
| Execute | 50% | 60% |
| Verify | 10% | 15% |
| Overhead | 10% | 15% |

## Cost Per Turn Monitoring

In Auto mode, you get multiple turns. Track per-turn cost:

| Turn | Max Cost | Alert |
|---|---|---|
| 1-3 | $0.05 | Normal |
| 4-6 | $0.10 | Watch |
| 7-9 | $0.15 | Warning |
| 10+ | $0.20+ | Stop and assess |

## Hacker's Quick Burn Check

Before each tool call, ask:

> "Is this call worth its cost?"

Use this checklist:

- [ ] Can I avoid this call entirely? (save 1,000+ tokens)
- [ ] Can I use a cheaper model? (Opus 4.8 vs Opus 5 = 60% savings)
- [ ] Can I batch this with another call? (save 200 tokens overhead)
- [ ] Can I use cached content? (save 80% of repeated tokens)

## Auto Mode Budget Guardrails

Set these hard limits in your task constraints:

```
HARD LIMITS:
- Max budget: $X.XX (XX,XXX tokens)
- Max iterations: X
- Max cost per turn: $0.XX
- Stop at 90% budget: YES
- Require approval at 95%: YES
```

## Post-Task Budget Report

Always include in final report:

```
📊 Budget Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Budget:    $X.XX (XX,XXX tokens)
Spent:     $X.XX (XX,XXX tokens)
Remaining: $X.XX (XX,XXX tokens)

Burn Rate by Phase:
  Clarify:   $X.XX (X% of budget)
  Plan:      $X.XX (X% of budget)
  Execute:   $X.XX (X% of budget)
  Verify:    $X.XX (X% of budget)

Model Used: claude-opus-4-8 (budget-friendly)
Total Turns: X

Efficiency: XX% of budget used
Status: ✅ UNDER BUDGET
```

## Emergency Budget Recovery

If you exceed budget by accident:

1. **Stop immediately** - do not proceed
2. **Report status** - what's done, what's remaining
3. **Offer minimal version** - "I can deliver 80% for half the cost"
4. **Ask for more budget** - "Add $X to finish?"

Never try to "sneak" past the budget. That erodes trust and wastes credits.