# Anti-patterns and their cheap rewrites

Each entry is a real habit that burns context, with the substitution.

## Reading

**Dumping a file to find one value**
```bash
cat package.json                          # ~2000 tokens
jq -r .version package.json               # ~5 tokens
```

**Reading a file you already read**
Nothing changed unless you changed it. If unsure:
```bash
md5sum src/app.ts                         # compare to the hash from before
```

**Reading a generated or vendored artifact**
`package-lock.json`, `yarn.lock`, `dist/*`, `*.min.js`, `*.map`, `node_modules/*`,
snapshots, migrations you don't need. These are enormous and near-zero signal.
Query them or skip them.

**`cat`-ing a log to find the failure**
```bash
cat build.log                             # 8000 lines
rg -n 'error|Error|ERR!' build.log | head -30
```

## Listing

**Recursive listing of a big tree**
```bash
ls -R .                                   # thousands of lines
git ls-files | head -50                   # respects .gitignore
find . -name '*.tsx' -not -path './node_modules/*' | head -30
```

**Checking existence by listing the parent**
```bash
ls -la src/components/                    # 200 entries
test -f src/components/Button.tsx && echo yes
```

## Searching

**Unscoped, uncapped search**
```bash
grep -r "user" .                          # matches node_modules, dist, lockfiles
rg -n 'user' --glob '!node_modules' --glob '*.ts' -m 20
```

**Searching for something too generic**
A one-word search returns hundreds of hits you then ignore. Add the distinguishing
token: `rg -n 'function getUser\b'` not `rg -n 'getUser'`.

**Text-searching structured data**
```bash
grep '"name"' package.json                # brittle, noisy
jq -r '.name' package.json
```

## Git

**Bare diff on an unknown changeset**
```bash
git diff                                  # could be 20k lines
git diff --stat                           # then diff only the files that matter
```

**Full log when you need one field**
```bash
git log -1                                # author, date, body, blank lines
git log -1 --format=%H
```

**`git add -A` then inspecting what happened**
Stage named files. You then already know what is staged.

## Shell hygiene

**Serial calls that could be one**
```bash
# three round-trips
mkdir -p out
cp a out/
echo done
# one
mkdir -p out && cp a out/ && echo done
```

**Letting tools print color and progress**
```bash
NO_COLOR=1 npm ci --silent 2>&1 | tail -5
```

**Leaving stderr noise in**
Add `2>/dev/null` when stderr is known-irrelevant. Keep it when it carries the
error you are hunting.

## API and network

**Fetching a whole object for one field**
```bash
gh api repos/o/r/pulls/42                        # large JSON
gh api repos/o/r/pulls/42 --jq '.head.ref'
```

**Listing without pagination limits**
```bash
gh api 'repos/o/r/issues?per_page=5&state=open' --jq '.[].title'
```

**Fetching a web page in full mode to check one fact**
Use a search phrase or truncated mode first.

## Process

**Narrating instead of doing**
Long explanations of what you are about to do cost the same as output. Do the work;
summarize once at the end.

**Re-deriving what a script could decide**
If a check is deterministic, put it in a script and run the script. Prose reasoning
is re-paid every session; a script is written once.

**Speculative reading "for context"**
Read what the task needs. Breadth-first reading of a repo is the single most
expensive habit there is — delegate that to a subagent if genuinely required.

**Repeating large content back to the user**
Do not echo a file you just wrote. Reference the path. The user can open it.
