---
name: dependency-hygiene
description: Use when adding, removing, upgrading, or auditing dependencies, when a lockfile conflicts, when a build breaks after an install, or when the user asks about updates, vulnerabilities, bundle size, or supply-chain risk. Apply before introducing any new package and before any major version bump.
metadata:
  version: "1.0"
  part-of: claude-power
---

# Dependency hygiene

Every dependency is permanent code you did not write, running with your privileges,
maintained by someone else. Adding one is a long-term commitment; treat it as a
design decision, not a convenience.

## Before adding anything

Ask, in this order:

1. **Does the standard library or an existing dependency already do this?** Check
   before adding. Duplicate capability is the most common avoidable dependency.
2. **How much of it will I use?** A whole package for one small function is usually
   worse than the function.
3. **Is it maintained?** Recent releases, open issues being answered, more than one
   maintainer.
4. **How heavy is the tree?** One direct dependency can pull dozens of transitive
   ones — that is the real cost.
5. **Does it need install scripts or native builds?** Install scripts execute
   arbitrary code on every developer machine and CI runner.
6. **Is the license compatible** with how this project is distributed?

```bash
# What does it actually pull in, before committing to it
npm info <pkg> version dist-tags time.modified
npm view <pkg> dependencies
```

Be alert to typosquatting: verify the exact package name against the project's own
documentation, not a guess or a memory. A one-character difference is a common attack.

## Adding it properly

- pin sensibly and **always commit the lockfile** — reproducible installs are the
  point of having one
- put build- and test-only packages in dev dependencies; shipping them enlarges the
  production attack surface
- use `npm ci` (not `npm install`) in CI so the lockfile is authoritative
- record *why* the dependency was added — future maintainers cannot infer it
  (`memory.sh note "added zod: runtime validation at API boundary"`)

## Upgrading

Separate the three kinds and never mix them in one commit:

- **patch/minor security fixes** — apply promptly, low risk
- **minor feature updates** — batch them, run the suite
- **major versions** — one at a time, read the changelog, expect breaking changes

```bash
npm outdated                                   # what is behind
npm audit --omit=dev | tail -20                # what is vulnerable in production
npm update --save                              # in-range updates
npm i <pkg>@latest                             # one major, deliberately
```

For a major bump: read the migration guide *first*, then upgrade, then run the full
suite, then check for deprecation warnings in the output. Do not upgrade several
majors at once — when it breaks you will not know which one did it.

## Lockfile conflicts

Never hand-edit a lockfile, and never resolve its conflict markers manually.
Regenerate it:

```bash
git checkout --theirs package-lock.json   # or --ours; either base is fine
npm install                                # regenerate from package.json
npm ci && npm test -- --run                # prove the result installs and passes
```

Then verify no unintended version drift crept in: `git diff --stat package-lock.json`
should be proportionate to the change you intended.

## Vulnerability triage

Not every advisory matters equally. Assess before acting:

- Is the vulnerable package in production, or only in dev/build?
- Is the vulnerable **code path** reachable from your usage?
- Is there a fixed version, and is it a breaking upgrade?
- Is the advisory a denial-of-service in a build tool, or remote code execution in a
  request handler? Those warrant very different urgency.

Do not run a blanket auto-fix that performs major upgrades unattended — that trades a
possible vulnerability for a probable outage. Fix what is reachable, deliberately.

If a vulnerability has no fix available, report it with the reachability assessment
and the mitigation options rather than silently leaving it.

## Removing dependencies

Deleting a package is one of the highest-value changes available. When you remove
code that used one:

```bash
rg -n "from ['\"]<pkg>|require\(['\"]<pkg>" --glob '!node_modules' | wc -l   # 0 = safe
npm uninstall <pkg>
npm ci && npm test -- --run
```

Check for unused dependencies periodically — they carry all the risk and none of the
benefit.

## Reporting

State what changed and why, with the risk assessment:

```
Added zod@3 (runtime validation at the API boundary; 0 transitive deps, MIT).
Upgraded express 4 -> 5 (breaking: router changes; migration applied, 214 tests pass).
Left lodash advisory GHSA-xxxx unfixed: dev-only, not reachable in production.
```

Never upgrade a major version, add a dependency with a nonstandard license, or change
the package manager without telling the user explicitly.
