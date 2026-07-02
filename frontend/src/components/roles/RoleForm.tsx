'use client'

import { useState, useEffect } from 'react'
import { Button, Input, Select } from '@/components/ui'
import { api } from '@/lib/api'
import { noLeadingSpace } from '@/lib/utils'

interface Props {
  initial?: { name: string; description?: string; organization_id: string; is_superadmin: boolean; is_admin: boolean; is_read_only: boolean }
  onSubmit: (data: any) => Promise<void>
  onCancel: () => void
  loading?: boolean
}

export function RoleForm({ initial, onSubmit, onCancel, loading }: Props) {
  const [form, setForm] = useState({
    name: initial?.name || '',
    description: initial?.description || '',
    organization_id: initial?.organization_id || '',
    is_superadmin: initial?.is_superadmin || false,
    is_admin: initial?.is_admin || false,
    is_read_only: initial?.is_read_only || false,
  })
  const [orgs, setOrgs] = useState<{ value: string; label: string }[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    api.organizations.list().then((data) => setOrgs(data.map((o) => ({ value: o.id, label: o.name }))))
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.name.trim() || !form.organization_id) { setError('Name and Organization are required'); return }
    setError('')
    await onSubmit(form)
  }

  const toggle = (key: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [key]: e.target.checked }))

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && <p className="text-sm text-red-600">{error}</p>}
      <Input id="name" label="Role Name" value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: noLeadingSpace(e.target.value) }))} placeholder="Enter role name" />
      <div className="space-y-1">
        <label htmlFor="description" className="form-label">Description</label>
        <textarea id="description" className="form-input" rows={2} value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: noLeadingSpace(e.target.value) }))} placeholder="Role description" />
      </div>
      <Select id="org" label="Organization" options={orgs} placeholder="Select organization" value={form.organization_id} onChange={(e) => setForm((f) => ({ ...f, organization_id: e.target.value }))} />
      <div className="space-y-2 pt-2">
        {(['is_superadmin', 'is_admin', 'is_read_only'] as const).map((key) => (
          <label key={key} className="flex items-center gap-2">
            <input type="checkbox" checked={form[key]} onChange={toggle(key)} className="rounded border-gray-300 text-primary-600 focus:ring-primary-500" />
            <span className="text-sm text-gray-700 capitalize">{key.replace('is_', '').replace('_', ' ')}</span>
          </label>
        ))}
      </div>
      <div className="flex justify-end gap-3 pt-2">
        <Button type="button" variant="secondary" onClick={onCancel}>Cancel</Button>
        <Button type="submit" loading={loading}>{initial ? 'Update' : 'Create'}</Button>
      </div>
    </form>
  )
}
