# Agent Skills

Agent Skills are folders of instructions, scripts, and resources that AI agents can discover and use to perform at specific tasks. Write once, use everywhere.

Aria uses skills to package capabilities that teams and individuals can use to complete specific tasks in a repeatable way. This repository is Aria's official remote source catalog. Aria ships no skill packages in its application or binary.

Learn more:

- [Agent Skills open standard](https://agentskills.io)

## Catalog status

The three source tiers are authority-qualified catalog classifications:

- [`.system`](skills/.system/) contains Aria-managed system-tier release units.
- [`.curated`](skills/.curated/) contains Aria-curated release units.
- [`.experimental`](skills/.experimental/) contains opt-in release units whose contracts may still evolve.

Every immediate child of a tier is one atomic downloadable release unit. Aria derives its identity from the entrypoint skill metadata and includes only child skills explicitly declared by that entrypoint. Capability domains, categories, assignments, and search tags are curated in `catalog-source.yaml`; directory names do not define them.

Published GitHub releases contain one tracked-source archive per release unit plus a signed `catalog.json`. Aria verifies catalog authority, delegated signatures, receipts, archive digests, and complete package inventories before installation. The GitHub URL is transport, not trust.
