import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api/client'

export interface User {
  id: string
  username: string
  email: string
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('bk_token'))
  const loading = ref(false)
  const error = ref<string | null>(null)

  const isLoggedIn = computed(() => !!token.value && !!user.value)

  function setToken(t: string) {
    token.value = t
    localStorage.setItem('bk_token', t)
  }

  function clearSession() {
    user.value = null
    token.value = null
    localStorage.removeItem('bk_token')
    localStorage.removeItem('bk_active_world')
  }

  async function login(email: string, password: string) {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.post('/auth/login', { email, password })
      setToken(data.access_token)
      user.value = data.user
    } catch (e: any) {
      error.value = e.response?.data?.detail ?? 'E-mail ou senha inválidos.'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function register(username: string, email: string, password: string) {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.post('/auth/register', { username, email, password })
      setToken(data.access_token)
      user.value = data.user
    } catch (e: any) {
      error.value = e.response?.data?.detail ?? 'Erro ao criar conta.'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchMe() {
    if (!token.value) return
    try {
      const { data } = await api.get('/users/me')
      user.value = data
    } catch {
      clearSession()
    }
  }

  function authHeaders(): Record<string, string> {
    return token.value ? { Authorization: `Bearer ${token.value}` } : {}
  }

  function logout() { clearSession() }

  return { user, token, loading, error, isLoggedIn, authHeaders, login, register, fetchMe, logout }
})
