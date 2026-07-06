'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { AppLayout } from '@/components/Layout/AppLayout'
import { Button, Card, Spinner, Badge } from '@/components/ui'
import { useAuth } from '@/context/AuthContext'
import { api } from '@/lib/api'
import { ensureDepartments, ensureDocumentTypes, getScopeKey } from '@/lib/store/catalog'
import { store } from '@/lib/store'
import { useAppDispatch, useAppSelector } from '@/lib/store/hooks'
import { patchAiSearch, resetAiSearch } from '@/lib/store/slices/formsSlice'
import type { SearchResultItem } from '@/lib/types'
import { Search, Languages, FileText, X, Filter, ChevronDown, Clock, BookOpen, ArrowRight, Sparkles } from 'lucide-react'
import { fetchSuggestions } from '@/lib/transliterate'

export default function AISearchPage() {
  const { user } = useAuth()
  const dispatch = useAppDispatch()
  const router = useRouter()
  const orgId = user?.organization_id ?? ''
  const isSuperuser = !!user?.is_superuser
  const scopeKey = getScopeKey(isSuperuser, orgId)

  const { query, language, filterDept, filterDocType, filterYear, showFilters } = useAppSelector((state) => state.forms.aiSearch)
  const [results, setResults] = useState<SearchResultItem[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  const [nextCursor, setNextCursor] = useState<string | null>(null)
  const [hasMore, setHasMore] = useState(false)
  const [elapsed, setElapsed] = useState(0)
  const departments = useAppSelector((state) => state.entities.departmentsByKey[scopeKey]?.items || [])
  const docTypes = useAppSelector((state) => state.entities.documentTypesByKey[scopeKey]?.items || [])
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [suggestIndex, setSuggestIndex] = useState(-1)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (!orgId) return
    ensureDepartments(dispatch, store.getState, orgId, isSuperuser).catch(() => {})
    ensureDocumentTypes(dispatch, store.getState, orgId, isSuperuser).catch(() => {})
  }, [dispatch, isSuperuser, orgId])

  const doSearch = useCallback(async (cursor?: string | null, append: boolean = false) => {
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
        page_size: 10,
        cursor: cursor || undefined,
      })
      if (append) {
        setResults(prev => [...prev, ...resp.results])
      } else {
        setResults(resp.results)
      }
      setNextCursor(resp.next_cursor || null)
      setHasMore(resp.has_more)
      setElapsed(resp.elapsed_ms)
    } finally {
      setLoading(false)
    }
  }, [query, orgId, language, filterDept, filterDocType, filterYear])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    dispatch(patchAiSearch({ query: e.target.value }))
    if (e.target.value.endsWith(' ')) setSuggestions([])
  }

  const handleSpace = async () => {
    const words = query.split(/\s+/)
    const lastWord = words[words.length - 1]
    if (!lastWord || /[\u0900-\u097F]/.test(lastWord) || language !== 'hi') {
      setSuggestions([])
      dispatch(patchAiSearch({ query: query + ' ' }))
      return
    }
    dispatch(patchAiSearch({ query: query + ' ' }))
    const sugs = await fetchSuggestions(lastWord)
    if (sugs.length) {
      setSuggestions(sugs)
      setSuggestIndex(0)
    } else {
      setSuggestions([])
    }
  }

  const applySuggestion = (sug: string) => {
    const words = query.replace(/\s+$/, '').split(/\s+/)
    words[words.length - 1] = sug
    dispatch(patchAiSearch({ query: words.join(' ') + ' ' }))
    setSuggestions([])
    setSuggestIndex(-1)
    inputRef.current?.focus()
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (suggestions.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSuggestIndex(prev => Math.min(prev + 1, suggestions.length - 1))
        return
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSuggestIndex(prev => Math.max(prev - 1, 0))
        return
      }
      if (e.key === 'Enter' && suggestIndex >= 0) {
        e.preventDefault()
        applySuggestion(suggestions[suggestIndex])
        return
      }
      if (e.key === 'Tab' && suggestIndex >= 0) {
        e.preventDefault()
        applySuggestion(suggestions[suggestIndex])
        return
      }
    }
    if (language === 'hi' && e.key === ' ' && !e.repeat) {
      e.preventDefault()
      handleSpace()
      return
    }
    if (e.key === 'Enter') handleSearch()
    if (e.key === 'Escape') setSuggestions([])
  }

  const handleSearch = () => doSearch(null)

  const loadMore = () => doSearch(nextCursor, true)

  const clearFilters = () => {
    dispatch(patchAiSearch({ filterDept: '', filterDocType: '', filterYear: '' }))
  }

  const handleReset = () => {
    dispatch(resetAiSearch())
    setResults([])
    setSearched(false)
    setNextCursor(null)
    setHasMore(false)
    setElapsed(0)
    setSuggestions([])
    setSuggestIndex(-1)
  }

  const hasFilters = filterDept || filterDocType || filterYear

  const highlightMatches = (text: string) => {
    if (!query.trim()) return text
    const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const parts = text.split(new RegExp(`(${escaped})`, 'gi'))
    return parts.map((part, i) =>
      part.toLowerCase() === query.toLowerCase()
        ? <span key={i} className="text-orange-600 bg-orange-50 font-medium rounded px-0.5">{part}</span>
        : part
    )
  }

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
                <button onClick={() => dispatch(patchAiSearch({ language: 'en' }))}
                  className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${language === 'en' ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
                  <Languages className="inline h-4 w-4 mr-1" />English
                </button>
                <button onClick={() => dispatch(patchAiSearch({ language: 'hi' }))}
                  className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${language === 'hi' ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
                  <Languages className="inline h-4 w-4 mr-1" />हिन्दी
                </button>
              </div>
              <div className="flex items-center gap-2">
                <Button type="button" variant="secondary" size="sm" onClick={handleReset}>Reset</Button>
                <button onClick={() => dispatch(patchAiSearch({ showFilters: !showFilters }))}
                className={`flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg transition-colors ${showFilters ? 'bg-primary-50 text-primary-700' : 'text-gray-500 hover:text-gray-700'}`}>
                <Filter className="h-4 w-4" /> Filters {hasFilters && <Badge variant="blue">!</Badge>}
              </button>
              </div>
            </div>

            <div className="flex gap-3">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input ref={inputRef} type="text" value={query} onChange={handleInputChange} onKeyDown={handleKeyDown}
                  lang={language === 'hi' ? 'hi' : 'en'} dir={language === 'hi' ? 'auto' : 'ltr'}
                  placeholder={language === 'en' ? 'Search documents by content...' : 'दस्तावेज़ सामग्री खोजें...'}
                  className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent" />
                {/* Transliteration suggestions */}
                {suggestions.length > 0 && (
                  <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-xl shadow-lg z-50 overflow-hidden">
                    {suggestions.map((sug, i) => (
                      <button key={i} onClick={() => applySuggestion(sug)}
                        onMouseEnter={() => setSuggestIndex(i)}
                        className={`w-full text-left px-4 py-2 text-sm flex items-center gap-2 transition-colors ${i === suggestIndex ? 'bg-primary-50 text-primary-700' : 'text-gray-700 hover:bg-gray-50'}`}>
                        <ArrowRight className={`h-3 w-3 ${i === suggestIndex ? 'text-primary-500' : 'text-gray-300'}`} />
                        <span className="text-base">{sug}</span>
                      </button>
                    ))}
                    <p className="px-4 py-1.5 text-xs text-gray-400 border-t border-gray-100 bg-gray-50/50">
                      ↑↓ Navigate · Enter/Tab select · Esc close
                    </p>
                  </div>
                )}
              </div>
              <Button onClick={handleSearch} disabled={loading || !query.trim()}>
                {loading ? <Spinner /> : <><Search className="h-4 w-4" /> Run Smart Search</>}
              </Button>
            </div>
            {language === 'hi' && (
              <p className="text-xs text-gray-400 flex items-center gap-1">
                <Languages className="h-3 w-3" /> हिंदी · type & press Space to transliterate
              </p>
            )}

            {/* Filter Panel */}
            {showFilters && (
              <div className="flex flex-wrap items-end gap-3 pt-2 border-t border-gray-100">
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Department</label>
                  <select value={filterDept} onChange={(e) => dispatch(patchAiSearch({ filterDept: e.target.value }))}
                    className="form-input text-sm py-1.5 pr-8">
                    <option value="">All Departments</option>
                    {departments.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Document Type</label>
                  <select value={filterDocType} onChange={(e) => dispatch(patchAiSearch({ filterDocType: e.target.value }))}
                    className="form-input text-sm py-1.5 pr-8">
                    <option value="">All Types</option>
                    {docTypes.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Year</label>
                  <input type="number" value={filterYear} onChange={(e) => dispatch(patchAiSearch({ filterYear: e.target.value }))}
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
                  <button onClick={() => router.push(`/files/${item.document_id}?page=${item.page_number || 1}`)}
                    className="w-full text-left space-y-2 cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 rounded-lg">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-2 min-w-0">
                        <FileText className="h-4 w-4 text-primary-600 shrink-0 mt-0.5" />
                        <span className="font-medium text-sm text-gray-900 hover:text-primary-600 truncate">
                          {item.document_subject || `Document ${item.document_id.slice(0, 12)}...`}
                        </span>
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
                    <p className="text-sm text-gray-600 line-clamp-3 leading-relaxed">{highlightMatches(item.content)}</p>
                      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-gray-400">
                        {item.file_number && <span>File No: {item.file_number}</span>}
                        {item.department && <span>Dept: {item.department}</span>}
                        {item.document_type && <span>Type: {item.document_type}</span>}
                        {item.page_number != null && <span>Page: {item.page_number}</span>}
                        {item.file_date && <span>Date: {item.file_date}</span>}
                      </div>
                      <div className="pt-2">
                        <Button variant="primary" size="sm" onClick={(e) => { e.stopPropagation(); router.push(`/ai-draft?document_id=${item.document_id}`) }}>
                          <Sparkles className="h-3.5 w-3.5" /> Generate Draft
                        </Button>
                      </div>
                    </button>
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
