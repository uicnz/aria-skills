---
name: skill-creator
description: Use when an Aria skill needs to be created or updated with reusable instructions, references, scripts, assets, or interface metadata.
---

# Skill Creator

## Overview

Create and revise focused Aria skills that package specialized workflows, domain knowledge, deterministic tooling, reusable assets, and UI metadata. This skill includes an initializer, an Aria metadata generator, a validator, and fallback icon templates so a new skill begins with the current Aria taxonomy rather than requiring cleanup afterward.

## Core Principles

### Keep Context Lean

Assume the agent already understands general software and reasoning patterns. Include only knowledge, constraints, workflows, and resources that materially improve execution.

- Prefer concise examples over long explanations.
- Keep `SKILL.md` under 500 lines.
- Move detailed or conditional material into routed references.
- Avoid duplicating content between `SKILL.md` and references.

### Match the Required Precision

- Use flexible prose when several approaches are valid.
- Use pseudocode or parameterized scripts when a preferred pattern allows variation.
- Use deterministic scripts and explicit sequences when mistakes are costly or consistency matters.

### Preserve Validation Integrity

Test added scripts directly. For complex skills, forward-test against realistic prompts and raw artifacts without leaking the intended answer or prior diagnosis into the test context.

## Canonical Aria Skill

```text
skill-name/
├── SKILL.md
├── agents/
│   └── aria.yaml
├── assets/
│   ├── skill-name.svg
│   └── skill-name.png
├── references/          # Optional detailed knowledge
└── scripts/             # Optional deterministic tooling
```

Retain other directories only when they support runtime behavior. Do not add auxiliary documentation such as `README.md`, installation guides, quick references, or changelogs.

## Creation Workflow

### 1. Understand the Skill

Establish concrete triggering examples before writing instructions:

- What would a user ask that should activate this skill?
- Which nearby requests should not activate it?
- What inputs, outputs, tools, and constraints recur?
- Which decisions require domain knowledge rather than general reasoning?
- Where should the skill be created? Default to `~/.aria/skills` when the user does not specify a location.

Avoid unnecessary clarification when the requested scope and location are already clear.

### 2. Plan Reusable Contents

For each representative task, identify what would otherwise need to be rediscovered or rewritten:

- Put procedural instructions in `SKILL.md`.
- Put detailed knowledge and schemas in `references/`.
- Put deterministic or repeated operations in `scripts/`.
- Put icons, templates, fonts, and output resources in `assets/`.

Create only resources the skill genuinely needs, apart from the standard Aria metadata and icon pair.

### 3. Initialize a New Skill

Always use the bundled initializer for a new skill:

```bash
python3 scripts/skill_init.py skill-name
python3 scripts/skill_init.py skill-name --path /custom/skills/path
python3 scripts/skill_init.py skill-name --resources scripts,references
```

The initializer normalizes the machine name, creates `SKILL.md`, copies matching fallback SVG and PNG icons, and generates `agents/aria.yaml`. It defaults to `~/.aria/skills`.

Pass explicit interface values when the defaults are not suitable:

```bash
python3 scripts/skill_init.py skill-name \
  --interface 'displayName=Skill Name' \
  --interface 'shortDescription=Create and update specialized workflows' \
  --interface 'defaultPrompt=Use $skill-name to handle this task.'
```

### 4. Edit the Skill

Write instructions for another Aria agent to follow. Use imperative or infinitive phrasing and include details that are beneficial and non-obvious.

#### Frontmatter

Keep exactly two fields:

```yaml
---
name: skill-name
description: Use when a request needs the skill's specific expertise or workflow.
---
```

- Make `name` identical to the lowercase, hyphenated directory name.
- Make `description` one clear, complete sentence about when to use the skill.
- Prefer the opening `Use when` posture.
- Keep workflow, implementation details, and capability inventories out of the description.
- Move useful detail displaced from the description into `## Overview`.

#### Body and Progressive Disclosure

- Put the scope and retained capability detail in `## Overview`.
- Keep the core workflow in `SKILL.md`.
- Link directly to each reference or to a navigable `references/INDEX.md`.
- Add a contents section to long references.
- Avoid deeply nested discovery paths unless the domain requires them.

#### Interface Metadata

Read `references/aria-yaml.md` before generating or editing metadata. Use the bundled generator when metadata changes:

```bash
python3 scripts/skill_meta.py /path/to/skill \
  --interface 'displayName=Skill Name' \
  --interface 'shortDescription=Create and update specialized workflows'
```

Keep icon paths synchronized with `assets/<skill-name>.svg` and `assets/<skill-name>.png`.

#### Assets

- Make the SVG and PNG visually identical.
- Use a 100×100 SVG canvas and a 100×100, 8-bit RGBA PNG.
- Use a relevant white glyph on a black circular field unless branding or user direction requires another treatment.
- Replace the initializer's fallback icons with a relevant source from the shared `<skills-root>/_assets/svg/` set before final validation.
- Never select a source whose filename contains `legacy`, case-insensitively.
- Record `Approved glyph: _assets/svg/<source>.svg` inside the finished SVG so the source remains auditable.
- Use the Skill Normalizer's `scripts/skill_icon.py` when available to generate and register the matching pair.

### 5. Validate

Run the bundled validator after creation and after material updates:

```bash
python3 scripts/skill_validate.py /path/to/skill
```

Also run added scripts, check local Markdown links, parse SVG assets, inspect generated icons visually, and remove placeholders or generated litter.

### 6. Iterate

Use the skill on real tasks, identify friction or missing knowledge, revise the smallest appropriate layer, and validate again. Forward-test when the workflow is complex enough that static inspection is insufficient.

## Updating Existing Skills

Skip initialization when the skill already exists. Read its complete `SKILL.md` and inspect its resources before editing. Preserve useful content, user changes, and runtime resources while migrating obsolete metadata or product-specific scaffolding into the Aria taxonomy.
