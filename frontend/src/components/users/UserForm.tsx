'use client'

import { useState, useEffect } from 'react'
import { Button, Input, Select } from '@/components/ui'
import { api } from '@/lib/api'
import { noLeadingSpace } from '@/lib/utils'

interface Props {
  initial?: { email: string; username: string; full_name?: string; employee_id?: string; organization_id: string; role_id: string; is_active: boolean }
  onSubmit: (data: any) => Promise<void>
  onCancel: () => void
  loading?: boolean
}

export function UserForm({ initial, onSubmit, onCancel, loading }: Props) {
  const [form, setForm] = useState({
    email: initial?.email || '',
    username: initial?.username || '',
    full_name: initial?.full_name || '',
    employee_id: initial?.employee_id || '',
    organization_id: initial?.organization_id || '',
    role_id: initial?.role_id || '',
    password: '',
    is_active: initial?.is_active ?? true,
  })
  const [orgs, setOrgs] = useState<{ value: string; label: string }[]>([])
  const [roles, setRoles] = useState<{ value: string; label: string }[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    api.organizations.list().then((data) => setOrgs(data.map((o) => ({ value: o.id, label: o.name }))))
    api.roles.list().then((data) => setRoles(data.map((r) => ({ value: r.id, label: r.name }))))
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.email.trim() || !form.username.trim() || !form.organization_id || !form.role_id) {
      setError('Please fill all required fields')
      return
    }
    if (!initial && !form.password) { setError('Password is required'); return }
    setError('')
    const payload = { ...form }
    if (!payload.password) delete (payload as any).password
    await onSubmit(payload)
  }

  const set = (key: string) => (e: any) => setForm((f) => ({ ...f, [key]: noLeadingSpace(e.target.value) }))

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="grid grid-cols-2 gap-4">
        <Input id="email" label="Email *" value={form.email} onChange={set('email')} placeholder="user@example.com" />
        <Input id="username" label="Username *" value={form.username} onChange={set('username')} placeholder="username" />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <Input id="full_name" label="Full Name" value={form.full_name} onChange={set('full_name')} placeholder="Full name" />
        <Input id="employee_id" label="Employee ID" value={form.employee_id} onChange={set('employee_id')} placeholder="Employee ID" />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <Select id="organization_id" label="Organization *" options={orgs} placeholder="Select organization" value={form.organization_id} onChange={set('organization_id')} />
        <Select id="role_id" label="Role *" options={roles} placeholder="Select role" value={form.role_id} onChange={set('role_id')} />
      </div>
      {!initial && <Input id="password" label="Password *" type="password" value={form.password} onChange={set('password')} placeholder="Enter password" />}
      <label className="flex items-center gap-2">
        <input type="checkbox" checked={form.is_active} onChange={(e) => setForm((f) => ({ ...f, is_active: e.target.checked }))} className="rounded border-gray-300 text-primary-600 focus:ring-primary-500" />
        <span className="text-sm text-gray-700">Active</span>
      </label>
      <div className="flex justify-end gap-3 pt-2">
        <Button type="button" variant="secondary" onClick={onCancel}>Cancel</Button>
        <Button type="submit" loading={loading}>{initial ? 'Update' : 'Create'}</Button>
      </div>
    </form>
  )
}
