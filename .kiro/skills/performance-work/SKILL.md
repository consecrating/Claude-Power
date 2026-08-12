---
name: performance-work
description: Use when something is slow, when asked to optimize or improve performance, when handling timeouts, high memory use, slow queries, slow page loads, or scaling concerns. Apply before accepting any optimization request at face value. Enforces measure, find the dominant cost, fix that, re-measure — and refuses speculative optimization.
metadata:
  version: "1.0"
  part-of: claude-power
---

# Performance work

Rules in priority order:

1. **Measure first.** An unmeasured optimization is a guess that costs readability.
2. **Fix the dominant cost.** Everything else is noise until it is dominant.
3. **Re-measure.** Otherwise you do not know whether you helped.

Intuition about where time goes is unreliable — including yours. The bottleneck is
frequently somewhere nobody suspected.

## Establish the number before touching code

You need a target and a baseline. Without both, "faster" is unfalsifiable.

- What operation is slow? (specific request, query, page, job)
- How slow, at what percentile? p50 and p99 behave very differently.
- How slow is acceptable? Optimization without a target never terminates.
- Is it slow always, or only at scale / under concurrency / with cold cache?

```bash
# crude but often sufficient
time <command>
for i in 1 2 3; do /usr/bin/time -f '%es %MkB' <command>; done

# where the time actually goes
node --cpu-prof app.js          # then inspect the profile
python -X importtime -c 'import app' 2>&1 | tail -20
py-spy top -- python app.py
```

Record the baseline in memory so it survives compaction:
`memory.sh note "baseline: /orders p99 = 2.4s, target 300ms"`.

## The usual dominant costs

Check these before micro-optimizing anything, in roughly descending order of how
often they are the real answer:

**N+1 queries.** One query per item in a loop. Almost always the answer in a slow
endpoint. Fix by batching or eager-loading, not by caching the symptom.

```bash
rg -n 'for .*\{[\s\S]{0,200}await .*(find|query|get)\(' --glob '*.ts' -m 10
```

**Missing index.** A query filtering or sorting on an unindexed column. Confirm with
the planner, do not assume:

```sql
EXPLAIN ANALYZE SELECT ... ;   -- look for Seq Scan on a large table
```

**Unbounded result sets.** Fetching everything to use a few. Push filtering,
sorting, and limiting into the query.

**Serial I/O that could be concurrent.** Independent awaits in sequence.

```ts
const [a, b] = await Promise.all([getA(), getB()]);   // not two awaits in a row
```

**Work repeated per request** that could be done once: compiling a regex, parsing
config, building a lookup table, opening a connection instead of pooling.

**Accidentally quadratic algorithms.** A nested scan over the same collection, or
`array.includes()` inside a loop — use a `Set` or `Map`.

**Oversized payloads.** Returning fields nobody uses; no compression; unoptimized
images; shipping an entire bundle to render one page.

**Chatty network calls.** Latency dominates; batch them.

## Where NOT to look first

Loop unrolling, micro-syntax choices, replacing a clear map/filter chain with a
manual loop, swapping a library for a marginally faster one. These trade real
readability for immeasurable gains — and they are almost never the dominant cost.

Do not add caching as a first move. Caching hides a problem and introduces
invalidation bugs, staleness, and a new failure mode. Fix the underlying cost first;
cache only what is genuinely expensive and genuinely reusable, and be explicit about
the invalidation rule.

## Change one thing at a time

Multiple simultaneous optimizations make attribution impossible, and one of them may
be making things worse. One change, re-measure, keep or revert.

```
baseline: p99 2400ms
+ batch order-item query:   p99 380ms   (keep — this was the N+1)
+ add Redis cache:          p99 370ms   (revert — 3ms for a whole new failure mode)
```

That table is the deliverable. Report measured numbers, never "should be faster".

## Correctness outranks speed

A fast wrong answer is worthless. After optimizing, the tests must still pass —
especially for changes to query shape, concurrency, or caching, where it is easy to
alter semantics:

- concurrent execution can change ordering guarantees
- batching can change transaction boundaries and error behavior
- caching can serve stale or cross-tenant data — verify the key includes the tenant

## Know when to stop

Stop when the target is met. "Faster" with no target is an infinite task, and each
additional optimization typically costs more complexity for less gain.

If the target cannot be met within the current architecture, say so plainly, with
the measurement, and describe what would be required. That is a decision for the
user, not something to be papered over with micro-optimizations.
