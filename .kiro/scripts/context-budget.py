#!/usr/bin/env python3
"""Measure and audit the token cost of a Kiro configuration.

``validate-frontmatter.py`` checks whether config is *correct*. This checks
whether it is *affordable*, and whether it can actually be selected from.

Two questions it answers that nothing else here does:

1. **What does this config cost before I type anything?** Skill bodies load on
   demand, but every skill's name and description load at session start, and
   ``inclusion: always`` steering loads in full. With enough skills installed
   that standing charge stops being small, and nothing measures it.

2. **Can the right skill still be picked?** Skills are selected by matching a
   request against descriptions. Two skills with near-identical descriptions do
   not give you two options; they give you a coin flip. Adding skills past that
   point makes selection worse, not better, and the failure is silent.

Zero dependencies, so it always runs. When ``opus5lean`` (Claude-Opus5) is
importable, pricing and exact token counts come from there; otherwise a local
estimator is used and every number is labelled as an estimate.

Usage:
    python3 .kiro/scripts/context-budget.py [--root .]
    python3 .kiro/scripts/context-budget.py --budget 2000     # CI gate
    python3 .kiro/scripts/context-budget.py --json
    python3 .kiro/scripts/context-budget.py --sessions-per-day 20

Exit 0 = within budget and no errors, 1 = budget exceeded or an error found.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# --------------------------------------------------------------------------
# Token counting
# --------------------------------------------------------------------------

try:  # Prefer the maintained implementation when the sibling repo is present.
    from opus5lean.pricing import PRICES  # noqa: F401
    from opus5lean.tokens import count as _opus5_count

    HAVE_OPUS5LEAN = True
except Exception:
    HAVE_OPUS5LEAN = False

# Fallback rates, USD per million tokens, for claude-opus-5. Only consulted
# when opus5lean is absent; install Claude-Opus5 for the maintained table.
FALLBACK_INPUT_RATE = 5.00
MILLION = 1_000_000

_PIECE = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?|\d+|\s+|[^\sA-Za-z\d]+")


def _estimate(text: str) -> int:
    """Offline token estimate: classify pieces, apply per-class ratios."""
    total = 0
    for m in _PIECE.finditer(text):
        piece = m.group()
        if piece.isspace():
            total += piece.count("\n")
        elif piece.isalpha():
            total += 1 if len(piece) <= 5 else max(1, round(len(piece) / 4.2))
        elif piece.isdigit():
            total += max(1, round(len(piece) / 3))
        else:
            total += max(1, round(len(piece) / 2))
    return max(1, total) if text.strip() else 0


def count(text: str, *, exact: bool = False) -> tuple[int, str]:
    """Return ``(tokens, method)``. ``method`` is "exact" or "estimate"."""
    if exact and HAVE_OPUS5LEAN:
        try:
            r = _opus5_count(text, exact=True)
            return int(r.tokens), str(r.method)
        except Exception:
            pass
    return _estimate(text), "estimate"


def usd(tokens: int) -> float:
    """Input-token cost in USD for claude-opus-5."""
    rate = FALLBACK_INPUT_RATE
    if HAVE_OPUS5LEAN:
        try:
            rate = PRICES["claude-opus-5"].input
        except Exception:
            pass
    return tokens / MILLION * rate


# --------------------------------------------------------------------------
# Frontmatter parsing (no PyYAML: this must always run)
# --------------------------------------------------------------------------

_FM = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?", re.S)


_BLOCK_MARKERS = {">", "|", ">-", "|-", ">+", "|+"}


def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Return ``(fields, body)`` for a leading YAML frontmatter block.

    Deliberately not a YAML parser — this must run with no dependencies, so
    PyYAML cannot be assumed. It reads top-level ``key: value`` pairs and, when
    a key's inline value is empty or a block marker, folds the indented lines
    beneath it into one string.

    That folding is the point. ``fileMatchPattern`` is normally written as a
    block sequence:

        fileMatchPattern:
          - ".kiro/skills/**/SKILL.md"

    A parser that only reads inline scalars sees an empty value and concludes
    the key is missing, which produces a confident and wrong "this can never
    trigger" error. Field *validity* remains ``validate-frontmatter.py``'s job;
    this only needs presence and length.
    """
    m = _FM.match(text)
    if not m:
        return {}, text

    fields: dict[str, str] = {}
    lines = m.group(1).splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#") or line[:1] in " \t":
            i += 1
            continue

        key, sep, value = line.partition(":")
        if not sep:
            i += 1
            continue
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]

        if not value or value in _BLOCK_MARKERS:
            # Fold the indented block beneath this key into a single value, so
            # presence and size are both measurable.
            collected: list[str] = []
            j = i + 1
            while j < len(lines) and (not lines[j].strip() or lines[j][:1] in " \t"):
                if lines[j].strip():
                    collected.append(lines[j].strip().lstrip("- ").strip())
                j += 1
            value = " ".join(collected)
            i = j
        else:
            i += 1

        fields[key] = value
    return fields, text[m.end():]


