'use client'

import { useEffect, useState, useCallback } from 'react'
import { AppLayout } from '@/components/Layout/AppLayout'
import { Button, Table, Modal } from '@/components/ui'
import { DepartmentForm } from '@/components/departments/DepartmentForm'
import { api } from '@/lib/api'
import type { Department } from '@/lib/types'
import { Plus, Pencil, Trash2 } from 'lucide-react'

export default function DepartmentsPage() {
  const [depts, setDepts] = useState<Department[]>([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<Department | null>(null)
  const [saving, setSaving] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try { setDepts(await api.departments.list()) }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  const handleSubmit = async (data: any) => {
    setSaving(true)
    try {
      if (editing) await api.departments.update(editing.id, data)
      else await api.departments.create(data)
      setModalOpen(false)
      setEditing(null)
      await load()
    } finally { setSaving(false) }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure?')) return
    await api.departments.delete(id)
    await load()
  }

  return (
    <AppLayout>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="page-title mb-0">Departments</h2>
          <p className="text-sm text-gray-500">Manage departments within organizations</p>
        </div>
        <Button onClick={() => { setEditing(null); setModalOpen(true) }}>
          <Plus className="h-4 w-4" /> Add Department
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
        data={depts}
        loading={loading}
      />

      <Modal open={modalOpen} onClose={() => { setModalOpen(false); setEditing(null) }} title={editing ? 'Edit Department' : 'Add Department'}>
        <DepartmentForm initial={editing || undefined} onSubmit={handleSubmit} onCancel={() => { setModalOpen(false); setEditing(null) }} loading={saving} />
      </Modal>
    </AppLayout>
  )
}
