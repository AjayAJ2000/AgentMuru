import React from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it, vi } from 'vitest'

import {
  CatalogBrowserView,
  JobTriggerView,
  WarehouseSelectorView,
} from './databricksComponents'

function findElement(node: React.ReactNode, type: string): React.ReactElement<Record<string, any>> {
  if (React.isValidElement(node)) {
    if (node.type === type) return node as React.ReactElement<Record<string, any>>
    const children = React.Children.toArray((node.props as Record<string, any>).children)
    for (const child of children) {
      try {
        return findElement(child, type)
      } catch {
        // Continue through the remaining child branches.
      }
    }
  }
  throw new Error(`No ${type} element found`)
}

describe('Databricks component views', () => {
  it('renders a labelled warehouse selector and emits only its identifier', () => {
    const onSelect = vi.fn()
    const element = WarehouseSelectorView({
      props: {
        label: 'SQL Warehouse',
        warehouses: [{ id: 'w1', name: 'Starter', state: 'RUNNING' }],
        selectedId: '',
      },
      onSelect,
    })
    const markup = renderToStaticMarkup(element)
    const select = findElement(element, 'select')

    select.props.onChange({ target: { value: 'w1' } })

    expect(markup).toContain('SQL Warehouse')
    expect(markup).toContain('Starter')
    expect(markup).toContain('RUNNING')
    expect(onSelect).toHaveBeenCalledWith('w1')
  })

  it('renders catalog hierarchy and emits a normalized table selection', () => {
    const onSelect = vi.fn()
    const element = CatalogBrowserView({
      props: {
        catalogs: [{
          name: 'main',
          schemas: [{
            name: 'default',
            tables: [{ name: 'events', full_name: 'main.default.events' }],
          }],
        }],
        selected: {},
      },
      onSelect,
    })
    const markup = renderToStaticMarkup(element)
    const button = findElement(element, 'button')

    button.props.onClick()

    expect(markup).toContain('main.default.events')
    expect(onSelect).toHaveBeenCalledWith({
      level: 'table',
      catalog: 'main',
      schema: 'default',
      table: 'events',
      full_name: 'main.default.events',
    })
  })

  it('renders honest loading, empty, error, and disabled job states', () => {
    const onTrigger = vi.fn()
    const loadingMarkup = renderToStaticMarkup(
      WarehouseSelectorView({ props: { warehouses: [], loading: true }, onSelect: vi.fn() }),
    )
    const emptyMarkup = renderToStaticMarkup(
      CatalogBrowserView({ props: { catalogs: [], emptyMessage: 'No catalogs' }, onSelect: vi.fn() }),
    )
    const job = JobTriggerView({
      props: { jobId: '42', label: 'Run job', error: 'Permission denied', disabled: true },
      onTrigger,
    })
    const jobMarkup = renderToStaticMarkup(job)
    const button = findElement(job, 'button')

    button.props.onClick()

    expect(loadingMarkup).toContain('Loading warehouses')
    expect(emptyMarkup).toContain('No catalogs')
    expect(jobMarkup).toContain('Permission denied')
    expect(button.props.disabled).toBe(true)
    expect(onTrigger).not.toHaveBeenCalled()
  })
})