# --------------------------------------------------------------------------
# Model
# --------------------------------------------------------------------------

RESERVED_STEERING = {"product.md", "tech.md", "structure.md"}

_STOP = frozenset("""
a an and are as at be been but by for from has have how if in into is it its of on or
that the their them then there these this to use used uses using was were what when
where which who why will with you your own not no also more most can cause apply also
""".split())

# A description shorter than this rarely contains enough signal to match a
# request reliably; longer than this is paid for at every session start.
DESC_MIN_CHARS = 40
DESC_MAX_CHARS = 600

# Jaccard overlap on content words above which two descriptions compete for the
# same requests. Calibrated against a real 63-skill install, where the genuine
# near-duplicate pair (two skills both covering theme.json, templates, template
# parts and patterns) scored 0.36 and everything unrelated sat below 0.25. A
# stricter bar looked clean while the ambiguity was still there.
SIMILAR_THRESHOLD = 0.35

# How many of the closest pairs to report even when none cross the threshold,
# so "no collisions" is a reading rather than an absence of output.
SIMILAR_REPORT_TOP = 3


@dataclass
class Item:
    """One config file and its measured cost."""

    kind: str  # "agents" | "steering" | "skill" | "reference"
    path: Path
    name: str
    tokens_always: int = 0  # loaded every session (or every turn, for AGENTS.md)
    tokens_on_demand: int = 0  # loaded only when triggered
    inclusion: str = ""
    description: str = ""

    @property
    def rel(self) -> str:
        return self.name


@dataclass
class Finding:
    level: str  # "error" | "warn" | "info"
    code: str
    message: str


@dataclass
class Report:
    root: Path
    method: str
    items: list[Item] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)

    # -- cost ----------------------------------------------------------------

    @property
    def per_turn(self) -> int:
        return sum(i.tokens_always for i in self.items if i.kind == "agents")

    @property
    def per_session(self) -> int:
        """Standing charge: AGENTS.md + always-steering + all skill descriptions."""
        return sum(i.tokens_always for i in self.items)

    @property
    def on_demand(self) -> int:
        return sum(i.tokens_on_demand for i in self.items)

    def always_contributors(self) -> list[Item]:
        return sorted(
            (i for i in self.items if i.tokens_always > 0),
            key=lambda i: -i.tokens_always,
        )

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "error"]

    @property
    def warns(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "warn"]

    def counts(self, kind: str) -> int:
        return sum(1 for i in self.items if i.kind == kind)


# --------------------------------------------------------------------------
# Scanning
# --------------------------------------------------------------------------


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]{3,}", text.lower()) if w not in _STOP}


