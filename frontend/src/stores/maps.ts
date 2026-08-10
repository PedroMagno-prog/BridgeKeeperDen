/** Store de Mapas (Pinia). */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/api/client'
import { useWorldsStore } from './worlds'
import type { Visibility } from './articles'

export interface MapLayer { id: string; name: string; is_default_active: boolean }
export interface MapPin {
  id: string; title: string
  x_position: number; y_position: number
  icon: string; color: string
  visibility: Visibility
  layer_id: string | null
  target_article_id: string | null
  target_map_id: string | null
  is_locked: boolean
}
export interface MapItem { id: string; title: string; image_url: string; created_at: string }
export interface MapDetail extends MapItem { layers: MapLayer[]; pins: MapPin[] }

export const useMapsStore = defineStore('maps', () => {
  const maps = ref<MapItem[]>([])
  const current = ref<MapDetail | null>(null)
  const activeLayers = ref<Set<string>>(new Set())
  const loading = ref(false)

  function wid() { return useWorldsStore().activeWorld?.id }

  async function fetchMaps() {
    const worldId = wid(); if (!worldId) return
    loading.value = true
    try {
      const { data } = await api.get<MapItem[]>(`/worlds/${worldId}/maps/`)
      maps.value = data
    } finally { loading.value = false }
  }

  async function fetchMap(id: string) {
    const worldId = wid(); if (!worldId) return
    const { data } = await api.get<MapDetail>(`/worlds/${worldId}/maps/${id}`)
    current.value = data
    // Ativar layers padrão
    activeLayers.value = new Set(data.layers.filter((l) => l.is_default_active).map((l) => l.id))
    return data
  }

  async function createMap(title: string, image_url: string) {
    const worldId = wid(); if (!worldId) return
    const { data } = await api.post<MapItem>(`/worlds/${worldId}/maps/`, { title, image_url })
    maps.value.unshift(data)
    return data
  }

  async function createPin(mapId: string, payload: Partial<MapPin>) {
    const worldId = wid(); if (!worldId) return
    const { data } = await api.post<MapPin>(`/worlds/${worldId}/maps/${mapId}/pins`, payload)
    current.value?.pins.push(data)
    return data
  }

  async function updatePin(mapId: string, pinId: string, payload: Partial<MapPin>) {
    const worldId = wid(); if (!worldId) return
    const { data } = await api.put<MapPin>(`/worlds/${worldId}/maps/${mapId}/pins/${pinId}`, payload)
    if (current.value) {
      const idx = current.value.pins.findIndex((p) => p.id === pinId)
      if (idx !== -1) current.value.pins[idx] = data
    }
    return data
  }

  function toggleLayer(layerId: string) {
    if (activeLayers.value.has(layerId)) activeLayers.value.delete(layerId)
    else activeLayers.value.add(layerId)
  }

  return { maps, current, activeLayers, loading, fetchMaps, fetchMap, createMap, createPin, updatePin, toggleLayer }
})
