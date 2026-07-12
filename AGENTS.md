# Aria Skills Catalog

This repository is the remotely published source catalog for Aria Skills. It is not copied into the Aria application or binary.

## Source taxonomy

```text
skills/
├── .system/        # authority-qualified system tier
├── .curated/       # authority-qualified curated tier
└── .experimental/  # authority-qualified experimental tier
```

Every immediate child of a tier is one atomic release unit. Its canonical identity comes from the inspected entrypoint `SKILL.md`, never from its directory name. An Aria sidecar may declare child skills; the entrypoint and its declared children are archived, signed, installed, updated, rolled back, and removed together.

Do not add package-name branches to catalog tooling. Tier roots are enumerated generically, and ignored or untracked files must never enter release archives.

## Publication

`catalog-source.yaml` contains public source and authority metadata. Private signing keys remain outside this repository. Aria's catalog release builder creates one archive per release unit and a signed `catalog.json` checkpoint for a GitHub release.

The catalog URL is a replaceable Aria default. Repository location does not establish trust; Aria verifies the configured authority and embedded root key before accepting delegated catalog, receipt, or archive evidence.