def scan(root: Path, *, exact: bool = False) -> Report:
    """Measure every config file under ``root``."""
    method = "estimate"
    rep = Report(root=root, method=method)
    kiro = root / ".kiro"

    def read(p: Path) -> str:
        try:
            return p.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            rep.findings.append(Finding("error", "unreadable", f"{p}: {exc}"))
            return ""

    # -- AGENTS.md: the only layer paid on every turn ---------------------
    agents = root / "AGENTS.md"
    if agents.is_file():
        tok, method = count(read(agents), exact=exact)
        rep.items.append(Item("agents", agents, "AGENTS.md", tokens_always=tok))
    else:
        rep.findings.append(
            Finding("info", "no-agents", "no AGENTS.md — no per-turn standing charge")
        )

    # -- steering ---------------------------------------------------------
    for path in sorted((kiro / "steering").glob("*.md")) if (kiro / "steering").is_dir() else []:
        text = read(path)
        fm, body = split_frontmatter(text)
        inclusion = fm.get("inclusion", "").strip() or "(unset)"
        desc = fm.get("description", "")

        if path.name in RESERVED_STEERING:
            rep.findings.append(
                Finding(
                    "error",
                    "reserved-steering",
                    f"steering/{path.name} is a reserved foundation filename your repo owns; "
                    "shipping it overwrites project context",
                )
            )

        body_tok, method = count(text, exact=exact)
        if inclusion == "always":
            # Loaded in full, every session.
            item = Item("steering", path, f"steering/{path.name}",
                        tokens_always=body_tok, inclusion=inclusion, description=desc)
            if body_tok > 700:
                rep.findings.append(
                    Finding(
                        "warn",
                        "fat-always-steering",
                        f"steering/{path.name} is always-on at ~{body_tok:,} tokens; "
                        "consider inclusion: fileMatch so it loads only when relevant",
                    )
                )
        else:
            # Only the description is standing cost; the body loads on trigger.
            desc_tok, _ = count(desc, exact=exact) if desc else (0, method)
            item = Item("steering", path, f"steering/{path.name}",
                        tokens_always=desc_tok, tokens_on_demand=body_tok,
                        inclusion=inclusion, description=desc)
            if inclusion == "(unset)":
                rep.findings.append(
                    Finding("warn", "steering-no-inclusion",
                            f"steering/{path.name} has no inclusion field; "
                            "behaviour depends on Kiro's default rather than intent")
                )
            if inclusion == "fileMatch" and not fm.get("fileMatchPattern"):
                rep.findings.append(
                    Finding("error", "filematch-no-pattern",
                            f"steering/{path.name} is inclusion: fileMatch with no "
                            "fileMatchPattern, so it can never trigger")
                )
        rep.items.append(item)

    # -- skills -----------------------------------------------------------
    skills_dir = kiro / "skills"
    for sk in sorted(p for p in skills_dir.glob("*") if p.is_dir()) if skills_dir.is_dir() else []:
        skill_md = sk / "SKILL.md"
        if not skill_md.is_file():
            rep.findings.append(
                Finding("error", "no-skill-md",
                        f"skills/{sk.name}/ has no SKILL.md, so it never loads")
            )
            continue

        text = read(skill_md)
        fm, body = split_frontmatter(text)
        name = fm.get("name", "").strip()
        desc = fm.get("description", "").strip()

        if not name:
            rep.findings.append(
                Finding("error", "skill-no-name",
                        f"skills/{sk.name}/SKILL.md has no name field")
            )
        elif name != sk.name:
            rep.findings.append(
                Finding("warn", "skill-name-mismatch",
                        f"skills/{sk.name}/ declares name: {name} — directory and name "
                        "disagree, which makes the skill hard to reference")
            )

        # The standing charge is name + description. No description means the
        # skill is installed but can never be matched to a request.
        if not desc:
            rep.findings.append(
                Finding("error", "skill-no-description",
                        f"skills/{sk.name}/ has no description, so it can never activate "
                        "— it is pure dead weight")
            )
        else:
            if len(desc) < DESC_MIN_CHARS:
                rep.findings.append(
                    Finding("warn", "desc-too-short",
                            f"skills/{sk.name}/ description is {len(desc)} chars; too little "
                            "signal to match requests reliably")
                )
            if len(desc) > DESC_MAX_CHARS:
                rep.findings.append(
                    Finding("warn", "desc-too-long",
                            f"skills/{sk.name}/ description is {len(desc):,} chars and is paid "
                            "for at every session start")
                )

        always_tok, method = count(f"{name}: {desc}", exact=exact)
        body_tok, _ = count(body, exact=exact)
        rep.items.append(
            Item("skill", skill_md, f"skills/{sk.name}", tokens_always=always_tok,
                 tokens_on_demand=body_tok, description=desc)
        )

        # references: on-demand only, but dead ones are still clutter
        refs = sorted((sk / "references").glob("*.md")) if (sk / "references").is_dir() else []
        for ref in refs:
            ref_tok, _ = count(read(ref), exact=exact)
            rep.items.append(
                Item("reference", ref, f"skills/{sk.name}/references/{ref.name}",
                     tokens_on_demand=ref_tok)
            )
            if ref.name not in body:
                rep.findings.append(
                    Finding("info", "unreferenced-reference",
                            f"skills/{sk.name}/references/{ref.name} is not mentioned in "
                            "SKILL.md, so nothing will ever load it")
                )

    rep.method = method
    _detect_collisions(rep)
    return rep


