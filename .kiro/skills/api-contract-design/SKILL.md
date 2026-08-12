---
name: api-contract-design
description: Use when designing or changing any interface consumed by others — REST or GraphQL endpoints, public functions, exported types, library surfaces, event payloads, CLI flags, config schemas, or database schemas shared across services. Apply when adding a field, renaming, deprecating, versioning, or when asked whether a change is breaking.
metadata:
  version: "1.0"
  part-of: claude-power
---

# API contract design

An interface is a promise. Internal code can be changed freely; a contract cannot,
because someone else depends on it and you cannot see all of them.

The first question for any interface change is always: **who consumes this, and can
they all be updated atomically?** If the answer is no, the change must be backward
compatible.

## Classify the change before making it

| Change | Breaking? |
|---|---|
| Add an optional field to a response | No |
| Add an optional parameter with a default | No |
| Add a new endpoint / function / variant | No |
| Rename anything | **Yes** |
| Remove a field, parameter, or endpoint | **Yes** |
| Make an optional parameter required | **Yes** |
| Narrow an accepted input type or range | **Yes** |
| Widen a returned type or add an enum variant | **Yes** for exhaustive consumers |
| Change a default value | **Yes** — silent behavior change, the worst kind |
| Change error codes, status codes, or error shape | **Yes** |
| Change ordering, pagination, or nullability | **Yes** |
| Tighten validation | **Yes** — previously accepted input now fails |

Two that get missed constantly: **changing a default** and **tightening validation**.
Both compile, both pass existing tests, both break consumers in production.

## Find the consumers

```bash
rg -n 'createOrder\(' --glob '!*test*' | wc -l      # in-repo call sites
rg -n '"/api/v1/orders"' --glob '!node_modules'      # in-repo HTTP callers
```

In-repo results are the *floor*, never the ceiling. External consumers — other
services, mobile clients you cannot force-update, third parties, saved integrations —
do not appear in your grep. For anything public, assume they exist.

## Compatible evolution

The expand/contract pattern, in order:

1. **Expand** — add the new form; keep the old working
2. **Migrate** — move consumers over; announce the deprecation
3. **Wait** — long enough for consumers you cannot control (mobile: months)
4. **Contract** — remove the old form, in a release that says so

```ts
// Expand: accept both, prefer the new, keep old working
function createOrder(opts: { items: Item[]; couponCode?: string; coupon?: string }) {
  const coupon = opts.couponCode ?? opts.coupon;   // old name still honored
  ...
}
```

Never skip step 3 because in-repo callers are all updated.

## Design rules

**Make the contract explicit.** Types, schemas, and validation at the boundary. An
interface whose shape is only discoverable by reading the implementation is not a
contract.

**Validate input at the edge**, once, and reject clearly. Do not let unvalidated data
reach business logic and fail deep in the stack.

**Return structured, actionable errors.** A consumer must be able to distinguish
retryable from fatal, and know what to fix:

```json
{ "error": { "code": "INVALID_COUPON", "message": "Coupon expired on 2026-01-31", "field": "couponCode" } }
```

Stable machine-readable `code`, human-readable `message`. Never leak internals,
stack traces, SQL, or secrets in an error.

**Prefer additive, explicit shapes.** Optional fields over overloaded meanings. A
new variant over a magic value. Never reuse a field for a second purpose.

**Be conservative in what you return, liberal in what you accept** — but never so
liberal that invalid input is silently coerced into a plausible wrong result.

**Paginate anything that can grow.** An unpaginated list endpoint is a latent
outage. Decide the pagination contract before launch; adding it later is breaking.

**Make destructive operations idempotent**, or require an idempotency key. Networks
retry whether or not you planned for it.

## Versioning

Version when you must break and cannot wait. Prefer *not* breaking.

- keep versions genuinely parallel; do not let v1 silently become v2's behavior
- state a support window and honor it
- for libraries, follow semver honestly — a breaking change in a minor release
  costs far more trust than a major bump costs convenience

## Before you ship an interface change

- [ ] classified as breaking or not, deliberately — not assumed
- [ ] consumers enumerated; external ones considered
- [ ] validation and error shape defined at the boundary
- [ ] defaults unchanged, or the change called out explicitly
- [ ] documented where consumers will actually look
- [ ] a test pins the contract, so a future refactor cannot silently alter it

If a change turns out to be breaking and the user did not ask for a breaking change:
**stop and tell them**, with the compatible alternative. Do not decide on their
behalf that the break is acceptable.
