'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { AppLayout } from '@/components/Layout/AppLayout'
import { Card, Button } from '@/components/ui'
import { api } from '@/lib/api'
import type { Organization } from '@/lib/types'
import { ArrowLeft } from 'lucide-react'
import Link from 'next/link'

export default function OrganizationDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [org, setOrg] = useState<Organization | null>(null)

  useEffect(() => {
    api.organizations.get(id).then(setOrg)
  }, [id])

  if (!org) return <AppLayout><div className="text-center py-16 text-gray-400">Loading...</div></AppLayout>

  return (
    <AppLayout>
      <Link href="/organizations" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-4">
        <ArrowLeft className="h-4 w-4" /> Back to Organizations
      </Link>
      <Card>
        <h2 className="text-xl font-bold mb-4">{org.name}</h2>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div><span className="text-gray-500">Address:</span> <span className="font-medium">{org.address || '-'}</span></div>
          <div><span className="text-gray-500">Status:</span> <span className="font-medium">{org.is_active ? 'Active' : 'Inactive'}</span></div>
          <div><span className="text-gray-500">Created:</span> <span className="font-medium">{new Date(org.created_at).toLocaleString()}</span></div>
        </div>
      </Card>
    </AppLayout>
  )
}
