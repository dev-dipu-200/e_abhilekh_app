'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import clsx from 'clsx'
import {
  LayoutDashboard,
  Building2,
  Users,
  Shield,
  Building,
  FileText,
  FolderOpen,
  FileUp,
  Search,
  PenTool,
  Settings,
  X,
} from 'lucide-react'
import { useLanguage } from '@/context/LanguageContext'
import { useAuth } from '@/context/AuthContext'
import type { TranslationKey } from '@/lib/translations'

const navItems: { href: string; key: TranslationKey; icon: React.ComponentType<{ className?: string }> }[] = [
  { href: '/dashboard', key: 'nav.dashboard', icon: LayoutDashboard },
  { href: '/organizations', key: 'nav.organizations', icon: Building2 },
  { href: '/users', key: 'nav.users', icon: Users },
  { href: '/roles', key: 'nav.roles', icon: Shield },
  { href: '/departments', key: 'nav.departments', icon: Building },
  { href: '/document-types', key: 'nav.documentTypes', icon: FileText },
  { href: '/files', key: 'nav.fileManagement', icon: FolderOpen },
  { href: '/ai-search', key: 'nav.aiSearch', icon: Search },
  { href: '/ai-draft', key: 'nav.aiDraft', icon: PenTool },
  { href: '/settings', key: 'nav.settings', icon: Settings },
]

interface SidebarProps {
  open: boolean
  onClose: () => void
}

export function Sidebar({ open, onClose }: SidebarProps) {
  const pathname = usePathname()
  const { t } = useLanguage()
  const { user } = useAuth()
  const visibleNavItems = navItems.filter((item) => item.href !== '/settings' || !!user?.is_superuser || !!user?.is_admin)

  const nav = (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-3 px-6 h-16 border-b border-white/10">
        <div className="w-9 h-9 brand-gradient rounded-xl flex items-center justify-center">
          <FileUp className="h-5 w-5 text-white" />
        </div>
        <span className="font-bold text-lg text-white">E-Abhilekh</span>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {visibleNavItems.map((item) => {
          const Icon = item.icon
          const active = pathname === item.href || pathname.startsWith(item.href + '/')
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onClose}
              className={clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150',
                active
                  ? 'bg-white/15 text-white'
                  : 'text-gray-300 hover:bg-white/10 hover:text-white'
              )}
            >
              <Icon className={clsx('h-5 w-5', active ? 'text-white' : 'text-gray-400')} />
              {t(item.key)}
            </Link>
          )
        })}
      </nav>

      <div className="px-4 py-4 border-t border-white/10">
        <p className="text-xs text-gray-500">{t('sidebar.version')}</p>
      </div>
    </div>
  )

  return (
    <>
      {/* Desktop */}
      <aside className="hidden lg:flex lg:flex-col lg:w-[260px] lg:fixed lg:inset-y-0 themed-sidebar border-r border-white/60">
        {nav}
      </aside>

      {/* Mobile */}
      {open && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="fixed inset-0 bg-black/50" onClick={onClose} />
          <aside className="relative w-[260px] h-full themed-sidebar shadow-2xl">
            <div className="absolute top-3 right-3">
              <button onClick={onClose} className="p-1 rounded-lg hover:bg-gray-100">
                <X className="h-5 w-5 text-gray-500" />
              </button>
            </div>
            {nav}
          </aside>
        </div>
      )}
    </>
  )
}
