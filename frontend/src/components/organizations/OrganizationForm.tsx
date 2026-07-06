'use client'

import { useState } from 'react'
import { Button, Input, Select } from '@/components/ui'
import { noLeadingSpace } from '@/lib/utils'

interface Props {
  initial?: {
    name: string
    address?: string
    is_active: boolean
    ai_provider?: string
    openai_embedding_model?: string
    openai_llm_model?: string
    has_openai_api_key?: boolean
  }
  onSubmit: (data: {
    name: string
    address?: string
    is_active: boolean
    ai_provider: string
    openai_api_key?: string
    openai_embedding_model?: string
    openai_llm_model?: string
    clear_openai_api_key?: boolean
  }) => Promise<void>
  onCancel: () => void
  loading?: boolean
}

export function OrganizationForm({ initial, onSubmit, onCancel, loading }: Props) {
  const [name, setName] = useState(initial?.name || '')
  const [address, setAddress] = useState(initial?.address || '')
  const [isActive, setIsActive] = useState(initial?.is_active ?? true)
  const [aiProvider, setAiProvider] = useState(initial?.ai_provider || 'ollama')
  const [openaiApiKey, setOpenaiApiKey] = useState('')
  const [openaiEmbeddingModel, setOpenaiEmbeddingModel] = useState(initial?.openai_embedding_model || 'text-embedding-3-large')
  const [openaiLlmModel, setOpenaiLlmModel] = useState(initial?.openai_llm_model || 'gpt-4o-mini')
  const [clearOpenAiKey, setClearOpenAiKey] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) { setError('Name is required'); return }
    if (aiProvider === 'openai') {
      const hasExistingKey = !!initial?.has_openai_api_key
      const usingExistingKey = hasExistingKey && !clearOpenAiKey && !openaiApiKey.trim()
      if (!usingExistingKey && !openaiApiKey.trim()) { setError('OpenAI API key is required for OpenAI provider'); return }
      if (!openaiEmbeddingModel.trim()) { setError('OpenAI embedding model is required'); return }
      if (!openaiLlmModel.trim()) { setError('OpenAI LLM model is required'); return }
    }
    setError('')
    await onSubmit({
      name: name.trim(),
      address: address.trim() || undefined,
      is_active: isActive,
      ai_provider: aiProvider,
      openai_api_key: openaiApiKey.trim() || undefined,
      openai_embedding_model: aiProvider === 'openai' ? openaiEmbeddingModel.trim() || undefined : undefined,
      openai_llm_model: aiProvider === 'openai' ? openaiLlmModel.trim() || undefined : undefined,
      clear_openai_api_key: aiProvider === 'openai' ? clearOpenAiKey : false,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Input id="name" label="Organization Name" value={name} onChange={(e) => setName(noLeadingSpace(e.target.value))} error={error} placeholder="Enter organization name" />
      <div className="space-y-1">
        <label htmlFor="address" className="form-label">Address</label>
        <textarea id="address" className="form-input" rows={3} value={address} onChange={(e) => setAddress(noLeadingSpace(e.target.value))} placeholder="Enter address (optional)" />
      </div>
      <Select
        id="ai_provider"
        label="AI Provider"
        value={aiProvider}
        onChange={(e) => setAiProvider(e.target.value)}
        options={[
          { value: 'ollama', label: 'Ollama (Fallback / Default)' },
          { value: 'openai', label: 'OpenAI (Primary)' },
        ]}
      />
      {aiProvider === 'openai' && (
        <>
          <Input
            id="openai_api_key"
            type="password"
            label={initial?.has_openai_api_key ? 'OpenAI API Key (leave blank to keep current)' : 'OpenAI API Key'}
            value={openaiApiKey}
            onChange={(e) => setOpenaiApiKey(noLeadingSpace(e.target.value))}
            placeholder="sk-..."
          />
          {initial?.has_openai_api_key && (
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={clearOpenAiKey}
                onChange={(e) => setClearOpenAiKey(e.target.checked)}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm text-gray-700">Clear saved OpenAI API key</span>
            </label>
          )}
          <Input
            id="openai_embedding_model"
            label="OpenAI Embedding Model"
            value={openaiEmbeddingModel}
            onChange={(e) => setOpenaiEmbeddingModel(noLeadingSpace(e.target.value))}
            placeholder="text-embedding-3-large"
          />
          <Input
            id="openai_llm_model"
            label="OpenAI LLM Model"
            value={openaiLlmModel}
            onChange={(e) => setOpenaiLlmModel(noLeadingSpace(e.target.value))}
            placeholder="gpt-4o-mini"
          />
          <p className="text-xs text-gray-500">
            OpenAI is used first for embeddings, AI Smart Search, and draft generation. If this config is missing, the backend falls back to Ollama.
          </p>
        </>
      )}
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
