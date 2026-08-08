import AxeBuilder from '@axe-core/playwright'
import { expect, test, type Page } from '@playwright/test'


function collectBrowserErrors(page: Page): string[] {
  const failures: string[] = []
  page.on('console', (message) => {
    if (message.type() === 'error') failures.push(`console: ${message.text()}`)
  })
  page.on('pageerror', (error) => failures.push(`page: ${error.message}`))
  page.on('requestfailed', (request) => {
    failures.push(`request: ${request.url()} ${request.failure()?.errorText ?? 'failed'}`)
  })
  return failures
}


test('Muru Workspace runs a replayable agent session', async ({ page }) => {
  const browserErrors = collectBrowserErrors(page)
  await page.goto('http://127.0.0.1:8065/')

  await expect(page.getByText('Muru Workspace', { exact: true })).toBeVisible()
  await page.getByRole('button', { name: 'New session' }).first().click()
  await expect(page.getByText('Runtime connected', { exact: true })).toBeVisible()

  await page.getByLabel('Give the agent an objective').fill('Say hello from the runtime')
  await page.getByRole('button', { name: 'Run', exact: true }).click()
  await expect(page.getByText('Hello. AgentMuru is running locally.', { exact: true })).toBeVisible()

  await page.getByRole('tab', { name: 'Trace' }).click()
  await expect(page.getByRole('listitem').getByText('model', { exact: true })).toBeVisible()

  const accessibility = await new AxeBuilder({ page }).analyze()
  const serious = accessibility.violations.filter(({ impact }) =>
    impact === 'serious' || impact === 'critical',
  )
  expect(serious, serious.map(({ id, help }) => `${id}: ${help}`).join('\n')).toEqual([])
  expect(browserErrors).toEqual([])
})


test('Muru Workspace remains usable on a mobile viewport', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('http://127.0.0.1:8065/')
  await expect(page.getByRole('button', { name: 'New session' }).first()).toBeVisible()
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  )
  expect(overflow).toBeLessThanOrEqual(1)
})
