---
name: safe-refactoring
description: Use when restructuring code without changing behavior — renaming, extracting, splitting files, moving modules, removing duplication, changing internal structure, or cleaning up legacy code. Apply for requests mentioning refactor, clean up, reorganize, simplify, extract, rename, or modernize, and whenever a change touches many call sites at once.
metadata:
  version: "1.0"
  part-of: claude-power
---

# Safe refactoring

A refactor changes structure and **preserves observable behavior**. If behavior
changes, it is not a refactor — it is a rewrite, and it needs different scrutiny and
a different review.

The defining risk: refactors touch many places at once, so mistakes are wide rather
than deep, and they hide easily in a large diff.

## Preconditions

Do not start until all three hold:

1. **A behavior baseline exists.** Tests that pass now, or a recorded manual check.
   Without a baseline you cannot demonstrate preservation. If coverage is missing on
   the code you are about to move, add tests *first* — against current behavior,
   including any bugs. Locking in current behavior is the point.
2. **The blast radius is known.** Count the call sites before editing.
3. **The tree is clean.** Never mix a refactor with a behavior change in the same
   commit; the diff becomes unreviewable and bisection becomes useless.

```bash
git status --short                       # must be clean
rg -c 'OldName' --glob '!node_modules' | sort -t: -k2 -rn   # blast radius
npm test -- --run >.kiro/.tmp/baseline.log 2>&1; tail -5 .kiro/.tmp/baseline.log
```

## Sequence: one mechanical change at a time

Each step should be independently verifiable and independently revertable.

1. add the new form alongside the old
2. move call sites over incrementally
3. verify after each meaningful batch
4. remove the old form once nothing references it
5. verify again

Resist doing steps 1–4 in a single edit across 40 files. If step 3 fails you will not
know which of the 40 caused it.

## Prefer mechanical transformations

Ranked by safety:

1. **Tool-driven rename** (IDE/LSP rename symbol, `ast-grep` rewrite) — understands
   scope, ignores strings and comments
2. **Structural pattern rewrite** — `ast-grep -p '...' -r '...'`
3. **Targeted manual edits** — file by file, verified
4. **Regex over the whole repo** — last resort, high risk

```bash
# Structural, scope-aware
ast-grep -p 'oldFn($$$ARGS)' -r 'newFn($$$ARGS)' --lang ts

# If you must use sed, enumerate files first and diff before committing
rg -l '\boldFn\b' --glob '*.ts' | xargs sed -i 's/\boldFn\b/newFn/g'
git diff --stat && git diff -U0 | head -60
```

Never blind-`sed` across a repo. It will hit strings, comments, unrelated
identifiers, and generated files.

## Verify preservation, not just compilation

Compiling proves shape, not behavior. After each batch:

```bash
npx tsc --noEmit                                  # types
npm test -- --run >.kiro/.tmp/after.log 2>&1      # behavior
diff <(rg -o 'Tests:.*' .kiro/.tmp/baseline.log) <(rg -o 'Tests:.*' .kiro/.tmp/after.log)
```

The test **count** must not drop. A refactor that silently stops collecting a test
file looks like success and is not. Compare counts, not just pass/fail.

Also check what compilation cannot see:

- dynamic references: reflection, string-keyed lookups, DI containers
- names crossing a boundary: API fields, DB columns, env vars, config keys,
  serialized payloads, i18n keys, CSS classes, template strings
- public exports — renaming one is a breaking change for consumers, not a refactor

```bash
rg -n "'OldName'|\"OldName\"|\`OldName\`" --glob '!node_modules'   # string references
```

## Scope discipline

While refactoring you will see other things worth fixing. Do not. Note them and
continue. Mixed-purpose diffs are the main reason refactors get rejected or cause
outages — reviewers cannot tell structural noise from semantic change.

One refactor, one commit, one intent. If you find a real bug mid-refactor: finish or
stash the refactor, fix the bug separately, then resume.

## Commit shape

```
refactor: extract OrderPricing from OrderService

Pure move: no behavior change. Call sites updated; test count
unchanged at 214.
```

Say explicitly that behavior is unchanged, and give the evidence. Reviewers of a
refactor are checking exactly that claim — make it easy to confirm.

## When to stop and reconsider

- tests fail and the cause is not obvious → revert to the last verified state; do not
  debug forward through a half-finished refactor
- the diff has grown beyond what one reviewer can hold → split it
- you cannot preserve behavior without also changing an interface → stop; that is an
  API change and needs the `api-contract-design` skill and the user's agreement
- there is no baseline and you cannot create one → say so before proceeding; an
  unverifiable refactor is a risk the user should accept knowingly, not discover later
