# Commands

```sh
bunx prettier --parser markdown --single-quote --tab-width 4 --use-tabs false --no-editorconfig --write "SKILL.md.tmpl" "**/SKILL.md.tmpl"
bunx prettier --parser markdown --single-quote --tab-width 4 --use-tabs false --no-editorconfig --write "SKILL.md" "**/SKILL.md"

markdownlint-cli2 --fix "SKILL.md.tmpl" "**/SKILL.md.tmpl"
markdownlint-cli2 --fix "SKILL.md" "**/SKILL.md"
```
