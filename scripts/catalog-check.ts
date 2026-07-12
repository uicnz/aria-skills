import { existsSync, lstatSync, readdirSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { parse as parseYaml } from 'yaml';

const tiers = ['system', 'curated', 'experimental'] as const;
const skillNamePattern = /^[a-z0-9]+(?:-[a-z0-9]+)*(?:\/[a-z0-9]+(?:-[a-z0-9]+)*)*$/;
const taxonomySegmentPattern = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

function object(value: unknown, label: string): Record<string, unknown> {
	if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error(`${label} must be an object.`);
	return value as Record<string, unknown>;
}

function validateCatalogTaxonomy(catalogPath: string, skillIds: ReadonlySet<string>): void {
	const source = object(parseYaml(readFileSync(catalogPath, 'utf8')), 'catalog-source.yaml');
	const domains = object(source.domains, 'catalog-source.yaml domains');
	const assignments = object(source.assignments, 'catalog-source.yaml assignments');
	for (const [domainId, rawDomain] of Object.entries(domains)) {
		if (!taxonomySegmentPattern.test(domainId)) throw new Error(`Invalid catalog domain ID: ${domainId}`);
		const domain = object(rawDomain, `catalog domain ${domainId}`);
		const categories = object(domain.categories, `catalog domain ${domainId} categories`);
		for (const categoryId of Object.keys(categories)) {
			if (!taxonomySegmentPattern.test(categoryId)) throw new Error(`Invalid catalog category ID: ${categoryId}`);
		}
	}
	for (const [skillId, rawAssignment] of Object.entries(assignments)) {
		if (!skillNamePattern.test(skillId)) throw new Error(`Invalid assigned Skill ID: ${skillId}`);
		const assignment = object(rawAssignment, `catalog assignment ${skillId}`);
		const domainId = assignment.domain;
		const categoryId = assignment.category;
		if (typeof domainId !== 'string' || typeof categoryId !== 'string') {
			throw new Error(`Catalog assignment must declare domain and category: ${skillId}`);
		}
		const domain = object(domains[domainId], `catalog assignment domain ${domainId}`);
		const categories = object(domain.categories, `catalog assignment domain ${domainId} categories`);
		if (!categories[categoryId]) throw new Error(`Unknown catalog category for ${skillId}: ${domainId}/${categoryId}`);
	}
	const assignmentIds = new Set(Object.keys(assignments));
	const missing = [...skillIds].filter(id => !assignmentIds.has(id)).sort();
	const unknown = [...assignmentIds].filter(id => !skillIds.has(id)).sort();
	if (missing.length > 0 || unknown.length > 0) {
		throw new Error(
			`Catalog taxonomy coverage mismatch. Missing: ${missing.join(', ') || 'none'}. Unknown: ${unknown.join(', ') || 'none'}.`
		);
	}
}

function skillName(root: string): string {
	const raw = readFileSync(path.join(root, 'SKILL.md'), 'utf8');
	const frontmatter = raw.match(/^---\s*\n([\s\S]*?)\n---(?:\s*\n|$)/);
	if (!frontmatter?.[1]) throw new Error(`SKILL.md has no YAML frontmatter: ${root}`);
	const parsed = parseYaml(frontmatter[1]) as { name?: unknown };
	if (typeof parsed.name !== 'string' || !skillNamePattern.test(parsed.name)) {
		throw new Error(`SKILL.md has an invalid name: ${root}`);
	}
	return parsed.name;
}

function childPaths(root: string): string[] {
	const sidecar = path.join(root, 'agents', 'aria.yaml');
	if (!existsSync(sidecar)) return [];
	const parsed = parseYaml(readFileSync(sidecar, 'utf8')) as {
		relationships?: { childSkills?: Array<string | { path?: unknown }> };
	};
	return (parsed.relationships?.childSkills ?? []).map(child => {
		const value = typeof child === 'string' ? child : child.path;
		if (typeof value !== 'string') throw new Error(`Invalid child skill declaration: ${sidecar}`);
		const normalized = path.posix.normalize(value.replace(/^\.\//, ''));
		if (!normalized || normalized === '..' || normalized.startsWith('../') || path.isAbsolute(normalized)) {
			throw new Error(`Child skill escapes its release unit: ${sidecar}`);
		}
		return normalized;
	});
}

function nestedSkillRoots(root: string): string[] {
	const output: string[] = [];
	const walk = (directory: string): void => {
		for (const entry of readdirSync(directory, { withFileTypes: true })) {
			if (entry.name === 'node_modules' || entry.name === '.git') continue;
			const pathname = path.join(directory, entry.name);
			if (entry.isSymbolicLink()) throw new Error(`Catalog source contains a link: ${pathname}`);
			if (!entry.isDirectory()) continue;
			if (existsSync(path.join(pathname, 'SKILL.md'))) output.push(pathname);
			walk(pathname);
		}
	};
	walk(root);
	return output;
}

const skillsRoot = path.resolve(process.argv[2] ?? 'skills');
let releaseUnits = 0;
let skills = 0;
const roots = [];
const identities = new Set<string>();
for (const tier of tiers) {
	const tierRoot = path.join(skillsRoot, `.${tier}`);
	if (!existsSync(tierRoot)) {
		roots.push({ tier, present: false, releaseUnits: 0, skills: 0 });
		continue;
	}
	const stat = lstatSync(tierRoot);
	if (!stat.isDirectory() || stat.isSymbolicLink()) throw new Error(`Tier root is not a regular directory: ${tierRoot}`);
	let tierUnits = 0;
	let tierSkills = 0;
	for (const entry of readdirSync(tierRoot, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
		if (entry.name.startsWith('.')) continue;
		const unitRoot = path.join(tierRoot, entry.name);
		if (entry.isSymbolicLink()) throw new Error(`Tier contains a link: ${unitRoot}`);
		if (!entry.isDirectory()) continue;
		if (!existsSync(path.join(unitRoot, 'SKILL.md'))) throw new Error(`Release unit has no SKILL.md: ${unitRoot}`);
		const declared = new Set<string>();
		const visit = (root: string, parentIdentity?: string): void => {
			const localName = skillName(root);
			const identity = parentIdentity ? `${parentIdentity}/${localName}` : localName;
			if (identities.has(identity)) throw new Error(`Skill identity occurs more than once: ${identity}`);
			identities.add(identity);
			declared.add(path.resolve(root));
			tierSkills += 1;
			for (const child of childPaths(root)) {
				const childRoot = path.resolve(root, ...child.split('/'));
				if (!childRoot.startsWith(`${path.resolve(root)}${path.sep}`) || !existsSync(path.join(childRoot, 'SKILL.md'))) {
					throw new Error(`Declared child skill is invalid: ${root}:${child}`);
				}
				visit(childRoot, identity);
			}
		};
		visit(unitRoot);
		const undeclared = nestedSkillRoots(unitRoot).filter(root => !declared.has(path.resolve(root)));
		if (undeclared.length > 0) throw new Error(`Release unit contains undeclared nested skills: ${undeclared.join(', ')}`);
		tierUnits += 1;
	}
	releaseUnits += tierUnits;
	skills += tierSkills;
	roots.push({ tier, present: true, releaseUnits: tierUnits, skills: tierSkills });
}
validateCatalogTaxonomy(path.join(skillsRoot, '..', 'catalog-source.yaml'), identities);
process.stdout.write(`${JSON.stringify({ roots, totals: { releaseUnits, skills } }, null, 2)}\n`);
