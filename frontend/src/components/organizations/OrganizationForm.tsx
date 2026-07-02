'use client'

import { useState } from 'react'
import { Button, Input } from '@/components/ui'
import { noLeadingSpace } from '@/lib/utils'

interface Props {
  initial?: { name: string; address?: string; is_active: boolean }
  onSubmit: (data: { name: string; address?: string; is_active: boolean }) => Promise<void>
  onCancel: () => void
  loading?: boolean
}

export function OrganizationForm({ initial, onSubmit, onCancel, loading }: Props) {
  const [name, setName] = useState(initial?.name || '')
  const [address, setAddress] = useState(initial?.address || '')
  const [isActive, setIsActive] = useState(initial?.is_active ?? true)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) { setError('Name is required'); return }
    setError('')
    await onSubmit({ name: name.trim(), address: address.trim() || undefined, is_active: isActive })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Input id="name" label="Organization Name" value={name} onChange={(e) => setName(noLeadingSpace(e.target.value))} error={error} placeholder="Enter organization name" />
      <div className="space-y-1">
        <label htmlFor="address" className="form-label">Address</label>
        <textarea id="address" className="form-input" rows={3} value={address} onChange={(e) => setAddress(noLeadingSpace(e.target.value))} placeholder="Enter address (optional)" />
      </div>
      <label className="flex items-center gap-2">
        <input type="checkbox" checked={isActive} onChange={(e) => setIsActive(e.target.checked)} className="rounded border-gray-300 text-primary-600 focus:ring-primary-500" />
        <span className="text-sm text-gray-700">Active</span>
      </label>
      <div className="flex justify-end gap-3 pt-2">
        <Button type="button" variant="secondary" onClick={onCancel}>Cancel</Button>
        <Button type="submit" loading={loading}>{initial ? 'Update' : 'Create'}</Button>
      </div>
    </form>
  )
}
