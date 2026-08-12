---
name: security-review
description: Use when reviewing or writing code that handles authentication, authorization, user input, secrets, credentials, file paths, database queries, outbound requests, uploads, deserialization, or multi-tenant data. Apply before merging changes to auth or permissions, when the user asks about security or vulnerabilities, and when adding a dependency. Defensive review of your own project's code.
metadata:
  version: "1.0"
  part-of: claude-power
---

# Security review

Scope: reviewing and hardening code in the project you are working on. The aim is to
catch the small number of mistakes that cause most real incidents.

Review the **diff** and its reachable paths, not the whole codebase. A focused review
of what changed beats a shallow pass over everything.

## Secrets

The most common and most damaging mistake, because it is irreversible once pushed.

```bash
git diff --cached | rg -n -i '(api[_-]?key|secret|password|token|private[_-]key|BEGIN [A-Z ]*PRIVATE KEY|aws_access_key_id)'
rg -n -i 'sk-[a-zA-Z0-9]{16,}|ghp_[a-zA-Z0-9]{20,}|AKIA[0-9A-Z]{16}' --glob '!node_modules'
git ls-files | rg -i '^\.env$|\.env\.(local|prod)' 
```

Rules:

- never commit a real credential, even to a private repo, even temporarily
- `.env` is gitignored; `.env.example` holds placeholder values only
- never log, print, or echo a secret's value — refer to it by key name
- never put a secret in a URL, query string, or error message
- if one was committed: it is compromised. It must be **rotated**, not just removed.
  Deleting the file does not remove it from history.

## Authorization — the check everyone forgets

Authentication asks *who are you*. Authorization asks *are you allowed to touch this
specific object*. Missing object-level authorization is the most common serious flaw
in application code.

```ts
// Authenticated but NOT authorized — any logged-in user reads any order
const order = await db.orders.findById(req.params.id);

// Correct: scope the query by the caller's identity
const order = await db.orders.findOne({ id: req.params.id, userId: req.user.id });
```

Check every handler the diff touches:

- is there an ownership or tenancy check, not merely a logged-in check?
- is it enforced **server-side**? Client-side checks are UX, not security.
- is the tenant/user id taken from the *session*, never from a request parameter?
- do list endpoints filter by tenant, or return everything?
- can an id be enumerated to reach another tenant's data?
- are admin-only routes actually gated, including any new one added here?

## Injection

The rule is the same across every context: **never build a command, query, or path by
concatenating untrusted input.** Use the mechanism that separates code from data.

| Context | Do | Never |
|---|---|---|
| SQL | parameterized queries / bound params | string interpolation into SQL |
| Shell | argument arrays, no shell | `sh -c "cmd " + input` |
| HTML | escape by default; framework auto-escaping | `innerHTML`, `dangerouslySetInnerHTML` |
| Paths | resolve, then verify inside the allowed root | joining user input onto a base path |
| NoSQL | validate types | passing a user object straight into a query filter |
| Templates | pass data as variables | building the template from input |

Path traversal check:

```ts
const full = path.resolve(ROOT, userPath);
if (!full.startsWith(path.resolve(ROOT) + path.sep)) throw new Error('invalid path');
```

Quote and escape any user-supplied value interpolated into a shell command — or
better, avoid the shell entirely.

## Outbound requests (SSRF)

If a user can influence a URL your server fetches, they can reach your internal
network and cloud metadata endpoints.

- allowlist hosts and schemes; do not merely deny-list
- block private ranges, loopback, and link-local (`169.254.169.254`)
- re-validate after redirects; do not follow redirects blindly
- set timeouts and response size caps

## Input validation

Validate at the trust boundary, by allowlist, with a schema. Check type, range,
length, and format — not just presence. Reject rather than coerce. Cap sizes on
every input that could be large: bodies, uploads, arrays, pagination limits, and
anything that becomes a loop bound.

For uploads: verify content type by inspecting bytes, not the filename or client
header; store outside the web root; never derive a filesystem path from the
user-supplied name.

## Data exposure

- do the API responses in this diff include fields the caller should not see —
  password hashes, internal ids, other users' data, tokens?
- prefer explicit field selection over returning whole records
- are errors generic externally and detailed only in server logs?
- does logging capture PII, tokens, card numbers, or full request bodies?
- do timing or error differences reveal whether an account exists?

## Dependencies

```bash
npm audit --omit=dev 2>/dev/null | tail -20
pip-audit 2>/dev/null | tail -20
```

Before adding a dependency: is it maintained, widely used, and does it need to run
install scripts? A new transitive tree is new attack surface. See
`dependency-hygiene`.

## Crypto

Do not implement it. Use the platform's vetted library.

- passwords: `argon2` or `bcrypt` — never a raw hash, never MD5/SHA1
- randomness for tokens: a CSPRNG (`crypto.randomBytes`), never `Math.random()`
- comparing secrets: constant-time comparison
- no hardcoded keys or IVs; no ECB; no homemade constructions

## Reporting findings

For each issue state: **where**, **what an attacker could do**, **how to fix**.
Rank by exploitability and impact, not by how easy it is to describe.

Do not pad a review with theoretical issues — it buries the real ones. If the diff is
clean, say it is clean and note what you checked.

Anything exploitable and reachable in production is stop-and-report, immediately,
before continuing with other work.
