'use client'

import { createContext, ReactNode, useContext, useEffect, useMemo, useState } from 'react'

export type ThemeName = 'sunrise' | 'citrus' | 'sand'

interface ThemeOption {
  id: ThemeName
  label: string
}

const THEME_OPTIONS: ThemeOption[] = [
  { id: 'sunrise', label: 'Sunrise' },
  { id: 'citrus', label: 'Citrus' },
  { id: 'sand', label: 'Sand' },
]

interface ThemeContextType {
  theme: ThemeName
  themes: ThemeOption[]
  setTheme: (theme: ThemeName) => void
  cycleTheme: () => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<ThemeName>('sunrise')

  useEffect(() => {
    const stored = window.localStorage.getItem('theme-preference') as ThemeName | null
    if (stored && THEME_OPTIONS.some((item) => item.id === stored)) {
      setThemeState(stored)
    }
  }, [])

  useEffect(() => {
    document.body.dataset.theme = theme
    window.localStorage.setItem('theme-preference', theme)
  }, [theme])

  const value = useMemo<ThemeContextType>(() => ({
    theme,
    themes: THEME_OPTIONS,
    setTheme: setThemeState,
    cycleTheme: () => {
      const currentIndex = THEME_OPTIONS.findIndex((item) => item.id === theme)
      const next = THEME_OPTIONS[(currentIndex + 1) % THEME_OPTIONS.length]
      setThemeState(next.id)
    },
  }), [theme])

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider')
  return ctx
}
