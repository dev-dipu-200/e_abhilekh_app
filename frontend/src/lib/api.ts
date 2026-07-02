const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

function getToken(): string | null {
  if (typeof window === 'undefined') return null
  try {
    const stored = localStorage.getItem('auth')
    if (stored) return JSON.parse(stored).token
  } catch {}
  return null
}

import { toast } from './toast'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      ...headers,
      ...(options?.headers as Record<string, string>),
    },
    ...options,
  })
  if (res.status === 401) {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth')
      window.location.href = '/login'
    }
    throw new Error('Unauthorized')
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: res.statusText }))
    toast(err.message || 'Request failed', 'error')
    throw new Error(err.message || 'Request failed')
  }
  const data = await res.json()
  if (data && typeof data === 'object' && 'result' in data && 'status_code' in data) {
    if (data.message && data.status_code < 300) {
      toast(data.message, 'success')
    }
    return data.result as T
  }
  return data
}

export { toast }

export const api = {
  organizations: {
    list: () => request<import('./types').Organization[]>('/organizations/'),
    get: (id: string) => request<import('./types').Organization>(`/organizations/${id}`),
    create: (data: Partial<import('./types').Organization>) =>
      request<import('./types').Organization>('/organizations/', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    update: (id: string, data: Partial<import('./types').Organization>) =>
      request<import('./types').Organization>(`/organizations/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
    delete: (id: string) =>
      request<void>(`/organizations/${id}`, { method: 'DELETE' }),
  },

  roles: {
    list: (orgId?: string) =>
      request<import('./types').Role[]>(`/roles/${orgId ? `?organization_id=${orgId}` : ''}`),
    get: (id: string) => request<import('./types').Role>(`/roles/${id}`),
    create: (data: Partial<import('./types').Role>) =>
      request<import('./types').Role>('/roles/', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: string, data: Partial<import('./types').Role>) =>
      request<import('./types').Role>(`/roles/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (id: string) => request<void>(`/roles/${id}`, { method: 'DELETE' }),
  },

  users: {
    list: (orgId?: string) =>
      request<import('./types').User[]>(`/users/${orgId ? `?organization_id=${orgId}` : ''}`),
    get: (id: string) => request<import('./types').User>(`/users/${id}`),
    create: (data: Partial<import('./types').User> & { password: string }) =>
      request<import('./types').User>('/users/', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: string, data: Partial<import('./types').User>) =>
      request<import('./types').User>(`/users/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (id: string) => request<void>(`/users/${id}`, { method: 'DELETE' }),
  },

  departments: {
    list: (orgId?: string) =>
      request<import('./types').Department[]>(`/departments/${orgId ? `?organization_id=${orgId}` : ''}`),
    get: (id: string) => request<import('./types').Department>(`/departments/${id}`),
    create: (data: Partial<import('./types').Department>) =>
      request<import('./types').Department>('/departments/', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: string, data: Partial<import('./types').Department>) =>
      request<import('./types').Department>(`/departments/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (id: string) => request<void>(`/departments/${id}`, { method: 'DELETE' }),
  },

  documentTypes: {
    list: (orgId?: string) =>
      request<import('./types').DocumentType[]>(`/document-types/${orgId ? `?organization_id=${orgId}` : ''}`),
    get: (id: string) => request<import('./types').DocumentType>(`/document-types/${id}`),
    create: (data: Partial<import('./types').DocumentType>) =>
      request<import('./types').DocumentType>('/document-types/', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: string, data: Partial<import('./types').DocumentType>) =>
      request<import('./types').DocumentType>(`/document-types/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (id: string) => request<void>(`/document-types/${id}`, { method: 'DELETE' }),
  },

  files: {
    documents: {
      list: (orgId: string, folderId?: string) =>
        request<import('./types').Document[]>(`/files/documents?organization_id=${orgId}${folderId ? `&folder_id=${folderId}` : ''}`),
      get: (id: string) => request<import('./types').Document>(`/files/documents/${id}`),
      upload: async (orgId: string, file: File, extra: { department_id: string; document_type_id: string; subject: string; folder_id?: string; parser_type?: string; designation?: string }) => {
        const token = getToken()
        const form = new FormData()
        form.append('file', file)
        const params = new URLSearchParams({ organization_id: orgId, department_id: extra.department_id, document_type_id: extra.document_type_id, subject: extra.subject })
        if (extra?.folder_id) params.append('folder_id', extra.folder_id)
        if (extra?.parser_type) params.append('parser_type', extra.parser_type)
        if (extra?.designation) params.append('designation', extra.designation)
        const res = await fetch(`${API_BASE}/files/documents?${params}`, {
          method: 'POST',
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          body: form,
        })
        if (!res.ok) {
          const err = await res.json().catch(() => ({ message: 'Upload failed' }))
          toast(err.message || 'Upload failed', 'error')
          throw new Error(err.message || 'Upload failed')
        }
        const data = await res.json()
        if (data.message && data.status_code < 300) toast(data.message, 'success')
        return data.result as import('./types').Document
      },
      update: (id: string, data: Partial<import('./types').Document>) =>
        request<import('./types').Document>(`/files/documents/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
      delete: (id: string) => request<void>(`/files/documents/${id}`, { method: 'DELETE' }),
    },
    search: (data: { query: string; organization_id: string; language?: string; department_id?: string; document_type_id?: string; year?: number; date_from?: string; date_to?: string; status?: string; page?: number; page_size?: number }) =>
      request<import('./types').SearchResponse>('/files/search', {
        method: 'POST',
        body: JSON.stringify({ ...data, language: data.language || 'en', page: data.page || 1, page_size: data.page_size || 10 }),
      }),
    folders: {
      list: (orgId: string, parentId?: string) =>
        request<import('./types').Folder[]>(`/files/folders?organization_id=${orgId}${parentId ? `&parent_id=${parentId}` : ''}`),
      create: (data: Partial<import('./types').Folder>) =>
        request<import('./types').Folder>('/files/folders', { method: 'POST', body: JSON.stringify(data) }),
      delete: (id: string) => request<void>(`/files/folders/${id}`, { method: 'DELETE' }),
    },
    departmentsList: (orgId: string) =>
      request<{ id: string; name: string }[]>(`/files/departments-list?organization_id=${orgId}`),
    documentTypesList: (orgId: string) =>
      request<{ id: string; name: string }[]>(`/files/document-types-list?organization_id=${orgId}`),
  },

  drafts: {
    templates: () =>
      request<import('./types').DraftTemplate[]>('/draft/templates'),
    generateStream: (data: import('./types').DraftGenerateRequest) =>
      `/draft/generate/stream`,
    generate: (data: import('./types').DraftGenerateRequest) =>
      request<import('./types').DraftGenerateResponse>('/draft/generate', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    check: (data: { reference_id: string; template_id: string; language?: string }) =>
      request<import('./types').DraftCheckResponse>('/draft/check', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    save: (data: import('./types').DraftSaveRequest) =>
      request<{ id: string; template_type: string }>('/draft/save', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    export: (draftId: string, format: string = 'docx') =>
      `${API_BASE}/draft/export`,
    attach: (draftId: string, documentId: string) =>
      request<{ id: string; filename: string }>('/draft/attach', {
        method: 'POST',
        body: JSON.stringify({ draft_id: draftId, document_id: documentId }),
      }),
  },

  dashboard: {
    stats: () => request<import('./types').DashboardStats>('/admin/dashboard'),
  },
}
