import { readdir, stat } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, join, resolve } from "node:path";


export const DEFAULT_BUDGETS = Object.freeze({
  index: 850_000,
  charts: 1_100_000,
  "plotly.min": 7_500_000,
  vendor: 250_000,
});


export async function checkBundleBudgets(directory, budgets = DEFAULT_BUDGETS) {
  const files = await readdir(directory);
  const sizes = {};
  const failures = [];

  for (const [chunk, budget] of Object.entries(budgets)) {
    const prefix = `${chunk}-`;
    const candidates = files.filter(
      (file) => file.startsWith(prefix) && file.endsWith(".js"),
    );
    if (candidates.length === 0) {
      failures.push(`${chunk} chunk is missing from ${directory}`);
      continue;
    }

    const candidateSizes = await Promise.all(
      candidates.map(async (file) => (await stat(join(directory, file))).size),
    );
    const size = Math.max(...candidateSizes);
    sizes[chunk] = size;
    if (size > budget) {
      failures.push(`${chunk} chunk is ${size} bytes; budget is ${budget} bytes`);
    }
  }

  return { failures, sizes };
}


async function main() {
  const scriptDirectory = dirname(fileURLToPath(import.meta.url));
  const directory = resolve(
    process.argv[2] ?? join(scriptDirectory, "..", "..", "brickflowui", "frontend", "dist", "assets"),
  );
  const result = await checkBundleBudgets(directory);
  console.log(JSON.stringify({ directory, ...result }, null, 2));
  return result.failures.length === 0 ? 0 : 1;
}


if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  process.exitCode = await main();
}
