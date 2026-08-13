/**
 * Módulo de API para gerenciamento de Pastas (ArticleFolder) e Árvore do Codex.
 */
import { api } from './client'

export interface ArticleSummary {
  id: string
  title: string
  folder_id: number | null
  visibility: 'TOTAL' | 'PARCIAL' | 'CONTROLADO' | 'NULA'
  in_game_date: string | null
  updated_at: string | null
  is_locked: boolean
  can_edit?: boolean
  can_delete?: boolean
}

export interface FolderTreeNode {
  id: number
  name: string
  parent_id: number | null
  children: FolderTreeNode[]
  articles: ArticleSummary[]
}

export interface WorldFolderTreeResponse {
  folders: FolderTreeNode[]
  root_articles: ArticleSummary[]
}

export interface FolderResponse {
  id: number
  world_id: string
  name: string
  parent_id: number | null
  created_at: string | null
  updated_at: string | null
}

export async function getFolderTree(worldId: string): Promise<WorldFolderTreeResponse> {
  const { data } = await api.get<WorldFolderTreeResponse>(`/worlds/${worldId}/folders/`)
  return data
}

export async function createFolder(
  worldId: string,
  payload: { name: string; parent_id?: number | null }
): Promise<FolderResponse> {
  const { data } = await api.post<FolderResponse>(`/worlds/${worldId}/folders/`, payload)
  return data
}

export async function updateFolder(
  worldId: string,
  folderId: number,
  payload: { name?: string; parent_id?: number | null }
): Promise<FolderResponse> {
  const { data } = await api.put<FolderResponse>(`/worlds/${worldId}/folders/${folderId}`, payload)
  return data
}

export async function deleteFolder(worldId: string, folderId: number): Promise<void> {
  await api.delete(`/worlds/${worldId}/folders/${folderId}`)
}
