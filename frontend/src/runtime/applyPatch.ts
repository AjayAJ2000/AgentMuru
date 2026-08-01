import type { Patch, VNodeData } from '../types'

export class PatchApplicationError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'PatchApplicationError'
  }
}

function validatePath(path: number[]): void {
  if (!Array.isArray(path) || path.some(index => !Number.isInteger(index) || index < 0)) {
    throw new PatchApplicationError('Patch path must contain non-negative integer indexes')
  }
}

function updateProps(tree: VNodeData, props: Record<string, unknown>): VNodeData {
  const nextProps = { ...tree.props }
  for (const [key, value] of Object.entries(props)) {
    if (value === null) delete nextProps[key]
    else nextProps[key] = value
  }
  return { ...tree, props: nextProps }
}

export function applyPatch(tree: VNodeData, patch: Patch): VNodeData {
  validatePath(patch.path)
  const { op, path, node, props } = patch

  if (path.length === 0) {
    if (op === 'replace') {
      if (!node) throw new PatchApplicationError('Root replace patch requires a node')
      return node
    }
    if (op === 'update_props') {
      if (!props) throw new PatchApplicationError('Update-props patch requires props')
      return updateProps(tree, props)
    }
    throw new PatchApplicationError(`Operation ${op} is invalid at the root path`)
  }

  const [index, ...rest] = path
  const children = [...tree.children]

  if (rest.length === 0) {
    if (op === 'insert') {
      if (!node) throw new PatchApplicationError('Insert patch requires a node')
      if (index > children.length) {
        throw new PatchApplicationError(`Insert index ${index} is outside the child list`)
      }
      children.splice(index, 0, node)
      return { ...tree, children }
    }

    if (index >= children.length) {
      throw new PatchApplicationError(`Patch index ${index} is outside the child list`)
    }

    if (op === 'remove') {
      children.splice(index, 1)
      return { ...tree, children }
    }
    if (op === 'replace') {
      if (!node) throw new PatchApplicationError('Replace patch requires a node')
      children[index] = node
      return { ...tree, children }
    }
    if (op === 'update_props') {
      if (!props) throw new PatchApplicationError('Update-props patch requires props')
      children[index] = updateProps(children[index], props)
      return { ...tree, children }
    }
  }

  if (index >= children.length) {
    throw new PatchApplicationError(`Patch parent index ${index} does not exist`)
  }
  children[index] = applyPatch(children[index], { ...patch, path: rest })
  return { ...tree, children }
}

export function applyPatches(tree: VNodeData, patches: Patch[]): VNodeData {
  return patches.reduce((current, patch) => applyPatch(current, patch), tree)
}
