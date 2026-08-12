/**
 * Store do Módulo de Inventários e Grupos (Pinia).
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/api/client'
import { useWorldsStore } from './worlds'

export type Visibility = 'TOTAL' | 'PARCIAL' | 'NULA'

export interface ArticleItemSummary {
  id: string
  title: string
  visibility: Visibility
  tags: string[]
}

export interface InventoryItem {
  id: string
  inventory_id: string
  article_id: string | null
  custom_name: string | null
  display_name: string
  quantity: number
  notes: string | null
  order_index: number
  created_at: string
  article?: ArticleItemSummary | null
}

export interface Inventory {
  id: string
  world_id: string
  group_id: string | null
  owner_article_id: string | null
  name: string
  description: string | null
  limit: number | null
  visibility: Visibility
  items_count: number
  is_over_limit: boolean
  created_by: string
  created_at: string
  updated_at: string
  items?: InventoryItem[]
  is_locked?: boolean
}

export interface InventoryGroup {
  id: string
  world_id: string
  name: string
  description: string | null
  visibility: Visibility
  icon: string | null
  inventories_count: number
  created_by: string
  created_at: string
  updated_at: string
  inventories?: Inventory[]
  is_locked?: boolean
}

export const useInventoryStore = defineStore('inventory', () => {
  const groups = ref<InventoryGroup[]>([])
  const inventories = ref<Inventory[]>([])
  const currentInventory = ref<Inventory | null>(null)
  const currentGroup = ref<InventoryGroup | null>(null)
  const loading = ref(false)

  function wid() {
    return useWorldsStore().activeWorld?.id
  }

  // ── Grupos ──────────────────────────────────────────────────────────────────

  async function fetchGroups() {
    const worldId = wid()
    if (!worldId) return
    loading.value = true
    try {
      const { data } = await api.get<InventoryGroup[]>(`/worlds/${worldId}/inventories/groups`)
      groups.value = data
    } finally {
      loading.value = false
    }
  }

  async function createGroup(payload: { name: string; description?: string | null; visibility?: Visibility; icon?: string | null }) {
    const worldId = wid()
    if (!worldId) throw new Error('Nenhum mundo ativo selecionado.')
    const cleanPayload = {
      name: payload.name.trim(),
      description: payload.description?.trim() || null,
      visibility: payload.visibility,
      icon: payload.icon || 'folder',
    }
    const { data } = await api.post<InventoryGroup>(`/worlds/${worldId}/inventories/groups`, cleanPayload)
    groups.value.push(data)
    return data
  }

  async function updateGroup(id: string, payload: Partial<InventoryGroup>) {
    const worldId = wid()
    if (!worldId) throw new Error('Nenhum mundo ativo selecionado.')
    const cleanPayload = {
      ...payload,
      name: payload.name ? payload.name.trim() : undefined,
      description: payload.description !== undefined ? (payload.description?.trim() || null) : undefined,
      icon: payload.icon !== undefined ? (payload.icon || 'folder') : undefined,
    }
    const { data } = await api.put<InventoryGroup>(`/worlds/${worldId}/inventories/groups/${id}`, cleanPayload)
    const idx = groups.value.findIndex((g) => g.id === id)
    if (idx !== -1) groups.value[idx] = data
    if (currentGroup.value?.id === id) currentGroup.value = data
    return data
  }

  async function deleteGroup(id: string) {
    const worldId = wid()
    if (!worldId) throw new Error('Nenhum mundo ativo selecionado.')
    await api.delete(`/worlds/${worldId}/inventories/groups/${id}`)
    groups.value = groups.value.filter((g) => g.id !== id)
    if (currentGroup.value?.id === id) currentGroup.value = null
  }

  // ── Inventários ─────────────────────────────────────────────────────────────

  async function fetchInventories(groupId?: string) {
    const worldId = wid()
    if (!worldId) return
    loading.value = true
    try {
      const params: Record<string, string> = {}
      if (groupId) params.group_id = groupId
      const { data } = await api.get<Inventory[]>(`/worlds/${worldId}/inventories/`, { params })
      inventories.value = data
    } finally {
      loading.value = false
    }
  }

  async function fetchInventory(id: string) {
    const worldId = wid()
    if (!worldId) return
    const { data } = await api.get<Inventory>(`/worlds/${worldId}/inventories/${id}`)
    currentInventory.value = data
    return data
  }

  async function createInventory(payload: {
    name: string
    group_id?: string | null
    owner_article_id?: string | null
    description?: string | null
    limit?: number | null
    visibility?: Visibility
  }) {
    const worldId = wid()
    if (!worldId) throw new Error('Nenhum mundo ativo selecionado.')
    const cleanPayload = {
      name: payload.name.trim(),
      group_id: payload.group_id || null,
      owner_article_id: payload.owner_article_id || null,
      description: payload.description?.trim() || null,
      limit: payload.limit ? Number(payload.limit) : null,
      visibility: payload.visibility,
    }
    const { data } = await api.post<Inventory>(`/worlds/${worldId}/inventories/`, cleanPayload)
    inventories.value.push(data)
    fetchGroups()
    return data
  }

  async function updateInventory(id: string, payload: Partial<Inventory>) {
    const worldId = wid()
    if (!worldId) throw new Error('Nenhum mundo ativo selecionado.')
    const cleanPayload = {
      ...payload,
      name: payload.name ? payload.name.trim() : undefined,
      group_id: payload.group_id !== undefined ? (payload.group_id || null) : undefined,
      owner_article_id: payload.owner_article_id !== undefined ? (payload.owner_article_id || null) : undefined,
      description: payload.description !== undefined ? (payload.description?.trim() || null) : undefined,
      limit: payload.limit !== undefined ? (payload.limit ? Number(payload.limit) : null) : undefined,
    }
    const { data } = await api.put<Inventory>(`/worlds/${worldId}/inventories/${id}`, cleanPayload)
    const idx = inventories.value.findIndex((i) => i.id === id)
    if (idx !== -1) inventories.value[idx] = data
    if (currentInventory.value?.id === id) currentInventory.value = data

    fetchGroups()
    return data
  }

  async function deleteInventory(id: string) {
    const worldId = wid()
    if (!worldId) return
    await api.delete(`/worlds/${worldId}/inventories/${id}`)
    inventories.value = inventories.value.filter((i) => i.id !== id)
    if (currentInventory.value?.id === id) currentInventory.value = null
    fetchGroups()
  }

  // ── Itens do Inventário ─────────────────────────────────────────────────────

  async function addItem(
    inventoryId: string,
    payload: {
      article_id?: string | null
      custom_name?: string | null
      quantity?: number
      notes?: string | null
    },
  ) {
    const worldId = wid()
    if (!worldId) return
    const { data } = await api.post<InventoryItem>(`/worlds/${worldId}/inventories/${inventoryId}/items`, payload)
    if (currentInventory.value && currentInventory.value.id === inventoryId) {
      if (!currentInventory.value.items) currentInventory.value.items = []
      currentInventory.value.items.push(data)
      currentInventory.value.items_count = currentInventory.value.items.length
      if (currentInventory.value.limit) {
        currentInventory.value.is_over_limit = currentInventory.value.items_count > currentInventory.value.limit
      }
    }
    fetchGroups()
    return data
  }

  async function updateItem(
    inventoryId: string,
    itemId: string,
    payload: Partial<InventoryItem>,
  ) {
    const worldId = wid()
    if (!worldId) return
    const { data } = await api.put<InventoryItem>(`/worlds/${worldId}/inventories/${inventoryId}/items/${itemId}`, payload)
    if (currentInventory.value && currentInventory.value.id === inventoryId && currentInventory.value.items) {
      const idx = currentInventory.value.items.findIndex((item) => item.id === itemId)
      if (idx !== -1) currentInventory.value.items[idx] = data
    }
    fetchGroups()
    return data
  }

  async function deleteItem(inventoryId: string, itemId: string) {
    const worldId = wid()
    if (!worldId) return
    await api.delete(`/worlds/${worldId}/inventories/${inventoryId}/items/${itemId}`)
    if (currentInventory.value && currentInventory.value.id === inventoryId && currentInventory.value.items) {
      currentInventory.value.items = currentInventory.value.items.filter((item) => item.id !== itemId)
      currentInventory.value.items_count = currentInventory.value.items.length
      if (currentInventory.value.limit) {
        currentInventory.value.is_over_limit = currentInventory.value.items_count > currentInventory.value.limit
      }
    }
    fetchGroups()
  }

  return {
    groups,
    inventories,
    currentInventory,
    currentGroup,
    loading,
    fetchGroups,
    createGroup,
    updateGroup,
    deleteGroup,
    fetchInventories,
    fetchInventory,
    createInventory,
    updateInventory,
    deleteInventory,
    addItem,
    updateItem,
    deleteItem,
  }
})
