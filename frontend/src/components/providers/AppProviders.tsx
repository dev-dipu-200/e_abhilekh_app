'use client'

import type { ReactNode } from 'react'
import { Provider } from 'react-redux'
import { store } from '@/lib/store'
import { ThemeProvider } from '@/context/ThemeContext'

export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <Provider store={store}>
      <ThemeProvider>{children}</ThemeProvider>
    </Provider>
  )
}
