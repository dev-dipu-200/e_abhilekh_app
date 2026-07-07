'use client'

import { useEffect, useState } from 'react'
import { AppLayout } from '@/components/Layout/AppLayout'
import { Button, Card, Input, Select } from '@/components/ui'
import { useAuth } from '@/context/AuthContext'
import { api } from '@/lib/api'
import type { AISettings } from '@/lib/types'

type FormErrors = {
  openai_api_key?: string
  openai_embedding_model?: string
  openai_llm_model?: string
  general?: string
}

const initialState: AISettings = {
  ai_provider: 'ollama',
  openai_embedding_model: 'text-embedding-3-large',
  openai_llm_model: 'gpt-4o-mini',
  has_openai_api_key: false,
  organization_ai_provider: 'ollama',
  organization_openai_embedding_model: undefined,
  organization_openai_llm_model: undefined,
  organization_has_openai_api_key: false,
}

export default function SettingsPage() {
  const { user } = useAuth()
  const [settings, setSettings] = useState<AISettings>(initialState)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [errors, setErrors] = useState<FormErrors>({})
  const [openaiApiKey, setOpenaiApiKey] = useState('')
  const [clearOpenAiKey, setClearOpenAiKey] = useState(false)

  const canManage = !!user?.is_superuser || !!user?.is_admin

  useEffect(() => {
    if (!canManage) {
      setLoading(false)
      return
    }
    api.settings.getAI()
      .then((data) => setSettings(data))
      .finally(() => setLoading(false))
  }, [canManage])

  const mapError = (message: string): FormErrors => {
    const normalized = message.toLowerCase()
    if (normalized.includes('api key')) {
      return { openai_api_key: message }
    }
    if (normalized.includes('embedding model and llm model must be different')) {
      return {
        openai_embedding_model: message,
        openai_llm_model: message,
      }
    }
    if (normalized.includes('embedding model')) {
      return { openai_embedding_model: message }
    }
    if (normalized.includes('llm model')) {
      return { openai_llm_model: message }
    }
    return { general: message }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (settings.ai_provider === 'openai') {
      const usingExistingKey = settings.has_openai_api_key && !clearOpenAiKey && !openaiApiKey.trim()
      if (!usingExistingKey && !openaiApiKey.trim()) {
        setErrors({ openai_api_key: 'OpenAI API key is required for OpenAI provider' })
        return
      }
      if (!settings.openai_embedding_model?.trim()) {
        setErrors({ openai_embedding_model: 'OpenAI embedding model is required' })
        return
      }
      if (!settings.openai_llm_model?.trim()) {
        setErrors({ openai_llm_model: 'OpenAI LLM model is required' })
        return
      }
    }

    setErrors({})
    setSaving(true)
    try {
      const updated = await api.settings.updateAI({
        ai_provider: settings.ai_provider,
        openai_api_key: openaiApiKey.trim() || undefined,
        openai_embedding_model: settings.ai_provider === 'openai' ? settings.openai_embedding_model?.trim() || undefined : undefined,
        openai_llm_model: settings.ai_provider === 'openai' ? settings.openai_llm_model?.trim() || undefined : undefined,
        clear_openai_api_key: settings.ai_provider === 'openai' ? clearOpenAiKey : false,
      })
      setSettings(updated)
      setOpenaiApiKey('')
      setClearOpenAiKey(false)
      setErrors({})
    } catch (err) {
      setErrors(mapError(err instanceof Error ? err.message : 'Unable to save settings'))
    } finally {
      setSaving(false)
    }
  }

  return (
    <AppLayout>
      <div className="mx-auto max-w-4xl space-y-6">
        <div>
          <h2 className="page-title mb-0">Settings</h2>
          <p className="text-sm text-gray-500">Admin and super_admin users can manage their own OpenAI key and models here.</p>
        </div>

        {!canManage ? (
          <Card className="p-6">
            <p className="text-sm text-gray-600">You do not have permission to manage AI settings.</p>
          </Card>
        ) : loading ? (
          <Card className="p-6">
            <p className="text-sm text-gray-600">Loading settings...</p>
          </Card>
        ) : (
          <>
            <Card className="p-6">
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Your AI Configuration</h3>
                <p className="text-sm text-gray-500">Your personal configuration is used first for AI Search and AI Draft. If it is missing or incomplete, organization settings and then Ollama are used as fallback.</p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                <Select
                  id="ai_provider"
                  label="AI Provider"
                  value={settings.ai_provider}
                  onChange={(e) => setSettings((prev) => ({ ...prev, ai_provider: e.target.value }))}
                  options={[
                    { value: 'ollama', label: 'Ollama Fallback' },
                    { value: 'openai', label: 'OpenAI Primary' },
                  ]}
                />

                {settings.ai_provider === 'openai' && (
                  <>
                    <Input
                      id="openai_api_key"
                      type="password"
                      label={settings.has_openai_api_key ? 'OpenAI API Key (leave blank to keep current)' : 'OpenAI API Key'}
                      value={openaiApiKey}
                      onChange={(e) => setOpenaiApiKey(e.target.value)}
                      placeholder="sk-..."
                      error={errors.openai_api_key}
                    />
                    {settings.has_openai_api_key && (
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
                      value={settings.openai_embedding_model || ''}
                      onChange={(e) => setSettings((prev) => ({ ...prev, openai_embedding_model: e.target.value }))}
                      placeholder="text-embedding-3-large"
                      error={errors.openai_embedding_model}
                    />
                    <Input
                      id="openai_llm_model"
                      label="OpenAI LLM Model"
                      value={settings.openai_llm_model || ''}
                      onChange={(e) => setSettings((prev) => ({ ...prev, openai_llm_model: e.target.value }))}
                      placeholder="gpt-4o-mini"
                      error={errors.openai_llm_model}
                    />
                  </>
                )}

                {errors.general && <p className="text-sm text-red-600">{errors.general}</p>}

                <div className="flex justify-end">
                  <Button type="submit" loading={saving}>Save Settings</Button>
                </div>
              </form>
            </Card>

            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900">Organization Fallback</h3>
              <div className="mt-4 space-y-2 text-sm text-gray-600">
                <p><span className="font-medium text-gray-900">Provider:</span> {settings.organization_ai_provider}</p>
                <p><span className="font-medium text-gray-900">Embedding Model:</span> {settings.organization_openai_embedding_model || 'Not configured'}</p>
                <p><span className="font-medium text-gray-900">LLM Model:</span> {settings.organization_openai_llm_model || 'Not configured'}</p>
                <p><span className="font-medium text-gray-900">Saved API Key:</span> {settings.organization_has_openai_api_key ? 'Configured' : 'Not configured'}</p>
              </div>
            </Card>
          </>
        )}
      </div>
    </AppLayout>
  )
}
