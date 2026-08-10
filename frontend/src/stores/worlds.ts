/**
 * Store de Mundos (Pinia).
 * Gerencia a lista de mundos e o mundo ativo.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api/client'

export interface World {
  id: string
  name: string
  description: string
  owner_id: string
  created_at: string
  role: 'MESTRE' | 'JOGADOR'
}

export const useWorldsStore = defineStore('worlds', () => {
  const worlds = ref<World[]>([])
  const activeWorld = ref<World | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const isMestre = computed(() => activeWorld.value?.role === 'MESTRE')

  async function fetchWorlds() {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.get<World[]>('/worlds/')
      worlds.value = data
      // Restaurar mundo ativo da sessão
      const savedId = localStorage.getItem('bk_active_world')
      if (savedId) {
        activeWorld.value = data.find((w) => w.id === savedId) ?? data[0] ?? null
      } else {
        activeWorld.value = data[0] ?? null
      }
    } catch (e: any) {
      error.value = e.response?.data?.detail ?? 'Erro ao carregar mundos'
    } finally {
      loading.value = false
    }
  }

  async function createWorld(name: string, description: string) {
    const { data } = await api.post<World>('/worlds/', { name, description })
    worlds.value.unshift(data)
    return data
  }

  function setActiveWorld(world: World) {
    activeWorld.value = world
    localStorage.setItem('bk_active_world', world.id)
  }

  return { worlds, activeWorld, loading, error, isMestre, fetchWorlds, createWorld, setActiveWorld }
})
