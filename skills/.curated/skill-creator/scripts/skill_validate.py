#!/usr/bin/env python3
"""Validate one completed skill against the current Aria baseline."""

from __future__ import annotations

import re
import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml


MAX_SKILL_NAME_LENGTH = 64
MACHINE_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", re.DOTALL)
SENTENCE_END_RE = re.compile(r"[.!?](?=\s|$)")
APPROVED_GLYPH_RE = re.compile(r"Approved glyph:\s+_assets/svg/([^\s]+\.svg)")
REQUIRED_INTERFACE_KEYS = {
    "defaultPrompt",
    "displayName",
    "iconLarge",
    "iconSmall",
    "shortDescription",
}


def validate_png(path: Path) -> str | None:
    try:
        with path.open("rb") as handle:
            header = handle.read(33)
        if header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
            return "invalid PNG signature or IHDR"
        width, height, bit_depth, color_type, _, _, _ = struct.unpack(
            ">IIBBBBB", header[16:29]
        )
    except (OSError, struct.error) as exc:
        return f"could not read PNG: {exc}"
    if (width, height) != (100, 100):
        return "PNG must be exactly 100×100"
    if bit_depth != 8 or color_type != 6:
        return "PNG must use 8-bit RGBA channels"
    return None


def validate_svg(path: Path) -> str | None:
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as exc:
        return f"invalid SVG: {exc}"
    if root.tag.rsplit("}", 1)[-1] != "svg":
        return "SVG root element must be <svg>"
    if root.get("width") != "100" or root.get("height") != "100":
        return "SVG must declare width=100 and height=100"
    if root.get("viewBox") != "0 0 100 100":
        return 'SVG must use viewBox="0 0 100 100"'
    return None


def validate_skill(skill_path: str | Path) -> tuple[bool, str]:
    root = Path(skill_path).expanduser().resolve()
    errors: list[str] = []
    if not root.is_dir():
        return False, f"Skill directory not found: {root}"

    name = root.name
    if not MACHINE_NAME_RE.fullmatch(name) or len(name) > MAX_SKILL_NAME_LENGTH:
        errors.append("directory name must be lowercase hyphen-case and at most 64 characters")

    skill_md = root / "SKILL.md"
    if not skill_md.is_file():
        errors.append("missing SKILL.md")
    else:
        content = skill_md.read_text(encoding="utf-8")
        match = FRONTMATTER_RE.match(content)
        if not match:
            errors.append("SKILL.md must begin with valid YAML frontmatter")
        else:
            try:
                frontmatter = yaml.safe_load(match.group(1))
            except yaml.YAMLError as exc:
                errors.append(f"invalid YAML frontmatter: {exc}")
                frontmatter = None
            if isinstance(frontmatter, dict):
                extras = sorted(set(frontmatter) - {"name", "description"})
                if extras:
                    errors.append(f"unsupported frontmatter fields: {', '.join(extras)}")
                if frontmatter.get("name") != name:
                    errors.append("frontmatter name must exactly match the directory name")
                description = frontmatter.get("description")
                if not isinstance(description, str) or not description:
                    errors.append("frontmatter description is missing")
                else:
                    if not description.startswith("Use when "):
                        errors.append("description must begin with 'Use when '")
                    if len(SENTENCE_END_RE.findall(description)) != 1:
                        errors.append("description must be one complete sentence")
            elif frontmatter is not None:
                errors.append("frontmatter must be a YAML mapping")
        if "TODO" in content:
            errors.append("SKILL.md still contains TODO placeholders")
        if not re.search(r"^## Overview\s*$", content, re.MULTILINE):
            errors.append("SKILL.md must contain an Overview section")
        if len(content.splitlines()) >= 500:
            errors.append("SKILL.md must remain under 500 lines")

    aria_yaml = root / "agents" / "aria.yaml"
    if not aria_yaml.is_file():
        errors.append("missing agents/aria.yaml")
    else:
        try:
            metadata = yaml.safe_load(aria_yaml.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            errors.append(f"invalid agents/aria.yaml: {exc}")
            metadata = None
        interface = metadata.get("interface") if isinstance(metadata, dict) else None
        if not isinstance(interface, dict):
            errors.append("agents/aria.yaml must contain an interface mapping")
        else:
            missing = sorted(REQUIRED_INTERFACE_KEYS - set(interface))
            if missing:
                errors.append(f"missing Aria interface fields: {', '.join(missing)}")
            short = interface.get("shortDescription")
            if isinstance(short, str) and not 25 <= len(short) <= 64:
                errors.append("shortDescription must be 25–64 characters")
            expected_small = f"./assets/{name}.svg"
            expected_large = f"./assets/{name}.png"
            if interface.get("iconSmall") != expected_small:
                errors.append(f"iconSmall must be {expected_small}")
            if interface.get("iconLarge") != expected_large:
                errors.append(f"iconLarge must be {expected_large}")
            prompt = interface.get("defaultPrompt")
            if not isinstance(prompt, str) or f"${name}" not in prompt:
                errors.append(f"defaultPrompt must contain ${name}")

    if (root / "agents" / "openai.yaml").exists():
        errors.append("agents/openai.yaml is not Aria metadata")

    svg_path = root / "assets" / f"{name}.svg"
    png_path = root / "assets" / f"{name}.png"
    if not svg_path.is_file():
        errors.append(f"missing assets/{name}.svg")
    else:
        error = validate_svg(svg_path)
        if error:
            errors.append(error)
        svg_text = svg_path.read_text(encoding="utf-8")
        provenance = APPROVED_GLYPH_RE.search(svg_text)
        if not provenance:
            errors.append("SVG must identify its approved glyph source")
        else:
            source_name = provenance.group(1)
            if Path(source_name).name != source_name:
                errors.append("SVG provenance source must be a direct approved glyph")
            if "legacy" in source_name.casefold():
                errors.append("SVG provenance selects a forbidden legacy glyph")
            if not (root.parent / "_assets" / "svg" / source_name).is_file():
                errors.append(
                    f"SVG provenance source is not in the approved set: {source_name}"
                )
    if not png_path.is_file():
        errors.append(f"missing assets/{name}.png")
    else:
        error = validate_png(png_path)
        if error:
            errors.append(error)

    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() == ".md" and "_" in path.name:
            errors.append(
                f"Markdown filename must use dashes instead of underscores: "
                f"{path.relative_to(root)}"
            )
        if path.name in {".DS_Store", "__pycache__"} or path.suffix == ".pyc":
            errors.append(f"generated litter remains: {path.relative_to(root)}")
        if path.name in {"LICENSE", "LICENSE.txt", "NOTICE", "NOTICE.txt", "license.txt"}:
            errors.append(f"unwanted local license artifact remains: {path.relative_to(root)}")
        if path.name == "CLAUDE.md" or ".claude" in path.parts:
            errors.append(f"Claude-specific artifact remains: {path.relative_to(root)}")

    if errors:
        return False, "\n".join(f"- {error}" for error in errors)
    return True, "Skill is valid!"


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 skill_validate.py <skill_directory>")
        return 1
    valid, message = validate_skill(sys.argv[1])
    print(message)
    return 0 if valid else 1


if __name__ == "__main__":
    sys.exit(main())
