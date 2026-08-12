---
name: codebase-recon
description: Use when working in an unfamiliar repository or an unfamiliar area of a known one, when you need to find where something lives, trace how a feature works end to end, or understand architecture before changing it. Apply for requests like "how does X work here", "where is Y implemented", "add a feature like Z", or before any change whose blast radius you cannot yet predict.
metadata:
  version: "1.0"
  part-of: claude-power
---

# Codebase recon

The goal is a mental model accurate enough to change the code safely, built with the
fewest bytes read. Breadth-first reading of a repository is the most expensive
mistake available; recon is deliberately depth-first along one thread.

## Never start by reading files

Start with structure, which is cheap and high-signal:

```bash
git ls-files | wc -l
git ls-files | sed 's|/.*||' | sort | uniq -c | sort -rn | head -15   # top-level shape
git ls-files | rg -o '\.[a-z0-9]+$' | sort | uniq -c | sort -rn | head -8
jq -r '.scripts | to_entries[] | "\(.key): \(.value)"' package.json 2>/dev/null
```

Read the README only if it exists and is short. Treat it as a claim about the code,
not a description of it — READMEs go stale.

## Find the seams first

Every codebase has a small number of places that reveal its architecture. Locate
these before anything else:

- **entry points** — `main`, `index`, `app`, `server`, CLI definitions, handlers
- **routing / dispatch** — maps external requests to internal code
- **data model** — schemas, migrations, type definitions
- **configuration** — reveals dependencies, environments, feature flags
- **dependency manifest** — the frameworks in play constrain everything else
- **test directory layout** — mirrors the intended module boundaries

```bash
git ls-files | rg -i '(main|index|app|server|router|routes|schema|migrations)' | head -20
```

## Trace one thread end to end

Do not map the whole system. Pick the single thread that your task touches and
follow it, in this direction:

**entry point → dispatch → handler → business logic → data access → back**

At each hop, use the search ladder rather than reading whole files:

```bash
rg -l 'createOrder'                      # which files
rg -n 'function createOrder|createOrder =' # the definition
rg -n 'createOrder\(' --glob '!*test*' -m 10   # the call sites
sed -n '120,170p' src/orders/service.ts  # only the range that matters
```

One complete thread teaches more than partial knowledge of ten.

## Questions worth answering explicitly

Before changing anything, be able to state:

1. Where does this behavior enter the system?
2. Where does the decision I need to change actually get made?
3. What else calls that code? (`rg -n 'symbol\(' | wc -l` — the blast radius)
4. What tests cover it? If none, that is a finding.
5. What is the established pattern here for this kind of change?
6. What will break if I get it wrong, and how would I notice?

## Match the local pattern

The most useful recon output is often a **precedent**: an existing feature that is
structurally analogous to what you must build. Find it and follow it.

```bash
# a similar route/model/handler already exists — copy its shape
git ls-files 'src/routes/*' | head -20
```

Consistency with a mediocre local pattern usually beats introducing a better foreign
one — unless the user asked for the change in pattern. Note the divergence rather
than silently deviating.

## When to delegate

If the question is open-ended — "how does authentication work here", "why is this
architected this way", "what would break if we changed X" — delegate to a
context-gathering subagent. You pay for its report, not its transcript. Do not
delegate a question one `rg` answers.

Never re-read files a subagent already reported on.

## Record what you learned

Findings are expensive to obtain and cheap to lose to compaction. Persist the map,
not the code:

```bash
M=.kiro/skills/context-durability/scripts/memory.sh
$M note "Order creation: routes/orders.ts:34 -> services/order.ts:120 -> repo/order.ts:88"
$M note "Auth middleware applied globally in app.ts:52; per-route overrides exist"
$M note "No tests cover the discount path — verification will need a manual check"
```

## Stop conditions

Stop recon and start working when you can answer the six questions above. Continued
reading past that point is procrastination with a token cost.

Conversely, if you cannot answer question 3 or 6, do not start editing — you do not
yet know what you might break.
