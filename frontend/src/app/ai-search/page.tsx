'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { AppLayout } from '@/components/Layout/AppLayout'
import { Button, Card, Spinner, Badge } from '@/components/ui'
import { useAuth } from '@/context/AuthContext'
import { api } from '@/lib/api'
import type { SearchResultItem } from '@/lib/types'
import { Search, Languages, FileText, X, Filter, ChevronDown, Clock, BookOpen } from 'lucide-react'

export default function AISearchPage() {
  const { user } = useAuth()
  const router = useRouter()
  const orgId = user?.organization_id ?? ''

  const [query, setQuery] = useState('')
  const [language, setLanguage] = useState<'en' | 'hi'>('en')
  const [results, setResults] = useState<SearchResultItem[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(false)
  const [elapsed, setElapsed] = useState(0)
  const [showFilters, setShowFilters] = useState(false)

  const [departments, setDepartments] = useState<{ id: string; name: string }[]>([])
  const [docTypes, setDocTypes] = useState<{ id: string; name: string }[]>([])
  const [filterDept, setFilterDept] = useState('')
  const [filterDocType, setFilterDocType] = useState('')
  const [filterYear, setFilterYear] = useState('')

  useEffect(() => {
    if (!orgId) return
    api.files.departmentsList(orgId).then(setDepartments).catch(() => {})
    api.files.documentTypesList(orgId).then(setDocTypes).catch(() => {})
  }, [orgId])

  const doSearch = useCallback(async (pageNum: number = 1, append: boolean = false) => {
    if (!query.trim() || !orgId) return
    setLoading(true)
    setSearched(true)
    try {
      const resp = await api.files.search({
        query: query.trim(),
        organization_id: orgId,
        language,
        department_id: filterDept || undefined,
        document_type_id: filterDocType || undefined,
        year: filterYear ? parseInt(filterYear) : undefined,
        page: pageNum,
        page_size: 10,
      })
      if (append) {
        setResults(prev => [...prev, ...resp.results])
      } else {
        setResults(resp.results)
      }
      setPage(pageNum)
      setHasMore(resp.has_more)
      setElapsed(resp.elapsed_ms)
    } finally {
      setLoading(false)
    }
  }, [query, orgId, language, filterDept, filterDocType, filterYear])

  const handleSearch = () => doSearch(1)

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSearch()
  }

  const loadMore = () => doSearch(page + 1, true)

  const clearFilters = () => {
    setFilterDept('')
    setFilterDocType('')
    setFilterYear('')
  }

  const hasFilters = filterDept || filterDocType || filterYear

  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h2 className="page-title">AI Search</h2>
          <p className="text-gray-500 -mt-4 mb-6">Semantic document search with filters</p>
        </div>

        {/* Search Hero */}
        <Card>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-sm font-medium text-gray-700">Language:</span>
                <button onClick={() => setLanguage('en')}
                  className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${language === 'en' ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
                  <Languages className="inline h-4 w-4 mr-1" />English
                </button>
                <button onClick={() => setLanguage('hi')}
                  className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${language === 'hi' ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
                  <Languages className="inline h-4 w-4 mr-1" />हिन्दी
                </button>
              </div>
              <button onClick={() => setShowFilters(!showFilters)}
                className={`flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg transition-colors ${showFilters ? 'bg-primary-50 text-primary-700' : 'text-gray-500 hover:text-gray-700'}`}>
                <Filter className="h-4 w-4" /> Filters {hasFilters && <Badge variant="blue">!</Badge>}
              </button>
            </div>

            <div className="flex gap-3">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input type="text" value={query} onChange={(e) => setQuery(e.target.value)} onKeyDown={handleKeyDown}
                  placeholder={language === 'en' ? 'Search documents by content...' : 'दस्तावेज़ सामग्री खोजें...'}
                  className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent" />
              </div>
              <Button onClick={handleSearch} disabled={loading || !query.trim()}>
                {loading ? <Spinner /> : <><Search className="h-4 w-4" /> Run Smart Search</>}
              </Button>
            </div>

            {/* Filter Panel */}
            {showFilters && (
              <div className="flex flex-wrap items-end gap-3 pt-2 border-t border-gray-100">
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Department</label>
                  <select value={filterDept} onChange={(e) => setFilterDept(e.target.value)}
                    className="form-input text-sm py-1.5 pr-8">
                    <option value="">All Departments</option>
                    {departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Document Type</label>
                  <select value={filterDocType} onChange={(e) => setFilterDocType(e.target.value)}
                    className="form-input text-sm py-1.5 pr-8">
                    <option value="">All Types</option>
                    {docTypes.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Year</label>
                  <input type="number" value={filterYear} onChange={(e) => setFilterYear(e.target.value)}
                    placeholder="e.g. 2026" className="form-input text-sm py-1.5 w-24" />
                </div>
                {hasFilters && (
                  <button onClick={clearFilters} className="text-xs text-red-500 hover:text-red-700 flex items-center gap-1 pb-1">
                    <X className="h-3 w-3" /> Clear Filters
                  </button>
                )}
              </div>
            )}
          </div>
        </Card>

        {/* Results */}
        <div className="space-y-3">
          {loading && results.length === 0 && (
            <div className="text-center py-16">
              <Spinner />
              <p className="text-gray-500 mt-2 text-sm">Searching documents...</p>
            </div>
          )}

          {!loading && searched && results.length === 0 && (
            <Card>
              <div className="text-center py-10 text-gray-500">
                <Search className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                <p className="font-medium">No results found for &ldquo;{query}&rdquo;</p>
                <p className="text-sm mt-1">Try different search terms or adjust filters</p>
              </div>
            </Card>
          )}

          {results.length > 0 && (
            <>
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-500">
                  Found {results.length} results {elapsed > 0 && <span className="ml-2">(<Clock className="inline h-3 w-3" /> {elapsed}ms)</span>}
                </p>
              </div>

              {results.map((item) => (
                <Card key={item.chunk_id}>
                  <div className="space-y-2">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-2 min-w-0">
                        <FileText className="h-4 w-4 text-primary-600 shrink-0 mt-0.5" />
                        <button onClick={() => router.push(`/files/${item.document_id}`)}
                          className="font-medium text-sm text-gray-900 hover:text-primary-600 text-left truncate">
                          {item.document_subject || `Document ${item.document_id.slice(0, 12)}...`}
                        </button>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <Badge variant={item.match_type === 'exact' ? 'green' : 'blue'}>
                          {item.match_type === 'exact' ? 'Exact Match' : 'Semantic Match'}
                        </Badge>
                        <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-purple-50 text-purple-700">
                          {(item.score * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 line-clamp-3 leading-relaxed">{item.content}</p>
                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-gray-400">
                      {item.file_number && <span>File No: {item.file_number}</span>}
                      {item.department && <span>Dept: {item.department}</span>}
                      {item.document_type && <span>Type: {item.document_type}</span>}
                      {item.page_number != null && <span>Page: {item.page_number}</span>}
                      {item.file_date && <span>Date: {item.file_date}</span>}
                    </div>
                  </div>
                </Card>
              ))}

              {hasMore && (
                <div className="text-center pt-2">
                  <Button variant="secondary" onClick={loadMore} loading={loading}>
                    <ChevronDown className="h-4 w-4" /> Load More Results
                  </Button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </AppLayout>
  )
}
