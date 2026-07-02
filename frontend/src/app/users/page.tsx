'use client'

import { useEffect, useState, useCallback } from 'react'
import { AppLayout } from '@/components/Layout/AppLayout'
import { Button, Table, Modal, Badge } from '@/components/ui'
import { UserForm } from '@/components/users/UserForm'
import { api } from '@/lib/api'
import type { User } from '@/lib/types'
import { Plus, Pencil, Trash2 } from 'lucide-react'

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<User | null>(null)
  const [saving, setSaving] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try { setUsers(await api.users.list()) }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  const handleSubmit = async (data: any) => {
    setSaving(true)
    try {
      if (editing) await api.users.update(editing.id, data)
      else await api.users.create(data)
      setModalOpen(false)
      setEditing(null)
      await load()
    } finally { setSaving(false) }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure?')) return
    await api.users.delete(id)
    await load()
  }

  return (
    <AppLayout>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="page-title mb-0">Users</h2>
          <p className="text-sm text-gray-500">Manage system users</p>
        </div>
        <Button onClick={() => { setEditing(null); setModalOpen(true) }}>
          <Plus className="h-4 w-4" /> Add User
        </Button>
      </div>

      <Table
        columns={[
          { key: 'email', header: 'Email' },
          { key: 'username', header: 'Username' },
          { key: 'full_name', header: 'Full Name' },
          {
            key: 'is_active', header: 'Status',
            render: (item) => <Badge variant={item.is_active ? 'green' : 'red'}>{item.is_active ? 'Active' : 'Inactive'}</Badge>,
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
        data={users}
        loading={loading}
      />

      <Modal open={modalOpen} onClose={() => { setModalOpen(false); setEditing(null) }} title={editing ? 'Edit User' : 'Add User'} size="lg">
        <UserForm initial={editing || undefined} onSubmit={handleSubmit} onCancel={() => { setModalOpen(false); setEditing(null) }} loading={saving} />
      </Modal>
    </AppLayout>
  )
}
