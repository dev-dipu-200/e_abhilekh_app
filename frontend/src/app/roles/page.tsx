'use client'

import { useEffect, useState, useCallback } from 'react'
import { AppLayout } from '@/components/Layout/AppLayout'
import { Button, Table, Modal, Badge } from '@/components/ui'
import { RoleForm } from '@/components/roles/RoleForm'
import { api } from '@/lib/api'
import type { Role } from '@/lib/types'
import { Plus, Pencil, Trash2 } from 'lucide-react'
import { useLanguage } from '@/context/LanguageContext'

export default function RolesPage() {
  const { t } = useLanguage()
  const [roles, setRoles] = useState<Role[]>([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Role | null>(null)
  const [saving, setSaving] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try { setRoles(await api.roles.list()) }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  const handleSubmit = async (data: any) => {
    setSaving(true)
    try {
      if (editing) await api.roles.update(editing.id, data)
      else await api.roles.create(data)
      setModalOpen(false)
      setEditing(null)
      await load()
    } finally { setSaving(false) }
  }

  const handleDelete = async (id: string) => {
    if (!confirm(t('common.areYouSure'))) return
    await api.roles.delete(id)
    await load()
  }

  return (
    <AppLayout>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="page-title mb-0">{t('roles.title')}</h2>
          <p className="text-sm text-gray-500">{t('roles.subtitle')}</p>
        </div>
        <Button onClick={() => { setEditing(null); setModalOpen(true) }}>
          <Plus className="h-4 w-4" /> {t('roles.add')}
        </Button>
      </div>

      <Table
        columns={[
          { key: 'name', header: t('roles.name') },
          { key: 'description', header: t('roles.description') },
          {
            key: 'is_superadmin', header: t('roles.permissions'),
            render: (item) => (
              <div className="flex gap-1 flex-wrap">
                {item.is_superadmin && <Badge variant="red">{t('roles.superadmin')}</Badge>}
                {item.is_admin && <Badge variant="blue">{t('roles.admin')}</Badge>}
                {item.is_read_only && <Badge variant="yellow">{t('roles.readOnly')}</Badge>}
                {!item.is_superadmin && !item.is_admin && !item.is_read_only && <Badge variant="gray">{t('roles.standard')}</Badge>}
              </div>
            ),
          },
          {
            key: 'actions', header: '', className: 'table-cell text-right',
            render: (item) => (
              <div className="flex justify-end gap-1">
                <Button variant="ghost" size="sm" onClick={() => { setEditing(item); setModalOpen(true) }}><Pencil className="h-4 w-4" /></Button>
                <Button variant="ghost" size="sm" onClick={() => handleDelete(item.id)}><Trash2 className="h-4 w-4 text-red-500" /></Button>
              </div>
            ),
          },
        ]}
        data={roles}
        loading={loading}
      />

      <Modal open={modalOpen} onClose={() => { setModalOpen(false); setEditing(null) }} title={editing ? t('roles.edit') : t('roles.add')}>
        <RoleForm initial={editing || undefined} onSubmit={handleSubmit} onCancel={() => { setModalOpen(false); setEditing(null) }} loading={saving} />
      </Modal>
    </AppLayout>
  )
}
