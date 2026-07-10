'use client'

import { useEffect, useState, useCallback } from 'react'
import { AppLayout } from '@/components/Layout/AppLayout'
import { Button, Table, Modal, Badge } from '@/components/ui'
import { OrganizationForm } from '@/components/organizations/OrganizationForm'
import { api } from '@/lib/api'
import type { Organization } from '@/lib/types'
import { Plus, Pencil, Trash2 } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import { useLanguage } from '@/context/LanguageContext'

export default function OrganizationsPage() {
  const { user } = useAuth()
  const { t } = useLanguage()
  const canCreateOrDelete = !!user?.is_superuser
  const canEdit = !!user?.is_superuser || !!user?.is_admin
  const [orgs, setOrgs] = useState<Organization[]>([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Organization | null>(null)
  const [saving, setSaving] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try { setOrgs(await api.organizations.list()) }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  const handleSubmit = async (data: Partial<Organization>) => {
    setSaving(true)
    try {
      if (editing) await api.organizations.update(editing.id, data)
      else await api.organizations.create(data)
      setModalOpen(false)
      setEditing(null)
      await load()
    } finally { setSaving(false) }
  }

  const handleDelete = async (id: string) => {
    if (!confirm(t('common.areYouSure'))) return
    await api.organizations.delete(id)
    await load()
  }

  return (
    <AppLayout>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="page-title mb-0">{t('org.title')}</h2>
          <p className="text-sm text-gray-500">{t('org.subtitle')}</p>
        </div>
        {canCreateOrDelete && (
          <Button onClick={() => { setEditing(null); setModalOpen(true) }}>
            <Plus className="h-4 w-4" /> {t('org.add')}
          </Button>
        )}
      </div>

      <Table
        columns={[
          { key: 'name', header: t('org.name') },
          { key: 'address', header: t('org.address') },
          {
            key: 'is_active', header: t('org.status'),
            render: (item) => <Badge variant={item.is_active ? 'green' : 'red'}>{item.is_active ? t('common.active') : t('common.inactive')}</Badge>,
          },
          {
            key: 'created_at', header: t('org.created'),
            render: (item) => new Date(item.created_at).toLocaleDateString(),
          },
          {
            key: 'actions', header: '', className: 'table-cell text-right',
            render: (item) => (
              <div className="flex justify-end gap-1">
                {canEdit && (
                  <Button variant="ghost" size="sm" onClick={() => { setEditing(item); setModalOpen(true) }}><Pencil className="h-4 w-4" /></Button>
                )}
                {canCreateOrDelete && (
                  <Button variant="ghost" size="sm" onClick={() => handleDelete(item.id)}><Trash2 className="h-4 w-4 text-red-500" /></Button>
                )}
              </div>
            ),
          },
        ]}
        data={orgs}
        loading={loading}
      />

      <Modal open={modalOpen} onClose={() => { setModalOpen(false); setEditing(null) }} title={editing ? t('org.edit') : t('org.add')}>
        <OrganizationForm initial={editing || undefined} onSubmit={handleSubmit} onCancel={() => { setModalOpen(false); setEditing(null) }} loading={saving} />
      </Modal>
    </AppLayout>
  )
}
