# Aria Skill Taxonomy

This document records the normalization baseline confirmed during ongoing work in the Aria skills directory. Update it as the user establishes more specific conventions.

## Canonical Tree

```text
skill-name/
├── SKILL.md
├── agents/
│   └── aria.yaml
├── assets/
│   ├── skill-name.svg
│   └── skill-name.png
├── references/          # When detailed knowledge is needed
└── scripts/             # When deterministic tooling is needed
```

Retain other runtime-useful directories such as `examples/` or `evaluations/` when the skill genuinely uses them. Do not create empty optional directories merely to resemble another skill.

## Naming

- Use lowercase letters, digits, and hyphens for the directory and frontmatter name.
- Make the directory name and frontmatter `name` identical.
- Use exactly two words for the directory name, frontmatter name, H1 title, and `displayName`; this is a structural requirement, not proof that the title is appropriate.
- Reassess every existing name, including already compliant two-word names, against the skill's trigger, full scope, short description, neighboring responsibilities, and collection-wide vocabulary.
- Retain an existing two-word name only after confirming that it remains the clearest, most accurate, and least ambiguous option.
- Use title case and spaces for `displayName`; keep the machine name lowercase and hyphenated.
- Before a collection-wide rename, pair every current directory with its description, short description, and display name; establish the complete proposed taxonomy before editing the first skill.
- Use the holistic inventory to design a suite that feels intentionally named as a collection, not merely to identify titles that violate the two-word structure.
- Resolve duplicate targets, provider families, neighboring responsibilities, grammatical patterns, and vocabulary consistency in that read-only planning pass, then apply the settled map serially.
- Prefer parallel naming where responsibilities are genuinely parallel, but do not force uniform wording when it weakens semantic precision.
- When a product or provider namespace must remain, reserve the first word for that namespace and make the second word the clearest single-word expression of the skill's job.
- Name the standard icons exactly `<skill-name>.svg` and `<skill-name>.png`.
- Use dashes instead of underscores in every Markdown filename.
- Name related Python utilities with a shared subject prefix followed by the action in snake_case, such as `skill_init.py`, `skill_validate.py`, `skill_meta.py`, `skill_audit.py`, `skill_inventory.py`, and `skill_rename.py`.
- Treat names and relative paths as case-sensitive.

### Provider Family Case Study: Notion

Do not solve the two-word constraint by dropping a product namespace that distinguishes a family of integration-specific skills. Keep `Notion` as the shared first word and choose one functional word that separates each workflow.

| Original name | Normalized title | Normalized slug | Functional distinction |
| --- | --- | --- | --- |
| Notion Knowledge Capture | **Notion Capture** | `notion-capture` | Converts chats, notes, conversations, and decisions into structured, linked Notion knowledge. |
| Notion Meeting Intelligence | **Notion Briefing** | `notion-briefing` | Prepares agendas, pre-reads, attendee context, and supporting meeting research. |
| Notion Research Documentation | **Notion Research** | `notion-research` | Synthesizes multiple Notion sources into cited briefs, comparisons, summaries, and reports. |
| Notion Spec to Implementation | **Notion Planning** | `notion-planning` | Converts specs into plans, tasks, dependencies, and progress tracking without claiming to implement the code. |

Apply the same reasoning to other product families: preserve the meaningful namespace, then make the second word carry the workflow distinction.

## SKILL.md Frontmatter

Use only these fields:

```yaml
---
name: skill-name
description: Use when an Aria skill needs a clearly stated triggering condition.
---
```

The description must:

- Be one complete sentence on one physical line.
- State when the skill should be used.
- Prefer the opening `Use when` posture.
- Avoid explaining how the skill works or listing everything it does.
- Retain sufficient trigger coverage for reliable discovery.

Move capability lists, supported formats, exclusions, special cases, and other useful detail displaced from the description into `## Overview` or an appropriate reference.

## SKILL.md Body

- Place `## Overview` near the beginning and include the skill's scope there.
- Use imperative or infinitive instructions.
- Keep the body concise and under 500 lines.
- Keep essential operating guidance in `SKILL.md` and route detailed domain material into `references/`.
- Link directly to reference files or to `references/INDEX.md` so agents can discover them.
- Add `references/INDEX.md` when a large library needs navigation.
- Avoid a redundant body section explaining when to use the skill; triggering belongs in frontmatter.
- Preserve local Markdown link integrity after moving files.

## Aria Interface Metadata

Use `agents/aria.yaml` with camelCase Aria keys:

```yaml
interface:
  displayName: "Skill Name"
  shortDescription: "A concise UI description between 25 and 64 characters"
  iconSmall: "./assets/skill-name.svg"
  iconLarge: "./assets/skill-name.png"
  defaultPrompt: "Use $skill-name to handle this task."
```

Requirements:

