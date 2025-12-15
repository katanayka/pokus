import React, { createContext, useCallback, useContext, useMemo, useRef, useState } from 'react'

import { decodeJwt } from '@/lib/jwt'
import { clearTokens, loadTokens, saveTokens, type Tokens } from '@/lib/storage'

type User = {
  userId: number
  username?: string
}

type LoginResult = { access: string; refresh: string }
type RefreshResult = { access: string; refresh?: string }

type AuthContextValue = {
  tokens: Tokens | null
  user: User | null
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  apiFetch: <T = unknown>(path: string, init?: RequestInit) => Promise<T>
  apiFetchNoAuth: <T = unknown>(path: string, init?: RequestInit) => Promise<T>
}

const AuthContext = createContext<AuthContextValue | null>(null)

function apiUrl(path: string) {
  const prefix = (import.meta.env.VITE_API_PREFIX as string | undefined) ?? '/api'
  const base = import.meta.env.VITE_API_BASE_URL as string | undefined

  const normalized = path.startsWith('/') ? path : `/${path}`

  if (base) return new URL(normalized, base).toString()

  if (normalized === prefix || normalized.startsWith(`${prefix}/`)) return normalized
  return `${prefix}${normalized}`
}

async function parseJsonResponse<T>(resp: Response): Promise<T> {
  const text = await resp.text()
  if (!text) return {} as T
  try {
    return JSON.parse(text) as T
  } catch {
    throw new Error(text)
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [tokens, setTokens] = useState<Tokens | null>(() => loadTokens())
  const refreshInFlight = useRef<Promise<string> | null>(null)
  const access = tokens?.access

  const user = useMemo(() => {
    if (!access) return null
    const payload = decodeJwt(access)
    if (!payload.user_id) return null
    return { userId: payload.user_id, username: payload.username }
  }, [access])

  const logout = useCallback(() => {
    clearTokens()
    setTokens(null)
  }, [])

  const apiFetchNoAuth = useCallback(async <T,>(path: string, init?: RequestInit) => {
    const resp = await fetch(apiUrl(path), init)
    if (!resp.ok) {
      const data = await parseJsonResponse<{ error?: string }>(resp)
      throw new Error(data?.error || `${resp.status} ${resp.statusText}`)
    }
    return parseJsonResponse<T>(resp)
  }, [])

  const refreshAccessToken = useCallback(async () => {
    if (!tokens?.refresh) throw new Error('No refresh token')
    if (!refreshInFlight.current) {
      refreshInFlight.current = (async () => {
        const resp = await fetch(apiUrl('/auth/refresh'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh: tokens.refresh }),
        })
        if (!resp.ok) {
          throw new Error('Session expired')
        }
        const data = await parseJsonResponse<RefreshResult>(resp)
        if (!data.access) throw new Error('Invalid refresh response')
        const next: Tokens = { access: data.access, refresh: data.refresh ?? tokens.refresh }
        saveTokens(next)
        setTokens(next)
        return next.access
      })().finally(() => {
        refreshInFlight.current = null
      })
    }
    return refreshInFlight.current
  }, [tokens])

  const apiFetch = useCallback(
    async <T,>(path: string, init?: RequestInit) => {
      if (!tokens?.access) {
        throw new Error('Not authenticated')
      }

      const doFetch = async (access: string) => {
        const headers = new Headers(init?.headers)
        headers.set('Authorization', `Bearer ${access}`)
        if (init?.body && !headers.has('Content-Type')) {
          headers.set('Content-Type', 'application/json')
        }
        return fetch(apiUrl(path), { ...init, headers })
      }

      let resp = await doFetch(tokens.access)
      if (resp.status === 401) {
        try {
          const nextAccess = await refreshAccessToken()
          resp = await doFetch(nextAccess)
        } catch {
          logout()
          throw new Error('Session expired')
        }
      }

      if (!resp.ok) {
        const data = await parseJsonResponse<{ error?: string }>(resp)
        throw new Error(data?.error || `${resp.status} ${resp.statusText}`)
      }
      return parseJsonResponse<T>(resp)
    },
    [logout, refreshAccessToken, tokens],
  )

  const login = useCallback(
    async (username: string, password: string) => {
      const resp = await fetch(apiUrl('/auth/login'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      })
      if (!resp.ok) {
        throw new Error('Invalid username/password')
      }
      const data = await parseJsonResponse<LoginResult>(resp)
      if (!data.access || !data.refresh) throw new Error('Invalid login response')
      const next: Tokens = { access: data.access, refresh: data.refresh }
      saveTokens(next)
      setTokens(next)
    },
    [],
  )

  const value = useMemo<AuthContextValue>(
    () => ({ tokens, user, login, logout, apiFetch, apiFetchNoAuth }),
    [apiFetch, apiFetchNoAuth, login, logout, tokens, user],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
