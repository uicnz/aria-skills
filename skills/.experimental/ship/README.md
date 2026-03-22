# ship

## Quick start: your first 10 minutes

1. Install ship (30 seconds — see below)
2. Run `/plan-review-founder` on any feature idea
3. Run `/review` on any branch with changes
4. Run `/qa` on your staging URL
5. Stop there. You'll know if this is for you.

Expect first useful run in under 5 minutes on any repo with tests already set up.

**If you only read one more section, read this one.**

## Install — takes 30 seconds

**Requirements:** [Aria](https://github.com/uicnz/aria), [Git](https://git-scm.com/), [Bun](https://bun.sh/) v1.0+

### Step 1: Install on your machine

Open Aria and paste this. Aria does the rest.

````markdown
Install ship:

1. Run **`git clone https://github.com/shaneholloman/ship.git ~/.aria/skills/ship && cd ~/.aria/skills/ship && ./setup`**

2. Add a `ship` section to `ARIA.md` that tells Aria to:
    - use the `/browse` skill from ship for all web browsing
    - never use `mcp__aria-in-chrome__*` tools
    - list these available skills:
        - `/plan-review-founder`
        - `/plan-review-eng`
        - `/plan-review-design`
        - `/design-consultation`
        - `/review`
        - `/ship`
        - `/browse`
        - `/qa`
        - `/qa-only`
        - `/qa-design-review`
        - `/setup-browser-cookies`
        - `/retro`
        - `/document-release`

3. Ask the user if they also want to add ship to the current project so teammates get it.

````

### Step 2: Add to your repo so teammates get it (optional)

````markdown
Add ship to this project:

1. Run **`cp -Rf ~/.aria/skills/ship .aria/skills/ship && rm -rf .aria/skills/ship/.git && cd .aria/skills/ship && ./setup`**

2. Add a `ship` section to this project's `ARIA.md` that tells Aria to:
    - use the `/browse` skill from ship for all web browsing
    - never use `mcp__aria-in-chrome__*` tools
    - list these available skills:
        - `/plan-review-founder`
        - `/plan-review-eng`
        - `/plan-review-design`
        - `/design-consultation`
        - `/review`
        - `/ship`
        - `/browse`
        - `/qa`
        - `/qa-only`
        - `/qa-design-review`
        - `/setup-browser-cookies`
        - `/retro`
        - `/document-release`
    - if ship skills are not working, run `cd .aria/skills/ship && ./setup` to build the binary and register skills

````

Real files get committed to your repo (not a submodule), so `git clone` just works. Everything lives inside `.aria/`. Nothing touches your PATH or runs in the background.

## See it work

```txt
You:    I want to add photo upload for sellers.
You:    `/plan-review-founder`
Aria:   "Photo upload" is not the feature. The real job is helping
        sellers create listings that actually sell. What if we
        auto-identify the product, pull specs and comps from the
        web, and draft the listing automatically? That's 10 stars.
        "Upload a photo" is 3 stars. Which are we building?
        [8 expansion proposals, you cherry-pick 5, defer 3 to backlog]

You:    `/plan-review-design`
Aria:   Design Score: B  |  AI Slop Score: C
        "Upload flow looks like a default Bootstrap form."
        [80-item audit, infers your design system, exports DESIGN.md]
        [flags 3 AI slop patterns: gradient hero, icon grid, uniform radius]

You:    `/plan-review-eng`
Aria:   ┌─────────┐    ┌──────────┐    ┌──────────┐    ┌─────────┐
        │ Upload  │───▶│ Classify │───▶│ Enrich   │───▶│ Draft   │
        │ (sync)  │    │ (async)  │    │ (async)  │    │ (async) │
        └─────────┘    └──────────┘    └──────────┘    └─────────┘
        [ASCII diagrams for every data flow, state machine, error path]
        [14-case test matrix, 6 failure modes mapped, 3 security concerns]

You:    Approve plan. Exit plan mode.
        [Aria writes 2,400 lines across 11 files — models, services,
        controllers, views, migrations, and tests. ~8 minutes.]

You:    `/review`
Aria:   [AUTO-FIXED] Orphan S3 cleanup on failed upload
        [AUTO-FIXED] Missing index on listings.status
        [ASK] Race condition on hero image selection → You: yes
        [traces every new enum value through all switch statements]
        3 issues — 2 auto-fixed, 1 fixed.

You:    `/qa https://staging.myapp.com`
Aria:   [opens real browser, logs in, uploads photos, clicks through flows]
        Upload → classify → enrich → draft: end to end ✓
        Mobile: ✓  |  Slow connection: ✓  |  Bad image: ✓
        [finds bug: preview doesn't clear on second upload — fixes it]
        Regression test generated.

You:    `/ship`
Aria:   Tests: 42 → 51 (+9 new)
        Coverage: 14/14 code paths (100%)
        PR: github.com/you/app/pull/42
```

One feature. Seven commands. The agent reframed the product, ran an 80-item design audit, drew the architecture, wrote 2,400 lines of code, found a race condition I would have missed, auto-fixed two issues, opened a real browser to QA test, found and fixed a bug I didn't know about, wrote 9 tests, and generated a regression test. That is not a copilot. That is a team.

## The team

| Skill                    | Your specialist        | What they do                                                                                                                                                             |
| ------------------------ | ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `/plan-review-founder`   | **Founder**.           | Rethink the problem. Find the 10-star product hiding inside the request. Four modes: Expansion, Selective Expansion, Hold Scope, Reduction.                              |
| `/plan-review-eng`       | **Eng Manager**        | Lock in architecture, data flow, diagrams, edge cases, and tests. Forces hidden assumptions into the open.                                                               |
| `/plan-review-design`    | **Senior Designer**    | 80-item design audit with letter grades. AI Slop detection. Infers your design system. Report only — never touches code.                                                 |
| `/design-consultation`   | **Design Partner**     | Build a complete design system from scratch. Knows the landscape, proposes creative risks, generates realistic product mockups. Design at the heart of all other phases. |
| `/review`                | **Staff Engineer**     | Find the bugs that pass CI but blow up in production. Auto-fixes the obvious ones. Flags completeness gaps.                                                              |
| `/ship`                  | **Release Engineer**   | Sync main, run tests, audit coverage, push, open PR. Bootstraps test frameworks if you don't have one. One command.                                                      |
| `/browse`                | **QA Engineer**        | Give the agent eyes. Real Chromium browser, real clicks, real screenshots. ~100ms per command.                                                                           |
| `/qa`                    | **QA Lead**            | Test your app, find bugs, fix them with atomic commits, re-verify. Auto-generates regression tests for every fix.                                                        |
| `/qa-only`               | **QA Reporter**        | Same methodology as /qa but report only. Use when you want a pure bug report without code changes.                                                                       |
| `/design-review`         | **Designer Who Codes** | Same audit as /plan-review-design, then fixes what it finds. Atomic commits, before/after screenshots.                                                                   |
| `/setup-browser-cookies` | **Session Manager**    | Import cookies from your real browser (Chrome, Arc, Brave, Edge) into the headless session. Test authenticated pages.                                                    |
| `/retro`                 | **Eng Manager**        | Team-aware weekly retro. Per-person breakdowns, shipping streaks, test health trends, growth opportunities.                                                              |
| `/document-release`      | **Technical Writer**   | Update all project docs to match what you just shipped. Catches stale READMEs automatically.                                                                             |

**[Deep dives with examples and philosophy for every skill →](docs/skills.md)**

## What's new and why it matters

**Design is at the heart.** `/design-consultation` doesn't just pick fonts. It researches what's out there in your space, proposes safe choices AND creative risks, generates realistic mockups of your actual product, and writes `DESIGN.md` — and then `/design-review` and `/plan-review-eng` read what you chose. Design decisions flow through the whole system.

**`/qa` was a massive unlock.** It let me go from 6 to 12 parallel workers. Aria saying _"I SEE THE ISSUE"_ and then actually fixing it, generating a regression test, and verifying the fix — that changed how I work. The agent has eyes now.

**Smart review routing.** Just like at a well-run startup: CEO doesn't have to look at infra bug fixes, design review isn't needed for backend changes. ship tracks what reviews are run, figures out what's appropriate, and just does the smart thing. The Review Readiness Dashboard tells you where you stand before you ship.

**Test everything.** `/ship` bootstraps test frameworks from scratch if your project doesn't have one. Every `/ship` run produces a coverage audit. Every `/qa` bug fix generates a regression test. 100% test coverage is the goal — tests make vibe coding safe instead of yolo coding.

**`/document-release` is the engineer you never had.** It reads every doc file in your project, cross-references the diff, and updates everything that drifted. README, ARCHITECTURE, CONTRIBUTING, ARIA.md, TODOS — all kept current automatically.

## 10 sessions at once

ship is powerful with one session. It is transformative with ten.

## Docs

| Doc                                | What it covers                                                                     |
| ---------------------------------- | ---------------------------------------------------------------------------------- |
| [Skill Deep Dives](docs/skills.md) | Philosophy, examples, and workflow for every skill (includes Greptile integration) |
| [Architecture](ARCHITECTURE.md)    | Design decisions and system internals                                              |
| [Browser Reference](BROWSER.md)    | Full command reference for `/browse`                                               |
| [Contributing](CONTRIBUTING.md)    | Dev setup, testing, contributor mode, and dev mode                                 |
| [Changelog](CHANGELOG.md)          | What's new in every version                                                        |

## Troubleshooting

**Skill not showing up?** `cd ~/.aria/skills/ship && ./setup`

**`/browse` fails?** `cd ~/.aria/skills/ship && bun install && bun run build`

**Stale install?** Run `/ship-upgrade` — or set `auto_upgrade: true` in `~/.ship/config.yaml`

**Aria says it can't see the skills?** Make sure your project's `ARIA.md` has a ship section. Add this:

````markdown
## ship

1. Use `/browse` from ship for all web browsing. Never use `mcp__aria-in-chrome__*` tools.

2. Available skills: 
    - `/plan-review-founder`
    - `/plan-review-eng`
    - `/plan-review-design`,
    - `/design-consultation`
    - `/review`
    - `/ship`
    - `/browse`
    - `/qa`
    - `/qa-only`
    - `/qa-design-review`,
    - `/setup-browser-cookies`
    - `/retro`
    - `/document-release`.

````

## License

MIT. Free forever. Go build something.
