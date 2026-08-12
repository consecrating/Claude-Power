# Command recipes

Copy-paste, low-byte commands. All assume a POSIX shell with `rg` and `jq`.

## Orientation in an unfamiliar repo

```bash
# Shape of the project, ~15 lines total
git ls-files | wc -l && git ls-files | sed 's|/.*||' | sort | uniq -c | sort -rn | head -15

# Languages by file count
git ls-files | rg -o '\.[a-z0-9]+$' | sort | uniq -c | sort -rn | head -10

# Entry points and config
git ls-files | rg -i '^(readme|makefile|dockerfile|package\.json|pyproject|go\.mod|cargo\.toml)' 

# Scripts available
jq -r '.scripts | to_entries[] | "\(.key): \(.value)"' package.json 2>/dev/null
```

## Finding code

```bash
# Which files mention it
rg -l 'PaymentIntent' --glob '!node_modules'

# How concentrated is it
rg -c 'PaymentIntent' --glob '*.ts' | sort -t: -k2 -rn | head

# Definition, not usages
rg -n '(class|function|const|interface|type) PaymentIntent\b'

# Where is it exported from
rg -n 'export .*PaymentIntent'

# Structural match (avoids comment/string false positives)
ast-grep -p 'async function $NAME($$$) { $$$ }' --lang ts

# Line numbers first, then read only that window
rg -n 'func main' cmd/server/main.go
sed -n '40,80p' cmd/server/main.go
```

## Git

```bash
git status --short
git log --oneline -10
git log -1 --format=%H
git diff --stat
git diff --name-only HEAD~1
git diff -U0 src/app.ts
git show --stat <sha>

# What changed in a file recently, compactly
git log --oneline -5 -- path/to/file

# Who last touched these lines
git log -1 --format='%an %ar' -L 40,60:src/app.ts

# Branch vs main, file list only
git diff --name-only main...HEAD

# Confirm a clean tree in one line
git status --porcelain | head -5
```

## JSON

```bash
jq -r .version package.json
jq -r '.dependencies | keys[]' package.json
jq -r '.dependencies | to_entries | length' package.json
jq -r '.[] | select(.state=="open") | .title' issues.json
jq -e . config.json >/dev/null && echo OK        # validate, no output on success
jq -r 'paths(scalars) | join(".")' config.json | head -30   # discover shape cheaply
```

## YAML

```bash
yq '.services | keys' docker-compose.yml
yq '.jobs | keys' .github/workflows/ci.yml
yq -r '.version' action.yml
```

## Builds and tests — redirect then interrogate

```bash
mkdir -p .kiro/.tmp

# Build
NO_COLOR=1 npm run build >.kiro/.tmp/build.log 2>&1 \
  || rg -n 'error|Error|ERR' .kiro/.tmp/build.log | head -30

# Tests (single run, never watch mode)
npm test -- --run >.kiro/.tmp/test.log 2>&1
tail -15 .kiro/.tmp/test.log                     # summary line
rg -n 'FAIL|✕|●|AssertionError' .kiro/.tmp/test.log | head -30

# Typecheck
npx tsc --noEmit >.kiro/.tmp/tsc.log 2>&1 || head -25 .kiro/.tmp/tsc.log

# Python
pytest -q >.kiro/.tmp/pytest.log 2>&1 || rg -n 'FAILED|Error' .kiro/.tmp/pytest.log | head -30

# Go
go build ./... 2>&1 | head -20
go test ./... 2>&1 | rg -v '^ok ' | head -20     # hide passing packages
```

## GitHub via `gh api`

Use REST endpoints with `--jq`. Avoid `gh pr create` / `gh pr` / `gh issue`
subcommands in sandboxes — they are GraphQL-backed and fail.

```bash
# Repo facts
gh api repos/{owner}/{repo} --jq '{default_branch,visibility}'

# Open PRs, titles only
gh api 'repos/{owner}/{repo}/pulls?state=open&per_page=10' --jq '.[] | "\(.number) \(.title)"'

# One PR's branch
gh api repos/{owner}/{repo}/pulls/42 --jq '.head.ref'

# PR review comments, compact
gh api repos/{owner}/{repo}/pulls/42/comments --jq '.[] | "\(.path):\(.line) \(.body)"'

# Issue body only
gh api repos/{owner}/{repo}/issues/7 --jq '.body'

# Create a PR (REST, works where `gh pr create` does not)
gh api repos/{owner}/{repo}/pulls -f title="..." -f body="..." -f head="branch" -f base="main" --jq '.html_url'

# CI failures only
gh run list --limit 3 --json databaseId,status,conclusion --jq '.[]'
gh run view <id> --log-failed | head -50
```

## Logs

```bash
rg -n 'ERROR|FATAL' app.log | head -30
rg -c 'ERROR' app.log                            # frequency first
tail -50 app.log
rg -n 'ERROR' -A 5 app.log | head -40            # error plus stack head
awk '/ERROR/{c++} END{print c}' app.log
```

## Change detection

```bash
md5sum src/app.ts                                 # before
md5sum src/app.ts                                 # after — compare hashes
md5sum $(git ls-files '*.ts') | md5sum            # fingerprint a whole set
```

## Filesystem probes

```bash
test -f path && echo yes
test -d dir && echo yes
wc -l < file
du -sh dir 2>/dev/null
find . -name '*.test.ts' -not -path './node_modules/*' | wc -l
```
