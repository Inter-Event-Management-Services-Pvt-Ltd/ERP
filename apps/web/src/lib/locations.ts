import type { PhysicalLocation } from '@/types'

export interface LocationTreeNode extends PhysicalLocation {
  children: LocationTreeNode[]
}

export function buildLocationTree(locations: PhysicalLocation[]): LocationTreeNode[] {
  const nodes = new Map<string, LocationTreeNode>()
  locations.forEach((loc) => nodes.set(loc.id, { ...loc, children: [] }))

  const roots: LocationTreeNode[] = []
  nodes.forEach((node) => {
    const parent = node.parent_location_id ? nodes.get(node.parent_location_id) : undefined
    if (parent) {
      parent.children.push(node)
    } else {
      roots.push(node)
    }
  })
  return roots
}

export function locationDisplayName(location: Pick<PhysicalLocation, 'label' | 'code'>): string {
  return location.label ?? location.code
}

export function locationPath(location: PhysicalLocation, locations: PhysicalLocation[]): string {
  const byId = new Map(locations.map((l) => [l.id, l]))
  const segments: string[] = []
  let current: PhysicalLocation | undefined = location
  while (current) {
    segments.unshift(locationDisplayName(current))
    current = current.parent_location_id ? byId.get(current.parent_location_id) : undefined
  }
  return segments.join(' › ')
}
