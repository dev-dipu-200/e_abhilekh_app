'use client'

import { createSlice, type PayloadAction } from '@reduxjs/toolkit'

interface AiSearchFormState {
  query: string
  language: 'en' | 'hi'
  filterDept: string
  filterDocType: string
  filterYear: string
  showFilters: boolean
}

interface AiDraftFormState {
  selectedTemplate: string
  selectedDoc: string
  instructions: string
  language: 'en' | 'hi'
  tone: string
  isInstructionsHindi: boolean
}

interface FileUploadFormState {
  parserType: string
  designation: string
  subject: string
  departmentId: string
  documentTypeId: string
  selectedOrgId: string
}

interface FormsState {
  aiSearch: AiSearchFormState
  aiDraft: AiDraftFormState
  fileUpload: FileUploadFormState
}

const initialState: FormsState = {
  aiSearch: {
    query: '',
    language: 'en',
    filterDept: '',
    filterDocType: '',
    filterYear: '',
    showFilters: false,
  },
  aiDraft: {
    selectedTemplate: '',
    selectedDoc: '',
    instructions: '',
    language: 'en',
    tone: 'formal',
    isInstructionsHindi: false,
  },
  fileUpload: {
    parserType: 'pymupdf',
    designation: '',
    subject: '',
    departmentId: '',
    documentTypeId: '',
    selectedOrgId: '',
  },
}

const formsSlice = createSlice({
  name: 'forms',
  initialState,
  reducers: {
    patchAiSearch(state, action: PayloadAction<Partial<AiSearchFormState>>) {
      state.aiSearch = { ...state.aiSearch, ...action.payload }
    },
    resetAiSearch(state) {
      state.aiSearch = initialState.aiSearch
    },
    patchAiDraft(state, action: PayloadAction<Partial<AiDraftFormState>>) {
      state.aiDraft = { ...state.aiDraft, ...action.payload }
    },
    resetAiDraft(state) {
      state.aiDraft = initialState.aiDraft
    },
    patchFileUpload(state, action: PayloadAction<Partial<FileUploadFormState>>) {
      state.fileUpload = { ...state.fileUpload, ...action.payload }
    },
    resetFileUpload(state) {
      state.fileUpload = initialState.fileUpload
    },
  },
})

export const {
  patchAiSearch,
  resetAiSearch,
  patchAiDraft,
  resetAiDraft,
  patchFileUpload,
  resetFileUpload,
} = formsSlice.actions

export default formsSlice.reducer
