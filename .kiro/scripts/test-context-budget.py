#!/usr/bin/env python3
"""Tests for context-budget.py, using synthetic config fixtures.

Plain assertions, no pytest, no network — this pack ships scripts rather than a
test suite, so the check has to run with nothing installed.

Usage:
    python3 .kiro/scripts/test-context-budget.py

Exit 0 = all pass, 1 = a failure.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_module():
    """Import context-budget.py despite the hyphen in its filename."""
    spec = importlib.util.spec_from_file_location("context_budget", HERE / "context-budget.py")
    mod = importlib.util.module_from_spec(spec)
    # dataclasses resolves types via sys.modules, so register before executing.
    sys.modules["context_budget"] = mod
    spec.loader.exec_module(mod)
    return mod


cb = load_module()

passed = 0
failed: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    global passed
    if condition:
        passed += 1
        print(f"  ok    {label}")
    else:
        failed.append(label)
        print(f"  FAIL  {label}" + (f" -- {detail}" if detail else ""))


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------


def build(root: Path, *, skills: dict[str, str], steering: dict[str, str],
          agents: str | None = None) -> None:
    """Write a synthetic Kiro config tree."""
    (root / ".kiro" / "skills").mkdir(parents=True, exist_ok=True)
    (root / ".kiro" / "steering").mkdir(parents=True, exist_ok=True)
    if agents is not None:
        (root / "AGENTS.md").write_text(agents, encoding="utf-8")
    for name, content in skills.items():
        d = root / ".kiro" / "skills" / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "SKILL.md").write_text(content, encoding="utf-8")
    for name, content in steering.items():
        (root / ".kiro" / "steering" / name).write_text(content, encoding="utf-8")


def skill(name: str, description: str, body: str = "\n# Body\n\nSome content.\n") -> str:
    return f"---\nname: {name}\ndescription: {description}\n---\n{body}"


def codes(rep) -> list[str]:
    return [f.code for f in rep.findings]


def run_cli(args: list[str]) -> int:
    """Invoke main() with its report suppressed, so test output stays readable."""
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return cb.main(args)


def _json_ok(root: Path) -> bool:
    """--json must be machine-readable, since a CI gate will parse it."""
    import json

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
        cb.main(["--root", str(root), "--json"])
    try:
        data = json.loads(buf.getvalue())
    except json.JSONDecodeError:
        return False
    return "cost" in data and "findings" in data and "per_session_tokens" in data["cost"]


# ---------------------------------------------------------------------------
# frontmatter parsing
# ---------------------------------------------------------------------------

print("frontmatter parsing")

fm, body = cb.split_frontmatter("---\nname: a\ndescription: hello\n---\nbody here\n")
check("reads inline scalars", fm.get("name") == "a" and fm.get("description") == "hello", str(fm))
check("returns the body", body.strip() == "body here", repr(body))

# The regression that produced a confident, wrong error: a block sequence value
# read as empty, making a present fileMatchPattern look missing.
fm, _ = cb.split_frontmatter(
    '---\ninclusion: fileMatch\nfileMatchPattern:\n  - ".kiro/**/*.md"\n  - "AGENTS.md"\n---\nx\n'
)
check("folds a block sequence into a value", bool(fm.get("fileMatchPattern")), str(fm))
check("block sequence keeps its items", "AGENTS.md" in fm.get("fileMatchPattern", ""), str(fm))

fm, _ = cb.split_frontmatter("---\ndescription: >\n  folded text here\n---\nx\n")
check("folds a block scalar", "folded text" in fm.get("description", ""), str(fm))

fm, _ = cb.split_frontmatter('---\nname: "quoted"\n---\nx\n')
check("strips matching quotes", fm.get("name") == "quoted", str(fm))

fm, body = cb.split_frontmatter("no frontmatter at all\n")
check("no frontmatter yields empty fields", fm == {}, str(fm))
check("no frontmatter returns full text", body.startswith("no frontmatter"), repr(body))

fm, _ = cb.split_frontmatter("---\nname: a\nmetadata:\n  version: \"1.0\"\n---\nx\n")
check("nested mapping does not leak into top level", "version" not in fm, str(fm))


# ---------------------------------------------------------------------------
# token counting
# ---------------------------------------------------------------------------

print("\ntoken counting")

tok, method = cb.count("hello world this is a test")
check("counts tokens", tok > 0, str(tok))
check("labels the method", method in ("exact", "estimate"), method)
check("empty text costs nothing", cb.count("")[0] == 0, str(cb.count("")))
check("longer text costs more", cb.count("a " * 200)[0] > cb.count("a " * 10)[0])
check("cost scales with tokens", cb.usd(1_000_000) > cb.usd(1_000))


# ---------------------------------------------------------------------------
# cost layering
# ---------------------------------------------------------------------------

print("\ncost layering")

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    build(
        root,
        agents="# Core\n\n" + ("Always-on directive. " * 40),
        skills={
            "alpha": skill("alpha", "Use when doing alpha things with widgets and gears.",
                           "\n# Alpha\n\n" + ("Body text. " * 300)),
        },
        steering={
            "always.md": "---\ninclusion: always\ndescription: Always on\n---\n"
                         + ("Standing rule. " * 50),
            "ondemand.md": '---\ninclusion: fileMatch\nfileMatchPattern:\n  - "*.py"\n'
                           "description: Only for python\n---\n" + ("Triggered rule. " * 200),
        },
    )
    rep = cb.scan(root)

    check("per-turn counts AGENTS.md", rep.per_turn > 0, str(rep.per_turn))
    check("per-session includes the per-turn layer", rep.per_session > rep.per_turn)
    check("skill body is on demand, not standing", rep.on_demand > 0, str(rep.on_demand))

    always = next(i for i in rep.items if i.rel == "steering/always.md")
    ondemand = next(i for i in rep.items if i.rel == "steering/ondemand.md")
    check("always steering is charged in full", always.tokens_always > 100,
          str(always.tokens_always))
    check("fileMatch steering body is not standing cost",
          ondemand.tokens_always < always.tokens_always, str(ondemand.tokens_always))
    check("fileMatch steering body is on demand", ondemand.tokens_on_demand > 100,
          str(ondemand.tokens_on_demand))

    sk = next(i for i in rep.items if i.rel == "skills/alpha")
    check("skill standing cost is only name+description", sk.tokens_always < 60,
          str(sk.tokens_always))
    check("skill body is on demand", sk.tokens_on_demand > 200, str(sk.tokens_on_demand))
    check("a present fileMatchPattern is not flagged missing",
          "filematch-no-pattern" not in codes(rep), str(codes(rep)))


# ---------------------------------------------------------------------------
# findings
# ---------------------------------------------------------------------------

print("\nfindings")

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    build(
        root,
        skills={
            "no-desc": "---\nname: no-desc\n---\n\n# Body\n",
            "mismatch": skill("different-name", "Use when the directory and name disagree here."),
            "tiny": skill("tiny", "Short."),
            "huge": skill("huge", "Use when " + ("x" * 700)),
        },
        steering={
            "broken.md": "---\ninclusion: fileMatch\ndescription: no pattern\n---\nbody\n",
            "noinc.md": "---\ndescription: no inclusion field\n---\nbody\n",
            "product.md": "---\ninclusion: always\n---\nreserved name\n",
        },
    )
    rep = cb.scan(root)
    found = codes(rep)

    check("missing description is an error", "skill-no-description" in found, str(found))
    check("name/directory mismatch is flagged", "skill-name-mismatch" in found, str(found))
    check("too-short description is flagged", "desc-too-short" in found, str(found))
    check("too-long description is flagged", "desc-too-long" in found, str(found))
    check("fileMatch without pattern is an error", "filematch-no-pattern" in found, str(found))
    check("missing inclusion is flagged", "steering-no-inclusion" in found, str(found))
    check("reserved steering filename is an error", "reserved-steering" in found, str(found))
    check("errors are separated from warnings", len(rep.errors) >= 3 and len(rep.warns) >= 3,
          f"errors={len(rep.errors)} warns={len(rep.warns)}")

# A skill directory with no SKILL.md never loads at all.
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    build(root, skills={}, steering={})
    (root / ".kiro" / "skills" / "empty").mkdir(parents=True)
    rep = cb.scan(root)
    check("skill dir with no SKILL.md is an error", "no-skill-md" in codes(rep), str(codes(rep)))


# ---------------------------------------------------------------------------
# description collisions
# ---------------------------------------------------------------------------

print("\ndescription collisions")

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    shared = ("Use when developing WordPress block themes: theme.json global settings, "
              "templates and template parts, patterns and style variations.")
    build(
        root,
        skills={
            "themes-a": skill("themes-a", shared),
            "themes-b": skill("themes-b", shared + " Also Site Editor troubleshooting."),
            "unrelated": skill("unrelated",
                               "Use when profiling database query latency and index selection."),
        },
        steering={},
    )
    rep = cb.scan(root)
    collisions = [f for f in rep.findings if f.code == "description-collision"]
    check("near-identical descriptions collide", len(collisions) >= 1, str(codes(rep)))
    check("the collision names both skills",
          collisions and "themes-a" in collisions[0].message and "themes-b" in collisions[0].message,
          collisions[0].message if collisions else "none")
    check("unrelated skills do not collide",
          all("unrelated" not in c.message for c in collisions),
          str([c.message for c in collisions]))

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    build(
        root,
        skills={
            "one": skill("one", "Use when profiling database query latency and index selection."),
            "two": skill("two", "Use when designing marketing banner artwork for social posts."),
        },
        steering={},
    )
    rep = cb.scan(root)
    # Silence would be ambiguous: no overlap, or a threshold set too high?
    check("nearest pairs are reported when none collide",
          "nearest-descriptions" in codes(rep), str(codes(rep)))


# ---------------------------------------------------------------------------
# CLI contract
# ---------------------------------------------------------------------------

print("\nCLI contract")

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    build(root, agents="# Core\n" + ("word " * 100),
          skills={"a": skill("a", "Use when testing the command line contract end to end.")},
          steering={})

    check("clean config exits 0", run_cli(["--root", str(root)]) == 0)
    check("generous budget exits 0", run_cli(["--root", str(root), "--budget", "100000"]) == 0)
    check("exceeded budget exits 1", run_cli(["--root", str(root), "--budget", "1"]) == 1)
    check("missing root exits 2", run_cli(["--root", str(root / "nope")]) == 2)
    check("--json emits parseable output", _json_ok(root), "json did not parse")

    no_kiro = Path(tmp) / "bare"
    no_kiro.mkdir()
    check("root without .kiro exits 2", run_cli(["--root", str(no_kiro)]) == 2)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    build(root, skills={"bad": "---\nname: bad\n---\n\n# no description\n"}, steering={})
    check("a config error exits 1", run_cli(["--root", str(root)]) == 1)


# ---------------------------------------------------------------------------

print()
if failed:
    print(f"FAILED  {len(failed)} of {passed + len(failed)} checks")
    for label in failed:
        print(f"  - {label}")
    sys.exit(1)
print(f"OK      {passed} checks passed")
sys.exit(0)
