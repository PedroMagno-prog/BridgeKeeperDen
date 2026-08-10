/** Store de Timeline (Pinia). */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/api/client'
import { useWorldsStore } from './worlds'
import type { Visibility } from './articles'

export interface TimelineEra { id: string; title: string; start_sort_order: number; end_sort_order: number }
export interface TimelineEvent {
  article_id: string; title: string
  in_game_date: string | null; in_game_sort_order: number | null
  visibility: Visibility; is_locked: boolean
}

export const useTimelineStore = defineStore('timeline', () => {
  const eras = ref<TimelineEra[]>([])
  const events = ref<TimelineEvent[]>([])
  const loading = ref(false)

  function wid() { return useWorldsStore().activeWorld?.id }

  async function fetchTimeline() {
    const worldId = wid(); if (!worldId) return
    loading.value = true
    try {
      const { data } = await api.get(`/worlds/${worldId}/timeline/`)
      eras.value = data.eras
      events.value = data.timeline_events
    } finally { loading.value = false }
  }

  async function createEra(title: string, start_sort_order: number, end_sort_order: number) {
    const worldId = wid(); if (!worldId) return
    const { data } = await api.post<TimelineEra>(`/worlds/${worldId}/timeline/eras`, { title, start_sort_order, end_sort_order })
    eras.value.push(data)
    eras.value.sort((a, b) => a.start_sort_order - b.start_sort_order)
    return data
  }

  async function deleteEra(eraId: string) {
    const worldId = wid(); if (!worldId) return
    await api.delete(`/worlds/${worldId}/timeline/eras/${eraId}`)
    eras.value = eras.value.filter((e) => e.id !== eraId)
  }

  return { eras, events, loading, fetchTimeline, createEra, deleteEra }
})
