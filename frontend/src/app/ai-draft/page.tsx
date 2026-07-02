'use client'

import { useState, useEffect, useRef } from 'react'
import { AppLayout } from '@/components/Layout/AppLayout'
import { Button, Card, Spinner } from '@/components/ui'
import { useAuth } from '@/context/AuthContext'
import { api } from '@/lib/api'
import { toast } from '@/lib/toast'
import type { DraftTemplate, Document } from '@/lib/types'
import { FileText, Send, Save, Download, Copy, Check, Bold, Italic, Underline, AlignLeft, AlignCenter, AlignRight, List, ListOrdered, ChevronRight, BookOpen } from 'lucide-react'

const TONE_OPTIONS = [
  { value: 'formal', label: 'Formal' },
  { value: 'semi-formal', label: 'Semi-Formal' },
  { value: 'neutral', label: 'Neutral' },
]

const TEMPLATE_ICONS: Record<string, string> = {
  letter: '📄',
  circular: '🔄',
  notice: '📢',
  rti: '📋',
  information: 'ℹ️',
}

export default function AIDraftPage() {
  const { user } = useAuth()
  const orgId = user?.organization_id ?? ''

  const [templates, setTemplates] = useState<DraftTemplate[]>([])
  const [documents, setDocuments] = useState<Document[]>([])
  const [selectedTemplate, setSelectedTemplate] = useState<string>('')
  const [selectedDoc, setSelectedDoc] = useState<string>('')
  const [instructions, setInstructions] = useState('')
  const [language, setLanguage] = useState<'en' | 'hi'>('en')
  const [tone, setTone] = useState('formal')

  const [generating, setGenerating] = useState(false)
  const [draftText, setDraftText] = useState('')
  const [draftSubject, setDraftSubject] = useState('')
  const [savedId, setSavedId] = useState<string | null>(null)
  const [showEditor, setShowEditor] = useState(false)
  const [copied, setCopied] = useState(false)

  const draftEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!orgId) return
    api.drafts.templates().then(setTemplates).catch(() => {})
    api.files.documents.list(orgId).then(setDocuments).catch(() => {})
  }, [orgId])

  useEffect(() => {
    if (draftEndRef.current) {
      draftEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [draftText])

  const handleTemplateSelect = (id: string) => {
    setSelectedTemplate(id)
    setDraftText('')
    setSavedId(null)
    setShowEditor(false)
  }

  const handleGenerate = async () => {
    if (!selectedTemplate || !selectedDoc) {
      toast('Please select a template and reference file', 'error')
      return
    }

    setGenerating(true)
    setDraftText('')
    setShowEditor(false)
    setSavedId(null)
    setCopied(false)

    const token = typeof window !== 'undefined' ? localStorage.getItem('auth') : null
    const accessToken = token ? JSON.parse(token).token : null
    const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

    try {
      const resp = await fetch(`${API_BASE}/draft/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        },
        body: JSON.stringify({
          template_id: selectedTemplate,
          reference_id: selectedDoc,
          instructions: instructions.trim(),
          language,
          tone,
        }),
      })
      const data = await resp.json()
      if (data.result) {
        setDraftText(data.result.draft_text || '')
        setDraftSubject(data.result.subject || '')
        setShowEditor(true)
        toast('Draft generated successfully', 'success')
      } else {
        toast(data.message || 'Generation failed', 'error')
      }
    } catch {
      toast('Failed to generate draft', 'error')
    } finally {
      setGenerating(false)
    }
  }

  const handleSave = async () => {
    if (!draftText.trim() || !selectedDoc) return
    try {
      const result = await api.drafts.save({
        reference_id: selectedDoc,
        template_id: selectedTemplate,
        language,
        tone,
        subject: draftSubject,
        instructions: instructions.trim(),
        draft_text: draftText,
        draft_html: draftText,
        draft_json: JSON.stringify({ draft_text: draftText, subject: draftSubject }),
      })
      setSavedId(result.id)
      toast('Draft saved successfully', 'success')
    } catch {
      toast('Failed to save draft', 'error')
    }
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(draftText)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
      toast('Copied to clipboard', 'success')
    } catch {
      toast('Failed to copy', 'error')
    }
  }

  const handleExport = async (format: string) => {
    if (!savedId) {
      // Save first then export
      await handleSave()
      if (!savedId) return
    }
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('auth') : null
      const accessToken = token ? JSON.parse(token).token : null
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

      const resp = await fetch(`${API_BASE}/draft/export`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        },
        body: JSON.stringify({ draft_id: savedId, format }),
      })
      if (resp.ok) {
        const blob = await resp.blob()
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `draft.${format}`
        a.click()
        URL.revokeObjectURL(url)
        toast('Draft exported', 'success')
      }
    } catch {
      toast('Failed to export draft', 'error')
    }
  }

  const selectedDocData = documents.find(d => d.id === selectedDoc)

  const TEMPLATE_ORDER = ['letter', 'circular', 'notice', 'rti', 'information']

  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h2 className="page-title">AI Draft Generator</h2>
          <p className="text-gray-500 -mt-4 mb-6">Generate government-style documents using AI</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Left Panel - Input */}
          <div className="lg:col-span-2 space-y-4">
            {/* Template Selection */}
            <Card>
              <h3 className="text-sm font-semibold text-gray-800 mb-3">Document Type</h3>
              <div className="grid grid-cols-2 gap-2">
                {TEMPLATE_ORDER.map(id => {
                  const tmpl = templates.find(t => t.id === id)
                  if (!tmpl) return null
                  const active = selectedTemplate === tmpl.id
                  return (
                    <button key={tmpl.id} onClick={() => handleTemplateSelect(tmpl.id)}
                      className={`text-left p-3 rounded-xl border-2 transition-all ${active ? 'border-primary-500 bg-primary-50' : 'border-gray-200 hover:border-gray-300 bg-white'}`}>
                      <span className="text-xl">{TEMPLATE_ICONS[tmpl.id] || '📄'}</span>
                      <p className={`text-sm font-medium mt-1 ${active ? 'text-primary-700' : 'text-gray-800'}`}>{tmpl.name}</p>
                      <p className="text-xs text-gray-400 mt-0.5 line-clamp-2">{tmpl.description}</p>
                    </button>
                  )
                })}
              </div>
            </Card>

            {/* Draft Parameters */}
            <Card>
              <h3 className="text-sm font-semibold text-gray-800 mb-3">Draft Parameters</h3>
              <div className="space-y-3">
                <div>
                  <label className="form-label">Reference File</label>
                  <select value={selectedDoc} onChange={(e) => setSelectedDoc(e.target.value)}
                    className="form-input">
                    <option value="">Select a document...</option>
                    {documents.map(d => (
                      <option key={d.id} value={d.id}>
                        {d.file?.split('/').pop() || d.id} {d.subject ? `- ${d.subject.slice(0, 40)}` : ''}
                      </option>
                    ))}
                  </select>
                  {selectedDocData && (
                    <div className="mt-2 p-2 bg-gray-50 rounded-lg text-xs text-gray-500 space-y-0.5">
                      {selectedDocData.file_number && <p>File No: {selectedDocData.file_number}</p>}
                      {selectedDocData.subject && <p>Subject: {selectedDocData.subject}</p>}
                    </div>
                  )}
                </div>

                <div>
                  <label className="form-label">
                    {language === 'en' ? 'Key Points / Instructions' : 'मुख्य बिंदु / निर्देश'}
                    {selectedTemplate === 'information' && <span className="text-red-500 ml-1">*</span>}
                  </label>
                  <div className="flex gap-2 mb-2">
                    <button onClick={() => setLanguage('en')}
                      className={`text-xs px-2 py-1 rounded ${language === 'en' ? 'bg-primary-100 text-primary-700' : 'bg-gray-100 text-gray-500'}`}>English</button>
                    <button onClick={() => setLanguage('hi')}
                      className={`text-xs px-2 py-1 rounded ${language === 'hi' ? 'bg-primary-100 text-primary-700' : 'bg-gray-100 text-gray-500'}`}>हिन्दी</button>
                  </div>
                  <textarea value={instructions} onChange={(e) => setInstructions(e.target.value)}
                    placeholder={language === 'en' ? 'Enter key points, requirements, or specific instructions...' : 'मुख्य बिंदु, आवश्यकताएं या विशेष निर्देश दर्ज करें...'}
                    rows={4} className="form-input resize-none" />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="form-label">Language</label>
                    <select value={language} onChange={(e) => setLanguage(e.target.value as 'en' | 'hi')}
                      className="form-input">
                      <option value="en">English</option>
                      <option value="hi">हिन्दी</option>
                    </select>
                  </div>
                  <div>
                    <label className="form-label">Tone</label>
                    <select value={tone} onChange={(e) => setTone(e.target.value)}
                      className="form-input">
                      {TONE_OPTIONS.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                    </select>
                  </div>
                </div>

                <Button onClick={handleGenerate} disabled={generating || !selectedTemplate || !selectedDoc} className="w-full">
                  {generating ? <Spinner /> : <Send className="h-4 w-4" />}
                  {generating ? 'Generating...' : 'Generate AI Draft'}
                </Button>
              </div>
            </Card>
          </div>

          {/* Right Panel - Output */}
          <div className="lg:col-span-3 space-y-4">
            <Card className="min-h-[500px] flex flex-col">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-gray-800 flex items-center gap-2">
                  <FileText className="h-4 w-4 text-primary-600" />
                  Generated Draft
                  {selectedTemplate && <span className="text-xs font-normal text-gray-400">/ {templates.find(t => t.id === selectedTemplate)?.name || selectedTemplate}</span>}
                </h3>
                {showEditor && (
                  <div className="flex items-center gap-1">
                    <button onClick={handleCopy} className="p-1.5 rounded hover:bg-gray-100 text-gray-500" title="Copy">
                      {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
                    </button>
                    <button onClick={handleSave} className="p-1.5 rounded hover:bg-gray-100 text-gray-500" title="Save">
                      <Save className="h-4 w-4" />
                    </button>
                    <button onClick={() => handleExport('docx')} className="p-1.5 rounded hover:bg-gray-100 text-gray-500" title="Export DOCX">
                      <Download className="h-4 w-4" />
                    </button>
                  </div>
                )}
              </div>

              {/* Background generation indicator */}
              {generating && (
                <div className="flex items-center gap-2 text-sm text-primary-600 mb-3 pb-3 border-b border-gray-100">
                  <Spinner />
                  <span>Synthesizing document from reference and context...</span>
                </div>
              )}

              {/* Draft Content */}
              <div className="flex-1">
                {!draftText && !generating && (
                  <div className="flex flex-col items-center justify-center py-16 text-gray-400">
                    <BookOpen className="h-12 w-12 mb-3 text-gray-300" />
                    <p className="font-medium text-gray-500">No draft generated yet</p>
                    <p className="text-sm mt-1">Select a template and reference file, then generate</p>
                  </div>
                )}
                {draftText && (
                  <div className="space-y-3">
                    {showEditor && (
                      <div className="flex flex-wrap items-center gap-1 pb-3 border-b border-gray-100">
                        <button className="p-1.5 rounded hover:bg-gray-100 text-gray-600"><Bold className="h-3.5 w-3.5" /></button>
                        <button className="p-1.5 rounded hover:bg-gray-100 text-gray-600"><Italic className="h-3.5 w-3.5" /></button>
                        <button className="p-1.5 rounded hover:bg-gray-100 text-gray-600"><Underline className="h-3.5 w-3.5" /></button>
                        <span className="w-px h-4 bg-gray-200 mx-1" />
                        <button className="p-1.5 rounded hover:bg-gray-100 text-gray-600"><AlignLeft className="h-3.5 w-3.5" /></button>
                        <button className="p-1.5 rounded hover:bg-gray-100 text-gray-600"><AlignCenter className="h-3.5 w-3.5" /></button>
                        <button className="p-1.5 rounded hover:bg-gray-100 text-gray-600"><AlignRight className="h-3.5 w-3.5" /></button>
                        <span className="w-px h-4 bg-gray-200 mx-1" />
                        <button className="p-1.5 rounded hover:bg-gray-100 text-gray-600"><List className="h-3.5 w-3.5" /></button>
                        <button className="p-1.5 rounded hover:bg-gray-100 text-gray-600"><ListOrdered className="h-3.5 w-3.5" /></button>
                      </div>
                    )}
                    <div className="prose prose-sm max-w-none">
                      <textarea
                        value={draftText}
                        onChange={(e) => setDraftText(e.target.value)}
                        className="w-full min-h-[300px] border-0 resize-none text-sm text-gray-800 leading-relaxed focus:outline-none font-mono"
                        style={{ lineHeight: '1.8' }}
                      />
                    </div>
                    <div ref={draftEndRef} />
                  </div>
                )}
              </div>

              {/* Bottom actions */}
              {showEditor && (
                <div className="flex items-center justify-between pt-3 mt-3 border-t border-gray-100">
                  <div className="flex items-center gap-2">
                    {savedId && <span className="text-xs text-green-600 flex items-center gap-1"><Check className="h-3 w-3" /> Saved</span>}
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="secondary" size="sm" onClick={() => handleExport('docx')}>
                      <Download className="h-3.5 w-3.5" /> DOCX
                    </Button>
                    <Button size="sm" onClick={handleSave}>
                      <Save className="h-3.5 w-3.5" /> Save Draft
                    </Button>
                  </div>
                </div>
              )}
            </Card>
          </div>
        </div>
      </div>
    </AppLayout>
  )
}
