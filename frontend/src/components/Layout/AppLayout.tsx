'use client'

import { ReactNode, useState, useEffect } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { useAuth } from '@/context/AuthContext'
import { Spinner } from '@/components/ui'

const pageTitles: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/organizations': 'Organizations',
  '/users': 'Users',
  '/roles': 'Roles',
  '/departments': 'Departments',
  '/document-types': 'Document Types',
  '/files': 'File Management',
  '/ai-search': 'AI Search',
  '/ai-draft': 'AI Draft Generator',
}

interface AppLayoutProps {
  children: ReactNode
}

export function AppLayout({ children }: AppLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const pathname = usePathname()
  const router = useRouter()
  const { user, loading } = useAuth()

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

  const title = Object.entries(pageTitles).find(([path]) =>
    pathname === path || pathname.startsWith(path + '/')
  )?.[1] || 'E-Abhilekh'

  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="lg:pl-[260px]">
        <Header title={title} onMenuClick={() => setSidebarOpen(true)} />
        <main className="page-container">{children}</main>
      </div>
    </div>
  )
}
