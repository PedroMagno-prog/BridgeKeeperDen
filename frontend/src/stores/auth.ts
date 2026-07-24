import { defineStore } from 'pinia'
import { ref } from 'vue'
import { apiFetch } from '../services/api'

export interface User {
  id: string
  username: string
  email: string
  created_at: string
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))
  const loading = ref(false)

  async function login(email: string, password: string) {
    loading.value = true
    try {
      const data = await apiFetch<{ access_token: string }>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      })
      token.value = data.access_token
      localStorage.setItem('token', data.access_token)
      await fetchMe()
    } finally {
      loading.value = false
    }
  }

  async function register(username: string, email: string, password: string) {
    loading.value = true
    try {
      await apiFetch<User>('/auth/register', {
        method: 'POST',
        body: JSON.stringify({ username, email, password }),
      })
      await login(email, password)
    } finally {
      loading.value = false
    }
  }

  async function fetchMe() {
    if (!token.value) return
    try {
      user.value = await apiFetch<User>('/auth/me')
    } catch {
      logout()
    }
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    window.location.href = '/login'
  }

  return { user, token, loading, login, register, fetchMe, logout }
})
