import { readFileSync, readdirSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

// src/lib/ → src/ → site/ → repo root → dist/
const DIST_DIR = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  '..', '..', '..', 'dist'
)

export interface NodeSummary {
  id: string
  type: string
  title: string
  source_path: string
  created_at: string | null
  sections: number
  entities: number
  outgoing_links: number
  backlinks: number
}

export interface Entity {
  type: string
  name: string
  path?: string
}

export interface Edge {
  source_id: string
  target_id: string
  edge_type: string
}

export interface Section {
  id: string
  type: string
  title: string
  content_html?: string
  content_text?: string
}

export interface KnowledgeNode {
  id: string
  type: string
  title: string
  source_path: string
  html_path?: string
  content_text?: string
  content_html?: string
  sections: Section[]
  entities: Entity[]
  outgoing_links: Edge[]
  backlinks: Edge[]
  git_commit?: string
  created_at?: string
  updated_at?: string
}

export function getIndex(): NodeSummary[] {
  return JSON.parse(readFileSync(path.join(DIST_DIR, 'index.json'), 'utf-8'))
}

export function getAllNodes(): KnowledgeNode[] {
  const nodesDir = path.join(DIST_DIR, 'nodes')
  return readdirSync(nodesDir)
    .filter(f => f.endsWith('.json'))
    .map(f => JSON.parse(readFileSync(path.join(nodesDir, f), 'utf-8')))
}

export function getNode(slug: string): KnowledgeNode {
  const nodesDir = path.join(DIST_DIR, 'nodes')
  const resolved = path.resolve(nodesDir, `${slug}.json`)
  if (!resolved.startsWith(nodesDir + path.sep)) {
    throw new Error(`Invalid node slug: ${slug}`)
  }
  return JSON.parse(readFileSync(resolved, 'utf-8'))
}

/** node id → URL slug (safe for filenames and URL path segments) */
export function idToSlug(id: string): string {
  return id.replace(/:/g, '__').replace(/\//g, '-')
}

/** URL slug → node id */
export function slugToId(slug: string): string {
  return slug.replace(/__/g, ':')
}

export const NODE_TYPE_COLOR: Record<string, string> = {
  AgentReport: '#38bdf8',
  agent_report: '#38bdf8',
  Document: '#a78bfa',
  CodeFile: '#34d399',
  Function: '#34d399',
  Concept: '#fbbf24',
  Decision: '#f87171',
}

export function nodeColor(type: string): string {
  return NODE_TYPE_COLOR[type] ?? '#94a3b8'
}

export function getCodeSymbols(nodeId: string): KnowledgeNode[] {
  const node = getNode(idToSlug(nodeId))
  const codefileIds = (node.backlinks ?? [])
    .filter(e => e.source_id.startsWith('codefile:') && e.edge_type === 'related_to')
    .map(e => e.source_id)
  if (codefileIds.length === 0) return []
  const filePaths = new Set(codefileIds.map(id => id.slice('codefile:'.length)))
  return getAllNodes().filter(n => {
    if (n.type !== 'Function' && n.type !== 'Class') return false
    const m = n.id.match(/^codesymbol:(.+):[^:]+$/)
    return m != null && filePaths.has(m[1])
  })
}
