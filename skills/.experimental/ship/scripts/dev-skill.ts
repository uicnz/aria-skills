#!/usr/bin/env bun

/**
 * dev:skill — Watch mode for SKILL.md template development.
 *
 * Watches .tmpl files, regenerates SKILL.md files on change,
 * validates all $B commands immediately.
 */

import { execSync } from "node:child_process";
import * as fs from "node:fs";
import * as path from "node:path";
import { validateSkill } from "../test/helpers/skill-parser";

const ROOT = path.resolve(import.meta.dir, "..");

const WATCHED_TEMPLATES = [
	{ tmpl: path.join(ROOT, "SKILL.md.tmpl"), output: "SKILL.md" },
	{ tmpl: path.join(ROOT, "instructions.md.tmpl"), output: "instructions.md" },
	{
		tmpl: path.join(ROOT, "browse", "SKILL.md.tmpl"),
		output: "browse/SKILL.md",
	},
];

const VALIDATED_FILES = [
	path.join(ROOT, "instructions.md"),
	path.join(ROOT, "browse", "SKILL.md"),
];

function formatExecError(err: unknown): string {
	if (typeof err === "object" && err !== null) {
		const stderr = "stderr" in err ? err.stderr : undefined;
		if (typeof stderr === "string" && stderr.trim().length > 0) {
			return stderr.trim();
		}
		if (stderr instanceof Buffer) {
			const output = stderr.toString().trim();
			if (output.length > 0) {
				return output;
			}
		}
	}

	if (err instanceof Error) {
		return err.message;
	}

	return String(err);
}

function regenerateAndValidate() {
	// Regenerate
	try {
		execSync("bun run scripts/gen-skill-docs.ts", { cwd: ROOT, stdio: "pipe" });
	} catch (err: unknown) {
		console.log(`  [gen]   ERROR: ${formatExecError(err)}`);
		return;
	}

	// Validate each generated file
	for (const fullPath of VALIDATED_FILES) {
		if (!fs.existsSync(fullPath)) continue;
		const output = path.relative(ROOT, fullPath);

		const result = validateSkill(fullPath);
		const totalValid = result.valid.length;
		const totalInvalid = result.invalid.length;
		const totalSnapErrors = result.snapshotFlagErrors.length;

		if (totalInvalid > 0 || totalSnapErrors > 0) {
			console.log(`  [check] \u274c ${output} (${totalValid} valid)`);
			for (const inv of result.invalid) {
				console.log(
					`          Unknown command: '${inv.command}' at line ${inv.line}`,
				);
			}
			for (const se of result.snapshotFlagErrors) {
				console.log(`          ${se.error} at line ${se.command.line}`);
			}
		} else {
			console.log(
				`  [check] \u2705 ${output} — ${totalValid} commands, all valid`,
			);
		}
	}
}

// Initial run
console.log("  [watch] Watching *.md.tmpl files...");
regenerateAndValidate();

// Watch for changes
for (const { tmpl } of WATCHED_TEMPLATES) {
	if (!fs.existsSync(tmpl)) continue;
	fs.watch(tmpl, () => {
		console.log(`\n  [watch] ${path.relative(ROOT, tmpl)} changed`);
		regenerateAndValidate();
	});
}

// Also watch commands.ts and snapshot.ts (source of truth changes)
const SOURCE_FILES = [
	path.join(ROOT, "browse", "src", "commands.ts"),
	path.join(ROOT, "browse", "src", "snapshot.ts"),
];

for (const src of SOURCE_FILES) {
	if (!fs.existsSync(src)) continue;
	fs.watch(src, () => {
		console.log(`\n  [watch] ${path.relative(ROOT, src)} changed`);
		regenerateAndValidate();
	});
}

// Keep alive
console.log("  [watch] Press Ctrl+C to stop\n");
