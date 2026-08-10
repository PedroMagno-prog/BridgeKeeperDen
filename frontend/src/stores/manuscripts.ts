/** Store de Manuscritos (Pinia). */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/api/client'
import { useWorldsStore } from './worlds'
import type { Visibility } from './articles'

export interface Manuscript { id: string; title: string; created_by: string; created_at: string }
export interface Chapter {
  id: string; title: string; content: string
  order_index: number; visibility: Visibility; is_locked: boolean
}

export const useManuscriptsStore = defineStore('manuscripts', () => {
  const manuscripts = ref<Manuscript[]>([])
  const currentManuscript = ref<Manuscript | null>(null)
  const chapters = ref<Chapter[]>([])
  const loading = ref(false)

  function wid() { return useWorldsStore().activeWorld?.id }

  async function fetchManuscripts() {
    const worldId = wid(); if (!worldId) return
    loading.value = true
    try {
      const { data } = await api.get<Manuscript[]>(`/worlds/${worldId}/manuscripts/`)
      manuscripts.value = data
    } finally { loading.value = false }
  }

  async function createManuscript(title: string) {
    const worldId = wid(); if (!worldId) return
    const { data } = await api.post<Manuscript>(`/worlds/${worldId}/manuscripts/`, { title })
    manuscripts.value.unshift(data)
    return data
  }

  async function fetchChapters(manuscriptId: string) {
    const worldId = wid(); if (!worldId) return
    loading.value = true
    try {
      const { data } = await api.get<Chapter[]>(`/worlds/${worldId}/manuscripts/${manuscriptId}/chapters`)
      chapters.value = data
    } finally { loading.value = false }
  }

  async function createChapter(manuscriptId: string, payload: Partial<Chapter>) {
    const worldId = wid(); if (!worldId) return
    const { data } = await api.post<Chapter>(`/worlds/${worldId}/manuscripts/${manuscriptId}/chapters`, payload)
    chapters.value.push(data)
    chapters.value.sort((a, b) => a.order_index - b.order_index)
    return data
  }

  function selectManuscript(ms: Manuscript) {
    currentManuscript.value = ms
    chapters.value = []
    fetchChapters(ms.id)
  }

  async function updateChapter(manuscriptId: string, chapterId: string, payload: Partial<Chapter>) {
    const worldId = wid(); if (!worldId) return
    const { data } = await api.put<Chapter>(`/worlds/${worldId}/manuscripts/${manuscriptId}/chapters/${chapterId}`, payload)
    const idx = chapters.value.findIndex((c) => c.id === chapterId)
    if (idx !== -1) chapters.value[idx] = data
    return data
  }

  return {
    manuscripts, currentManuscript, chapters, loading,
    fetchManuscripts, createManuscript, fetchChapters, createChapter, selectManuscript, updateChapter,
  }
})