def _detect_collisions(rep: Report) -> None:
    """Flag skills whose descriptions compete for the same requests.

    Selection works by matching a request against descriptions. Two skills
    describing the same territory do not offer two options, they offer a coin
    flip — and the loser silently never runs.
    """
    skills = [i for i in rep.items if i.kind == "skill" and i.description]
    profiles = [(i, _words(i.description)) for i in skills]

    scored: list[tuple[float, Item, Item]] = []
    for idx, (a, wa) in enumerate(profiles):
        for b, wb in profiles[idx + 1:]:
            if not wa or not wb:
                continue
            scored.append((len(wa & wb) / len(wa | wb), a, b))

    scored.sort(key=lambda t: -t[0])
    flagged = [t for t in scored if t[0] >= SIMILAR_THRESHOLD]

    for overlap, a, b in flagged:
        rep.findings.append(
            Finding(
                "warn",
                "description-collision",
                f"{a.rel} and {b.rel} descriptions overlap {overlap:.0%}; "
                "a request matching both will pick unpredictably, and the loser "
                "silently never runs",
            )
        )

    # Report the closest pairs even when none cross the line. Silence here is
    # ambiguous — it could mean "no overlap" or "threshold set too high" — and
    # the second is how a real collision stays hidden.
    if not flagged and scored:
        nearest = ", ".join(
            f"{a.rel}/{b.rel} {ov:.0%}" for ov, a, b in scored[:SIMILAR_REPORT_TOP]
        )
        rep.findings.append(
            Finding(
                "info",
                "nearest-descriptions",
                f"no pair crossed {SIMILAR_THRESHOLD:.0%}; closest were {nearest}",
            )
        )


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------


def table(headers: list[str], rows: list[list[str]], indent: str = "  ") -> str:
    widths = [len(h) for h in headers]
    for r in rows:
        for i, c in enumerate(r):
            widths[i] = max(widths[i], len(str(c)))

    def numeric(i: int) -> bool:
        vals = [str(r[i]) for r in rows if str(r[i]).strip()]
        return bool(vals) and all(
            v.lstrip("~$").rstrip("%").replace(",", "").replace(".", "").isdigit() for v in vals
        )

    align = [numeric(i) for i in range(len(headers))]

    def fmt(cells: list[str]) -> str:
        return indent + "  ".join(
            str(c).rjust(widths[i]) if align[i] else str(c).ljust(widths[i])
            for i, c in enumerate(cells)
        ).rstrip()

    sep = indent + "  ".join("-" * w for w in widths)
    return "\n".join([fmt(headers), sep, *(fmt(r) for r in rows)])


