import { describe, expect, it } from 'vitest'
import { PatchApplicationError, applyPatch, applyPatches } from './applyPatch'
import type { VNodeData } from '../types'

const leaf = (value: string): VNodeData => ({
  type: 'text',
  props: { value },
  children: [],
  key: null,
})

const root: VNodeData = {
  type: 'div',
  props: { title: 'old' },
  children: [leaf('first')],
  key: null,
}

describe('applyPatch', () => {
  it('rejects a nested patch whose parent path does not exist', () => {
    expect(() => applyPatch(root, { op: 'replace', path: [4, 0], node: leaf('x') }))
      .toThrow(PatchApplicationError)
  })

  it('applies replace, update_props, insert, and remove immutably', () => {
    const updated = applyPatches(root, [
      { op: 'update_props', path: [], props: { title: 'new' } },
      { op: 'insert', path: [1], node: leaf('second') },
      { op: 'replace', path: [0], node: leaf('first-updated') },
    ])

    expect(updated.props.title).toBe('new')
    expect(updated.children.map(child => child.props.value)).toEqual(['first-updated', 'second'])
    expect(root.props.title).toBe('old')
    expect(root.children.map(child => child.props.value)).toEqual(['first'])

    const removed = applyPatch(updated, { op: 'remove', path: [1] })
    expect(removed.children.map(child => child.props.value)).toEqual(['first-updated'])
  })
})
