---
name: pr-craft
description: Use when committing, branching, pushing, opening a pull request, writing a commit message or PR description, or responding to review comments. Apply whenever work needs to be delivered for human review, and on Kiro Web where the PR is the only surface the user can actually see the change on.
metadata:
  version: "1.0"
  part-of: claude-power
---

# PR craft

On Kiro Web the user has no terminal and no filesystem. **The pull request is the
product.** A correct change delivered in an unreviewable PR has not been delivered.

Optimize for one thing: a reviewer's ability to convince themselves the change is
correct, quickly.

## Branch and commit

```bash
git checkout -b feat/device-code-login       # descriptive; never work on main
git add src/auth/device.ts src/auth/index.ts # named files, never -A or .
git commit -m "Add device-code grant to auth service"
git push -u origin feat/device-code-login
```

Rules:

- never commit directly to `main` or `master` unless explicitly asked
- stage named files — `git add -A` sweeps up stray artifacts, logs, and secrets
- one logical change per commit; refactor and behavior change never share a commit
- never `--amend` after a pre-commit hook failure — fix, re-stage, make a new commit
- never `--no-verify`, never force-push, unless the user explicitly asks

## Commit messages

Subject: imperative mood, ≤50 characters, no trailing period. It completes the
sentence "this commit will…".

```
Add device-code grant to auth service

The CLI cannot use a redirect-based flow, so login was blocked on
headless machines. Adds RFC 8628 device authorization; the existing
password flow is untouched.

Rejected the implicit flow: it returns no refresh token, which
criterion 2 requires.
```

The body explains **why**, and what you rejected. The diff already shows *what*.
Rationale in the commit message is the cheapest documentation there is, and it is
exactly what someone doing archaeology in six months needs.

## PR description

Structure it so a reviewer can stop reading as soon as they have what they need:

```markdown
## What
One or two sentences. The change, not the journey.

## Why
The problem. Link the issue if there is one.

## How
Only the non-obvious decisions, and the alternatives rejected.

## Verification
What you actually ran and observed:
- `npm test -- --run` → 214 passed (was 212; 2 new)
- manual: device flow against staging returns a refresh token

## Notes for the reviewer
- Out of scope, noticed but not fixed: `src/legacy/auth.ts` duplicates
  token parsing — separate cleanup.
- Unverified: token expiry behavior; needs a real IdP.
```

The **Verification** section is the important one, and the one usually missing. State
what you ran and what you observed — not "tests pass". Declare anything unverified
explicitly; a reviewer who discovers an unverified claim themselves stops trusting the
whole description.

## Creating the PR

```bash
# Check for an existing PR before creating one
gh api "repos/{owner}/{repo}/pulls?state=all&per_page=10" \
  --jq '.[] | "\(.number) \(.state) \(.head.ref)"'

# Create via REST; gh pr create is GraphQL-backed and fails in sandboxes
gh api repos/{owner}/{repo}/pulls \
  -f title="Add device-code grant to auth service" \
  -f body="$(cat .kiro/.tmp/pr-body.md)" \
  -f head="feat/device-code-login" \
  -f base="main" \
  --jq '.html_url'
```

If a prior PR for this work is merged or closed, create a **new branch and a new PR**
rather than reusing the old branch.

Always give the user the resulting URL. If you pushed a branch without a PR, give the
branch URL. They cannot find it otherwise.

## Keep the diff reviewable

- if the diff exceeds roughly 400 lines of real change, consider splitting it
- separate mechanical churn (renames, formatting, generated files) into its own commit
  so semantic changes are visible
- never commit commented-out code, debug prints, or `.kiro/.tmp/` artifacts
- check before pushing:

```bash
git diff --cached --stat
git diff --cached | rg -n -i '(console\.log|dbg!|TODO|FIXME|api[_-]?key|secret|password|token)'
```

## Responding to review

On Kiro Web, `/kiro all` addresses every reviewer comment across the PR; `/kiro fix`
addresses one thread. Feedback from the task creator's PR comments also becomes
learnings applied to future work.

When responding:

- address the comment's **substance**, not only its letter — if a reviewer flags one
  instance of a pattern, check whether it recurs
- if you disagree, say so with reasoning rather than silently complying; a reviewer
  can be wrong, and unexplained compliance hides that
- do not force-push over review history; add commits so the reviewer can see the delta
- reply per thread with what changed, briefly
- run `capture-learning.sh add` for any comment that reflects a standing convention —
  a repeated review comment is a missing steering rule

## Never

- push secrets, credentials, or `.env` files
- force-push a shared branch, or rewrite history someone may have pulled
- open a PR whose description claims verification you did not perform
- merge your own PR unless explicitly asked
- bundle an unrelated "drive-by fix" into a PR — it costs the reviewer far more than
  it saves you
