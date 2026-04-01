import axios from 'axios'
import type { StartRequest, StartResponse, HealthResponse, HistoryItem } from '@/types/api'
import { useSettingsStore } from '@/store/settingsStore'

// Read baseURL lazily so Settings changes take effect without a page reload
function getBaseUrl(): string {
  const url = useSettingsStore.getState().apiBaseUrl
  return url.replace(/\/$/, '')
}

const client = axios.create({ timeout: 30_000 })

client.interceptors.request.use((config) => {
  config.baseURL = getBaseUrl()
  return config
})

export interface ApiError {
  message: string
  status?: number
}

client.interceptors.response.use(
  (res) => res,
  (err: unknown) => {
    if (axios.isAxiosError(err)) {
      const message = (err.response?.data as { detail?: string })?.detail ?? err.message
      const error: ApiError = { message, status: err.response?.status }
      return Promise.reject(error)
    }
    return Promise.reject({ message: 'Unknown error' } as ApiError)
  }
)

export const supportApi = {
  start: async (data: StartRequest): Promise<StartResponse> => {
    const res = await client.post<StartResponse>('/support/start', data)
    return res.data
  },

  history: async (conversationId: string): Promise<HistoryItem[]> => {
    const res = await client.get<HistoryItem[]>(`/support/history/${conversationId}`)
    return res.data
  },

  deleteHistory: async (conversationId: string): Promise<{ status: string; message: string }> => {
    const res = await client.delete<{ status: string; message: string }>(`/support/history/${conversationId}`)
    return res.data
  },

  health: async (): Promise<HealthResponse> => {
    const res = await client.get<HealthResponse>('/health')
    return res.data
  },
}
