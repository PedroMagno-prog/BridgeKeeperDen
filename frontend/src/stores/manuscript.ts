import { defineStore } from 'pinia'
import { ref } from 'vue'
import { apiFetch } from '../services/api'

export interface ManuscriptChapter {
  id: string
  manuscript_id: string
  title: string
  content: string
  order_index: number
  visibility: 'TOTAL' | 'PARCIAL' | 'NULA'
  is_locked: boolean
}

export interface Manuscript {
  id: string
  world_id: string
  title: string
  created_by: string
  created_at: string
  chapters: ManuscriptChapter[]
}

export const useManuscriptStore = defineStore('manuscript', () => {
  const manuscripts = ref<Manuscript[]>([])
  const currentManuscript = ref<Manuscript | null>(null)
  const currentChapters = ref<ManuscriptChapter[]>([])
  const loading = ref(false)

  async function fetchManuscripts(worldId: string) {
    loading.value = true
    try {
      manuscripts.value = await apiFetch<Manuscript[]>(`/worlds/${worldId}/manuscripts`)
    } finally {
      loading.value = false
    }
  }

  async function createManuscript(worldId: string, title: string) {
    loading.value = true
    try {
      const newMs = await apiFetch<Manuscript>(`/worlds/${worldId}/manuscripts`, {
        method: 'POST',
        body: JSON.stringify({ title }),
      })
      manuscripts.value.push(newMs)
      return newMs
    } finally {
      loading.value = false
    }
  }

  async function fetchChapters(worldId: string, manuscriptId: string) {
    loading.value = true
    try {
      currentChapters.value = await apiFetch<ManuscriptChapter[]>(
        `/worlds/${worldId}/manuscripts/${manuscriptId}/chapters`
      )
    } finally {
      loading.value = false
    }
  }

  async function createChapter(worldId: string, manuscriptId: string, payload: any) {
    const newCh = await apiFetch<ManuscriptChapter>(
      `/worlds/${worldId}/manuscripts/${manuscriptId}/chapters`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      }
    )
    currentChapters.value.push(newCh)
    return newCh
  }

  return {
    manuscripts,
    currentManuscript,
    currentChapters,
    loading,
    fetchManuscripts,
    createManuscript,
    fetchChapters,
    createChapter,
  }
})
