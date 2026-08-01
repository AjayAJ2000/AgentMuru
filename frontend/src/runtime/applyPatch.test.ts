import { describe, expect, it } from 'vitest'

import type { VNodeData } from '../types'
import { applyPatch, applyPatches, PatchApplicationError } from './applyPatch'

function leaf(value: string): VNodeData {
  return { type: 'Text', props: { value }, children: [], key: null }
}

function root(): VNodeData {
  return {
    type: 'Column',
    props: { title: 'old', removable: true },
    children: [leaf('first')],
    key: null,
  }
}

describe('applyPatch', () => {
  it('applies root prop updates without mutating the source tree', () => {
    const source = root()
    const updated = applyPatch(source, {
      op: 'update_props',
      path: [],
      props: { title: 'new', removable: null },
    })

    expect(updated.props).toEqual({ title: 'new' })
    expect(source.props).toEqual({ title: 'old', removable: true })
  })

  it('applies replace, insert, and remove operations', () => {
    const updated = applyPatches(root(), [
      { op: 'insert', path: [1], node: leaf('second') },
      { op: 'replace', path: [0], node: leaf('first-updated') },
      { op: 'remove', path: [1] },
    ])

    expect(updated.children.map(child => child.props.value)).toEqual(['first-updated'])
  })

  it('applies descending removals generated for a shrinking page tree', () => {
    const source: VNodeData = {
      type: 'Column',
      props: {},
      children: ['0', '1', '2', '3', '4'].map(leaf),
      key: null,
    }

    const updated = applyPatches(source, [
      { op: 'remove', path: [4] },
      { op: 'remove', path: [3] },
      { op: 'remove', path: [2] },
      { op: 'remove', path: [1] },
    ])

    expect(updated.children.map(child => child.props.value)).toEqual(['0'])
  })

  it('rejects ascending removals after an earlier removal shifts the child list', () => {
    const source: VNodeData = {
      type: 'Column',
      props: {},
      children: ['0', '1', '2', '3', '4'].map(leaf),
      key: null,
    }

    expect(() => applyPatches(source, [
      { op: 'remove', path: [1] },
      { op: 'remove', path: [2] },
      { op: 'remove', path: [3] },
      { op: 'remove', path: [4] },
    ])).toThrow('Patch index 3 is outside the child list')
  })

  it('updates a nested node through its complete parent path', () => {
    const source: VNodeData = {
      type: 'Column',
      props: {},
      children: [{ type: 'Row', props: {}, children: [leaf('old')], key: null }],
      key: null,
    }

    const updated = applyPatch(source, {
      op: 'update_props',
      path: [0, 0],
      props: { value: 'new' },
    })

    expect(updated.children[0].children[0].props.value).toBe('new')
  })

  it.each([
    { op: 'replace' as const, path: [4, 0], node: leaf('x') },
    { op: 'remove' as const, path: [-1] },
    { op: 'insert' as const, path: [3], node: leaf('x') },
    { op: 'replace' as const, path: [0] },
  ])('rejects malformed or out-of-bounds patch %#', patch => {
    expect(() => applyPatch(root(), patch)).toThrow(PatchApplicationError)
  })
})
