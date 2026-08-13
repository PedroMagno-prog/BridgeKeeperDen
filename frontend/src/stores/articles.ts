/**
 * Store de Artigos (Pinia).
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/api/client'
import { useWorldsStore } from './worlds'
import {
  getFolderTree,
  createFolder,
  updateFolder,
  deleteFolder,
  type FolderTreeNode,
  type ArticleSummary,
  type WorldFolderTreeResponse,
} from '@/api/folders'

export type Visibility = 'TOTAL' | 'PARCIAL' | 'CONTROLADO' | 'NULA'

export interface ArticleSection {
  id: string
  title: string
  content: string
  order_index: number
  image_url?: string | null
}

export interface InventoryItem {
  id: string
  item_name: string
  quantity: number
  description: string | null
}

export interface Article {
  id: string
  folder_id?: number | null
  title: string
  content?: string
  visibility: Visibility
  in_game_date: string | null
  in_game_sort_order: number | null
  tags: string[]
  sections?: ArticleSection[]
  inventory_items?: InventoryItem[]
  created_by: string
  created_at: string
  updated_at: string
  is_locked: boolean
  can_edit?: boolean
  can_delete?: boolean
}

export interface UserPermission {
  user_id: string
  username: string
  email: string
  visibility: Visibility
}

export interface ArticleResolveResult {
  exists: boolean
  article_id: string | null
  title: string
  visibility: Visibility | null
  is_locked: boolean
}

export interface MentionSuggestion {
  id: string
  title: string
  visibility: Visibility
  tags: string[]
}

export interface BacklinkItem {
  article_id: string
  title: string
  visibility: Visibility
  section_title: string
  snippet: string
  is_locked: boolean
}

export const useArticlesStore = defineStore('articles', () => {
  const articles = ref<Article[]>([])
  const current = ref<Article | null>(null)
  const currentBacklinks = ref<BacklinkItem[]>([])
  const loading = ref(false)
  const searchQuery = ref('')
  const tagFilter = ref('')

  // Estado da Árvore de Pastas (Etapa 10)
  const folderTree = ref<FolderTreeNode[]>([])
  const rootArticles = ref<ArticleSummary[]>([])
  const expandedFolderIds = ref<Set<number>>(new Set())
  const selectedArticleId = ref<string | null>(null)

  function wid() {
    return useWorldsStore().activeWorld?.id
  }

  async function fetchFolderTree() {
    const worldId = wid()
    if (!worldId) return
    loading.value = true
    try {
      const res: WorldFolderTreeResponse = await getFolderTree(worldId)
      folderTree.value = res.folders
      rootArticles.value = res.root_articles
    } finally {
      loading.value = false
    }
  }

  function toggleFolderExpand(folderId: number) {
    if (expandedFolderIds.value.has(folderId)) {
      expandedFolderIds.value.delete(folderId)
    } else {
      expandedFolderIds.value.add(folderId)
    }
    // Para reatividade no Vue (Set ref mutation)
    expandedFolderIds.value = new Set(expandedFolderIds.value)
  }

  function expandFolder(folderId: number) {
    if (!expandedFolderIds.value.has(folderId)) {
      expandedFolderIds.value.add(folderId)
      expandedFolderIds.value = new Set(expandedFolderIds.value)
    }
  }

  async function createNewFolder(name: string, parentId?: number | null) {
    const worldId = wid()
    if (!worldId) return
    const folder = await createFolder(worldId, { name, parent_id: parentId })
    if (parentId) {
      expandFolder(parentId)
    }
    await fetchFolderTree()
    return folder
  }

  async function renameFolder(folderId: number, newName: string) {
    const worldId = wid()
    if (!worldId) return
    await updateFolder(worldId, folderId, { name: newName })
    await fetchFolderTree()
  }

  async function removeFolder(folderId: number) {
    const worldId = wid()
    if (!worldId) return
    await deleteFolder(worldId, folderId)
    expandedFolderIds.value.delete(folderId)
    expandedFolderIds.value = new Set(expandedFolderIds.value)
    await fetchFolderTree()
    await fetchArticles()
  }

  async function moveArticleToFolder(articleId: string, targetFolderId: number | null) {
    await updateArticle(articleId, { folder_id: targetFolderId })
    await fetchFolderTree()
  }

  async function patchArticleContent(articleId: string, content: string) {
    const worldId = wid()
    if (!worldId) return
    const { data } = await api.patch<Article>(`/worlds/${worldId}/articles/${articleId}/content`, {
      content,
    })
    if (current.value?.id === articleId) {
      current.value = data
    }
    return data
  }

  async function fetchArticles() {
    const worldId = wid()
    if (!worldId) return
    loading.value = true
    try {
      const params: Record<string, string> = {}
      if (searchQuery.value) params.search = searchQuery.value
      if (tagFilter.value) params.tag = tagFilter.value
      const { data } = await api.get<Article[]>(`/worlds/${worldId}/articles/`, { params })
      articles.value = data
    } finally {
      loading.value = false
    }
  }

  function expandFolderAncestors(folderId: number | null) {
    if (!folderId) return
    const findAndExpand = (folders: FolderTreeNode[], targetId: number): boolean => {
      for (const f of folders) {
        if (f.id === targetId) {
          expandedFolderIds.value.add(f.id)
          return true
        }
        if (f.children && f.children.length > 0) {
          if (findAndExpand(f.children, targetId)) {
            expandedFolderIds.value.add(f.id)
            return true
          }
        }
      }
      return false
    }
    findAndExpand(folderTree.value, folderId)
    expandedFolderIds.value = new Set(expandedFolderIds.value)
  }

  async function fetchArticle(id: string) {
    const worldId = wid()
    if (!worldId) return
    selectedArticleId.value = id
    const { data } = await api.get<Article>(`/worlds/${worldId}/articles/${id}`)
    current.value = data
    if (data.folder_id) {
      expandFolderAncestors(data.folder_id)
    }
    fetchBacklinks(id)
    return data
  }

  async function resolveArticle(title: string): Promise<ArticleResolveResult | null> {
    const worldId = wid()
    if (!worldId) return null
    const { data } = await api.get<ArticleResolveResult>(`/worlds/${worldId}/articles/resolve`, {
      params: { title },
    })
    return data
  }

  async function searchMentions(query: string): Promise<MentionSuggestion[]> {
    const worldId = wid()
    if (!worldId) return []
    const { data } = await api.get<MentionSuggestion[]>(`/worlds/${worldId}/articles/search-mentions`, {
      params: { query },
    })
    return data
  }

  async function fetchBacklinks(articleId: string): Promise<BacklinkItem[]> {
    const worldId = wid()
    if (!worldId) return []
    const { data } = await api.get<BacklinkItem[]>(`/worlds/${worldId}/articles/${articleId}/backlinks`)
    currentBacklinks.value = data
    return data
  }

  async function createArticle(payload: Partial<Article>) {
    const worldId = wid()
    if (!worldId) return
    const { data } = await api.post<Article>(`/worlds/${worldId}/articles/`, payload)
    articles.value.unshift(data)
    await fetchFolderTree()
    return data
  }

  async function updateArticle(id: string, payload: Partial<Article>) {
    const worldId = wid()
    if (!worldId) return
    const { data } = await api.put<Article>(`/worlds/${worldId}/articles/${id}`, payload)
    const idx = articles.value.findIndex((a) => a.id === id)
    if (idx !== -1) articles.value[idx] = data
    current.value = data
    return data
  }

  async function deleteArticle(id: string) {
    const worldId = wid()
    if (!worldId) return
    await api.delete(`/worlds/${worldId}/articles/${id}`)
    articles.value = articles.value.filter((a) => a.id !== id)
    if (current.value?.id === id) current.value = null
    await fetchFolderTree()
  }

  async function updateInventory(articleId: string, items: Omit<InventoryItem, 'id'>[]) {
    const worldId = wid()
    if (!worldId) return
    const { data } = await api.post<InventoryItem[]>(
      `/worlds/${worldId}/articles/${articleId}/inventory`,
      { items },
    )
    return data
  }

  async function importObsidianVault(file: File, useFoldersAsTags: boolean) {
    const worldId = wid()
    if (!worldId) throw new Error('Nenhum mundo selecionado.')

    const formData = new FormData()
    formData.append('file', file)
    formData.append('use_folders_as_tags', String(useFoldersAsTags))

    const { data } = await api.post<{ imported_count: number; skipped_count: number; folders_created: number; message: string }>(
      `/worlds/${worldId}/articles/import/obsidian`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )

    await fetchFolderTree()
    await fetchArticles()
    return data
  }

  async function fetchPermissions(articleId: string): Promise<UserPermission[]> {
    const worldId = wid()
    if (!worldId) return []
    const { data } = await api.get<UserPermission[]>(`/worlds/${worldId}/articles/${articleId}/permissions`)
    return data
  }

  async function updatePermissions(articleId: string, permissions: { user_id: string; visibility: Visibility }[]) {
    const worldId = wid()
    if (!worldId) return
    await api.put(`/worlds/${worldId}/articles/${articleId}/permissions`, { permissions })
  }

  async function uploadSectionImage(articleId: string, sectionId: string, file: File) {
    const worldId = wid()
    if (!worldId) return
    const formData = new FormData()
    formData.append('file', file)
    const { data } = await api.post<{ image_url: string }>(
      `/worlds/${worldId}/articles/${articleId}/sections/${sectionId}/image`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
    return data.image_url
  }

  return {
    articles, current, currentBacklinks, loading, searchQuery, tagFilter,
    folderTree, rootArticles, expandedFolderIds, selectedArticleId,
    fetchFolderTree, toggleFolderExpand, expandFolder, expandFolderAncestors, createNewFolder, renameFolder, removeFolder,
    moveArticleToFolder, patchArticleContent,
    fetchArticles, fetchArticle, resolveArticle, searchMentions, fetchBacklinks, createArticle, updateArticle, deleteArticle, updateInventory, importObsidianVault,
    fetchPermissions, updatePermissions, uploadSectionImage,
  }
})
