import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface Usuario {
  id: number
  nome: string
  email: string
}

export const useAuthStore = defineStore('auth', () => {
  const usuario = ref<Usuario | null>(null)
  const token = ref<string | null>(localStorage.getItem('bk_token'))
  const loading = ref(false)
  const error = ref<string | null>(null)

  const isLoggedIn = computed(() => !!token.value && !!usuario.value)

  function setToken(t: string) {
    token.value = t
    localStorage.setItem('bk_token', t)
  }

  function clearSession() {
    usuario.value = null
    token.value = null
    localStorage.removeItem('bk_token')
  }

  function authHeaders(): Record<string, string> {
    return token.value ? { Authorization: `Bearer ${token.value}` } : {}
  }

  async function login(email: string, senha: string) {
    loading.value = true
    error.value = null
    try {
      const res = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, senha }),
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail ?? 'E-mail ou senha inválidos.')
      }
      const data = await res.json()
      setToken(data.access_token)
      usuario.value = data.usuario
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Erro desconhecido.'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function cadastrar(nome: string, email: string, senha: string) {
    loading.value = true
    error.value = null
    try {
      const res = await fetch('/api/v1/auth/cadastro', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nome, email, senha }),
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail ?? 'Erro ao criar conta.')
      }
      const data = await res.json()
      setToken(data.access_token)
      usuario.value = data.usuario
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Erro desconhecido.'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchMe() {
    if (!token.value) return
    try {
      const res = await fetch('/api/v1/usuarios/me', { headers: authHeaders() })
      if (!res.ok) { clearSession(); return }
      usuario.value = await res.json()
    } catch {
      clearSession()
    }
  }

  function logout() { clearSession() }

  return { usuario, token, loading, error, isLoggedIn, authHeaders, login, cadastrar, fetchMe, logout }
})
