import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useAuthStore } from './auth'

export interface Personagem {
  id: number
  nome: string
  classe: string
  raca: string
  jogador_id: number
}

export const usePersonagensStore = defineStore('personagens', () => {
  const lista = ref<Personagem[]>([])
  const loading = ref(false)
  const saving = ref(false)
  const error = ref<string | null>(null)

  async function fetchPersonagens() {
    const auth = useAuthStore()
    loading.value = true
    error.value = null
    try {
      const res = await fetch('/api/v1/personagens/', { headers: auth.authHeaders() })
      if (!res.ok) throw new Error('Erro ao carregar personagens.')
      lista.value = await res.json()
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Erro desconhecido.'
    } finally {
      loading.value = false
    }
  }

  async function criarPersonagem(payload: { nome: string; classe: string; raca: string }) {
    const auth = useAuthStore()
    saving.value = true
    error.value = null
    try {
      const res = await fetch('/api/v1/personagens/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...auth.authHeaders() },
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail ?? 'Erro ao criar personagem.')
      }
      const novo: Personagem = await res.json()
      lista.value.push(novo)
      return novo
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Erro desconhecido.'
      throw e
    } finally {
      saving.value = false
    }
  }

  async function atualizarPersonagem(
    id: number,
    payload: Partial<{ nome: string; classe: string; raca: string }>,
  ) {
    const auth = useAuthStore()
    saving.value = true
    error.value = null
    try {
      const res = await fetch(`/api/v1/personagens/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', ...auth.authHeaders() },
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail ?? 'Erro ao atualizar personagem.')
      }
      const atualizado: Personagem = await res.json()
      const idx = lista.value.findIndex((p) => p.id === id)
      if (idx !== -1) lista.value[idx] = atualizado
      return atualizado
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Erro desconhecido.'
      throw e
    } finally {
      saving.value = false
    }
  }

  async function deletarPersonagem(id: number) {
    const auth = useAuthStore()
    error.value = null
    try {
      const res = await fetch(`/api/v1/personagens/${id}`, {
        method: 'DELETE',
        headers: auth.authHeaders(),
      })
      if (!res.ok) throw new Error('Erro ao deletar personagem.')
      lista.value = lista.value.filter((p) => p.id !== id)
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Erro desconhecido.'
    }
  }

  function reset() {
    lista.value = []
    error.value = null
  }

  return { lista, loading, saving, error, fetchPersonagens, criarPersonagem, atualizarPersonagem, deletarPersonagem, reset }
})
