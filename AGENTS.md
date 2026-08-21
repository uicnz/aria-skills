# Aria Skill Source

This repository is the remotely published Source for Aria Skills. It is not copied into the Aria application or binary.

## Source taxonomy

```text
skills/
├── .system/        # authority-qualified system tier
├── .curated/       # authority-qualified curated tier
└── .experimental/  # authority-qualified experimental tier
```

Every immediate child of a tier is one atomic release unit. Its canonical identity comes from the inspected entrypoint `SKILL.md`, never from its directory name. An Aria sidecar may declare child skills; the entrypoint and its declared children are archived, signed, installed, updated, rolled back, and removed together.

The reserved `_assets/` child is the sole non-Skill exception. It contains tracked tier-level shared authoring assets, must contain only regular files and directories, and is never counted as a Skill identity or release unit. A tier-level `manifest.yaml` is the hashed registry for the materialized source collection.

Do not add package-name branches to Source tooling. Tier roots are enumerated generically, and ignored or untracked files must never enter release archives.

## Publication

`source.yaml` contains public Source and authority metadata plus the curated domain, category, assignment, and search-tag projection. This is human-authored Source policy, not identity inferred from paths or package-name logic in Aria. Every tracked Skill identity must have exactly one assignment and every assignment must reference a declared domain/category. Private signing keys remain outside this repository. Aria's Source release builder creates one archive per release unit and a signed `source.json` checkpoint for a GitHub release.

GitHub release retention is rolling: after a newly published release is verified as the latest checkpoint, remove every superseded GitHub release and its tag. Runtime rollback is owned by locally retained immutable generations and lifecycle receipts, not by an online release archive.

The Source URL is a replaceable Aria default. Repository location does not establish trust; Aria verifies the configured authority and embedded root key before accepting delegated index, receipt, or archive evidence.
