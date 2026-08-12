---
name: test-strategy
description: Use when writing, fixing, or reviewing tests, when deciding what to test, when tests are flaky or slow, or when coverage is discussed. Apply for requests to add tests, improve testing, fix a failing suite, or verify a change. Focuses tests on defects that actually occur rather than on coverage percentage.
metadata:
  version: "1.0"
  part-of: claude-power
---

# Test strategy

A test earns its keep by failing when the code is wrong. A test that cannot fail —
or that fails for reasons unrelated to correctness — is a liability: it costs time to
run, time to maintain, and it manufactures false confidence.

Do not add tests unless asked, or unless the change genuinely needs them for
verification. When you do add them, make them count.

## Write the failure first

Before trusting any new test, see it fail for the intended reason.

- for a bug fix: write the test, watch it fail, then fix, then watch it pass
- for new behavior: write the assertion first, or revert your implementation briefly
  to confirm the test catches its absence
- a test that passed the first time you ran it, against unwritten code, is testing
  nothing

This single habit eliminates most worthless tests.

## What to test

Target the places defects concentrate:

- **boundaries** — 0, 1, empty, null, max, off-by-one, first/last
- **branches your change introduced** — every new conditional path
- **error paths** — the untested `catch` is where production incidents live
- **contracts** — what callers are promised: shapes, invariants, ordering, idempotency
- **the specific bug** — every fix gets a test that pins it
- **round trips** — encode/decode, serialize/deserialize, write/read

## What not to test

- getters, setters, and pure pass-throughs
- framework or library behavior — that is their test suite's job
- implementation details: private methods, call order, internal structure. These
  tests break on every refactor while catching no defects.
- mock behavior. `expect(mock).toHaveBeenCalled()` as the *only* assertion tests your
  mock setup, not your code.
- generated code, and reimplementations of the code under test in the test itself

## Test the contract, not the mechanism

```
Brittle:  expect(service.cache.entries.length).toBe(1)
Durable:  expect(await service.get('k')).toBe('v')          // second call still correct
```

Assert on observable outcomes. If a refactor that preserves behavior breaks your
test, the test was measuring the wrong thing.

## Flakiness is a defect

A flaky test is worse than no test: it trains everyone to ignore failures. Never
retry, skip, or delete a flaky test to get green. Find the nondeterminism:

| Cause | Fix |
|---|---|
| real time / `Date.now()` | inject a clock or freeze time |
| `sleep` waiting for async | wait on the actual condition |
| shared or leaked state | isolate per test; reset fixtures |
| test order dependence | make each test independent; run in random order to prove it |
| real network | stub at the boundary |
| unordered collections | sort before comparing, or assert set-wise |
| parallel workers sharing a resource | give each worker its own, or serialize that test |

## Mock only at boundaries

Mock what you do not own and cannot control: network, clock, randomness, filesystem
when it is incidental, third-party services, payment providers.

Do not mock your own internals. Heavily mocked tests pass while the real integration
is broken — every unit passes, the system does not work. If mocking your own code is
the only way to test it, that is a design signal, not a testing problem.

## Diagnosing a failing suite

```bash
npm test -- --run >.kiro/.tmp/test.log 2>&1
tail -20 .kiro/.tmp/test.log                    # summary: how many ran, not just pass/fail
rg -n 'FAIL|✕|AssertionError' .kiro/.tmp/test.log | head -20
npm test -- -t 'the failing test'               # then isolate one
```

Always check the **collected count**. A suite that reports success having run zero
tests is the classic false green — see `verification-discipline`.

Fix the code, not the assertion. Changing an assertion to match wrong output is
deleting the test while appearing to keep it.

## Coverage

Coverage tells you what was *executed*, not what was *verified*. 100% coverage with
no meaningful assertions is worthless; 60% coverage concentrated on branches, error
paths, and boundaries is strong.

Use coverage to find untested error paths. Never as a target to satisfy.

## Absolute rules

- Never delete or `skip` a test to make a suite pass. Fix it or report it.
- Never weaken an assertion to accommodate wrong behavior.
- Never add `|| true`, `--passWithNoTests`, or retry wrappers to hide failure.
- Never claim tests pass without having run them and read the count.
