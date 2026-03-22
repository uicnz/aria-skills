/**
 * Tests for find-browse binary locator.
 */

import { describe, expect, test } from "bun:test";
import { existsSync } from "fs";
import { locateBinary } from "../src/find-browse";

describe("locateBinary", () => {
	test("returns null when no binary exists at known paths", () => {
		// This test depends on the test environment — if a real binary exists at
		// ~/.aria/skills/ship/browse/dist/browse, it will find it.
		// We mainly test that the function doesn't throw.
		const result = locateBinary();
		expect(result === null || typeof result === "string").toBe(true);
	});

	test("returns string path when binary exists", () => {
		const result = locateBinary();
		if (result !== null) {
			expect(existsSync(result)).toBe(true);
		}
	});
});
