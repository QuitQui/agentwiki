import { readFileSync, existsSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

export interface Neighbor {
  id: string
  type: string
  title: string
  hops: 1 | 2
}

export interface DegreeEntry {
  id: string
  title: string
  out_degree: number
  in_degree: number
}

export interface GraphStats {
  node_count: number
  edge_count: number
  top_by_degree: DegreeEntry[]
}

const DIST_DIR =
  process.env.AGENTWIKI_DIST_DIR ??
  path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..', '..', 'dist')

let _neighbors: Record<string, Neighbor[]> | null = null
let _stats: GraphStats | null = null

function loadNeighbors(): Record<string, Neighbor[]> {
  if (_neighbors) return _neighbors
  const p = path.join(DIST_DIR, 'neighbors.json')
  _neighbors = existsSync(p) ? (JSON.parse(readFileSync(p, 'utf-8')) as Record<string, Neighbor[]>) : {}
  return _neighbors
}

function loadStats(): GraphStats | null {
  if (_stats) return _stats
  const p = path.join(DIST_DIR, 'graph_stats.json')
  if (!existsSync(p)) return null
  _stats = JSON.parse(readFileSync(p, 'utf-8')) as GraphStats
  return _stats
}

export function getNeighbors(id: string): Neighbor[] {
  return loadNeighbors()[id] ?? []
}

export function getGraphStats(): GraphStats | null {
  return loadStats()
}
