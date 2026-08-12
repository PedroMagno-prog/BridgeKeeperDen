/**
 * Store de Artigos (Pinia).
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/api/client'
import { useWorldsStore } from './worlds'

export type Visibility = 'TOTAL' | 'PARCIAL' | 'NULA'

export interface ArticleSection {
  id: string
  title: string
  content: string
  order_index: number
}

export interface InventoryItem {
  id: string
  item_name: string
  quantity: number
  description: string | null
}

export interface Article {
  id: string
  title: string
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

  function wid() {
    return useWorldsStore().activeWorld?.id
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

  async function fetchArticle(id: string) {
    const worldId = wid()
    if (!worldId) return
    const { data } = await api.get<Article>(`/worlds/${worldId}/articles/${id}`)
    current.value = data
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

    const { data } = await api.post<{ imported_count: number; skipped_count: number; message: string }>(
      `/worlds/${worldId}/articles/import/obsidian`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )

    await fetchArticles()
    return data
  }

  return {
    articles, current, currentBacklinks, loading, searchQuery, tagFilter,
    fetchArticles, fetchArticle, resolveArticle, searchMentions, fetchBacklinks, createArticle, updateArticle, deleteArticle, updateInventory, importObsidianVault,
  }
})
