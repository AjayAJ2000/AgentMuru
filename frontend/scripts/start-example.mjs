import { spawn } from "node:child_process";
import { delimiter, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";


const [examplePath, port] = process.argv.slice(2);
if (!examplePath || !port) {
  console.error("usage: node scripts/start-example.mjs <example.py> <port>");
  process.exit(2);
}

const python = process.platform === "win32" ? "python" : "python3";
const repositoryRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const pythonPath = [repositoryRoot, process.env.PYTHONPATH].filter(Boolean).join(delimiter);
const child = spawn(python, [resolve(examplePath)], {
  cwd: repositoryRoot,
  env: {
    ...process.env,
    DATABRICKS_APP_PORT: port,
    PYTHONPATH: pythonPath,
    PYTHONUNBUFFERED: "1",
  },
  stdio: "inherit",
});

child.once("error", (error) => {
  console.error(error.message);
  process.exitCode = 1;
});
child.once("exit", (code, signal) => {
  process.exitCode = code ?? (signal ? 1 : 0);
});

for (const signal of ["SIGINT", "SIGTERM"]) {
  process.once(signal, () => child.kill(signal));
}
