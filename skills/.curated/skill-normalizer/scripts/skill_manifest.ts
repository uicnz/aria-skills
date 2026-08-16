#!/usr/bin/env bun

import { closeSync, existsSync, fsyncSync, mkdirSync, openSync, readdirSync, renameSync, rmSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

type AuthorityKind = 'home' | 'project';

interface Options {
	apply: boolean;
	ariaSource: string;
	authorityId: string;
	authorityKind: AuthorityKind;
	generationsRoot: string;
	outputPath: string;
	revision: number;
	skillsRoot: string;
}

function argument(name: string): string | null {
	const index = process.argv.indexOf(`--${name}`);
	const value = index >= 0 ? process.argv[index + 1] : undefined;
	return value && !value.startsWith('--') ? value : null;
}

function flag(name: string): boolean {
	return process.argv.includes(`--${name}`);
}

function parseOptions(): Options {
	const skillsRoot = path.resolve(argument('skills-root') ?? path.join(import.meta.dir, '..', '..'));
	const managedTier = /^\.(system|curated|experimental)$/u.exec(path.basename(skillsRoot))?.[1] ?? null;
	const ariaSourceValue = argument('aria-source') ?? process.env.ARIA_SOURCE_ROOT;
	if (!ariaSourceValue) throw new Error('Pass --aria-source or set ARIA_SOURCE_ROOT.');
	const ariaSource = path.resolve(ariaSourceValue);
	const authorityKindValue = argument('authority-kind') ?? 'home';
	if (authorityKindValue !== 'home' && authorityKindValue !== 'project') {
		throw new Error('--authority-kind must be home or project.');
	}
	const revisionValue = argument('revision') ?? '1';
	const revision = Number(revisionValue);
	if (!Number.isSafeInteger(revision) || revision < 0) {
		throw new Error('--revision must be a nonnegative integer.');
	}
	return {
		apply: flag('apply'),
		ariaSource,
		authorityId:
			argument('authority-id') ??
			(authorityKindValue === 'home' ? (managedTier ? `aria-${managedTier}` : 'home') : path.basename(skillsRoot)),
		authorityKind: authorityKindValue,
		generationsRoot: path.resolve(
			argument('generations-root') ??
				path.join(managedTier ? path.dirname(path.dirname(skillsRoot)) : path.dirname(skillsRoot), 'state', 'skills', 'generations')
		),
		outputPath: path.resolve(argument('output') ?? path.join(skillsRoot, 'manifest.yaml')),
		revision,
		skillsRoot,
	};
}

function skillDirectories(skillsRoot: string): string[] {
	return readdirSync(skillsRoot, { withFileTypes: true })
		.filter(entry => entry.isDirectory() && existsSync(path.join(skillsRoot, entry.name, 'SKILL.md')))
		.map(entry => entry.name)
		.sort((left, right) => left.localeCompare(right));
}

function writeAtomically(outputPath: string, content: string): void {
	const directory = path.dirname(outputPath);
	mkdirSync(directory, { recursive: true });
	const temporaryPath = path.join(directory, `.manifest.${process.pid}.${crypto.randomUUID()}.tmp`);
	let descriptor: number | null = null;
	try {
		descriptor = openSync(temporaryPath, 'wx', 0o600);
		writeFileSync(descriptor, content, 'utf8');
		fsyncSync(descriptor);
		closeSync(descriptor);
		descriptor = null;
		renameSync(temporaryPath, outputPath);
	} finally {
		if (descriptor !== null) closeSync(descriptor);
		rmSync(temporaryPath, { force: true });
	}
}

const options = parseOptions();
const modulePath = (relativePath: string): string =>
	pathToFileURL(path.join(options.ariaSource, relativePath)).href;
const manifestModule = await import(modulePath('agent/src/primitives/skills/manifest.ts'));
const sourceModule = await import(modulePath('agent/src/primitives/skills/source-adapter.ts'));
const generationModule = await import(modulePath('agent/src/primitives/skills/generation-store.ts'));
const requireFromAria = createRequire(path.join(options.ariaSource, 'package.json'));
const { stringify: stringifyYaml } = requireFromAria('yaml') as {
	stringify(value: unknown, options?: { lineWidth?: number }): string;
};

const skillIds = skillDirectories(options.skillsRoot);
if (skillIds.length === 0) throw new Error(`No immediate child skills found in ${options.skillsRoot}.`);

const records: Record<string, unknown> = {};
const generations: Array<{ skillId: string; plan: unknown }> = [];
for (const skillId of skillIds) {
	const sourceRoot = path.join(options.skillsRoot, skillId);
	const inspected = sourceModule.inspectSkillSourcePackage(sourceRoot);
	if (inspected.sourceIdentity !== skillId) {
		throw new Error(
			`Directory and frontmatter names differ: ${skillId} != ${inspected.sourceIdentity}.`
		);
	}
	if (inspected.childPackages.length > 0) {
		throw new Error(`Flat manifest compilation does not accept child packages: ${skillId}.`);
	}
	const record = {
		sourcePath: skillId,
		currentGeneration: `sha256:${'0'.repeat(64)}`,
		version: inspected.version,
		interface: inspected.interface,
		invocation: inspected.invocation,
		instructions: { load: inspected.instructionPaths },
		dependencies: inspected.dependencies,
		policy: inspected.policy,
		relationships: inspected.relationships,
		source: {
			adapterId: inspected.adapterId,
			sourceIdentity: inspected.sourceIdentity,
			sourceDigest: inspected.sourceDigest,
			sourceRepository: null,
			sourceRef: null,
			provenance: {
				normalizationDigest: inspected.normalizationEvidence.normalizationDigest,
				evidencePaths: inspected.normalizationEvidence.evidencePaths,
				acquisition: { kind: 'release' },
			},
		},
		distribution: null,
		verificationState: options.authorityKind === 'home' ? 'userInstalled' : 'projectAuthored',
		derivedFrom: null,
	};
	const generation = generationModule.inspectSkillGeneration({ skillId, record, sourceRoot });
	record.currentGeneration = generation.generationDigest;
	records[skillId] = manifestModule.SkillManifestRecordSchema.parse(record);
	generations.push({ skillId, plan: generation });
}

const manifest = manifestModule.SkillManifestSchema.parse({
	schema: manifestModule.SKILL_MANIFEST_SCHEMA_ID,
	revision: options.revision,
	contentHash: `sha256:${'0'.repeat(64)}`,
	authority: { kind: options.authorityKind, id: options.authorityId },
	skills: records,
});
manifest.contentHash = manifestModule.computeSkillManifestContentHash(manifest);
const validated = manifestModule.parseSkillManifest(manifest);
if (!validated) throw new Error('Compiled manifest failed schema or content-hash validation.');
const yaml = stringifyYaml(validated, { lineWidth: 0 });

if (options.apply) {
	for (const generation of generations) {
		generationModule.materializeSkillGeneration(options.generationsRoot, generation.plan);
	}
	writeAtomically(options.outputPath, yaml);
}

process.stdout.write(
	`${JSON.stringify(
		{
			mode: options.apply ? 'applied' : 'dry-run',
			authority: validated.authority,
			contentHash: validated.contentHash,
			generationsRoot: options.generationsRoot,
			outputPath: options.outputPath,
			revision: validated.revision,
			skillCount: skillIds.length,
			skills: skillIds,
		},
		null,
		2
	)}\n`
);
