'use client'

import { useState } from 'react'
import { AppLayout } from '@/components/Layout/AppLayout'
import { Button, Card, Spinner } from '@/components/ui'
import { useAuth } from '@/context/AuthContext'
import { api } from '@/lib/api'
import type { SearchResultItem } from '@/lib/types'
import { Search, Languages, FileText } from 'lucide-react'

export default function AISearchPage() {
  const { user } = useAuth()
  const orgId = user?.organization_id ?? ''

  const [query, setQuery] = useState('')
  const [language, setLanguage] = useState<'en' | 'hi'>('en')
  const [results, setResults] = useState<SearchResultItem[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)

  const handleSearch = async () => {
    if (!query.trim() || !orgId) return
    setLoading(true)
    setSearched(true)
    try {
      const resp = await api.files.search({ query: query.trim(), organization_id: orgId, language, limit: 15 })
      setResults(resp.results)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSearch()
  }

  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h2 className="page-title">AI Search</h2>
          <p className="text-gray-500 -mt-4 mb-6">Semantic search across documents in Hindi or English</p>
        </div>

        <Card>
          <div className="space-y-4">
            <div className="flex items-center gap-4 mb-2">
              <span className="text-sm font-medium text-gray-700">Language:</span>
              <button
                onClick={() => setLanguage('en')}
                className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  language === 'en'
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                <Languages className="inline h-4 w-4 mr-1" />
                English
              </button>
              <button
                onClick={() => setLanguage('hi')}
                className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  language === 'hi'
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                <Languages className="inline h-4 w-4 mr-1" />
                हिन्दी
              </button>
            </div>

            <div className="flex gap-3">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={language === 'en' ? 'Search documents...' : 'दस्तावेज़ खोजें...'}
                  className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>
              <Button onClick={handleSearch} disabled={loading || !query.trim()}>
                {loading ? <Spinner /> : 'Search'}
              </Button>
            </div>
          </div>
        </Card>

        <div className="space-y-3">
          {loading && (
            <div className="text-center py-12">
              <Spinner />
              <p className="text-gray-500 mt-2 text-sm">Searching...</p>
            </div>
          )}

          {!loading && searched && results.length === 0 && (
            <Card>
              <div className="text-center py-8 text-gray-500">
                <FileText className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                <p>No results found for &quot;{query}&quot;</p>
                <p className="text-sm mt-1">Try a different search term or upload documents first</p>
              </div>
            </Card>
          )}

          {!loading && results.map((item) => (
            <Card key={item.chunk_id}>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-primary-600" />
                    <span className="font-medium text-sm text-gray-900">
                      {item.document_subject || `Document ${item.document_id}`}
                    </span>
                  </div>
                  <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-green-50 text-green-700">
                    {(item.score * 100).toFixed(1)}% match
                  </span>
                </div>
                <p className="text-sm text-gray-600 line-clamp-3">{item.content}</p>
                <div className="flex items-center gap-3 text-xs text-gray-400">
                  <span>ID: {item.document_id}</span>
                  {item.page_number != null && <span>Page: {item.page_number}</span>}
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </AppLayout>
  )
}
