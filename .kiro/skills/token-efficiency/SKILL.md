---
name: token-efficiency
description: Use when a task involves reading files, searching a codebase, inspecting git history or diffs, running builds or tests, calling APIs, or processing JSON/YAML/logs — anything where output size drives cost. Also apply for requests mentioning tokens, credits, cost, budget, speed, context limits, large files, or truncated output. Governs how to shape every tool call so it returns the fewest bytes that still answer the question.
metadata:
  version: "1.0"
  part-of: claude-power
---

# Token efficiency

Cost is driven by **bytes returned into context**, not by number of tool calls.
Three small targeted calls beat one call that dumps 5,000 lines. Optimize for
information density, not call count.

## The two questions

Before every tool call:

1. **Can I avoid this call entirely?** Do I already know this? Did an earlier call
   or a subagent already return it? Re-reading what you already read is pure waste.
2. **If I must call, how do I minimize bytes returned?** Filter, project, cap, and
   silence at the source — never post-filter in your head after pulling everything.

## Core rules

**Never dump to find.** Do not read a whole file to get one value, or list a whole
directory to check one path. Query for exactly the field, line, or count you need.

**Cap every unbounded output.** Any command whose size you cannot predict gets
`| head -N`, `-m N`, `--max-count`, `-n N`, or `| wc -l` first. Discover the size
before you request the content.

**Count before you read.** `rg -c pattern` or `wc -l` costs a few bytes and tells
you whether the real read is 10 lines or 10,000.

**Project, don't post-filter.** `jq -r '.items[].name'` not `cat file.json`.
`gh api ... --jq '.head.ref'` not fetching the whole PR object.
`git log --format='%h %s'` not `git log`.

**Silence success.** Working tools should say nothing. Use `-q`, `--quiet`,
`--silent`, `NO_COLOR=1`, `2>/dev/null`. ANSI color codes are pure token tax.

**Redirect, then interrogate.** Builds and test suites produce enormous output that
is 99% irrelevant. Send it to a file, then extract only failures:

```bash
npm test >.kiro/.tmp/test.log 2>&1 || rg -n 'FAIL|✕|Error|failed' .kiro/.tmp/test.log | head -40
```

**Batch dependent work, parallelize independent work.** Chain with `&&` in one
shell call when steps depend on each other. When calls are independent, issue them
in the same tool block so they run concurrently.

**Track change by hash.** To know whether a file changed, compare `md5sum` output,
not file contents.

**Prefer coreutils over a Python one-liner** for simple transforms — less to write,
less to read back, no interpreter startup.

## Structured data

Match the tool to the format. Never parse structured data with `grep` when a real
query tool exists.

| Format | Tool | Example |
|---|---|---|
| JSON | `jq` | `jq -r '.dependencies \| keys[]' package.json` |
| YAML | `yq` | `yq '.services \| keys' docker-compose.yml` |
| CSV/TSV | `awk`, `cut` | `cut -d, -f2 data.csv \| sort -u` |
| GitHub API | `gh api --jq` | `gh api repos/o/r/pulls/1 --jq '.head.ref'` |
| XML/HTML | `xmllint --xpath` | targeted node extraction |

## Code search

Escalate only as needed — stop at the first step that answers the question:

1. `rg -l pattern --glob '*.ts'` — which files? (filenames only)
2. `rg -c pattern --glob '*.ts'` — how many hits per file?
3. `rg -n pattern --glob '*.ts' -m 5` — the actual lines, capped
4. `rg -n -C 3 pattern path/to/one/file.ts` — context, one file only
5. read the file — only once you know the specific line range

Use `ast-grep` when structure matters more than text (`ast-grep -p 'function $A($$$) { $$$ }'`),
which avoids the false positives that force wider text searches.

## Reading files

- Know the line range before reading. Get it from `rg -n`.
- Read that range, not the file.
- For unknown large files: `wc -l`, then `sed -n '1,40p'` to see shape, then target.
- Never read a lockfile, minified bundle, binary, or generated artifact. Query it.

## Git

```bash
git status --short                    # not `git status`
git log --oneline -10                 # not `git log`
git diff --stat                       # always before a real diff
git diff --name-only                  # just what changed
git diff -U0 path/to/file             # no context lines
git show --stat <sha>                 # shape before content
```

Never run a bare `git diff` on an unknown changeset — check `--stat` first.

## Delegation

Delegating to a subagent moves exploration cost out of your context: you pay for
its summary, not its transcript. Use it for open-ended investigation ("how does
auth work here"). Do not use it for a question you can answer with one `rg`.

Never re-read files a subagent already reported on, and never re-invoke a subagent
on the same question reworded.

## Reference material

- `references/anti-patterns.md` — the expensive mistakes, with cheap rewrites
- `references/command-recipes.md` — copy-paste recipes for git, search, JSON, logs,
  builds, and GitHub API
- `references/budgeting.md` — how to allocate effort on a long task, and how
  context spend compounds across turns
