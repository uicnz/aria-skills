#!/usr/bin/env bun

/**
 * skill:check — Health summary for all SKILL.md files.
 *
 * Reports:
 *   - Command validation (valid/invalid/snapshot errors)
 *   - Template coverage (which SKILL.md files have .tmpl sources)
 *   - Freshness check (generated files match committed files)
 */

import { execSync } from "node:child_process";
import * as fs from "node:fs";
import * as path from "node:path";
import { validateSkill } from "../test/helpers/skill-parser";

const ROOT = path.resolve(import.meta.dir, "..");

function getExecStdout(err: unknown): string {
	if (typeof err === "object" && err !== null && "stdout" in err) {
		const stdout = err.stdout;
		if (typeof stdout === "string") {
			return stdout;
		}
		if (stdout instanceof Buffer) {
			return stdout.toString();
		}
	}

	return "";
}

// Find all instruction files that may contain operational command content
const VALIDATION_FILES = [
	"instructions.md",
	"browse/SKILL.md",
	"qa/SKILL.md",
	"qa-only/SKILL.md",
	"review/SKILL.md",
	"retro/SKILL.md",
	"plan-review-founder/SKILL.md",
	"plan-review-eng/SKILL.md",
	"setup-browser-cookies/SKILL.md",
	"plan-review-design/SKILL.md",
	"design-review/SKILL.md",
	"ship-upgrade/SKILL.md",
	"document-release/SKILL.md",
].filter((f) => fs.existsSync(path.join(ROOT, f)));

let hasErrors = false;

// ─── Skills ─────────────────────────────────────────────────

console.log("  Instructions:");
for (const file of VALIDATION_FILES) {
	const fullPath = path.join(ROOT, file);
	const result = validateSkill(fullPath);

	if (result.warnings.length > 0) {
		console.log(
			`  \u26a0\ufe0f  ${file.padEnd(30)} — ${result.warnings.join(", ")}`,
		);
		continue;
	}

	const totalValid = result.valid.length;
	const totalInvalid = result.invalid.length;
	const totalSnapErrors = result.snapshotFlagErrors.length;

	if (totalInvalid > 0 || totalSnapErrors > 0) {
		hasErrors = true;
		console.log(
			`  \u274c ${file.padEnd(30)} — ${totalValid} valid, ${totalInvalid} invalid, ${totalSnapErrors} snapshot errors`,
		);
		for (const inv of result.invalid) {
			console.log(`      line ${inv.line}: unknown command '${inv.command}'`);
		}
		for (const se of result.snapshotFlagErrors) {
			console.log(`      line ${se.command.line}: ${se.error}`);
		}
	} else {
		console.log(
			`  \u2705 ${file.padEnd(30)} — ${totalValid} commands, all valid`,
		);
	}
}

// ─── Templates ──────────────────────────────────────────────

console.log("\n  Templates:");
const TEMPLATES = [
	{ tmpl: "SKILL.md.tmpl", output: "SKILL.md" },
	{ tmpl: "instructions.md.tmpl", output: "instructions.md" },
	{ tmpl: "browse/SKILL.md.tmpl", output: "browse/SKILL.md" },
];

for (const { tmpl, output } of TEMPLATES) {
	const tmplPath = path.join(ROOT, tmpl);
	const outPath = path.join(ROOT, output);
	if (!fs.existsSync(tmplPath)) {
		console.log(`  \u26a0\ufe0f  ${output.padEnd(30)} — no template`);
		continue;
	}
	if (!fs.existsSync(outPath)) {
		hasErrors = true;
		console.log(
			`  \u274c ${output.padEnd(30)} — generated file missing! Run: bun run gen:skill-docs`,
		);
		continue;
	}
	console.log(`  \u2705 ${tmpl.padEnd(30)} \u2192 ${output}`);
}

// Skills without templates
for (const file of VALIDATION_FILES) {
	const tmplPath = path.join(ROOT, `${file}.tmpl`);
	if (!fs.existsSync(tmplPath) && !TEMPLATES.some((t) => t.output === file)) {
		console.log(
			`  \u26a0\ufe0f  ${file.padEnd(30)} — no template (OK if no $B commands)`,
		);
	}
}

// ─── Freshness ──────────────────────────────────────────────

console.log("\n  Freshness:");
try {
	execSync("bun run scripts/gen-skill-docs.ts --dry-run", {
		cwd: ROOT,
		stdio: "pipe",
	});
	console.log("  \u2705 All generated files are fresh");
} catch (err: unknown) {
	hasErrors = true;
	const output = getExecStdout(err);
	console.log("  \u274c Generated files are stale:");
	for (const line of output
		.split("\n")
		.filter((l: string) => l.startsWith("STALE"))) {
		console.log(`      ${line}`);
	}
	console.log("      Run: bun run gen:skill-docs");
}

console.log("");
process.exit(hasErrors ? 1 : 0);
