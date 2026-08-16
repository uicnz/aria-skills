#!/usr/bin/env python3
"""Build one Aria icon pair from an approved non-legacy glyph."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


SVG_BODY_RE = re.compile(r"<svg\b[^>]*>(.*)</svg>\s*\Z", re.DOTALL | re.IGNORECASE)


class IconError(RuntimeError):
    pass


def resolve_source(skills_root: Path, raw_source: str) -> Path:
    source_name = raw_source if raw_source.endswith(".svg") else f"{raw_source}.svg"
    source = (skills_root / "_assets" / "svg" / source_name).resolve()
    approved_root = (skills_root / "_assets" / "svg").resolve()
    if source.parent != approved_root:
        raise IconError("source must be a direct child of <skills-root>/_assets/svg")
    if "legacy" in source.name.casefold():
        raise IconError(f"legacy glyphs are forbidden: {source.name}")
    if not source.is_file():
        raise IconError(f"approved glyph does not exist: {source}")
    return source


def build_svg(source: Path) -> str:
    source_text = source.read_text(encoding="utf-8")
    try:
        source_root = ET.fromstring(source_text)
    except ET.ParseError as exc:
        raise IconError(f"approved glyph is invalid SVG: {exc}") from exc
    view_box = source_root.get("viewBox")
    if not view_box:
        raise IconError("approved glyph is missing viewBox")
    match = SVG_BODY_RE.search(source_text)
    if not match:
        raise IconError("could not isolate approved glyph contents")
    body = match.group(1).strip().replace("currentColor", "#fff")
    provenance = f"_assets/svg/{source.name}"
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" '
        'viewBox="0 0 100 100">\n'
        f"  <!-- Approved glyph: {provenance} -->\n"
        '  <circle cx="50" cy="50" r="49" fill="#000"/>\n'
        f'  <svg x="17" y="17" width="66" height="66" viewBox="{view_box}" '
        'preserveAspectRatio="xMidYMid meet">\n'
        f"{body}\n"
        "  </svg>\n"
        "</svg>\n"
    )


def update_aria_yaml(path: Path, skill_name: str) -> None:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"(?m)^  icon(?:Small|Large):\s*.*\n?", "", text)
    anchor = re.compile(r"(?m)^(  shortDescription:\s*.*)$")
    if not anchor.search(text):
        raise IconError("agents/aria.yaml is missing interface.shortDescription")
    icon_lines = (
        f'  iconSmall: "./assets/{skill_name}.svg"\n'
        f'  iconLarge: "./assets/{skill_name}.png"'
    )
    text = anchor.sub(rf"\1\n{icon_lines}", text, count=1)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def render_png(svg_path: Path, png_path: Path) -> None:
    renderer = shutil.which("rsvg-convert")
    if not renderer:
        raise IconError("rsvg-convert is required to render the matching PNG")
    subprocess.run(
        [
            renderer,
            "--width",
            "100",
            "--height",
            "100",
            "--output",
            str(png_path),
            str(svg_path),
        ],
        check=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create one Aria SVG/PNG icon pair from the approved glyph set."
    )
    parser.add_argument("skills_root", type=Path)
    parser.add_argument("skill_name")
    parser.add_argument("source_glyph", help="approved SVG filename or basename")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    skills_root = args.skills_root.expanduser().resolve()
    skill_dir = skills_root / args.skill_name
    if not (skill_dir / "SKILL.md").is_file():
        raise IconError(f"skill does not exist: {skill_dir}")
    aria_path = skill_dir / "agents" / "aria.yaml"
    if not aria_path.is_file():
        raise IconError(f"skill is missing agents/aria.yaml: {skill_dir}")

    source = resolve_source(skills_root, args.source_glyph)
    assets_dir = skill_dir / "assets"
    assets_dir.mkdir(exist_ok=True)
    svg_path = assets_dir / f"{args.skill_name}.svg"
    png_path = assets_dir / f"{args.skill_name}.png"
    svg_path.write_text(build_svg(source), encoding="utf-8")
    render_png(svg_path, png_path)
    update_aria_yaml(aria_path, args.skill_name)
    print(f"PASS: {args.skill_name} <- _assets/svg/{source.name}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (IconError, OSError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
