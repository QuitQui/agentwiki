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
  return JSON.parse(
    readFileSync(path.join(DIST_DIR, 'nodes', `${slug}.json`), 'utf-8')
  )
}

/** node id → URL slug (replace : with __) */
export function idToSlug(id: string): string {
  return id.replace(/:/g, '__')
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
