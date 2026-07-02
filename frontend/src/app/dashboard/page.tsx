'use client'

import { useEffect, useState } from 'react'
import { AppLayout } from '@/components/Layout/AppLayout'
import { StatCard, Card } from '@/components/ui'
import { api } from '@/lib/api'
import type { DashboardStats } from '@/lib/types'
import { Building2, Users, FileText, Building, ArrowUpRight } from 'lucide-react'

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.dashboard.stats()
      .then(setStats)
      .finally(() => setLoading(false))
  }, [])

  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h2 className="page-title">Dashboard</h2>
          <p className="text-gray-500 -mt-4 mb-6">Overview of your E-Abhilekh system</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard label="Organizations" value={loading ? '...' : stats?.total_organizations || 0} icon={<Building2 className="h-6 w-6" />} color="blue" />
          <StatCard label="Users" value={loading ? '...' : stats?.total_users || 0} icon={<Users className="h-6 w-6" />} color="green" />
          <StatCard label="Documents" value={loading ? '...' : stats?.total_documents || 0} icon={<FileText className="h-6 w-6" />} color="purple" />
          <StatCard label="Departments" value={loading ? '...' : stats?.total_departments || 0} icon={<Building className="h-6 w-6" />} color="yellow" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-900">Recent Activity</h3>
              <ArrowUpRight className="h-4 w-4 text-gray-400" />
            </div>
            <p className="text-sm text-gray-500 text-center py-8">No recent activity</p>
          </Card>
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-900">Quick Actions</h3>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: 'Upload Document', href: '/files' },
                { label: 'Create User', href: '/users' },
                { label: 'Add Organization', href: '/organizations' },
                { label: 'Manage Roles', href: '/roles' },
              ].map((action) => (
                <a
                  key={action.label}
                  href={action.href}
                  className="p-3 rounded-xl border border-gray-200 text-sm font-medium text-gray-700 hover:bg-gray-50 hover:border-gray-300 transition-all text-center"
                >
                  {action.label}
                </a>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </AppLayout>
  )
}
