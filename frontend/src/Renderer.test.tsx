// @vitest-environment jsdom

import React, { act } from 'react'
import { createRoot, type Root } from 'react-dom/client'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { Renderer } from './Renderer'
import type { VNodeData } from './types'

(globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT: boolean }).IS_REACT_ACT_ENVIRONMENT = true

const modalNode: VNodeData = {
  type: 'Modal',
  props: {
    title: 'Executive brief',
    visible: true,
    size: 'md',
    close: 'close-modal',
  },
  children: [
    {
      type: 'Button',
      props: { label: 'Review details', click: 'review-details' },
      children: [],
      key: null,
    },
  ],
  key: null,
}

describe('Modal accessibility', () => {
  let container: HTMLDivElement
  let root: Root
  let trigger: HTMLButtonElement
  let dispatch: ReturnType<typeof vi.fn>

  beforeEach(() => {
    container = document.createElement('div')
    trigger = document.createElement('button')
    trigger.textContent = 'Open executive brief'
    document.body.append(trigger, container)
    trigger.focus()
    dispatch = vi.fn()
    root = createRoot(container)
  })

  afterEach(() => {
    act(() => root.unmount())
    document.body.replaceChildren()
  })

  function renderModal(node = modalNode) {
    act(() => {
      root.render(
        <Renderer
          node={node}
          dispatch={dispatch}
          navigate={vi.fn()}
          pendingEvents={new Map()}
          themeMode="light"
          setThemeMode={vi.fn()}
        />,
      )
    })
  }

  it('renders a labelled modal dialog and an accessible close control', () => {
    renderModal()

    const dialog = container.querySelector<HTMLElement>('[role="dialog"]')
    const title = container.querySelector<HTMLElement>('.bf-modal-title')
    const close = container.querySelector<HTMLButtonElement>('.bf-modal-close')
    const action = container.querySelector<HTMLButtonElement>('.bf-modal-body .bf-btn')

    expect(dialog).not.toBeNull()
    expect(dialog?.getAttribute('aria-modal')).toBe('true')
    expect(title?.id).toBeTruthy()
    expect(dialog?.getAttribute('aria-labelledby')).toBe(title?.id)
    expect(close?.getAttribute('aria-label')).toBe('Close Executive brief')
    expect(action?.dataset.bfFocusKey).toBe('0-0')
  })

  it('moves focus into the dialog and restores the trigger when the modal unmounts', () => {
    renderModal()

    const close = container.querySelector<HTMLButtonElement>('.bf-modal-close')
    expect(document.activeElement).toBe(close)

    renderModal({ type: 'Text', props: { value: 'Closed' }, children: [], key: null })
    expect(document.activeElement).toBe(trigger)
  })

  it('restores focus to a server-rendered replacement for the trigger', () => {
    trigger.dataset.bfFocusKey = 'open-executive-brief'
    renderModal()

    const replacement = document.createElement('button')
    replacement.textContent = trigger.textContent
    replacement.dataset.bfFocusKey = trigger.dataset.bfFocusKey
    trigger.replaceWith(replacement)
    trigger = replacement

    renderModal({ type: 'Text', props: { value: 'Closed' }, children: [], key: null })
    expect(document.activeElement).toBe(replacement)
  })

  it('restores the correct keyed trigger when duplicate labels survive an opening patch', () => {
    function ModalFlow() {
      const [phase, setPhase] = React.useState<'initial' | 'open' | 'closed'>('initial')
      const suffix = phase === 'initial' ? 'initial' : phase === 'open' ? 'replacement' : 'final'
      const children: VNodeData[] = [
        {
          type: 'Button',
          props: { label: 'Executive brief', click: `decoy-${suffix}` },
          children: [],
          key: null,
        },
        {
          type: 'Button',
          props: { label: 'Executive brief', click: `target-${suffix}` },
          children: [],
          key: null,
        },
      ]
      if (phase === 'open') children.push(modalNode)
      const node: VNodeData = {
        type: 'Column',
        props: {},
        children,
        key: null,
      }

      return (
        <Renderer
          node={node}
          dispatch={(eventId) => {
            if (eventId === 'target-initial') setPhase('open')
            if (eventId === 'close-modal') setPhase('closed')
          }}
          navigate={vi.fn()}
          pendingEvents={new Map()}
          themeMode="light"
          setThemeMode={vi.fn()}
        />
      )
    }

    act(() => root.render(<ModalFlow />))
    const openingButtons = container.querySelectorAll<HTMLButtonElement>('.bf-column > .bf-btn')
    const openingTrigger = openingButtons[1]
    expect(openingButtons[0].textContent).toBe(openingTrigger.textContent)
    expect(openingTrigger.dataset.bfFocusKey).toBe('0-1')
    openingTrigger?.focus()
    act(() => openingTrigger?.click())

    const openButtons = container.querySelectorAll<HTMLButtonElement>('.bf-column > .bf-btn')
    expect(openButtons[1].dataset.bfFocusKey).toBe('0-1')
    const serverReplacement = openButtons[1].cloneNode(true) as HTMLButtonElement
    openButtons[1].replaceWith(serverReplacement)
    expect(openingTrigger?.isConnected).toBe(false)
    const close = container.querySelector<HTMLButtonElement>('.bf-modal-close')
    expect(document.activeElement).toBe(close)

    act(() => close?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })))
    const closedButtons = container.querySelectorAll<HTMLButtonElement>('.bf-column > .bf-btn')
    const replacement = closedButtons[1]
    expect(closedButtons[0].textContent).toBe(replacement.textContent)
    expect(replacement).not.toBe(openingTrigger)
    expect(document.activeElement).toBe(replacement)
  })

  it('excludes hidden, non-rendered, inert, aria-hidden, and disabled controls from the focus trap', () => {
    renderModal()

    const close = container.querySelector<HTMLButtonElement>('.bf-modal-close')
    const body = container.querySelector<HTMLElement>('.bf-modal-body')
    const action = body?.querySelector<HTMLButtonElement>('.bf-btn')
    const hidden = document.createElement('button')
    hidden.hidden = true
    const nonRendered = document.createElement('button')
    nonRendered.style.display = 'none'
    const inert = document.createElement('button')
    inert.setAttribute('inert', '')
    const ariaHidden = document.createElement('button')
    ariaHidden.setAttribute('aria-hidden', 'true')
    const disabled = document.createElement('button')
    disabled.disabled = true
    body?.append(hidden, nonRendered, inert, ariaHidden, disabled)

    action?.focus()
    act(() => action?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', bubbles: true })))
    expect(document.activeElement).toBe(close)
  })

  it('dispatches close on Escape and contains Tab focus within the dialog', () => {
    renderModal()

    const close = container.querySelector<HTMLButtonElement>('.bf-modal-close')
    const action = container.querySelector<HTMLButtonElement>('.bf-modal-body .bf-btn')
    expect(close).not.toBeNull()
    expect(action).not.toBeNull()

    action?.focus()
    act(() => action?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', bubbles: true })))
    expect(document.activeElement).toBe(close)

    act(() => close?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', shiftKey: true, bubbles: true })))
    expect(document.activeElement).toBe(action)

    act(() => action?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })))
    expect(dispatch).toHaveBeenCalledWith('close-modal', {})
  })

  it('gives the popup close control an accessible name', () => {
    const popupNode: VNodeData = {
      type: 'Popup',
      props: {
        title: 'Quick filters',
        visible: true,
        close: 'close-popup',
      },
      children: [],
      key: null,
    }

    act(() => {
      root.render(
        <Renderer
          node={popupNode}
          dispatch={dispatch}
          navigate={vi.fn()}
          pendingEvents={new Map()}
          themeMode="light"
          setThemeMode={vi.fn()}
        />,
      )
    })

    const close = container.querySelector<HTMLButtonElement>('.bf-popup .bf-modal-close')
    expect(close?.getAttribute('aria-label')).toBe('Close Quick filters')
  })
})
