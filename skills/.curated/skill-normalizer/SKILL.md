---
name: skill-normalizer
description: Use when an Aria skill needs to be created, audited, migrated, or normalized for compliance with the current Aria skill taxonomy.
---

# Skill Normalizer

## Overview

Standardize one Aria skill at a time across naming, trigger metadata, instructions, interface metadata, icons, resource layout, legacy cleanup, and validation. Use directory-wide metadata inventories to design the collection as a cohesively named and categorized suite before making local changes, and preserve useful domain knowledge by moving it to the correct layer rather than discarding it during simplification.

This is a living normalization skill. Apply the confirmed baseline in `references/aria-taxonomy.md`, then update that reference and the audit script when the user establishes a more nuanced convention.

## Operating Posture

- Treat a collection-wide request as a serial queue and work on exactly one target skill at a time.
- Do not batch-read, batch-rename, or batch-edit skills unless the user explicitly asks for batch execution; asking to normalize an entire collection does not by itself authorize batching.
- Read the target `SKILL.md` completely before editing it, then inspect the complete skill tree and relevant bundled resources.
- Preserve user-authored content and unrelated changes. Move useful material before removing obsolete files.
- Distinguish a confirmed Aria convention from an inference based on neighboring skills; ask before turning a consequential inference into a repository-wide rule.
- Finish, validate, and report the current skill before moving to the next one.

## Workflow

1. Resolve the exact skill directory and confirm its folder name.
2. When naming or metadata requires cross-skill judgment, inventory the relevant fields across the complete skills directory and establish the cohesive target taxonomy before editing the first queued skill.
3. Read the complete `SKILL.md`, inspect `agents/`, `assets/`, `references/`, and `scripts/`, and identify legacy product-specific artifacts.
4. Run the bundled audit before editing to capture the starting state:

   ```bash
   python3 scripts/skill_audit.py /absolute/path/to/skill
   ```

5. Normalize the frontmatter description using the rules below and move displaced scope or capability details into `## Overview`.
6. Normalize the body for concise instructions and progressive disclosure. Keep essential workflow guidance in `SKILL.md`; move detailed knowledge into routed references.
7. Normalize `agents/aria.yaml`, the icon pair, resource directories, names, and paths against `references/aria-taxonomy.md`.
8. Remove obsolete Claude Code scaffolding, system litter, and auxiliary documentation only after preserving any useful information they contain.
9. Re-run the audit, validate the skill with the available skill validator, check local Markdown links, and visually inspect generated icons.
10. For collection-wide changes, synchronize the manifest and the scoped domain/category assignments after the physical skill suite is settled.
11. Report the files changed, content migrated, artifacts removed, validations run, and any convention that still needs user confirmation.

## Directory Inventory

Run `scripts/skill_inventory.py` to compare one metadata or taxonomy field across every immediate child skill. Every value is paired with its parent directory, the script defaults to the Aria skills directory containing this skill, and missing values remain visible in the output:

```bash
python3 scripts/skill_inventory.py --field name
python3 scripts/skill_inventory.py --field description
python3 scripts/skill_inventory.py --field short-description
python3 scripts/skill_inventory.py --field all
```

Use `description` for the `SKILL.md` trigger sentence and `short-description` for `agents/aria.yaml`. Run `--list-fields` to discover every selector, pass an explicit skills-directory path when inventorying another collection, or add `--format json` for structured output.

For collection-wide naming, inventory at least `name`, `description`, `short-description`, and `display-name`; then decide the proposed name for the entire collection before applying the first rename. The purpose of this enumeration is to design one coherent naming suite, not merely to locate individual word-count violations. Reassess every current name during this pass, including names that already contain exactly two words. Resolve semantic fit, clarity, collisions, provider families, functional distinctions, grammatical patterns, and vocabulary consistency before deciding whether to retain or replace each name. Use that holistic map as comparison context while continuing to normalize, validate, and report exactly one target skill at a time.

After settling a name semantically, use `scripts/skill_rename.py` to synchronize one skill's directory, frontmatter, H1, Aria metadata, invocation token, icon filenames, internal paths, and manifest entry. Run it without `--apply` first, inspect the dry run, then apply and validate that skill before invoking it again:

```bash
python3 scripts/skill_rename.py /path/to/skills old-name new-name \
  --title "New Name" \
  --default-prompt 'Use $new-name to handle this task.'
python3 scripts/skill_rename.py /path/to/skills old-name new-name \
  --title "New Name" \
  --default-prompt 'Use $new-name to handle this task.' \
  --apply
```

After choosing a modern source glyph, use `scripts/skill_icon.py` to create one matching SVG/PNG pair, register both paths in `agents/aria.yaml`, and record the approved source inside the SVG:

```bash
python3 scripts/skill_icon.py /path/to/skills skill-name source-glyph.svg
```

After the source directories are normalized, use `scripts/skill_manifest.ts` to compile a fresh collection manifest with Aria's authoritative schemas, source adapters, generation builder, YAML serializer, and hash functions. Run the dry compilation first, then apply only after its inventory matches the intended physical suite:

```bash
bun scripts/skill_manifest.ts \
  --skills-root /path/to/skills \
  --aria-source /path/to/aria
bun scripts/skill_manifest.ts \
  --skills-root /path/to/skills \
  --aria-source /path/to/aria \
  --revision 1 \
  --apply
```

