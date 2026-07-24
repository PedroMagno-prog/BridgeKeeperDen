import { defineStore } from 'pinia'
import { ref } from 'vue'
import { apiFetch } from '../services/api'

export interface MapLayer {
  id: string
  map_id: string
  name: string
  is_default_active: boolean
}

export interface MapPin {
  id: string
  map_id: string
  layer_id?: string
  target_article_id?: string
  target_map_id?: string
  title: string
  x_position: number
  y_position: number
  icon: string
  color: string
  visibility: 'TOTAL' | 'PARCIAL' | 'NULA'
  is_locked: boolean
}

export interface MapData {
  id: string
  world_id: string
  title: string
  image_url: string
  created_at: string
  layers: MapLayer[]
  pins: MapPin[]
}

export const useMapStore = defineStore('map', () => {
  const maps = ref<MapData[]>([])
  const currentMap = ref<MapData | null>(null)
  const loading = ref(false)

  async function fetchMaps(worldId: string) {
    loading.value = true
    try {
      maps.value = await apiFetch<MapData[]>(`/worlds/${worldId}/maps`)
    } finally {
      loading.value = false
    }
  }

  async function fetchMapById(worldId: string, mapId: string) {
    loading.value = true
    try {
      currentMap.value = await apiFetch<MapData>(`/worlds/${worldId}/maps/${mapId}`)
    } finally {
      loading.value = false
    }
  }

  async function createMap(worldId: string, payload: { title: string; image_url: string }) {
    loading.value = true
    try {
      const newMap = await apiFetch<MapData>(`/worlds/${worldId}/maps`, {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      maps.value.push(newMap)
      return newMap
    } finally {
      loading.value = false
    }
  }

  async function createPin(worldId: string, mapId: string, pin: any) {
    const newPin = await apiFetch<MapPin>(`/worlds/${worldId}/maps/${mapId}/pins`, {
      method: 'POST',
      body: JSON.stringify(pin),
    })
    if (currentMap.value && currentMap.value.id === mapId) {
      currentMap.value.pins.push(newPin)
    }
    return newPin
  }

  async function updatePin(worldId: string, mapId: string, pinId: string, pin: any) {
    const updatedPin = await apiFetch<MapPin>(`/worlds/${worldId}/maps/${mapId}/pins/${pinId}`, {
      method: 'PUT',
      body: JSON.stringify(pin),
    })
    if (currentMap.value && currentMap.value.id === mapId) {
      const idx = currentMap.value.pins.findIndex((p) => p.id === pinId)
      if (idx !== -1) currentMap.value.pins[idx] = updatedPin
    }
    return updatedPin
  }

  return {
    maps,
    currentMap,
    loading,
    fetchMaps,
    fetchMapById,
    createMap,
    createPin,
    updatePin,
  }
})
