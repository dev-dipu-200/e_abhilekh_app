'use client'

import { api } from '@/lib/api'
import type { AppDispatch, RootState } from './index'
import {
  setDepartmentsFailure,
  setDepartmentsLoading,
  setDepartmentsSuccess,
  setDocumentTypesFailure,
  setDocumentTypesLoading,
  setDocumentTypesSuccess,
} from './slices/entitiesSlice'

export const ALL_SCOPE_KEY = '__all__'

export function getScopeKey(isSuperuser: boolean, organizationId: string) {
  return isSuperuser ? ALL_SCOPE_KEY : organizationId
}

export async function ensureDepartments(
  dispatch: AppDispatch,
  getState: () => RootState,
  organizationId: string,
  isSuperuser: boolean,
  force = false
) {
  const key = getScopeKey(isSuperuser, organizationId)
  if (!key) return
  const cache = getState().entities.departmentsByKey[key]
  if (!force && cache?.loaded) return
  dispatch(setDepartmentsLoading(key))
  try {
    const items = isSuperuser ? await api.departments.list() : await api.departments.list(organizationId)
    dispatch(setDepartmentsSuccess({ key, items }))
  } catch (error) {
    dispatch(setDepartmentsFailure({ key, error: error instanceof Error ? error.message : 'Failed to load departments' }))
    throw error
  }
}

export async function ensureDocumentTypes(
  dispatch: AppDispatch,
  getState: () => RootState,
  organizationId: string,
  isSuperuser: boolean,
  force = false
) {
  const key = getScopeKey(isSuperuser, organizationId)
  if (!key) return
  const cache = getState().entities.documentTypesByKey[key]
  if (!force && cache?.loaded) return
  dispatch(setDocumentTypesLoading(key))
  try {
    const items = isSuperuser ? await api.documentTypes.list() : await api.documentTypes.list(organizationId)
    dispatch(setDocumentTypesSuccess({ key, items }))
  } catch (error) {
    dispatch(setDocumentTypesFailure({ key, error: error instanceof Error ? error.message : 'Failed to load document types' }))
    throw error
  }
}
