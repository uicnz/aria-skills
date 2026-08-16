#!/usr/bin/env python3
"""Audit one skill against the current Aria normalization baseline."""

from __future__ import annotations

import argparse
import re
import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote


FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", re.DOTALL)
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
MACHINE_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SENTENCE_END_RE = re.compile(r"[.!?](?=\s|$)")
APPROVED_GLYPH_RE = re.compile(r"Approved glyph:\s+_assets/svg/([^\s]+\.svg)")
SHORT_DESCRIPTION_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[./-][A-Za-z0-9]+)*")
REQUIRED_INTERFACE_KEYS = (
    "displayName",
    "shortDescription",
    "iconSmall",
    "iconLarge",
    "defaultPrompt",
)


class Audit:
    def __init__(self, root: Path, strict: bool = False) -> None:
        self.root = root
        self.strict = strict
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def run(self) -> int:
        if not self.root.is_dir():
            self.error(f"skill directory does not exist: {self.root}")
            return self.report()

        name = self.root.name
        if not MACHINE_NAME_RE.fullmatch(name):
            self.error("directory name must be lowercase hyphen-case")
        if len(name.split("-")) != 2:
            self.error("skill name must contain exactly two hyphen-separated words")

        skill_text = self.check_skill_md(name)
        self.check_aria_yaml(name)
        self.check_icons(name)
        self.check_tree()
        if skill_text is not None:
            self.check_markdown_links()
        return self.report()

    def check_skill_md(self, name: str) -> str | None:
        path = self.root / "SKILL.md"
        if not path.is_file():
            self.error("missing SKILL.md")
            return None

        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            self.error("SKILL.md is not valid UTF-8")
            return None

        match = FRONTMATTER_RE.match(text)
        if not match:
            self.error("SKILL.md must begin with YAML frontmatter")
            return text

        fields: dict[str, str] = {}
        for line in match.group(1).splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            if line[:1].isspace() or ":" not in line:
                self.error("frontmatter values must use one-line top-level fields")
                continue
            key, value = line.split(":", 1)
            fields[key.strip()] = self.unquote(value.strip())

        extras = sorted(set(fields) - {"name", "description"})
        if extras:
            self.error(f"frontmatter has unsupported fields: {', '.join(extras)}")
        if fields.get("name") != name:
            self.error(f"frontmatter name must exactly match directory name {name!r}")

        description = fields.get("description", "")
        if not description:
            self.error("frontmatter description is missing")
        else:
            if not description.startswith("Use when "):
                self.error("description must begin with 'Use when '")
            if len(SENTENCE_END_RE.findall(description)) != 1:
                self.error("description must be one complete sentence")
            if description[-1:] not in ".!?":
                self.error("description must end with sentence punctuation")

        if not re.search(r"^## Overview\s*$", text, re.MULTILINE):
            self.error("SKILL.md must contain an Overview section")
        title = re.search(r"^# (.+?)\s*$", text, re.MULTILINE)
        if not title:
            self.error("SKILL.md must contain an H1 title")
        elif len(title.group(1).split()) != 2:
            self.error("SKILL.md H1 title must contain exactly two words")
        if len(text.splitlines()) >= 500:
            self.error("SKILL.md must remain under 500 lines")
        return text

    def check_aria_yaml(self, name: str) -> None:
        path = self.root / "agents" / "aria.yaml"
        if not path.is_file():
            self.error("missing agents/aria.yaml")
            return

        text = path.read_text(encoding="utf-8")
        if not re.search(r"^interface:\s*$", text, re.MULTILINE):
            self.error("agents/aria.yaml must contain an interface mapping")

        values: dict[str, str] = {}
        for line in text.splitlines():
            match = re.fullmatch(r'  ([A-Za-z][A-Za-z0-9]*):\s*(["\'])(.*?)\2\s*', line)
            if match:
                values[match.group(1)] = match.group(3)

        for key in REQUIRED_INTERFACE_KEYS:
            if key not in values:
                self.error(f"agents/aria.yaml is missing quoted interface.{key}")

        short = values.get("shortDescription", "")
        if short and not 25 <= len(short) <= 64:
            self.error("interface.shortDescription must be 25–64 characters")
        if short:
            word_count = len(SHORT_DESCRIPTION_WORD_RE.findall(short))
            if not 6 <= word_count <= 12:
                self.warn(
                    "interface.shortDescription should preferably contain about ten words "
                    f"(found {word_count})"
                )

        display_name = values.get("displayName", "")
        if display_name and len(display_name.split()) != 2:
            self.error("interface.displayName must contain exactly two words")

        expected_small = f"./assets/{name}.svg"
        expected_large = f"./assets/{name}.png"
        if values.get("iconSmall") != expected_small:
            self.error(f"interface.iconSmall must be {expected_small!r}")
        if values.get("iconLarge") != expected_large:
            self.error(f"interface.iconLarge must be {expected_large!r}")
        if values.get("defaultPrompt") and f"${name}" not in values["defaultPrompt"]:
            self.error(f"interface.defaultPrompt must contain ${name}")

        if (self.root / "agents" / "openai.yaml").exists():
            self.error("agents/openai.yaml remains; migrate product metadata to agents/aria.yaml")

    def check_icons(self, name: str) -> None:
        svg_path = self.root / "assets" / f"{name}.svg"
        png_path = self.root / "assets" / f"{name}.png"

        if not svg_path.is_file():
            self.error(f"missing assets/{name}.svg")
        else:
            try:
                root = ET.parse(svg_path).getroot()
                if root.tag.rsplit("}", 1)[-1] != "svg":
                    self.error("SVG asset root element must be <svg>")
                if root.get("width") != "100" or root.get("height") != "100":
                    self.error("SVG asset must declare width=100 and height=100")
                if root.get("viewBox") != "0 0 100 100":
                    self.error('SVG asset must use viewBox="0 0 100 100"')
                svg_text = svg_path.read_text(encoding="utf-8").lower()
                if not any(token in svg_text for token in ('fill="#000"', 'fill="black"', 'fill="#000000"')):
                    self.warn("SVG does not contain an explicit black fill")
                if not any(token in svg_text for token in ('fill="#fff"', 'fill="white"', 'fill="#ffffff"')):
                    self.warn("SVG does not contain an explicit white fill")
                provenance_match = APPROVED_GLYPH_RE.search(
                    svg_path.read_text(encoding="utf-8")
                )
                if not provenance_match:
                    self.error("SVG must identify its approved glyph source")
                else:
                    source_name = provenance_match.group(1)
                    if Path(source_name).name != source_name:
                        self.error("SVG provenance source must be a direct approved glyph")
                    if "legacy" in source_name.casefold():
                        self.error("SVG provenance selects a forbidden legacy glyph")
                    approved_source = self.root.parent / "_assets" / "svg" / source_name
                    if not approved_source.is_file():
                        self.error(
                            f"SVG provenance source is not in the approved set: {source_name}"
                        )
            except (ET.ParseError, UnicodeDecodeError) as exc:
                self.error(f"SVG asset is invalid: {exc}")

        if not png_path.is_file():
            self.error(f"missing assets/{name}.png")
        else:
            try:
                with png_path.open("rb") as handle:
                    header = handle.read(33)
                if header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
                    raise ValueError("invalid PNG signature or IHDR")
                width, height, bit_depth, color_type, _, _, _ = struct.unpack(
                    ">IIBBBBB", header[16:29]
                )
                if (width, height) != (100, 100):
                    self.error("PNG asset must be exactly 100×100 pixels")
                if bit_depth != 8 or color_type != 6:
                    self.error("PNG asset must use 8-bit RGBA channels")
            except (OSError, ValueError, struct.error) as exc:
                self.error(f"PNG asset is invalid: {exc}")

    def check_tree(self) -> None:
        forbidden_names = {
            ".DS_Store",
            "CLAUDE.md",
            "README.md",
            "CHANGELOG.md",
            "INSTALLATION_GUIDE.md",
            "LICENSE",
            "LICENSE.txt",
            "NOTICE",
            "NOTICE.txt",
            "QUICK_REFERENCE.md",
            "license.txt",
        }
        for path in self.root.rglob("*"):
            rel = path.relative_to(self.root)
            if path.is_file() and path.suffix.lower() == ".md" and "_" in path.name:
                self.error(f"replace underscores with dashes in Markdown filename: {rel}")
            if path.name in forbidden_names:
                self.error(f"remove or migrate extraneous artifact: {rel}")
            if path.name == "__pycache__" or path.suffix == ".pyc":
                self.error(f"remove generated cache artifact: {rel}")
            if ".claude" in path.parts:
                self.error(f"remove or migrate Claude-specific artifact: {rel}")

        singular_reference = self.root / "reference"
        if singular_reference.exists():
            self.error("rename reference/ to references/")

        allowed_top_level = {
            "SKILL.md",
            "agents",
            "assets",
            "references",
            "scripts",
        }
        for path in self.root.iterdir():
            if path.name not in allowed_top_level:
                self.warn(f"review non-canonical top-level entry: {path.name}")

        references = self.root / "references"
        if references.is_dir():
            reference_count = sum(1 for path in references.rglob("*.md") if path.name != "INDEX.md")
            if reference_count >= 10 and not (references / "INDEX.md").is_file():
                self.warn("large reference library should include references/INDEX.md")

    def check_markdown_links(self) -> None:
        markdown_files = [self.root / "SKILL.md"]
        references = self.root / "references"
        if references.is_dir():
            markdown_files.extend(references.rglob("*.md"))

        for source in markdown_files:
            text = source.read_text(encoding="utf-8")
            for raw_target in MARKDOWN_LINK_RE.findall(text):
                target = raw_target.strip().strip("<>").split("#", 1)[0]
                if not target or re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE):
                    continue
                target = unquote(target.split(" ", 1)[0])
                if Path(target).is_absolute():
                    continue
                if not (source.parent / target).resolve().exists():
                    rel = source.relative_to(self.root)
                    self.error(f"broken local Markdown link in {rel}: {raw_target}")

    @staticmethod
    def unquote(value: str) -> str:
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            return value[1:-1]
        return value

    def report(self) -> int:
        for message in self.errors:
            print(f"ERROR: {message}")
        for message in self.warnings:
            print(f"WARN: {message}")

        failed = bool(self.errors or (self.strict and self.warnings))
        if failed:
            print(
                f"FAIL: {self.root} ({len(self.errors)} errors, "
                f"{len(self.warnings)} warnings)"
            )
            return 1

        print(f"PASS: {self.root} ({len(self.warnings)} warnings)")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit one skill against the current Aria taxonomy."
    )
    parser.add_argument("skill_dir", type=Path, help="path to one Aria skill directory")
    parser.add_argument(
        "--strict", action="store_true", help="treat audit warnings as failures"
    )
    args = parser.parse_args()
    return Audit(args.skill_dir.expanduser().resolve(), strict=args.strict).run()


if __name__ == "__main__":
    sys.exit(main())
