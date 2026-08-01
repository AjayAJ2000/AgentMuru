import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";


function collectBrowserErrors(page: Page): string[] {
  const failures: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") failures.push(`console: ${message.text()}`);
  });
  page.on("pageerror", (error) => failures.push(`page: ${error.message}`));
  page.on("requestfailed", (request) => {
    failures.push(`request: ${request.url()} ${request.failure()?.errorText ?? "failed"}`);
  });
  return failures;
}


async function expectNoSeriousAccessibilityViolations(page: Page) {
  const results = await new AxeBuilder({ page }).analyze();
  const violations = results.violations.filter(({ impact }) =>
    impact === "serious" || impact === "critical",
  );
  expect(violations, violations.map(({ id, help }) => `${id}: ${help}`).join("\n"))
    .toEqual([]);
}


test("counter works by mouse and keyboard without browser errors", async ({ page }) => {
  const browserErrors = collectBrowserErrors(page);
  await page.goto("http://127.0.0.1:8065/");

  await expect(page.getByRole("heading", { name: "Counter" }).first()).toBeVisible();
  await page.getByRole("button", { name: "+", exact: true }).click();
  await expect(page.getByText("Count: 1", { exact: true })).toBeVisible();

  await page.keyboard.press("Tab");
  await expect(page.locator(":focus")).toBeVisible();
  await expectNoSeriousAccessibilityViolations(page);
  expect(browserErrors).toEqual([]);
});


test("counter remains usable at a mobile viewport", async ({ page }) => {
  const browserErrors = collectBrowserErrors(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("http://127.0.0.1:8065/");

  await expect(page.getByRole("button", { name: "+", exact: true })).toBeVisible();
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  expect(overflow).toBeLessThanOrEqual(1);
  expect(browserErrors).toEqual([]);
});


test("component studio supports search, dialog, tabs, charts, and accessibility", async ({ page }) => {
  const browserErrors = collectBrowserErrors(page);
  await page.goto("http://127.0.0.1:8066/");

  await expect(page.getByText("BrickflowUI Component Studio", { exact: true }).first()).toBeVisible();
  await expect(page.getByText("Component inventory", { exact: true })).toBeVisible();
  await page.getByLabel("Search components").fill("pipeline");
  await expectNoSeriousAccessibilityViolations(page);

  await page.getByRole("button", { name: "Open detail drawer" }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await expect(page.getByText("Why this example matters", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Close drawer" }).click();
  await expect(page.getByRole("dialog")).toBeHidden();

  await page.getByRole("tab", { name: "Visuals" }).click();
  await expect(page.getByText("Runs vs success rate", { exact: true })).toBeVisible();
  await expect(page.getByText("Latency trend", { exact: true })).toBeVisible();
  await expect(page.getByText("Pipeline map", { exact: true })).toBeVisible();
  await expectNoSeriousAccessibilityViolations(page);
  expect(browserErrors).toEqual([]);
});
