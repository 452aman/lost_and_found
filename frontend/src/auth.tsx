import { useQuery, useQueryClient } from '@tanstack/react-query'
import { createContext, useContext, type ReactNode } from 'react'
import { api, tokens } from './api'
import type { User } from './types'

interface AuthCtx {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}
const Ctx = createContext<AuthCtx>(null!)
export const useAuth = () => useContext(Ctx)

export function AuthProvider({ children }: { children: ReactNode }) {
  const qc = useQueryClient()
  const { data: user, isLoading } = useQuery({
    queryKey: ['me'],
    queryFn: async () => (await api.get<User>('/auth/me')).data,
    enabled: !!tokens.access,
    retry: false,
  })

  const login = async (email: string, password: string) => {
    const body = new URLSearchParams({ username: email, password })
    const r = await api.post('/auth/login', body)
    tokens.set(r.data.access_token, r.data.refresh_token)
    await qc.invalidateQueries({ queryKey: ['me'] })
  }
  const logout = () => { tokens.clear(); qc.clear(); window.location.href = '/login' }

  return <Ctx.Provider value={{ user: user ?? null, loading: !!tokens.access && isLoading, login, logout }}>{children}</Ctx.Provider>
}