def render(rep: Report, *, top: int, sessions_per_day: int, budget: int | None) -> str:
    mark = "" if rep.method == "exact" else "~"
    lines: list[str] = []

    lines.append(f"Kiro config budget  root={rep.root}  tokens={rep.method}")
    lines.append("")
    lines.append(
        f"  {rep.counts('skill')} skills, {rep.counts('steering')} steering, "
        f"{rep.counts('reference')} reference files"
    )
    lines.append("")

    # -- the standing charge ---------------------------------------------
    lines.append("  Standing cost, paid before you type anything:")
    lines.append("")
    rows = [
        ["per turn (AGENTS.md)", f"{mark}{rep.per_turn:,}", f"${usd(rep.per_turn):.4f}"],
        ["per session (startup)", f"{mark}{rep.per_session:,}", f"${usd(rep.per_session):.4f}"],
        ["on demand (not paid until triggered)", f"{mark}{rep.on_demand:,}", "-"],
    ]
    lines.append(table(["layer", "tokens", "cost"], rows))
    lines.append("")

    monthly_sessions = sessions_per_day * 30
    monthly = usd(rep.per_session) * monthly_sessions
    lines.append(
        f"  At {sessions_per_day} sessions/day the startup charge alone is "
        f"${monthly:.2f}/month ({monthly_sessions:,} sessions), before any work."
    )
    lines.append("")

    # -- biggest contributors -------------------------------------------
    contributors = rep.always_contributors()[:top]
    if contributors:
        lines.append(f"  Largest contributors to the per-session charge (top {len(contributors)}):")
        lines.append("")
        rows = []
        total = rep.per_session or 1
        for i in contributors:
            label = i.rel + (f"  [{i.inclusion}]" if i.kind == "steering" else "")
            rows.append([label, f"{mark}{i.tokens_always:,}", f"{i.tokens_always / total * 100:.0f}%"])
        lines.append(table(["file", "tokens", "share"], rows))
        lines.append("")

    # -- findings --------------------------------------------------------
    for level, heading in (("error", "Errors"), ("warn", "Warnings"), ("info", "Notes")):
        group = [f for f in rep.findings if f.level == level]
        if not group:
            continue
        lines.append(f"  {heading} ({len(group)}):")
        for f in group:
            lines.append(f"    [{f.code}] {f.message}")
        lines.append("")

    # -- verdict ---------------------------------------------------------
    if budget is not None:
        over = rep.per_session > budget
        verdict = "OVER" if over else "within"
        lines.append(
            f"  Budget: {mark}{rep.per_session:,} / {budget:,} tokens per session — {verdict}"
        )
        if over:
            lines.append(
                f"    {rep.per_session - budget:,} tokens over. Remove unused skills, or move "
                "always-on steering to fileMatch."
            )
        lines.append("")

    if rep.method != "exact":
        lines.append("  tokens are estimated (typically within ~10-15%); --exact confirms, unbilled")
    if not HAVE_OPUS5LEAN:
        lines.append("  opus5lean not importable — fallback price table; install Claude-Opus5")

    return "\n".join(lines)


def to_json(rep: Report, *, sessions_per_day: int, budget: int | None) -> str:
    return json.dumps(
        {
            "root": str(rep.root),
            "token_method": rep.method,
            "counts": {
                "skills": rep.counts("skill"),
                "steering": rep.counts("steering"),
                "references": rep.counts("reference"),
            },
            "cost": {
                "per_turn_tokens": rep.per_turn,
                "per_session_tokens": rep.per_session,
                "on_demand_tokens": rep.on_demand,
                "per_session_usd": round(usd(rep.per_session), 6),
                "monthly_usd_at_sessions_per_day": round(
                    usd(rep.per_session) * sessions_per_day * 30, 4
                ),
            },
            "budget": budget,
            "over_budget": (budget is not None and rep.per_session > budget),
            "contributors": [
                {"file": i.rel, "kind": i.kind, "tokens_always": i.tokens_always,
                 "inclusion": i.inclusion or None}
                for i in rep.always_contributors()
            ],
            "findings": [
                {"level": f.level, "code": f.code, "message": f.message} for f in rep.findings
            ],
        },
        indent=2,
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Measure and audit the token cost of a Kiro configuration."
    )
    p.add_argument("--root", default=".", help="project root containing AGENTS.md and .kiro/")
    p.add_argument("--budget", type=int, help="fail if the per-session charge exceeds this")
    p.add_argument("--sessions-per-day", type=int, default=10, help="for the monthly projection")
    p.add_argument("--top", type=int, default=15, help="how many contributors to list")
    p.add_argument("--exact", action="store_true", help="exact token counts (unbilled, needs key)")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.add_argument("--strict", action="store_true", help="treat warnings as failures too")
    args = p.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"error: no such directory: {root}", file=sys.stderr)
        return 2
    if not (root / ".kiro").is_dir():
        print(f"error: no .kiro/ directory under {root}", file=sys.stderr)
        return 2

    rep = scan(root, exact=args.exact)

    if args.json:
        print(to_json(rep, sessions_per_day=args.sessions_per_day, budget=args.budget))
    else:
        print(render(rep, top=args.top, sessions_per_day=args.sessions_per_day, budget=args.budget))

    failed = bool(rep.errors)
    if args.budget is not None and rep.per_session > args.budget:
        failed = True
    if args.strict and rep.warns:
        failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
