import axios from 'axios'

const ACCESS = 'lf_access'
const REFRESH = 'lf_refresh'

export const tokens = {
  get access() { return localStorage.getItem(ACCESS) },
  set(access: string, refresh: string) { localStorage.setItem(ACCESS, access); localStorage.setItem(REFRESH, refresh) },
  clear() { localStorage.removeItem(ACCESS); localStorage.removeItem(REFRESH) },
  get refresh() { return localStorage.getItem(REFRESH) },
}

export const api = axios.create({ baseURL: '/api/v1' })

api.interceptors.request.use((cfg) => {
  if (tokens.access) cfg.headers.Authorization = `Bearer ${tokens.access}`
  return cfg
})

// One in-flight refresh shared by all requests that hit a 401 at the same time.
let refreshing: Promise<string> | null = null

api.interceptors.response.use(
  (r) => r,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retried && tokens.refresh && !original.url?.includes('/auth/')) {
      original._retried = true
      refreshing ??= axios
        .post('/api/v1/auth/refresh', { refresh_token: tokens.refresh })
        .then((r) => { tokens.set(r.data.access_token, r.data.refresh_token); return r.data.access_token as string })
        .finally(() => { refreshing = null })
      try {
        const access = await refreshing
        original.headers.Authorization = `Bearer ${access}`
        return api(original)
      } catch {
        tokens.clear()
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  },
)

export const errMsg = (e: unknown): string => {
  const d = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d)) return d.map((x) => x.msg).join('; ')
  return 'Something went wrong'
}
