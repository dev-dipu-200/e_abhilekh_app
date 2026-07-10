'use client'

import { useEffect, useState, useCallback } from 'react'
import { AppLayout } from '@/components/Layout/AppLayout'
import { Button, Table, Modal, Input, Select } from '@/components/ui'
import { useAuth } from '@/context/AuthContext'
import { useLanguage } from '@/context/LanguageContext'
import { api } from '@/lib/api'
import { ensureDocumentTypes, getScopeKey } from '@/lib/store/catalog'
import { useAppDispatch, useAppSelector } from '@/lib/store/hooks'
import { store } from '@/lib/store'
import type { DocumentType } from '@/lib/types'
import { Plus, Pencil, Trash2 } from 'lucide-react'
import { noLeadingSpace } from '@/lib/utils'

function DocumentTypeForm({ initial, onSubmit, onCancel, loading, nameLabel, nameLabelPlaceholder, orgLabel, orgPlaceholder, cancelLabel, submitLabel, errorText }: {
  initial?: { name: string; organization_id: string }
  onSubmit: (data: { name: string; organization_id: string }) => Promise<void>
  onCancel: () => void
  loading?: boolean
  nameLabel: string
  nameLabelPlaceholder: string
  orgLabel: string
  orgPlaceholder: string
  cancelLabel: string
  submitLabel: string
  errorText: string
}) {
  const [name, setName] = useState(initial?.name || '')
  const [orgId, setOrgId] = useState(initial?.organization_id || '')
  const [orgs, setOrgs] = useState<{ value: string; label: string }[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    api.organizations.list().then((data) => setOrgs(data.map((o) => ({ value: o.id, label: o.name }))))
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim() || !orgId) { setError(errorText); return }
    setError('')
    await onSubmit({ name: name.trim(), organization_id: orgId })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && <p className="text-sm text-red-600">{error}</p>}
      <Input id="name" label={nameLabel} value={name} onChange={(e) => setName(noLeadingSpace(e.target.value))} placeholder={nameLabelPlaceholder} />
      <Select id="org" label={orgLabel} options={orgs} placeholder={orgPlaceholder} value={orgId} onChange={(e) => setOrgId(e.target.value)} />
      <div className="flex justify-end gap-3 pt-2">
        <Button type="button" variant="secondary" onClick={onCancel}>{cancelLabel}</Button>
        <Button type="submit" loading={loading}>{submitLabel}</Button>
      </div>
    </form>
  )
}

export default function DocumentTypesPage() {
  const { user } = useAuth()
  const { t } = useLanguage()
  const dispatch = useAppDispatch()
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<DocumentType | null>(null)
  const [saving, setSaving] = useState(false)
  const orgId = user?.organization_id ?? ''
  const scopeKey = getScopeKey(!!user?.is_superuser, orgId)
  const itemsCache = useAppSelector((state) => state.entities.documentTypesByKey[scopeKey])
  const items = itemsCache?.items || []
  const loading = !itemsCache?.loaded || itemsCache.status === 'loading'

  const load = useCallback(async (force = false) => {
    await ensureDocumentTypes(dispatch, store.getState, orgId, !!user?.is_superuser, force)
  }, [dispatch, orgId, user?.is_superuser])

  useEffect(() => { load().catch(() => {}) }, [load])

  const handleSubmit = async (data: any) => {
    setSaving(true)
    try {
      if (editing) await api.documentTypes.update(editing.id, data)
      else await api.documentTypes.create(data)
      setModalOpen(false)
      setEditing(null)
      await load(true)
    } finally { setSaving(false) }
  }

  const handleDelete = async (id: string) => {
    if (!confirm(t('common.areYouSure'))) return
    await api.documentTypes.delete(id)
    await load(true)
  }

  return (
    <AppLayout>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="page-title mb-0">{t('docTypes.title')}</h2>
          <p className="text-sm text-gray-500">{t('docTypes.subtitle')}</p>
        </div>
        <Button onClick={() => { setEditing(null); setModalOpen(true) }}>
          <Plus className="h-4 w-4" /> {t('docTypes.add')}
        </Button>
      </div>

      <Table
        columns={[
          { key: 'name', header: t('common.name') },
          {
            key: 'created_at', header: t('common.created'),
            render: (item) => new Date(item.created_at).toLocaleDateString(),
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
        data={items}
        loading={loading}
      />

      <Modal open={modalOpen} onClose={() => { setModalOpen(false); setEditing(null) }} title={editing ? t('docTypes.edit') : t('docTypes.addFull')}>
        <DocumentTypeForm
          initial={editing || undefined}
          onSubmit={handleSubmit}
          onCancel={() => { setModalOpen(false); setEditing(null) }}
          loading={saving}
          nameLabel={t('docTypes.name')}
          nameLabelPlaceholder={t('docTypes.namePlaceholder')}
          orgLabel={t('docTypes.organization')}
          orgPlaceholder={t('docTypes.selectOrganization')}
          cancelLabel={t('common.cancel')}
          submitLabel={editing ? t('common.update') : t('common.create')}
          errorText={t('common.allFieldsRequired')}
        />
      </Modal>
    </AppLayout>
  )
}
