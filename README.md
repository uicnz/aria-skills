# Agent Skills

Agent Skills are folders of instructions, scripts, and resources that AI agents can discover and use to perform at specific tasks. Write once, use everywhere.

Aria uses skills to help package capabilities that teams and individuals can use to complete specific tasks in a repeatable way. This repository catalogs skills for use and distribution with Aria.

Learn more:

- [Agent Skills open standard](https://agentskills.io)

## Catalog status

This repository is being normalized to Aria's canonical skill shape.

- [`.system`](skills/.system/) is reserved for future Aria-managed system skills. Those skills will return after the runtime primitive and install surface are implemented in-product.
- [`.curated`](skills/.curated/) contains managed skills that Aria intends to ship and maintain.
- [`.experimental`](skills/.experimental/) contains managed skills that are intentionally less stable while the primitive is still evolving.

For now, treat this repository as the source catalog and working corpus for Aria-managed skills. Managed install and update flows are intentionally deferred while the primitive is implemented.
