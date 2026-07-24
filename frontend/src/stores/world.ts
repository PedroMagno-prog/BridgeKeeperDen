import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiFetch } from '../services/api'

export interface World {
  id: string
  name: string
  description?: string
  owner_id: string
  user_role?: 'MESTRE' | 'JOGADOR'
  created_at: string
}

export const useWorldStore = defineStore('world', () => {
  const worlds = ref<World[]>([])
  const activeWorldId = ref<string | null>(localStorage.getItem('activeWorldId'))
  const loading = ref(false)

  const activeWorld = computed(() =>
    worlds.value.find((w) => w.id === activeWorldId.value) || null
  )

  const activeUserRole = computed(() => activeWorld.value?.user_role || 'JOGADOR')

  async function fetchWorlds() {
    loading.value = true
    try {
      worlds.value = await apiFetch<World[]>('/worlds')
      const firstWorld = worlds.value[0]
      if (!activeWorldId.value && firstWorld) {
        selectWorld(firstWorld.id)
      }
    } finally {
      loading.value = false
    }
  }

  async function createWorld(name: string, description?: string) {
    loading.value = true
    try {
      const newWorld = await apiFetch<World>('/worlds', {
        method: 'POST',
        body: JSON.stringify({ name, description }),
      })
      worlds.value.push(newWorld)
      selectWorld(newWorld.id)
      return newWorld
    } finally {
      loading.value = false
    }
  }

  function selectWorld(id: string) {
    activeWorldId.value = id
    localStorage.setItem('activeWorldId', id)
  }

  return {
    worlds,
    activeWorldId,
    activeWorld,
    activeUserRole,
    loading,
    fetchWorlds,
    createWorld,
    selectWorld,
  }
})
