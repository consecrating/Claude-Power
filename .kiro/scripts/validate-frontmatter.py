#!/usr/bin/env python3
"""Strict YAML frontmatter validation for this Kiro configuration pack.

Complements validate-config.sh: that script uses awk and catches structural
problems, this one parses the frontmatter with a real YAML parser and rejects
fields Kiro does not document. Inventing a frontmatter field is a silent
failure — the file loads but the field is ignored — so this check exists to
make it loud.

Usage:
    python3 .kiro/scripts/validate-frontmatter.py [--root .]

Exit 0 = clean, 1 = at least one error.
Requires PyYAML. Exits 0 with a notice if PyYAML is unavailable, so it never
becomes a hard blocker in a minimal environment.
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import sys

try:
    import yaml
except ImportError:  # pragma: no cover
    print("notice: PyYAML not installed; skipping strict frontmatter validation")
    print("        install with: pip install pyyaml")
    sys.exit(0)

FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n", re.S)

# Documented fields only. Anything else is very likely a typo or an invention.
SKILL_FIELDS = {"name", "description", "license", "compatibility", "metadata"}
STEERING_FIELDS = {"inclusion", "fileMatchPattern", "name", "description"}
AGENT_FIELDS = {
    "name", "description", "prompt", "model", "tools", "excludedTools",
    "toolAliases", "allowedTools", "permissions", "toolsSettings", "resources",
    "hooks", "mcpServers", "includeMcpJson", "includePowers",
    "keyboardShortcut", "welcomeMessage",
}
INCLUSION_MODES = {"always", "fileMatch", "auto", "manual"}
RESERVED_STEERING = {"product.md", "tech.md", "structure.md"}
NAME_RE = re.compile(r"^[a-z0-9-]+$")

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)
    print(f"ERROR  {msg}")


def warn(msg: str) -> None:
    warnings.append(msg)
    print(f"WARN   {msg}")


def load_frontmatter(path: str):
    """Return (dict, error) — error is a string if the block is unusable."""
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    if not text.startswith("---\n"):
        return None, "frontmatter must start at the first byte (no leading blank line)"
    match = FRONTMATTER.match(text)
    if not match:
        return None, "frontmatter block is not terminated by a closing ---"
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        return None, f"invalid YAML: {str(exc).splitlines()[0]}"
    if data is None:
        return {}, None
    if not isinstance(data, dict):
        return None, "frontmatter must be a mapping"
    return data, None


def check_skill(path: str) -> None:
    data, problem = load_frontmatter(path)
    if problem:
        err(f"{path}: {problem}")
        return

    unknown = set(data) - SKILL_FIELDS
    if unknown:
        err(f"{path}: undocumented frontmatter field(s): {sorted(unknown)}")

    folder = os.path.basename(os.path.dirname(path))
    name = data.get("name")
    desc = data.get("description")

    if not name:
        err(f"{path}: missing required field 'name'")
    else:
        if name != folder:
            err(f"{path}: name '{name}' must equal folder name '{folder}'")
        if len(name) > 64:
            err(f"{path}: name is {len(name)} chars (max 64)")
        if not NAME_RE.match(str(name)):
            err(f"{path}: name '{name}' must be lowercase letters, digits, hyphens")

    if not desc:
        err(f"{path}: missing required field 'description'")
    else:
        if len(desc) > 1024:
            err(f"{path}: description is {len(desc)} chars (max 1024)")
        elif len(desc) < 40:
            warn(f"{path}: description is only {len(desc)} chars; it is the activation trigger")

    print(f"ok     skill    {folder:24} desc={len(desc or '')}ch")


def check_steering(path: str) -> None:
    base = os.path.basename(path)
    if base in RESERVED_STEERING:
        err(f"{path}: reserved foundation filename owned by the host repo — rename it")

    data, problem = load_frontmatter(path)
    if problem:
        warn(f"{path}: {problem} (treated as inclusion: always — loaded every turn)")
        return

    unknown = set(data) - STEERING_FIELDS
    if unknown:
        err(f"{path}: undocumented frontmatter field(s): {sorted(unknown)}")

    inclusion = data.get("inclusion", "always")
    if inclusion not in INCLUSION_MODES:
        err(f"{path}: invalid inclusion '{inclusion}' (must be one of {sorted(INCLUSION_MODES)})")
    elif inclusion == "fileMatch":
        pattern = data.get("fileMatchPattern")
        if not pattern:
            err(f"{path}: inclusion: fileMatch requires 'fileMatchPattern'")
        elif not isinstance(pattern, (str, list)):
            err(f"{path}: fileMatchPattern must be a string or a list of strings")
    elif inclusion == "auto":
        for field in ("name", "description"):
            if not data.get(field):
                err(f"{path}: inclusion: auto requires '{field}'")
    elif inclusion == "always":
        warn(f"{path}: inclusion: always is paid on every turn — confirm that is intended")

    print(f"ok     steering {base:34} inclusion={inclusion}")


def check_agent(path: str) -> None:
    data, problem = load_frontmatter(path)
    if problem:
        err(f"{path}: {problem}")
        return

    unknown = set(data) - AGENT_FIELDS
    if unknown:
        err(f"{path}: undocumented frontmatter field(s): {sorted(unknown)}")

    if not data.get("description"):
        warn(f"{path}: no description; the agent picker will show nothing useful")

    if "model" in data:
        warn(
            f"{path}: 'model' is set to {data['model']!r} — Kiro does not publish model IDs, "
            "and an unrecognized ID silently falls back to the default. Verify with /model."
        )

    perms = data.get("permissions")
    if isinstance(perms, dict):
        valid_caps = {"fs_read", "fs_write", "shell", "web_fetch", "web_search",
                      "mcp", "subagent", "all"}
        valid_effects = {"allow", "ask", "deny"}
        for i, rule in enumerate(perms.get("rules", []) or []):
            if not isinstance(rule, dict):
                err(f"{path}: permissions.rules[{i}] must be a mapping")
                continue
            cap = rule.get("capability")
            eff = rule.get("effect")
            if cap not in valid_caps:
                err(f"{path}: permissions.rules[{i}] invalid capability {cap!r}")
            if eff not in valid_effects:
                err(f"{path}: permissions.rules[{i}] invalid effect {eff!r}")

    print(f"ok     agent    {os.path.basename(path):34} model_pinned={'model' in data}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="repository root (default: .)")
    args = parser.parse_args()

    root = os.path.abspath(args.root)
    os.chdir(root)

    skills = sorted(glob.glob(".kiro/skills/*/SKILL.md"))
    steering = sorted(glob.glob(".kiro/steering/*.md"))
    agents = sorted(glob.glob(".kiro/agents/*.md"))

    # A skill folder without SKILL.md never loads — the filename must be exact.
    for folder in sorted(glob.glob(".kiro/skills/*/")):
        if not os.path.isfile(os.path.join(folder, "SKILL.md")):
            err(f"{folder}: no SKILL.md (the filename must be exactly SKILL.md)")

    if not skills and not steering and not agents:
        print(f"validate-frontmatter: nothing found under {root}/.kiro — wrong directory?")
        return 1

    print("validate-frontmatter: strict YAML check")
    for path in skills:
        check_skill(path)
    for path in steering:
        check_steering(path)
    for path in agents:
        check_agent(path)

    print(f"\nvalidate-frontmatter: {len(errors)} error(s), {len(warnings)} warning(s)")
    if errors:
        return 1
    print("validate-frontmatter: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
