'use client'

import { Menu, Bell, User, LogOut, Palette } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import { useLanguage } from '@/context/LanguageContext'
import { useTheme } from '@/context/ThemeContext'

interface HeaderProps {
  onMenuClick: () => void
  title: string
}

export function Header({ onMenuClick, title }: HeaderProps) {
  const { user, logout } = useAuth()
  const { language, toggleLanguage, t } = useLanguage()
  const { theme, cycleTheme, themes } = useTheme()
  const currentTheme = themes.find((item) => item.id === theme)

  return (
    <header className="sticky top-0 z-30 themed-header border-b border-white/60">
      <div className="flex items-center justify-between h-16 px-4 lg:px-6">
        <div className="flex items-center gap-3">
          <button
            onClick={onMenuClick}
            className="lg:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <Menu className="h-5 w-5 text-gray-600" />
          </button>
          <h1 className="text-lg font-semibold text-gray-900">{title}</h1>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={cycleTheme}
            className="px-3 py-1.5 rounded-xl theme-chip text-sm font-medium transition-colors hover:bg-white"
            title="Change theme"
          >
            <span className="inline-flex items-center gap-2">
              <Palette className="h-4 w-4 text-primary-600" />
              <span className="hidden md:inline">{currentTheme?.label || 'Theme'}</span>
            </span>
          </button>
          <button
            onClick={toggleLanguage}
            className="px-3 py-1.5 rounded-xl theme-chip text-sm font-medium hover:bg-white transition-colors"
          >
            {language === 'en' ? 'हिन्दी' : 'English'}
          </button>
          <button className="p-2 rounded-xl hover:bg-white/90 transition-colors relative">
            <Bell className="h-5 w-5 text-gray-500" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full" />
          </button>
          <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-white/55 border border-white/60 backdrop-blur-sm">
            <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
              <User className="h-4 w-4 text-primary-600" />
            </div>
            <span className="text-sm font-medium text-gray-700 hidden sm:block">
              {user?.full_name || user?.username || 'User'}
            </span>
          </div>
          <button
            onClick={logout}
            className="p-2 rounded-lg hover:bg-red-50 hover:text-red-600 transition-colors text-gray-400"
            title={t('header.logout')}
          >
            <LogOut className="h-5 w-5" />
          </button>
        </div>
      </div>
    </header>
  )
}
