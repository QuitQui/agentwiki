import { readFileSync, existsSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

export interface SimilarNode {
  id: string
  title: string
  score: number
}

const _defaultDist = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..', '..', 'dist')
const _envDist = process.env.AGENTWIKI_DIST_DIR ? path.resolve(process.env.AGENTWIKI_DIST_DIR) : null
const DIST_DIR = _envDist ?? _defaultDist

let _cache: Record<string, SimilarNode[]> | null = null

function load(): Record<string, SimilarNode[]> {
  if (_cache) return _cache
  const p = path.join(DIST_DIR, 'similar.json')
  _cache = existsSync(p) ? (JSON.parse(readFileSync(p, 'utf-8')) as Record<string, SimilarNode[]>) : {}
  return _cache
}

export function getSimilar(id: string): SimilarNode[] {
  return load()[id] ?? []
}
