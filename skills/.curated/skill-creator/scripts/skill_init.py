#!/usr/bin/env python3
"""Initialize a new skill using the Aria taxonomy."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

from skill_meta import format_display_name, write_aria_yaml


MAX_SKILL_NAME_LENGTH = 64
ALLOWED_RESOURCES = {"assets", "references", "scripts"}
DEFAULT_SKILLS_PATH = Path.home() / ".aria" / "skills"

SKILL_TEMPLATE = """---
name: {skill_name}
description: Use when TODO is replaced with the exact triggering condition for this skill.
---

# {skill_title}

## Overview

[TODO: Preserve the skill's scope, capabilities, supported formats, exclusions, and other useful context here.]

## Workflow

1. [TODO: Add concise imperative steps another Aria agent can follow.]
2. [TODO: Route detailed or conditional guidance into references when needed.]
3. [TODO: State the required output and validation.]
"""

EXAMPLE_SCRIPT = '''#!/usr/bin/env python3
"""Replace this placeholder with a deterministic helper or delete it."""


def main() -> None:
    raise NotImplementedError("Implement or remove this placeholder")


if __name__ == "__main__":
    main()
'''

EXAMPLE_REFERENCE = """# Reference

Replace this placeholder with detailed knowledge that should be loaded only when needed, or delete it.
"""

EXAMPLE_ASSET = """Replace this placeholder with a runtime asset or delete it.
"""


def normalize_skill_name(skill_name: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", skill_name.strip().lower())
    return re.sub(r"-{2,}", "-", normalized.strip("-"))


def parse_resources(raw_resources: str) -> list[str]:
    resources = [item.strip() for item in raw_resources.split(",") if item.strip()]
    invalid = sorted(set(resources) - ALLOWED_RESOURCES)
    if invalid:
        allowed = ", ".join(sorted(ALLOWED_RESOURCES))
        raise ValueError(f"unknown resource types: {', '.join(invalid)}; allowed: {allowed}")
    return list(dict.fromkeys(resources))


def create_default_icons(skill_dir: Path, skill_name: str) -> None:
    template_dir = Path(__file__).resolve().parent.parent / "assets"
    assets_dir = skill_dir / "assets"
    assets_dir.mkdir(exist_ok=True)
    for suffix in ("svg", "png"):
        source = template_dir / f"default-skill.{suffix}"
        destination = assets_dir / f"{skill_name}.{suffix}"
        if not source.is_file():
            raise FileNotFoundError(f"missing fallback icon template: {source}")
        shutil.copyfile(source, destination)
    print(f"[OK] Created assets/{skill_name}.svg and assets/{skill_name}.png")


def create_resource_dirs(
    skill_dir: Path, resources: list[str], include_examples: bool
) -> None:
    for resource in resources:
        resource_dir = skill_dir / resource
        resource_dir.mkdir(exist_ok=True)
        if not include_examples:
            print(f"[OK] Created {resource}/")
            continue
        if resource == "scripts":
            path = resource_dir / "example.py"
            path.write_text(EXAMPLE_SCRIPT, encoding="utf-8")
            path.chmod(0o755)
        elif resource == "references":
            path = resource_dir / "example.md"
            path.write_text(EXAMPLE_REFERENCE, encoding="utf-8")
        else:
            path = resource_dir / "example.txt"
            path.write_text(EXAMPLE_ASSET, encoding="utf-8")
        print(f"[OK] Created {path.relative_to(skill_dir)}")


def init_skill(
    skill_name: str,
    path: Path,
    resources: list[str],
    include_examples: bool,
    interface_overrides: list[str],
) -> Path | None:
    skill_dir = path.expanduser().resolve() / skill_name
    if skill_dir.exists():
        print(f"[ERROR] Skill directory already exists: {skill_dir}")
        return None

    try:
        skill_dir.mkdir(parents=True)
        print(f"[OK] Created skill directory: {skill_dir}")

        title = format_display_name(skill_name)
        (skill_dir / "SKILL.md").write_text(
            SKILL_TEMPLATE.format(skill_name=skill_name, skill_title=title),
            encoding="utf-8",
        )
        print("[OK] Created SKILL.md")

        create_default_icons(skill_dir, skill_name)
        if not write_aria_yaml(skill_dir, skill_name, interface_overrides):
            return None
        create_resource_dirs(skill_dir, resources, include_examples)
    except (OSError, ValueError) as exc:
        print(f"[ERROR] Could not initialize skill: {exc}")
        return None

    print(f"\n[OK] Skill {skill_name!r} initialized at {skill_dir}")
    print("\nNext steps:")
    print("1. Replace every TODO and finish the one-sentence Use when description")
    print("2. Replace the fallback icons with a relevant matching pair when available")
    print("3. Add only the references, scripts, and assets the skill needs")
    print("4. Review agents/aria.yaml and keep every name and path synchronized")
    print("5. Run scripts/skill_validate.py against the completed skill")
    return skill_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a new Aria skill directory.")
    parser.add_argument("skill_name", help="skill name, normalized to hyphen-case")
    parser.add_argument(
        "--path",
        type=Path,
        default=DEFAULT_SKILLS_PATH,
        help=f"output directory (default: {DEFAULT_SKILLS_PATH})",
    )
    parser.add_argument(
        "--resources",
        default="",
        help="comma-separated optional directories: scripts,references,assets",
    )
    parser.add_argument(
        "--examples",
        action="store_true",
        help="create placeholders in explicitly requested resource directories",
    )
    parser.add_argument(
        "--interface",
        action="append",
        default=[],
        help="Aria interface override in camelCase key=value form (repeatable)",
    )
    args = parser.parse_args()

    skill_name = normalize_skill_name(args.skill_name)
    if not skill_name:
        print("[ERROR] Skill name must include at least one letter or digit.")
        return 1
    if len(skill_name) > MAX_SKILL_NAME_LENGTH:
        print(
            f"[ERROR] Skill name is {len(skill_name)} characters; "
            f"maximum is {MAX_SKILL_NAME_LENGTH}."
        )
        return 1
    if skill_name != args.skill_name:
        print(f"Note: normalized {args.skill_name!r} to {skill_name!r}.")

    try:
        resources = parse_resources(args.resources)
    except ValueError as exc:
        print(f"[ERROR] {exc}")
        return 1
    if args.examples and not resources:
        print("[ERROR] --examples requires --resources.")
        return 1

    print(f"Initializing Aria skill: {skill_name}")
    print(f"   Location: {args.path.expanduser()}")
    if resources:
        print(f"   Optional resources: {', '.join(resources)}")
    print()

    result = init_skill(
        skill_name,
        args.path,
        resources,
        args.examples,
        args.interface,
    )
    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(main())
