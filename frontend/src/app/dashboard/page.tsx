'use client'

import { useEffect, useState } from 'react'
import { AppLayout } from '@/components/Layout/AppLayout'
import { StatCard, Card } from '@/components/ui'
import { api } from '@/lib/api'
import type { DashboardStats } from '@/lib/types'
import { Building2, Users, FileText, Building, ArrowUpRight } from 'lucide-react'
import { useLanguage } from '@/context/LanguageContext'
import type { TranslationKey } from '@/lib/translations'

export default function DashboardPage() {
  const { t } = useLanguage()
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.dashboard.stats()
      .then(setStats)
      .finally(() => setLoading(false))
  }, [])

  const formatTime = (value?: string) => {
    if (!value) return ''
    const dt = new Date(value)
    if (Number.isNaN(dt.getTime())) return ''
    return dt.toLocaleString()
  }

  const quickActions = [
    { labelKey: 'dashboard.uploadDocument' as TranslationKey, href: '/files' },
    { labelKey: 'dashboard.createUser' as TranslationKey, href: '/users' },
    { labelKey: 'dashboard.addOrganization' as TranslationKey, href: '/organizations' },
    { labelKey: 'dashboard.manageRoles' as TranslationKey, href: '/roles' },
  ]

  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h2 className="page-title">{t('title.dashboard')}</h2>
          <p className="text-gray-500 -mt-4 mb-6">{t('dashboard.overview')}</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard label={t('dashboard.organizations')} value={loading ? '...' : stats?.total_organizations || 0} icon={<Building2 className="h-6 w-6" />} color="blue" />
          <StatCard label={t('dashboard.users')} value={loading ? '...' : stats?.total_users || 0} icon={<Users className="h-6 w-6" />} color="green" />
          <StatCard label={t('dashboard.documents')} value={loading ? '...' : stats?.total_documents || 0} icon={<FileText className="h-6 w-6" />} color="purple" />
          <StatCard label={t('dashboard.departments')} value={loading ? '...' : stats?.total_departments || 0} icon={<Building className="h-6 w-6" />} color="yellow" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-900">{t('dashboard.recentActivity')}</h3>
              <ArrowUpRight className="h-4 w-4 text-gray-400" />
            </div>
            {loading ? (
              <p className="text-sm text-gray-500 text-center py-8">{t('dashboard.loadingActivity')}</p>
            ) : stats?.recent_activity?.length ? (
              <div className="space-y-3">
                {stats.recent_activity.map((item) => (
                  <div key={item.id} className="rounded-xl border border-gray-200 p-3">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-medium text-gray-900">{item.action}</p>
                        <p className="text-xs text-gray-500 mt-1">
                          {item.document_subject || item.file_number || item.document_id}
                        </p>
                        {item.details && <p className="text-xs text-gray-500 mt-1">{item.details}</p>}
                        {(item.user_name || item.created_at) && (
                          <p className="text-xs text-gray-400 mt-2">
                            {[item.user_name, formatTime(item.created_at)].filter(Boolean).join(' • ')}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500 text-center py-8">{t('dashboard.noRecentActivity')}</p>
            )}
          </Card>
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-900">{t('dashboard.quickActions')}</h3>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {quickActions.map((action) => (
                <a
                  key={action.labelKey}
                  href={action.href}
                  className="p-3 rounded-xl border border-gray-200 text-sm font-medium text-gray-700 hover:bg-gray-50 hover:border-gray-300 transition-all text-center"
                >
                  {t(action.labelKey)}
                </a>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </AppLayout>
  )
}
