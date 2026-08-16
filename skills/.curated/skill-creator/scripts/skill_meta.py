#!/usr/bin/env python3
"""Create agents/aria.yaml for an Aria skill folder."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml


ACRONYMS = {"API", "CI", "CLI", "GH", "LLM", "MCP", "PDF", "PR", "SQL", "UI", "URL"}
BRANDS = {
    "fastapi": "FastAPI",
    "github": "GitHub",
    "openai": "OpenAI",
    "openapi": "OpenAPI",
    "pagerduty": "PagerDuty",
    "sqlite": "SQLite",
}
SMALL_WORDS = {"and", "or", "to", "up", "with"}
ALLOWED_INTERFACE_KEYS = {
    "brandColor",
    "defaultPrompt",
    "displayName",
    "iconLarge",
    "iconSmall",
    "shortDescription",
}


def yaml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{escaped}"'


def format_display_name(skill_name: str) -> str:
    words = [word for word in skill_name.split("-") if word]
    formatted: list[str] = []
    for index, word in enumerate(words):
        lower = word.lower()
        upper = word.upper()
        if upper in ACRONYMS:
            formatted.append(upper)
        elif lower in BRANDS:
            formatted.append(BRANDS[lower])
        elif index > 0 and lower in SMALL_WORDS:
            formatted.append(lower)
        else:
            formatted.append(word.capitalize())
    return " ".join(formatted)


def generate_short_description(display_name: str) -> str:
    candidates = (
        f"Create and update {display_name} workflows",
        f"Build reliable {display_name} workflows",
        f"Guidance and tools for {display_name}",
        f"Work effectively with {display_name}",
    )
    for candidate in candidates:
        if 25 <= len(candidate) <= 64:
            return candidate
    suffix = " workflows"
    return f"{display_name[:64 - len(suffix)].rstrip()}{suffix}"


def read_frontmatter_name(skill_dir: Path) -> str | None:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        print(f"[ERROR] SKILL.md not found in {skill_dir}")
        return None

    content = skill_md.read_text(encoding="utf-8")
    match = re.match(r"^---\r?\n(.*?)\r?\n---", content, re.DOTALL)
    if not match:
        print("[ERROR] Invalid SKILL.md frontmatter format.")
        return None

    try:
        frontmatter = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        print(f"[ERROR] Invalid YAML frontmatter: {exc}")
        return None
    if not isinstance(frontmatter, dict):
        print("[ERROR] Frontmatter must be a YAML dictionary.")
        return None

    name = frontmatter.get("name")
    if not isinstance(name, str) or not name.strip():
        print("[ERROR] Frontmatter 'name' is missing or invalid.")
        return None
    return name.strip()


def parse_interface_overrides(raw_overrides: list[str]) -> dict[str, str] | None:
    overrides: dict[str, str] = {}
    for item in raw_overrides:
        if "=" not in item:
            print(f"[ERROR] Invalid interface override {item!r}. Use key=value.")
            return None
        key, value = (part.strip() for part in item.split("=", 1))
        if key not in ALLOWED_INTERFACE_KEYS:
            allowed = ", ".join(sorted(ALLOWED_INTERFACE_KEYS))
            print(f"[ERROR] Unknown interface field {key!r}. Allowed: {allowed}")
            return None
        overrides[key] = value
    return overrides


def write_aria_yaml(
    skill_dir: str | Path, skill_name: str, raw_overrides: list[str]
) -> Path | None:
    overrides = parse_interface_overrides(raw_overrides)
    if overrides is None:
        return None

    values = {
        "displayName": format_display_name(skill_name),
        "shortDescription": "",
        "iconSmall": f"./assets/{skill_name}.svg",
        "iconLarge": f"./assets/{skill_name}.png",
        "defaultPrompt": f"Use ${skill_name} to handle this task.",
    }
    values.update(overrides)
    if not values["shortDescription"]:
        values["shortDescription"] = generate_short_description(values["displayName"])

    short = values["shortDescription"]
    if not 25 <= len(short) <= 64:
        print(
            "[ERROR] shortDescription must be 25-64 characters "
            f"(got {len(short)})."
        )
        return None
    if f"${skill_name}" not in values["defaultPrompt"]:
        print(f"[ERROR] defaultPrompt must contain ${skill_name}.")
        return None

    ordered_keys = ["displayName", "shortDescription", "iconSmall", "iconLarge"]
    if "brandColor" in values:
        ordered_keys.append("brandColor")
    ordered_keys.append("defaultPrompt")

    lines = ["interface:"]
    lines.extend(f"  {key}: {yaml_quote(values[key])}" for key in ordered_keys)

    agents_dir = Path(skill_dir) / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    output_path = agents_dir / "aria.yaml"
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("[OK] Created agents/aria.yaml")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Create agents/aria.yaml for a skill.")
    parser.add_argument("skill_dir", help="path to the skill directory")
    parser.add_argument("--name", help="override the SKILL.md frontmatter name")
    parser.add_argument(
        "--interface",
        action="append",
        default=[],
        help="interface override in camelCase key=value form (repeatable)",
    )
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).expanduser().resolve()
    if not skill_dir.is_dir():
        print(f"[ERROR] Skill directory not found: {skill_dir}")
        return 1

    skill_name = args.name or read_frontmatter_name(skill_dir)
    if not skill_name:
        return 1
    return 0 if write_aria_yaml(skill_dir, skill_name, args.interface) else 1


if __name__ == "__main__":
    sys.exit(main())
