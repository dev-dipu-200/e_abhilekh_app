'use client'

import { ReactNode, useState, useEffect } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { useAuth } from '@/context/AuthContext'
import { useLanguage } from '@/context/LanguageContext'
import type { TranslationKey } from '@/lib/translations'
import { Spinner } from '@/components/ui'

const pageTitleKeys: Record<string, string> = {
  '/dashboard': 'title.dashboard',
  '/organizations': 'title.organizations',
  '/users': 'title.users',
  '/roles': 'title.roles',
  '/departments': 'title.departments',
  '/document-types': 'title.documentTypes',
  '/files': 'title.fileManagement',
  '/ai-search': 'title.aiSearch',
  '/ai-draft': 'title.aiDraft',
  '/settings': 'title.settings',
}

interface AppLayoutProps {
  children: ReactNode
  fullWidth?: boolean
}

export function AppLayout({ children, fullWidth = true }: AppLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const pathname = usePathname()
  const router = useRouter()
  const { user, loading } = useAuth()
  const { t } = useLanguage()

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login')
    }
  }, [loading, user, router])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Spinner />
      </div>
    )
  }

  if (!user) return null

  const titleKey = (Object.entries(pageTitleKeys).find(([path]) =>
    pathname === path || pathname.startsWith(path + '/')
  )?.[1] || 'title.eAbhilekh') as TranslationKey
  const title = t(titleKey)

  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="lg:pl-[260px]">
        <Header title={title} onMenuClick={() => setSidebarOpen(true)} />
        <main className={fullWidth ? 'p-6' : 'page-container'}>{children}</main>
      </div>
    </div>
  )
}
