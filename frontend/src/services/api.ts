const BASE_URL = '/api/v1'

export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem('token')
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  let response: Response
  try {
    response = await fetch(`${BASE_URL}${endpoint}`, {
      ...options,
      headers,
    })
  } catch (err: any) {
    throw new Error('Não foi possível conectar ao servidor backend (offline ou erro de rede).')
  }

  if (response.status === 401) {
    localStorage.removeItem('token')
    if (window.location.pathname !== '/login') {
      window.location.href = '/login'
    }
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => null)
    let message = 'Ocorreu um erro na requisição.'

    if (errorData && errorData.detail) {
      if (typeof errorData.detail === 'string') {
        message = errorData.detail
      } else if (Array.isArray(errorData.detail)) {
        message = errorData.detail.map((errItem: any) => errItem.msg || JSON.stringify(errItem)).join('; ')
      } else if (typeof errorData.detail === 'object') {
        message = JSON.stringify(errorData.detail)
      }
    } else if (response.status === 502 || response.status === 504) {
      message = 'O servidor backend (port 8000) está inacessível (502/504 Gateway Error).'
    } else if (response.statusText) {
      message = `Erro ${response.status}: ${response.statusText}`
    }

    throw new Error(message)
  }

  if (response.status === 204) {
    return {} as T
  }

  return response.json()
}
