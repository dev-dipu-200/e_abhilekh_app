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
  X,
} from 'lucide-react'

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/organizations', label: 'Organizations', icon: Building2 },
  { href: '/users', label: 'Users', icon: Users },
  { href: '/roles', label: 'Roles', icon: Shield },
  { href: '/departments', label: 'Departments', icon: Building },
  { href: '/document-types', label: 'Document Types', icon: FileText },
  { href: '/files', label: 'File Management', icon: FolderOpen },
  { href: '/ai-search', label: 'AI Search', icon: Search },
]

interface SidebarProps {
  open: boolean
  onClose: () => void
}

export function Sidebar({ open, onClose }: SidebarProps) {
  const pathname = usePathname()

  const nav = (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-3 px-6 h-16 border-b border-gray-100">
        <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
          <FileUp className="h-5 w-5 text-white" />
        </div>
        <span className="font-bold text-lg text-gray-900">E-Abhilekh</span>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
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
                  ? 'bg-primary-50 text-primary-700'
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
              )}
            >
              <Icon className={clsx('h-5 w-5', active ? 'text-primary-600' : 'text-gray-400')} />
              {item.label}
            </Link>
          )
        })}
      </nav>

      <div className="px-4 py-4 border-t border-gray-100">
        <p className="text-xs text-gray-400">v1.0.0</p>
      </div>
    </div>
  )

  return (
    <>
      {/* Desktop */}
      <aside className="hidden lg:flex lg:flex-col lg:w-[260px] lg:fixed lg:inset-y-0 bg-white border-r border-gray-200">
        {nav}
      </aside>

      {/* Mobile */}
      {open && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="fixed inset-0 bg-black/50" onClick={onClose} />
          <aside className="relative w-[260px] h-full bg-white shadow-2xl">
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
