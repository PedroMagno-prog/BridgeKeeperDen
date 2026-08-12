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
  invite_code: string
  owner_id: string
  created_at: string
  role: 'MESTRE' | 'JOGADOR'
}

export interface WorldMemberDetail {
  id: string
  user_id: string
  username: string
  email: string
  role: 'MESTRE' | 'JOGADOR'
  joined_at?: string
}

export interface WorldInviteInfo {
  invite_code: string
  world_id: string
  world_name: string
  world_description: string | null
  owner_username: string
  members_count: number
}

export const useWorldsStore = defineStore('worlds', () => {
  const worlds = ref<World[]>([])
  const activeWorld = ref<World | null>(null)
  const members = ref<WorldMemberDetail[]>([])
  const inviteInfo = ref<WorldInviteInfo | null>(null)
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

  async function fetchMembers(worldId: string) {
    const { data } = await api.get<WorldMemberDetail[]>(`/worlds/${worldId}/members`)
    members.value = data
    return data
  }

  async function fetchInviteInfo(code: string) {
    const { data } = await api.get<WorldInviteInfo>(`/worlds/invite-info/${code}`)
    inviteInfo.value = data
    return data
  }

  async function joinWorld(code: string) {
    const { data } = await api.post<World>(`/worlds/join/${code}`)
    const existing = worlds.value.find((w) => w.id === data.id)
    if (!existing) {
      worlds.value.unshift(data)
    }
    setActiveWorld(data)
    return data
  }

  async function rotateInviteCode(worldId: string) {
    const { data } = await api.post<{ invite_code: string }>(`/worlds/${worldId}/rotate-invite`)
    if (activeWorld.value && activeWorld.value.id === worldId) {
      activeWorld.value.invite_code = data.invite_code
    }
    const target = worlds.value.find((w) => w.id === worldId)
    if (target) target.invite_code = data.invite_code
    return data.invite_code
  }

  async function addMemberDirect(worldId: string, emailOrUsername: string, role: 'MESTRE' | 'JOGADOR' = 'JOGADOR') {
    const { data } = await api.post<WorldMemberDetail>(`/worlds/${worldId}/members`, {
      user_id_or_email: emailOrUsername,
      role,
    })
    members.value.push(data)
    return data
  }

  async function updateMemberRole(worldId: string, userId: string, role: 'MESTRE' | 'JOGADOR') {
    const { data } = await api.put<WorldMemberDetail>(`/worlds/${worldId}/members/${userId}/role`, { role })
    const m = members.value.find((item) => item.user_id === userId)
    if (m) m.role = data.role
    return data
  }

  async function removeMember(worldId: string, userId: string) {
    await api.delete(`/worlds/${worldId}/members/${userId}`)
    members.value = members.value.filter((m) => m.user_id !== userId)
  }

  return {
    worlds, activeWorld, members, inviteInfo, loading, error, isMestre,
    fetchWorlds, createWorld, setActiveWorld, fetchMembers, fetchInviteInfo,
    joinWorld, rotateInviteCode, addMemberDirect, updateMemberRole, removeMember,
  }
})
