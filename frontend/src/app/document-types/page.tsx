'use client'

import { useEffect, useState, useCallback } from 'react'
import { AppLayout } from '@/components/Layout/AppLayout'
import { Button, Table, Modal, Input, Select } from '@/components/ui'
import { api } from '@/lib/api'
import type { DocumentType } from '@/lib/types'
import { Plus, Pencil, Trash2 } from 'lucide-react'
import { noLeadingSpace } from '@/lib/utils'

function DocumentTypeForm({ initial, onSubmit, onCancel, loading }: {
  initial?: { name: string; organization_id: string }
  onSubmit: (data: { name: string; organization_id: string }) => Promise<void>
  onCancel: () => void
  loading?: boolean
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
    if (!name.trim() || !orgId) { setError('All fields required'); return }
    setError('')
    await onSubmit({ name: name.trim(), organization_id: orgId })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && <p className="text-sm text-red-600">{error}</p>}
      <Input id="name" label="Document Type Name" value={name} onChange={(e) => setName(noLeadingSpace(e.target.value))} placeholder="e.g. Letter, Circular" />
      <Select id="org" label="Organization" options={orgs} placeholder="Select organization" value={orgId} onChange={(e) => setOrgId(e.target.value)} />
      <div className="flex justify-end gap-3 pt-2">
        <Button type="button" variant="secondary" onClick={onCancel}>Cancel</Button>
        <Button type="submit" loading={loading}>{initial ? 'Update' : 'Create'}</Button>
      </div>
    </form>
  )
}

export default function DocumentTypesPage() {
  const [items, setItems] = useState<DocumentType[]>([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<DocumentType | null>(null)
  const [saving, setSaving] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try { setItems(await api.documentTypes.list()) }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  const handleSubmit = async (data: any) => {
    setSaving(true)
    try {
      if (editing) await api.documentTypes.update(editing.id, data)
      else await api.documentTypes.create(data)
      setModalOpen(false)
      setEditing(null)
      await load()
    } finally { setSaving(false) }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure?')) return
    await api.documentTypes.delete(id)
    await load()
  }

  return (
    <AppLayout>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="page-title mb-0">Document Types</h2>
          <p className="text-sm text-gray-500">Define document classification types</p>
        </div>
        <Button onClick={() => { setEditing(null); setModalOpen(true) }}>
          <Plus className="h-4 w-4" /> Add Type
        </Button>
      </div>

      <Table
        columns={[
          { key: 'name', header: 'Name' },
          {
            key: 'created_at', header: 'Created',
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

      <Modal open={modalOpen} onClose={() => { setModalOpen(false); setEditing(null) }} title={editing ? 'Edit Document Type' : 'Add Document Type'}>
        <DocumentTypeForm initial={editing || undefined} onSubmit={handleSubmit} onCancel={() => { setModalOpen(false); setEditing(null) }} loading={saving} />
      </Modal>
    </AppLayout>
  )
}
