/** Store de Quests e Graph View (Pinia). */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/api/client'
import { useWorldsStore } from './worlds'
import type { Visibility } from './articles'

export type QuestStatus = 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED' | 'ON_HOLD'
export type QuestCategory = 'MAIN_QUEST' | 'SIDE_QUEST' | 'MONSTER_HUNT' | 'ARTIFACT_SEARCH' | 'OUTPOST' | 'FACTION'

export interface QuestObjective {
  id: string
  description: string
  is_completed: boolean
  order_index: number
}

export interface Quest {
  id: string
  world_id: string
  title: string
  description: string
  category: QuestCategory
  status: QuestStatus
  visibility: Visibility
  rewards?: string | null
  article_id?: string | null
  article_title?: string | null
  objectives: QuestObjective[]
  created_by: string
  created_at: string
  updated_at: string
  is_locked: boolean
}

export interface GraphNode {
  id: string
  label: string
  type: 'ARTICLE' | 'QUEST' | 'MAP' | 'PIN'
  category?: string | null
  visibility: Visibility
  is_locked: boolean
}

export interface GraphEdge {
  id: string
  source: string
  target: string
  label?: string | null
}

export interface WorldGraph {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export const useQuestsStore = defineStore('quests', () => {
  const quests = ref<Quest[]>([])
  const currentGraph = ref<WorldGraph>({ nodes: [], edges: [] })
  const loading = ref(false)
  const searchQuery = ref('')
  const categoryFilter = ref<string>('')
  const statusFilter = ref<string>('')

  function wid() { return useWorldsStore().activeWorld?.id }

  async function fetchQuests() {
    const worldId = wid(); if (!worldId) return
    loading.value = true
    try {
      const params: Record<string, string> = {}
      if (searchQuery.value) params.search = searchQuery.value
      if (categoryFilter.value) params.category = categoryFilter.value
      if (statusFilter.value) params.status = statusFilter.value
      const { data } = await api.get<Quest[]>(`/worlds/${worldId}/quests/`, { params })
      quests.value = data
    } finally { loading.value = false }
  }

  async function createQuest(payload: Partial<Quest>) {
    const worldId = wid(); if (!worldId) return
    const { data } = await api.post<Quest>(`/worlds/${worldId}/quests/`, payload)
    quests.value.unshift(data)
    return data
  }

  async function updateQuest(id: string, payload: Partial<Quest>) {
    const worldId = wid(); if (!worldId) return
    const { data } = await api.put<Quest>(`/worlds/${worldId}/quests/${id}`, payload)
    const idx = quests.value.findIndex((q) => q.id === id)
    if (idx !== -1) quests.value[idx] = data
    return data
  }

  async function deleteQuest(id: string) {
    const worldId = wid(); if (!worldId) return
    await api.delete(`/worlds/${worldId}/quests/${id}`)
    quests.value = quests.value.filter((q) => q.id !== id)
  }

  async function toggleObjective(questId: string, objectiveId: string) {
    const worldId = wid(); if (!worldId) return
    const { data } = await api.patch<QuestObjective>(
      `/worlds/${worldId}/quests/${questId}/objectives/${objectiveId}/toggle`
    )
    const q = quests.value.find((item) => item.id === questId)
    if (q) {
      const obj = q.objectives.find((o) => o.id === objectiveId)
      if (obj) obj.is_completed = data.is_completed
    }
    return data
  }

  async function fetchWorldGraph() {
    const worldId = wid(); if (!worldId) return
    loading.value = true
    try {
      const { data } = await api.get<WorldGraph>(`/worlds/${worldId}/graph/`)
      currentGraph.value = data
      return data
    } finally { loading.value = false }
  }

  return {
    quests, currentGraph, loading, searchQuery, categoryFilter, statusFilter,
    fetchQuests, createQuest, updateQuest, deleteQuest, toggleObjective, fetchWorldGraph,
  }
})
