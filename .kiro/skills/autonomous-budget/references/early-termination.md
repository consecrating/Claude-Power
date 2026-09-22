# Early Termination: "Good Enough" Testing

## The Hacker's Test: Can We Halve the Output?

After each deliverable, run this check:

```
Can we produce 90% of the quality with 50% of the tokens?
```

If YES → Use the minimal version
If NO → Keep the full version

## The 90/50 Rule

| Full output | Minimal version | When to use |
|---|---|---|
| 100% | 50% | Good enough for prototypes, spikes |
| 90% | 45% | Acceptable for most features |
| 70% | 35% | Only for debugging, temp files |
| 50% | 25% | Never - too low quality |

## Termination Checklist

Before ending, verify:

- [ ] Output is **reproducible** (re-running gives same results)
- [ ] Output is **testable** (can be verified cheaply)
- [ ] Output is **documented** (key assumptions noted)
- [ ] No obvious **quick wins** left (can we trim 10% more?)

## Quick "Good Enough" Templates

### 1. Code Generation

Full:
```python
def process_data(data):
    """Process data according to spec.
    
    This function handles all edge cases including:
    - Empty input
    - Invalid types
    - Out of range values
    - Concurrent modifications
    """
    if not data:
        return []
    # ... 200 lines of defensive code
```

Minimal (90% quality, 50% tokens):
```python
def process_data(data):
    """Process data. Returns empty list for empty input."""
    return [d for d in data if d is not None]
```

Use minimal when: prototype, spike, internal tool

### 2. Documentation

Full: 2,000 tokens with examples, use cases, troubleshooting

Minimal (90% quality): 1,000 tokens with just the essentials

Use minimal when: code comments, quick reference

### 3. Test Coverage

Full: 100% coverage, edge cases, integration tests

Minimal (90% quality): Core paths + 1-2 edge cases

Use minimal when: rapid iteration, known stable code

## The 3-Iteration Rule

No task should take more than 3 iterations to reach "good enough":

1. **Iteration 1** — Minimum viable deliverable
2. **Iteration 2** — Fix critical issues
3. **Iteration 3** — Polish if time permits

If you need more than 3 iterations, the task is either:
- Too complex (split into smaller tasks)
- Not well-defined (go back to clarify)
- Using the wrong model (switch to Opus 4.8)

## Auto Mode Optimization

In Auto mode, set these early termination conditions:

| Condition | Action |
|---|---|
| Budget 80% used | Alert + ask to continue |
| Budget 95% used | Hard stop, report status |
| 3 iterations without improvement | Declare "good enough" done |
| Quality >90% achieved | Declare done, even if budget remains |

## Hacker's Mantra

> **Ship first. Polish later. Perfection is expensive.**

The goal is progress, not perfection. You can always improve the output later - but only if the user has credits to pay for it.