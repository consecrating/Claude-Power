# Budgeting a long task

## Why spend compounds

Context is re-sent every turn. A 3,000-token file you pulled in on turn 4 is still
being paid for on turn 40. The cost of a careless read is not its size — it is its
size multiplied by the number of turns remaining.

This has three consequences:

1. **Early waste is the most expensive waste.** A bloated orientation phase taxes
   the entire session.
2. **Pulling in a large artifact once can force compaction later**, which costs a
   summarization pass and loses detail permanently.
3. **Precision early buys headroom late**, when you actually need room for the diff
   you are writing.

## Phase budget

| Phase | Target share | Discipline |
|---|---|---|
| Orient | ~10% | filenames, counts, structure — not contents |
| Locate | ~15% | `rg -l` → `rg -c` → `rg -n` → targeted read |
| Understand | ~20% | read only the ranges that matter; delegate breadth |
| Change | ~40% | the actual work |
| Verify | ~15% | targeted checks, not full re-reads |

If orientation is eating half the budget, stop and delegate the exploration to a
subagent so its transcript stays out of your context.

## Choosing where exploration happens

| Situation | Do this |
|---|---|
| Known file, known symbol | direct `rg -n` then targeted read |
| Known file, unknown structure | `rg -n` for anchors, `sed -n` a window |
| Unknown files, specific symbol | `rg -l` then narrow |
| Open-ended ("how does X work") | delegate to a subagent |
| Repo-wide audit | delegate, or script it and read the script's summary |

A subagent's cost to you is its final report. A wide `rg` dumped into your own
context costs you its entire output, forever.

## Signals you are overspending

- You have read the same file more than once.
- You ran a command whose output you scrolled past without using.
- You read a file "to understand the project" without a specific question.
- Your last three tool calls each returned more than 100 lines.
- You are summarizing tool output back to the user verbatim.
- You read a lockfile, a build artifact, or `node_modules`.

## Precision beats parsimony

The goal is not "few tool calls." Ten calls returning 5 lines each is far cheaper
than one call returning 2,000. Do not batch-read files to "save calls" — that
optimizes the wrong variable.

Conversely, do not make a call you do not need in order to look thorough.

## When compaction is near

Compaction is automatic and irreversible; you may not get a warning. Before a long
operation, ensure durable state is on disk (see the `context-durability` skill).
Assume any un-persisted decision will be lost.

Practical habit: persist before you spend. Write the checkpoint, then run the
expensive step.

## Credits vs tokens

Tokens are context bytes. Credits are model invocations. They optimize differently:

- Fewer, better-targeted turns reduce **credits**.
- Smaller tool output reduces **tokens**.
- A hook with `action.type: "agent"` starts a new model loop and costs **credits**;
  `"command"` hooks cost none. Prefer command actions.
- Asking a clarifying question costs one cheap turn and can save an entire wrong
  implementation. That is a good trade — do not conflate frugality with guessing.
