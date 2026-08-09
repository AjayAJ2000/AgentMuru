import { spawn, type ChildProcess } from 'node:child_process'
import { once } from 'node:events'
import { resolve } from 'node:path'

import { expect, test } from '@playwright/test'


const port = 8066
const origin = `http://127.0.0.1:${port}`


async function waitForServer(): Promise<void> {
  const deadline = Date.now() + 20_000
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`${origin}/health`)
      if (response.ok) return
    } catch {
      // The process is still opening its listening socket.
    }
    await new Promise((resolveWait) => setTimeout(resolveWait, 100))
  }
  throw new Error('Durable AgentMuru fixture did not become ready')
}


async function startServer(database: string): Promise<ChildProcess> {
  const child = spawn(
    'python',
    [
      '-m',
      'tests.fixtures.durable_workspace_server',
      '--database', database,
      '--port', String(port),
    ],
    {
      cwd: resolve('..'),
      env: process.env,
      stdio: 'pipe',
    },
  )
  await waitForServer()
  return child
}


async function stopServer(child: ChildProcess | undefined): Promise<void> {
  if (!child || child.exitCode !== null) return
  child.kill()
  await Promise.race([
    once(child, 'exit'),
    new Promise((resolveWait) => setTimeout(resolveWait, 5_000)),
  ])
}


test('Muru Workspace restores durable history after a server restart', async ({ page }, testInfo) => {
  const database = testInfo.outputPath('agentmuru.db')
  let server: ChildProcess | undefined
  try {
    server = await startServer(database)
    await page.goto(origin)
    await page.getByRole('button', { name: 'New session' }).first().click()
    await expect(page.getByText('Runtime connected', { exact: true })).toBeVisible()
    await page.getByLabel('Give the agent an objective').fill('Create durable history')
    await page.getByRole('button', { name: 'Run', exact: true }).click()
    await expect(page.getByText('Durable AgentMuru history restored.', { exact: true })).toBeVisible()

    await stopServer(server)
    server = undefined
    await expect(page.getByText('Reconnecting', { exact: true })).toBeVisible()

    server = await startServer(database)
    await page.reload()
    await expect(page.getByText('Runtime connected', { exact: true })).toBeVisible()
    await expect(page.getByText('Create durable history', { exact: true })).toBeVisible()
    await expect(page.getByText('Durable AgentMuru history restored.', { exact: true })).toBeVisible()
  } finally {
    await stopServer(server)
  }
})