- Quote all string values.
- Keep `displayName` concise; prefer two words when that remains clear.
- Keep `shortDescription` readable at a glance and between 25 and 64 characters.
- Prefer roughly ten words in a compact capability phrase beginning with a strong verb.
- Include the exact `$skill-name` token in `defaultPrompt`.
- Point `iconSmall` and `iconLarge` to existing, case-sensitive paths.
- Use `agents/aria.yaml`, not product metadata copied unchanged from another runtime.

## Domains and Categories

Keep installed skill identity and integrity in the machine-owned `manifest.yaml`, and keep human organization in the scoped `.aria/settings/skills.yaml`. Do not add domain or category keys to skill packages, interface sidecars, directory paths, or manifest records.

Define each domain with a label, description, order, and category map. Keep category IDs and human-facing labels to one word, treating categories as compact grouping tags beneath the broader domain. Assign a registered skill by stable skill ID using both a domain and a category; Aria requires the pair together. Design the vocabulary from a holistic collection inventory so neighboring skills group consistently, then validate the file with Aria's `SkillSettingsSchema` and effective-settings resolver. A collection intended to be fully categorized should have exactly one valid assignment for every registered skill and no stale assignments.

## Icons

The current generic icon treatment is:

- A relevant white glyph on a black circular field with transparent outer corners.
- A 100×100 SVG with `width="100"`, `height="100"`, and `viewBox="0 0 100 100"`.
- A 100×100 sRGB PNG with 8-bit RGBA channels.
- An SVG and PNG that depict the same geometry, scale, position, colors, and transparency.
- Exact filenames matching the skill name.

Prefer a relevant glyph from the shared `<skills-root>/_assets/svg/` library. Build the candidate list by excluding every source filename containing `legacy`, case-insensitively:

```bash
rg --files /path/to/skills/_assets/svg | rg -vi 'legacy'
```

Never select, copy, convert, trace, adapt, or rename a legacy source into eligibility. Legacy glyphs have not received the modern stroke thickness and detail refinements, so mixing them into the skill collection breaks visual cohesion. If no suitable modern glyph exists, choose another non-legacy metaphor or use the shared fallback icon. Preserve a deliberate brand icon when the skill or user requires one.

Record the selected source in the normalized SVG as `Approved glyph: _assets/svg/<source>.svg`. Generate the pair one skill at a time with `scripts/skill_icon.py`; the audit treats missing, unknown, or legacy provenance as an error.

## Bundled Resources

- Use `references/` for material an agent loads into context as needed.
- Use `scripts/` for deterministic or repeatedly needed operations, and test added scripts.
- Before normalizing a field that benefits from cross-skill comparison, use `scripts/skill_inventory.py --field <field>` to enumerate that field across every immediate child skill; missing values must remain visible.
- After normalizing a complete flat collection, use `scripts/skill_manifest.ts` with the Aria source tree to compile the machine-owned manifest and immutable generations from the immediate child directories that contain `SKILL.md`.
- Use `assets/` for icons, templates, fonts, and files used in outputs rather than read as instructions.
- Prefer `references/` over the singular `reference/` when normalizing legacy layouts.
- Avoid duplicated content between `SKILL.md` and references.
- Avoid unrelated auxiliary documents such as `README.md`, changelogs, and installation guides.

## Legacy Cleanup

Remove these after migrating useful content:

- `CLAUDE.md` and `.claude/` configuration.
- Claude-only settings, prompts, and obsolete evaluation scaffolding.
- `.DS_Store`, `__pycache__/`, `.pyc` files, and other system litter.
- Local license and notice files that do not support runtime behavior.
- Template placeholders and empty directories.
- Auxiliary human-facing documentation that does not support agent runtime behavior.

Do not delete unfamiliar files solely because they are absent from the canonical minimum. Inspect them, determine their runtime value, and preserve or migrate them deliberately.

## Completion Checklist

- Read the complete target `SKILL.md` before editing.
- Confirm folder name, frontmatter name, icon basenames, metadata references, and invocation token agree.
- Confirm the chosen title was semantically assessed rather than retained solely because it already contained two words.
- Confirm the chosen title strengthens the cohesion of the complete suite without obscuring the skill's distinct responsibility.
- Confirm the description is one complete `Use when` sentence and the displaced detail appears in Overview.
- Confirm `agents/aria.yaml` uses the Aria key casing and all required interface fields.
- Confirm the SVG parses and the PNG is 100×100, 8-bit RGBA.
- Confirm the source glyph came from the non-legacy subset of `<skills-root>/_assets/svg/`, or document that a deliberate brand icon or shared fallback was used.
- Visually compare the SVG and PNG.
- Check all local Markdown links.
- Remove confirmed legacy artifacts and system litter.
- Run the bundled audit and the available skill validator.
- Compile and validate the collection manifest after directory additions, removals, renames, metadata changes, or bundled-resource changes.
- Validate scoped domain/category settings and confirm assignment coverage after collection-wide taxonomy changes.
- Treat collection-wide scope as a serial queue, not as permission to batch-read, batch-rename, or batch-edit skills.
- Complete, validate, and report one skill before starting another unless the user explicitly requests batch execution.
