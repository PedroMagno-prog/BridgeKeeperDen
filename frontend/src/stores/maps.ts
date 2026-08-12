/** Store de Mapas (Pinia). */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/api/client'
import { useWorldsStore } from './worlds'
import type { Visibility } from './articles'

export interface MapBreadcrumb {
  id: string
  title: string
}

export interface MapLayer { id: string; name: string; is_default_active: boolean }

export interface MapPinArticleSummary {
  id: string
  title: string
  visibility: Visibility
  tags: string[]
  first_section_preview?: string | null
}

export interface MapPin {
  id: string; title: string
  x_position: number; y_position: number
  icon: string; color: string
  visibility: Visibility
  layer_id: string | null
  target_article_id: string | null
  target_map_id: string | null
  target_article?: MapPinArticleSummary | null
  target_map_title?: string | null
  is_locked: boolean
}

export interface MapItem { id: string; title: string; image_url: string; created_at: string }
export interface MapDetail extends MapItem { layers: MapLayer[]; pins: MapPin[] }

export const useMapsStore = defineStore('maps', () => {
  const maps = ref<MapItem[]>([])
  const current = ref<MapDetail | null>(null)
  const breadcrumbs = ref<MapBreadcrumb[]>([])
  const activeLayers = ref<Set<string>>(new Set())
  const loading = ref(false)

  function wid() { return useWorldsStore().activeWorld?.id }

  function pushBreadcrumb(item: MapBreadcrumb) {
    const idx = breadcrumbs.value.findIndex((b) => b.id === item.id)
    if (idx !== -1) {
      breadcrumbs.value = breadcrumbs.value.slice(0, idx + 1)
    } else {
      breadcrumbs.value.push(item)
    }
  }

  function clearBreadcrumbs() {
    breadcrumbs.value = []
  }

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
    pushBreadcrumb({ id: data.id, title: data.title })
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

  async function updateMap(mapId: string, payload: { title?: string; image_url?: string }) {
    const worldId = wid(); if (!worldId) return
    const { data } = await api.put<MapItem>(`/worlds/${worldId}/maps/${mapId}`, payload)
    const idx = maps.value.findIndex((m) => m.id === mapId)
    if (idx !== -1) maps.value[idx] = data
    if (current.value?.id === mapId) {
      current.value.title = data.title
      current.value.image_url = data.image_url
    }
    return data
  }

  async function deleteMap(mapId: string) {
    const worldId = wid(); if (!worldId) return
    await api.delete(`/worlds/${worldId}/maps/${mapId}`)
    maps.value = maps.value.filter((m) => m.id !== mapId)
    if (current.value?.id === mapId) current.value = null
  }

  async function createLayer(mapId: string, name: string, is_default_active: boolean = true) {
    const worldId = wid(); if (!worldId) return
    const { data } = await api.post<MapLayer>(`/worlds/${worldId}/maps/${mapId}/layers`, { name, is_default_active })
    if (current.value) current.value.layers.push(data)
    activeLayers.value.add(data.id)
    return data
  }

  async function deleteLayer(mapId: string, layerId: string) {
    const worldId = wid(); if (!worldId) return
    await api.delete(`/worlds/${worldId}/maps/${mapId}/layers/${layerId}`)
    if (current.value) {
      current.value.layers = current.value.layers.filter((l) => l.id !== layerId)
    }
    activeLayers.value.delete(layerId)
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

  async function updatePinPosition(mapId: string, pinId: string, x: number, y: number) {
    return updatePin(mapId, pinId, { x_position: x, y_position: y })
  }

  async function deletePin(mapId: string, pinId: string) {
    const worldId = wid(); if (!worldId) return
    await api.delete(`/worlds/${worldId}/maps/${mapId}/pins/${pinId}`)
    if (current.value) {
      current.value.pins = current.value.pins.filter((p) => p.id !== pinId)
    }
  }

  function toggleLayer(layerId: string) {
    if (activeLayers.value.has(layerId)) activeLayers.value.delete(layerId)
    else activeLayers.value.add(layerId)
  }

  return {
    maps, current, breadcrumbs, activeLayers, loading,
    fetchMaps, fetchMap, createMap, updateMap, deleteMap,
    createLayer, deleteLayer, createPin, updatePin, updatePinPosition, deletePin, toggleLayer,
    pushBreadcrumb, clearBreadcrumbs,
  }
})
