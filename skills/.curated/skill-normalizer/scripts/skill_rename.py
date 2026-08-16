#!/usr/bin/env python3
"""Synchronize one Aria skill identity after a semantic rename decision."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", re.DOTALL)
MACHINE_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)+$")
TEXT_SUFFIXES = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".mjs",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}


class RenameError(RuntimeError):
    pass


def quoted_interface_value(text: str, key: str) -> str | None:
    match = re.search(
        rf'(?m)^  {re.escape(key)}:\s*(["\'])(.*?)\1\s*$',
        text,
    )
    return match.group(2) if match else None


def set_quoted_interface_value(text: str, key: str, value: str) -> str:
    replacement = f"  {key}: {json.dumps(value, ensure_ascii=False)}"
    pattern = re.compile(rf'(?m)^  {re.escape(key)}:\s*(["\']).*?\1\s*$')
    if pattern.search(text):
        return pattern.sub(replacement, text, count=1)
    raise RenameError(f"agents/aria.yaml is missing quoted interface.{key}")


def replace_skill_identity(text: str, old: str, new: str) -> str:
    replacements = (
        (f"$ARIA_HOME/skills/{old}/", f"$ARIA_HOME/skills/{new}/"),
        (f"/.aria/skills/{old}/", f"/.aria/skills/{new}/"),
        (f"/skills/{old}/", f"/skills/{new}/"),
        (f"${old}", f"${new}"),
    )
    for source, target in replacements:
        text = text.replace(source, target)
    return text


def update_skill_md(path: Path, old: str, new: str, title: str) -> str:
    text = replace_skill_identity(path.read_text(encoding="utf-8"), old, new)
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise RenameError("SKILL.md must begin with YAML frontmatter")

    frontmatter = match.group(1)
    if not re.search(r"(?m)^name:\s*.+$", frontmatter):
        raise RenameError("SKILL.md frontmatter is missing name")
    frontmatter = re.sub(r"(?m)^name:\s*.+$", f"name: {new}", frontmatter, count=1)
    text = text[: match.start(1)] + frontmatter + text[match.end(1) :]

    if not re.search(r"(?m)^# .+$", text):
        raise RenameError("SKILL.md is missing an H1 title")
    return re.sub(r"(?m)^# .+$", f"# {title}", text, count=1)


def resolve_icon_move(
    skill_dir: Path,
    aria_text: str,
    key: str,
    new_name: str,
    suffix: str,
) -> tuple[str, tuple[Path, Path] | None, str | None]:
    current_value = quoted_interface_value(aria_text, key)
    if current_value is None:
        return aria_text, None, f"interface.{key} is absent"
    if "legacy" in Path(current_value).name.casefold():
        raise RenameError(f"interface.{key} selects forbidden legacy icon: {current_value}")

    source = skill_dir / current_value.removeprefix("./")
    expected_value = f"./assets/{new_name}{suffix}"
    destination = skill_dir / "assets" / f"{new_name}{suffix}"
    aria_text = set_quoted_interface_value(aria_text, key, expected_value)

    if source == destination:
        return aria_text, None, None
    if not source.is_file():
        return aria_text, None, f"referenced icon is missing: {current_value}"
    if destination.exists():
        raise RenameError(f"icon destination already exists: {destination}")
    return aria_text, (source, destination), None


def update_aria_yaml(
    path: Path,
    skill_dir: Path,
    old: str,
    new: str,
    title: str,
    default_prompt: str,
) -> tuple[str, list[tuple[Path, Path]], list[str]]:
    text = replace_skill_identity(path.read_text(encoding="utf-8"), old, new)
    text = set_quoted_interface_value(text, "displayName", title)
    text = set_quoted_interface_value(text, "defaultPrompt", default_prompt)

    moves: list[tuple[Path, Path]] = []
    warnings: list[str] = []
    for key, suffix in (("iconSmall", ".svg"), ("iconLarge", ".png")):
        text, move, warning = resolve_icon_move(
            skill_dir, text, key, new, suffix
        )
        if move:
            moves.append(move)
        if warning:
            warnings.append(warning)

    for source, destination in moves:
        old_relative = f"./{source.relative_to(skill_dir).as_posix()}"
        new_relative = f"./{destination.relative_to(skill_dir).as_posix()}"
        text = text.replace(old_relative, new_relative)
    return text, moves, warnings


def update_other_text_files(
    skill_dir: Path,
    old: str,
    new: str,
    path_replacements: list[tuple[str, str]],
) -> dict[Path, str]:
    updates: dict[Path, str] = {}
    excluded = {skill_dir / "SKILL.md", skill_dir / "agents" / "aria.yaml"}
    for path in skill_dir.rglob("*"):
        if not path.is_file() or path in excluded or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        updated = replace_skill_identity(text, old, new)
        for source, destination in path_replacements:
            updated = updated.replace(source, destination)
        if updated != text:
            updates[path] = updated
    return updates


def update_manifest(
    path: Path,
    old: str,
    new: str,
    title: str,
    default_prompt: str,
) -> tuple[str | None, str | None]:
    if not path.is_file():
        return None, "manifest.yaml is absent"

    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    start = next((i for i, line in enumerate(lines) if line.rstrip("\r\n") == f"  {old}:"), None)
    if start is None:
        return None, f"manifest.yaml has no entry for {old}"

    end = len(lines)
    for index in range(start + 1, len(lines)):
        if re.match(r"^  [^\s].*:\s*$", lines[index].rstrip("\r\n")):
            end = index
            break

    block = lines[start:end]
    block[0] = f"  {new}:\n"
    rewritten: list[str] = []
    index = 0
    while index < len(block):
        line = block[index]
        stripped = line.strip()
        if stripped.startswith("sourcePath:"):
            rewritten.append(f"    sourcePath: {new}\n")
        elif line.startswith("      displayName:"):
            rewritten.append(f"      displayName: {title}\n")
        elif line.startswith("      defaultPrompt:"):
            rewritten.append(
                f"      defaultPrompt: {json.dumps(default_prompt, ensure_ascii=False)}\n"
            )
            index += 1
            while index < len(block):
                continuation = block[index]
                if continuation.strip():
                    indent = len(continuation) - len(continuation.lstrip(" "))
                    if indent <= 6:
                        index -= 1
                        break
                index += 1
        elif stripped.startswith("sourceIdentity:"):
            indent = line[: len(line) - len(line.lstrip(" "))]
            rewritten.append(f"{indent}sourceIdentity: {new}\n")
        else:
            rewritten.append(replace_skill_identity(line, old, new))
        index += 1

    lines[start:end] = rewritten
    return "".join(lines), None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Synchronize one Aria skill's identity and optionally rename its directory."
    )
    parser.add_argument("skills_root", type=Path)
    parser.add_argument("current_name")
    parser.add_argument("new_name")
    parser.add_argument("--title", required=True)
    parser.add_argument("--default-prompt", required=True)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="write changes; without this flag, only print the planned operations",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.skills_root.expanduser().resolve()
    old = args.current_name
    new = args.new_name
    title = args.title.strip()
    default_prompt = args.default_prompt.strip()

    if not root.is_dir():
        raise RenameError(f"skills root does not exist: {root}")
    if not MACHINE_NAME_RE.fullmatch(new) or len(new.split("-")) != 2:
        raise RenameError("new name must contain exactly two lowercase hyphenated words")
    if len(title.split()) != 2:
        raise RenameError("display title must contain exactly two words")
    if f"${new}" not in default_prompt:
        raise RenameError(f"default prompt must contain ${new}")

    skill_dir = root / old
    destination_dir = root / new
    if not skill_dir.is_dir():
        raise RenameError(f"skill directory does not exist: {skill_dir}")
    if old != new and destination_dir.exists():
        raise RenameError(f"destination already exists: {destination_dir}")

    skill_path = skill_dir / "SKILL.md"
    aria_path = skill_dir / "agents" / "aria.yaml"
    if not skill_path.is_file() or not aria_path.is_file():
        raise RenameError("skill must contain SKILL.md and agents/aria.yaml")

    skill_text = update_skill_md(skill_path, old, new, title)
    aria_text, icon_moves, warnings = update_aria_yaml(
        aria_path, skill_dir, old, new, title, default_prompt
    )
    path_replacements = [
        (
            f"./{source.relative_to(skill_dir).as_posix()}",
            f"./{destination.relative_to(skill_dir).as_posix()}",
        )
        for source, destination in icon_moves
    ]
    other_updates = update_other_text_files(
        skill_dir, old, new, path_replacements
    )
    manifest_path = root / "manifest.yaml"
    manifest_text, manifest_warning = update_manifest(
        manifest_path, old, new, title, default_prompt
    )
    if manifest_warning:
        warnings.append(manifest_warning)

    action = "APPLY" if args.apply else "DRY-RUN"
    print(f"{action}: {old} -> {new} ({title})")
    for source, destination in icon_moves:
        print(f"  icon: {source.name} -> {destination.name}")
    for path in sorted(other_updates):
        print(f"  text: {path.relative_to(skill_dir)}")
    if old != new:
        print(f"  directory: {old} -> {new}")
    for warning in warnings:
        print(f"  WARN: {warning}")

    if not args.apply:
        return 0

    skill_path.write_text(skill_text, encoding="utf-8")
    aria_path.write_text(aria_text, encoding="utf-8")
    for path, text in other_updates.items():
        path.write_text(text, encoding="utf-8")
    for source, destination in icon_moves:
        destination.parent.mkdir(parents=True, exist_ok=True)
        source.rename(destination)
    if old != new:
        skill_dir.rename(destination_dir)
    if manifest_text is not None:
        manifest_path.write_text(manifest_text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RenameError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
