#!/usr/bin/env python3
"""Enumerate one Aria skill metadata field across a skills directory."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", re.DOTALL)
TITLE_RE = re.compile(r"^# (.+?)\s*$", re.MULTILINE)
KEY_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):(?:\s*(.*))?$")

FIELD_LABELS = {
    "directory": "Directory names",
    "name": "Skill names",
    "description": "Frontmatter descriptions",
    "title": "H1 titles",
    "display-name": "Display names",
    "short-description": "Short descriptions",
    "icon-small": "Small icon paths",
    "icon-large": "Large icon paths",
    "default-prompt": "Default prompts",
}

FIELD_ALIASES = {
    "all": "all",
    "metadata": "all",
    "taxonomy": "all",
    "directory": "directory",
    "directories": "directory",
    "folder": "directory",
    "folders": "directory",
    "name": "name",
    "names": "name",
    "description": "description",
    "descriptions": "description",
    "descriptor": "description",
    "descriptors": "description",
    "title": "title",
    "titles": "title",
    "display-name": "display-name",
    "display-names": "display-name",
    "displayname": "display-name",
    "short-description": "short-description",
    "short-descriptions": "short-description",
    "short-descriptor": "short-description",
    "short-descriptors": "short-description",
    "shortdescription": "short-description",
    "icon-small": "icon-small",
    "small-icon": "icon-small",
    "iconsmall": "icon-small",
    "icon-large": "icon-large",
    "large-icon": "icon-large",
    "iconlarge": "icon-large",
    "default-prompt": "default-prompt",
    "default-prompts": "default-prompt",
    "prompt": "default-prompt",
    "prompts": "default-prompt",
    "defaultprompt": "default-prompt",
}

INTERFACE_KEYS = {
    "display-name": ("displayName", "display_name"),
    "short-description": ("shortDescription", "short_description"),
    "icon-small": ("iconSmall", "icon_small"),
    "icon-large": ("iconLarge", "icon_large"),
    "default-prompt": ("defaultPrompt", "default_prompt"),
}


@dataclass(frozen=True)
class SkillRecord:
    directory: str
    name: str
    description: str
    title: str
    display_name: str
    short_description: str
    icon_small: str
    icon_large: str
    default_prompt: str

    def value(self, field: str) -> str:
        return str(getattr(self, field.replace("-", "_")))


def decode_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        try:
            decoded = ast.literal_eval(value)
            if isinstance(decoded, str):
                return decoded
        except (SyntaxError, ValueError):
            if value[0] == "'":
                return value[1:-1].replace("''", "'")
            return value[1:-1]
    return value


def parse_flat_mapping(text: str, required_indent: int = 0) -> dict[str, str]:
    lines = text.splitlines()
    values: dict[str, str] = {}
    index = 0

    while index < len(lines):
        raw = lines[index]
        indent = len(raw) - len(raw.lstrip(" "))
        if indent != required_indent:
            index += 1
            continue

        match = KEY_RE.match(raw[indent:])
        if not match:
            index += 1
            continue

        key, raw_value = match.group(1), (match.group(2) or "").strip()
        if raw_value in {"|", "|-", "|+", ">", ">-", ">+"}:
            folded = raw_value.startswith(">")
            block: list[str] = []
            index += 1
            while index < len(lines):
                continuation = lines[index]
                continuation_indent = len(continuation) - len(continuation.lstrip(" "))
                if continuation.strip() and continuation_indent <= required_indent:
                    break
                block.append(continuation.strip())
                index += 1
            values[key] = (" " if folded else "\n").join(block).strip()
            continue

        values[key] = decode_scalar(raw_value)
        index += 1

    return values


def parse_interface(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}

    lines = path.read_text(encoding="utf-8").splitlines()
    for index, raw in enumerate(lines):
        if raw.strip() != "interface:":
            continue
        base_indent = len(raw) - len(raw.lstrip(" "))
        block: list[str] = []
        for continuation in lines[index + 1 :]:
            indent = len(continuation) - len(continuation.lstrip(" "))
            if continuation.strip() and indent <= base_indent:
                break
            block.append(continuation)
        return parse_flat_mapping("\n".join(block), base_indent + 2)
    return {}


def first_value(values: dict[str, str], keys: tuple[str, ...]) -> str:
    for key in keys:
        if key in values:
            return values[key]
    return ""


def normalize_output(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def read_skill(skill_dir: Path) -> SkillRecord:
    skill_text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    frontmatter_match = FRONTMATTER_RE.match(skill_text)
    frontmatter = (
        parse_flat_mapping(frontmatter_match.group(1)) if frontmatter_match else {}
    )
    title_match = TITLE_RE.search(skill_text)

    aria_path = skill_dir / "agents" / "aria.yaml"
    legacy_path = skill_dir / "agents" / "openai.yaml"
    interface = parse_interface(aria_path if aria_path.is_file() else legacy_path)

    return SkillRecord(
        directory=skill_dir.name,
        name=normalize_output(frontmatter.get("name", "")),
        description=normalize_output(frontmatter.get("description", "")),
        title=normalize_output(title_match.group(1) if title_match else ""),
        display_name=normalize_output(first_value(interface, INTERFACE_KEYS["display-name"])),
        short_description=normalize_output(
            first_value(interface, INTERFACE_KEYS["short-description"])
        ),
        icon_small=normalize_output(first_value(interface, INTERFACE_KEYS["icon-small"])),
        icon_large=normalize_output(first_value(interface, INTERFACE_KEYS["icon-large"])),
        default_prompt=normalize_output(
            first_value(interface, INTERFACE_KEYS["default-prompt"])
        ),
    )


def collect_skills(root: Path) -> list[SkillRecord]:
    skill_dirs = sorted(
        (path.parent for path in root.glob("*/SKILL.md")),
        key=lambda path: path.name.casefold(),
    )
    return [read_skill(path) for path in skill_dirs]


def markdown_value(value: str) -> str:
    if not value:
        return "**[missing]**"
    return value


def print_markdown(records: list[SkillRecord], fields: list[str]) -> None:
    for field_index, field in enumerate(fields):
        if field_index:
            print()
        print(f"## {FIELD_LABELS[field]} ({len(records)})")
        print()
        for record in records:
            print(f"- `{record.directory}`: {markdown_value(record.value(field))}")


def print_json(records: list[SkillRecord], fields: list[str]) -> None:
    if len(fields) == len(FIELD_LABELS):
        payload: object = [
            {field: record.value(field) for field in fields} for record in records
        ]
    else:
        field = fields[0]
        payload = [
            {"directory": record.directory, field: record.value(field)}
            for record in records
        ]
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def parse_args() -> argparse.Namespace:
    default_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(
        description="List one metadata or taxonomy field across sibling Aria skills.",
        epilog=(
            "Examples: skill_inventory.py --field name; "
            "skill_inventory.py --field description; "
            "skill_inventory.py /path/to/skills --field all"
        ),
    )
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=default_root,
        help=f"skills directory (default: {default_root})",
    )
    parser.add_argument(
        "--field",
        default="all",
        help="field or common plural alias to enumerate (default: all)",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="output format (default: markdown)",
    )
    parser.add_argument(
        "--list-fields",
        action="store_true",
        help="print canonical field selectors and exit",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.list_fields:
        print("all")
        for field in FIELD_LABELS:
            print(field)
        return 0

    requested = args.field.strip().lower().replace("_", "-")
    field = FIELD_ALIASES.get(requested)
    if field is None:
        valid = ", ".join(("all", *FIELD_LABELS))
        print(f"ERROR: unknown field {args.field!r}; choose from: {valid}", file=sys.stderr)
        return 2

    root = args.root.expanduser().resolve()
    if not root.is_dir():
        print(f"ERROR: skills directory does not exist: {root}", file=sys.stderr)
        return 1

    records = collect_skills(root)
    if not records:
        print(f"ERROR: no immediate child skills found in: {root}", file=sys.stderr)
        return 1

    fields = list(FIELD_LABELS) if field == "all" else [field]
    if args.format == "json":
        print_json(records, fields)
    else:
        print_markdown(records, fields)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
