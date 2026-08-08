import { defineConfig } from "@playwright/test";


export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  expect: { timeout: 5_000 },
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    browserName: "chromium",
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  webServer: {
    command: "cd .. && python -m agentmuru.cli.main run examples.hello_agent:application --host 127.0.0.1 --port 8065",
    url: "http://127.0.0.1:8065/api/v1/app",
    timeout: 30_000,
    reuseExistingServer: !process.env.CI,
  },
});
