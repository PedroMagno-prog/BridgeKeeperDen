/**
 * API client com axios e interceptor JWT automático.
 */
import axios from 'axios'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

// Injeta o token JWT em todas as requisições autenticadas
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('bk_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Redireciona para login em caso de 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('bk_token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  },
)
