---
inclusion: auto
name: verification-discipline
description: Use before reporting a task complete, or when about to claim something works, is fixed, passes, or is deployed. Apply when the user asks "is it done", "did it work", "are you sure", or when wrapping up a multi-step change, opening a PR, or summarizing results.
---

# Verification discipline

A green exit code proves a command ran. It does not prove the goal was met.

## The gap that causes false "done"

These all exit 0 while achieving nothing:

- a test command that matched zero tests
- a build that wrote to a path nobody reads
- `grep` inside a `|| true` chain
- a script whose real work sat behind an unmet `if`
- a formatter that "succeeded" because the file list was empty
- a push to a branch that no PR tracks

So: never infer success from the absence of an error. Infer it from the presence
of the intended effect.

## Procedure

1. **Re-read the original request.** Not your summary of it — the actual words.
   Long sessions drift; the goal is defined at the start, not by the last turn.
2. **Enumerate acceptance criteria explicitly.** Exact outputs, values, file
   paths, formats, counts, names. If the user said "all four", the number is four.
3. **Observe the artifact, not the process.** Read the file that was written.
   Count the rows. Curl the endpoint. Check the PR exists and its diff is right.
4. **Confirm the negative.** Did anything unintended change? `git status --short`
   and `git diff --stat` are near-free and catch collateral damage.
5. **Report per criterion**, marking each verified, failed, or unverifiable.

## Cheap, high-signal checks

```bash
# The work actually landed
git status --short && git diff --stat

# Tests actually selected something
<test-cmd> 2>&1 | tail -20        # look for the collected/ran count, not just "ok"

# The file has the content, not just a timestamp
rg -c 'expected-token' path/to/file

# Structured config still parses
jq -e . file.json >/dev/null && echo JSON-OK
```

## Reporting rules

- Never write "should work", "should be fixed", or "I've made sure that" as a
  substitute for having checked.
- If you could not verify something, say which criterion and why. An honest
  partial result is more useful than a confident wrong one.
- If verification fails, fix it and re-verify before reporting. Do not report a
  failure you had the means to resolve.
- Distinguish "I ran it and observed X" from "I reason that X follows."
