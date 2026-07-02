'use client'

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react'
import { useRouter } from 'next/navigation'
import { toast } from '@/lib/toast'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

interface AuthUser {
  user_id: string
  email: string
  username: string
  full_name: string | null
  is_superuser: boolean
  organization_id: string
}

interface AuthContextType {
  user: AuthUser | null
  token: string | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    const stored = localStorage.getItem('auth')
    if (stored) {
      try {
        const parsed = JSON.parse(stored)
        setToken(parsed.token)
        setUser(parsed.user)
      } catch {
        localStorage.removeItem('auth')
      }
    }
    setLoading(false)
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ message: 'Login failed' }))
      toast(err.message || 'Login failed', 'error')
      throw new Error(err.message || 'Login failed')
    }
    const body = await res.json()
    const data = body.result
    toast('Login successful', 'success')
    const authUser: AuthUser = {
      user_id: data.user_id,
      email: data.email,
      username: data.username,
      full_name: data.full_name,
      is_superuser: data.is_superuser,
      organization_id: data.organization_id,
    }
    localStorage.setItem('auth', JSON.stringify({ token: data.access_token, user: authUser }))
    setToken(data.access_token)
    setUser(authUser)
  }, [])

  const logout = useCallback(async () => {
    try {
      await fetch(`${API_BASE}/auth/logout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: '{}',
      })
    } catch {
      // ignore
    }
    localStorage.removeItem('auth')
    setToken(null)
    setUser(null)
    router.push('/login')
  }, [token, router])

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
