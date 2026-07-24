import { defineStore } from 'pinia'
import { ref } from 'vue'
import { apiFetch } from '../services/api'

export interface TimelineEra {
  id: string
  world_id: string
  title: string
  start_sort_order: number
  end_sort_order: number
}

export interface TimelineEvent {
  article_id: string
  title: string
  in_game_date?: string
  in_game_sort_order?: number
  visibility: 'TOTAL' | 'PARCIAL' | 'NULA'
  snippet?: string
  is_locked: boolean
}

export interface TimelineData {
  eras: TimelineEra[]
  timeline_events: TimelineEvent[]
}

export const useTimelineStore = defineStore('timeline', () => {
  const timelineData = ref<TimelineData>({ eras: [], timeline_events: [] })
  const loading = ref(false)

  async function fetchTimeline(worldId: string) {
    loading.value = true
    try {
      timelineData.value = await apiFetch<TimelineData>(`/worlds/${worldId}/timeline`)
    } finally {
      loading.value = false
    }
  }

  return { timelineData, loading, fetchTimeline }
})
