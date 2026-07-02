'use client'

import { useState, useEffect } from 'react'
import { Button, Input, Select } from '@/components/ui'
import { api } from '@/lib/api'
import { noLeadingSpace } from '@/lib/utils'

interface Props {
  initial?: { name: string; organization_id: string }
  onSubmit: (data: { name: string; organization_id: string }) => Promise<void>
  onCancel: () => void
  loading?: boolean
}

export function DepartmentForm({ initial, onSubmit, onCancel, loading }: Props) {
  const [name, setName] = useState(initial?.name || '')
  const [orgId, setOrgId] = useState(initial?.organization_id || '')
  const [orgs, setOrgs] = useState<{ value: string; label: string }[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    api.organizations.list().then((data) => setOrgs(data.map((o) => ({ value: o.id, label: o.name }))))
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim() || !orgId) { setError('Name and Organization are required'); return }
    setError('')
    await onSubmit({ name: name.trim(), organization_id: orgId })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && <p className="text-sm text-red-600">{error}</p>}
      <Input id="name" label="Department Name" value={name} onChange={(e) => setName(noLeadingSpace(e.target.value))} placeholder="Enter department name" />
      <Select id="org" label="Organization" options={orgs} placeholder="Select organization" value={orgId} onChange={(e) => setOrgId(e.target.value)} />
      <div className="flex justify-end gap-3 pt-2">
        <Button type="button" variant="secondary" onClick={onCancel}>Cancel</Button>
        <Button type="submit" loading={loading}>{initial ? 'Update' : 'Create'}</Button>
      </div>
    </form>
  )
}