The compiler treats immediate child directories containing `SKILL.md` as the complete flat suite, so removed directories and virtual manifest-only records are omitted automatically. It verifies directory/frontmatter identity, rejects child-package families, materializes every immutable generation, and writes the manifest atomically.

Collection categories do not belong in `SKILL.md`, `agents/aria.yaml`, directory paths, or `manifest.yaml`. Define human-facing domains and their categories in the scoped `.aria/settings/skills.yaml`, then assign each registered skill by stable skill ID. Keep category IDs and labels to one word and treat them as concise grouping tags beneath the more descriptive domain. Establish the complete category vocabulary from the holistic inventory before writing assignments, and validate the settings with Aria's `SkillSettingsSchema` and effective-settings resolver.

## Description Rules

- Keep YAML frontmatter to exactly `name` and `description`.
- Make `name` exactly match the lowercase, hyphenated skill directory name.
- Write `description` as one clear, complete sentence about when the skill should be used.
- Begin with `Use when` unless the user establishes a different trigger-sentence convention.
- Describe triggering contexts, not the workflow, implementation method, feature inventory, or instructions for using the skill.
- Move information lost through simplification into the opening Overview without narrowing the skill's intended trigger coverage.

## Short Description Rules

- Treat `interface.shortDescription` cleanup as a separate UI-summary normalization phase after trigger-description work.
- Write a compact capability phrase, not a trigger sentence or workflow instruction.
- Prefer roughly ten words while staying within Aria's 25–64 character limit.
- Begin with a strong verb, name the concrete artifact or task, and retain only the distinguishing constraint.
- Avoid filler, marketing language, implementation detail, and redundant repetition of the display name.
- Inventory the complete collection for cohesion, then read, edit, and validate each skill serially.
- Preserve displaced scope in `## Overview` or a routed reference.

## Naming Rules

- Use exactly two words for the skill name and display title, treating word count as a structural constraint rather than a quality judgment.
- Never retain a name merely because it already contains two words; confirm that it is the clearest, most accurate, and least ambiguous title for the skill's actual trigger and scope.
- Choose names against the complete collection taxonomy rather than judging a directory in isolation.
- Optimize for suite-level cohesion through parallel grammar, stable provider namespaces, and consistent functional vocabulary, while avoiding forced uniformity that obscures meaningful distinctions.
- When a product or provider namespace must remain, use it as the first word and compress the skill's distinct job into one precise second word.
- Keep the filesystem and frontmatter name lowercase and hyphenated, even when the display title uses spaces and title case.
- Name the standard icon pair exactly after the skill: `assets/<skill-name>.svg` and `assets/<skill-name>.png`.
- Keep every metadata path synchronized with the actual case-sensitive filename.
- Use the Notion family case study in `references/aria-taxonomy.md` when a shared namespace makes two-word naming difficult.

## Structure and Assets

Use `references/aria-taxonomy.md` as the detailed source of truth for the canonical tree, `agents/aria.yaml`, bundled-resource routing, legacy cleanup, and icon specifications.

For the current icon baseline:

- Register the SVG as `iconSmall` and the PNG as `iconLarge`.
- Make the SVG and PNG visually identical, with a relevant white glyph on a black circular field unless a deliberate brand treatment or user instruction overrides that default.
- Use a 100×100 SVG canvas and a 100×100, 8-bit RGBA PNG.
- Prefer a relevant glyph from the shared `<skills-root>/_assets/svg/` library.
- Never select, copy, convert, trace, or adapt a source icon whose filename contains `legacy`, case-insensitively; those glyphs predate the modernized stroke and detail system.
- When no suitable non-legacy glyph exists, use the shared fallback icon rather than a legacy candidate.
- Record the exact approved source as `Approved glyph: _assets/svg/<source>.svg` inside the normalized SVG so provenance can be audited.

## Legacy Migration

- Treat Claude-specific instructions as content to evaluate, not content to delete automatically.
- Move reusable domain guidance into `SKILL.md` or `references/` before removing `CLAUDE.md`, `.claude/`, Claude-only settings, or obsolete evaluation scaffolding.
- Remove `.DS_Store`, placeholder files, generated litter, and extraneous documents such as `README.md` when they do not serve the agent at runtime.
- Do not remove legitimate scripts, references, examples, or evaluations merely because they are not part of the minimum tree.

## Validation

Run both layers when available:

```bash
python3 scripts/skill_audit.py /absolute/path/to/skill
python3 /path/to/skill-creator/scripts/skill_validate.py /absolute/path/to/skill
```

After a collection-wide normalization, dry-run and apply `scripts/skill_manifest.ts`, then confirm its reported skill count and names exactly match the physical suite.

Also confirm that `.aria/settings/skills.yaml` parses successfully, every registered skill has exactly one valid domain/category assignment when complete categorization is intended, and no assignment references a missing skill, domain, or category.

The audit encodes only the mechanically testable conventions established so far. It can verify that a name has two words, but it cannot determine whether those are the best two words. Complete the semantic naming review separately, treat warnings as review prompts, inspect icon fidelity visually, and update the audit when the taxonomy becomes more nuanced.
