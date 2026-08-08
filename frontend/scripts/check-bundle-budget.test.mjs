import assert from "node:assert/strict";
import { mkdtemp, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { checkBundleBudgets } from "./check-bundle-budget.mjs";


test("accepts hashed production chunks within their byte budgets", async () => {
  const directory = await mkdtemp(join(tmpdir(), "muru-bundles-"));
  await writeFile(join(directory, "index-abc.js"), Buffer.alloc(8));
  await writeFile(join(directory, "vendor-def.js"), Buffer.alloc(4));

  const result = await checkBundleBudgets(directory, {
    index: 10,
    vendor: 5,
  });

  assert.deepEqual(result.failures, []);
  assert.equal(result.sizes.index, 8);
  assert.equal(result.sizes.vendor, 4);
});


test("reports missing and oversized chunks", async () => {
  const directory = await mkdtemp(join(tmpdir(), "muru-bundles-"));
  await writeFile(join(directory, "index-abc.js"), Buffer.alloc(11));

  const result = await checkBundleBudgets(directory, {
    index: 10,
    charts: 20,
  });

  assert.match(result.failures.join("\n"), /index.*11.*10/i);
  assert.match(result.failures.join("\n"), /charts.*missing/i);
});
