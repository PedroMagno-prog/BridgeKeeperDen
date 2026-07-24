import { defineStore } from 'pinia'
import { ref } from 'vue'
import { apiFetch } from '../services/api'

export interface ArticleSection {
  id: string
  article_id: string
  title: string
  content: string
  order_index: number
}

export interface CharacterInventoryItem {
  id: string
  article_id: string
  item_name: string
  quantity: number
  description?: string
}

export interface Article {
  id: string
  world_id: string
  title: string
  visibility: 'TOTAL' | 'PARCIAL' | 'NULA'
  in_game_date?: string
  in_game_sort_order?: number
  created_by: string
  created_at: string
  updated_at: string
  is_locked: boolean
  tags: string[]
  sections: ArticleSection[]
  inventory_items: CharacterInventoryItem[]
}

export const useArticleStore = defineStore('article', () => {
  const articles = ref<Article[]>([])
  const currentArticle = ref<Article | null>(null)
  const loading = ref(false)

  async function fetchArticles(worldId: string, tag?: string, search?: string) {
    loading.value = true
    try {
      let url = `/worlds/${worldId}/articles`
      const params = new URLSearchParams()
      if (tag) params.append('tag', tag)
      if (search) params.append('search', search)
      if (params.toString()) url += `?${params.toString()}`

      articles.value = await apiFetch<Article[]>(url)
    } finally {
      loading.value = false
    }
  }

  async function fetchArticleById(worldId: string, articleId: string) {
    loading.value = true
    try {
      currentArticle.value = await apiFetch<Article>(`/worlds/${worldId}/articles/${articleId}`)
    } finally {
      loading.value = false
    }
  }

  async function createArticle(worldId: string, payload: any) {
    loading.value = true
    try {
      const newArt = await apiFetch<Article>(`/worlds/${worldId}/articles`, {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      articles.value.push(newArt)
      return newArt
    } finally {
      loading.value = false
    }
  }

  async function updateArticle(worldId: string, articleId: string, payload: any) {
    loading.value = true
    try {
      const updated = await apiFetch<Article>(`/worlds/${worldId}/articles/${articleId}`, {
        method: 'PUT',
        body: JSON.stringify(payload),
      })
      currentArticle.value = updated
      const idx = articles.value.findIndex((a) => a.id === articleId)
      if (idx !== -1) articles.value[idx] = updated
      return updated
    } finally {
      loading.value = false
    }
  }

  async function addInventoryItem(worldId: string, articleId: string, item: any) {
    const newItem = await apiFetch<CharacterInventoryItem>(
      `/worlds/${worldId}/articles/${articleId}/inventory`,
      {
        method: 'POST',
        body: JSON.stringify(item),
      }
    )
    if (currentArticle.value && currentArticle.value.id === articleId) {
      currentArticle.value.inventory_items.push(newItem)
    }
    return newItem
  }

  return {
    articles,
    currentArticle,
    loading,
    fetchArticles,
    fetchArticleById,
    createArticle,
    updateArticle,
    addInventoryItem,
  }
})
