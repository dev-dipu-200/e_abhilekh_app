'use client'

import { createSlice, type PayloadAction } from '@reduxjs/toolkit'
import type { Department, Document, DocumentType } from '@/lib/types'

type CacheStatus = 'idle' | 'loading' | 'succeeded' | 'failed'

interface ListCache<T> {
  items: T[]
  status: CacheStatus
  loaded: boolean
  error?: string | null
}

interface EntitiesState {
  documentsByOrg: Record<string, ListCache<Document>>
  departmentsByKey: Record<string, ListCache<Department>>
  documentTypesByKey: Record<string, ListCache<DocumentType>>
}

const emptyCache = <T,>(): ListCache<T> => ({
  items: [],
  status: 'idle',
  loaded: false,
  error: null,
})

const initialState: EntitiesState = {
  documentsByOrg: {},
  departmentsByKey: {},
  documentTypesByKey: {},
}

const ensureCache = <T,>(cache: Record<string, ListCache<T>>, key: string): ListCache<T> => {
  return cache[key] || emptyCache<T>()
}

const entitiesSlice = createSlice({
  name: 'entities',
  initialState,
  reducers: {
    setDocumentsLoading(state, action: PayloadAction<string>) {
      state.documentsByOrg[action.payload] = {
        ...ensureCache(state.documentsByOrg, action.payload),
        status: 'loading',
        error: null,
      }
    },
    setDocumentsSuccess(state, action: PayloadAction<{ key: string; items: Document[] }>) {
      state.documentsByOrg[action.payload.key] = {
        items: action.payload.items,
        status: 'succeeded',
        loaded: true,
        error: null,
      }
    },
    setDocumentsFailure(state, action: PayloadAction<{ key: string; error: string }>) {
      state.documentsByOrg[action.payload.key] = {
        ...ensureCache(state.documentsByOrg, action.payload.key),
        status: 'failed',
        error: action.payload.error,
      }
    },
    invalidateDocuments(state, action: PayloadAction<string | undefined>) {
      if (action.payload) {
        delete state.documentsByOrg[action.payload]
        return
      }
      state.documentsByOrg = {}
    },
    setDepartmentsLoading(state, action: PayloadAction<string>) {
      state.departmentsByKey[action.payload] = {
        ...ensureCache(state.departmentsByKey, action.payload),
        status: 'loading',
        error: null,
      }
    },
    setDepartmentsSuccess(state, action: PayloadAction<{ key: string; items: Department[] }>) {
      state.departmentsByKey[action.payload.key] = {
        items: action.payload.items,
        status: 'succeeded',
        loaded: true,
        error: null,
      }
    },
    setDepartmentsFailure(state, action: PayloadAction<{ key: string; error: string }>) {
      state.departmentsByKey[action.payload.key] = {
        ...ensureCache(state.departmentsByKey, action.payload.key),
        status: 'failed',
        error: action.payload.error,
      }
    },
    invalidateDepartments(state, action: PayloadAction<string | undefined>) {
      if (action.payload) {
        delete state.departmentsByKey[action.payload]
        return
      }
      state.departmentsByKey = {}
    },
    setDocumentTypesLoading(state, action: PayloadAction<string>) {
      state.documentTypesByKey[action.payload] = {
        ...ensureCache(state.documentTypesByKey, action.payload),
        status: 'loading',
        error: null,
      }
    },
    setDocumentTypesSuccess(state, action: PayloadAction<{ key: string; items: DocumentType[] }>) {
      state.documentTypesByKey[action.payload.key] = {
        items: action.payload.items,
        status: 'succeeded',
        loaded: true,
        error: null,
      }
    },
    setDocumentTypesFailure(state, action: PayloadAction<{ key: string; error: string }>) {
      state.documentTypesByKey[action.payload.key] = {
        ...ensureCache(state.documentTypesByKey, action.payload.key),
        status: 'failed',
        error: action.payload.error,
      }
    },
    invalidateDocumentTypes(state, action: PayloadAction<string | undefined>) {
      if (action.payload) {
        delete state.documentTypesByKey[action.payload]
        return
      }
      state.documentTypesByKey = {}
    },
  },
})

export const {
  setDocumentsLoading,
  setDocumentsSuccess,
  setDocumentsFailure,
  invalidateDocuments,
  setDepartmentsLoading,
  setDepartmentsSuccess,
  setDepartmentsFailure,
  invalidateDepartments,
  setDocumentTypesLoading,
  setDocumentTypesSuccess,
  setDocumentTypesFailure,
  invalidateDocumentTypes,
} = entitiesSlice.actions

export default entitiesSlice.reducer
