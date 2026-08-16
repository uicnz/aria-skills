# Aria Skills

Aria Skills are folders of instructions, scripts, and resources that AI agents can discover and use to perform at specific tasks. Write once, use everywhere.

Aria uses skills to package capabilities that teams and individuals can use to complete specific tasks in a repeatable way. This repository is Aria's official remote source catalog. Aria ships no skill packages in its application or binary.

Learn more:

- [Agent Skills open standard](https://agentskills.io)

## Catalog status

The three source tiers are authority-qualified catalog classifications:

- [`.system`](skills/.system/) contains Aria-managed system-tier release units.
- [`.curated`](skills/.curated/) contains Aria-curated release units.
- [`.experimental`](skills/.experimental/) contains opt-in release units whose contracts may still evolve.

Every immediate child of a tier is one atomic downloadable release unit, except the reserved `_assets/` directory of tracked shared authoring assets. Aria derives Skill identity from entrypoint metadata and includes only child skills explicitly declared by that entrypoint. Each populated tier carries its own hashed `manifest.yaml`. Capability domains, categories, assignments, and search tags are curated in `catalog-source.yaml`; directory names do not define them.

The latest GitHub release contains one tracked-source archive per release unit plus a signed `catalog.json`; superseded releases and tags are removed. Aria verifies catalog authority, delegated signatures, receipts, archive digests, and complete package inventories before installation. Runtime rollback uses locally retained immutable generations, and the GitHub URL is transport, not trust.
