export interface Organization {
  id: string
  name: string
  address?: string
  is_active: boolean
  ai_provider: string
  openai_api_key?: string
  openai_embedding_model?: string
  openai_llm_model?: string
  clear_openai_api_key?: boolean
  has_openai_api_key: boolean
  created_at: string
}

export interface Role {
  id: string
  name: string
  description?: string
  organization_id: string
  is_superadmin: boolean
  is_admin: boolean
  is_read_only: boolean
  created_at: string
}

export interface User {
  id: string
  email: string
  username: string
  full_name?: string
  employee_id?: string
  organization_id: string
  role_id: string
  is_active: boolean
  is_superuser: boolean
  created_at: string
}

export interface AISettings {
  ai_provider: string
  openai_api_key?: string
  openai_embedding_model?: string
  openai_llm_model?: string
  clear_openai_api_key?: boolean
  has_openai_api_key: boolean
  organization_ai_provider: string
  organization_openai_embedding_model?: string
  organization_openai_llm_model?: string
  organization_has_openai_api_key: boolean
}

export interface Department {
  id: string
  name: string
  organization_id: string
  created_at: string
}

export interface DocumentType {
  id: string
  name: string
  organization_id: string
  created_at: string
}

export interface Folder {
  id: string
  name: string
  parent_id?: string
  organization_id: string
  created_by_id: string
  created_at: string
}

export interface Document {
  id: string
  file: string
  file_number?: string
  designation?: string
  subject?: string
  organization_id: string
  organization_name?: string
  department_id?: string
  department_name?: string
  document_type_id?: string
  document_type_name?: string
  folder_id?: string
  status: string
  priority: string
  amount?: string
  uploader_id: string
  is_starred: boolean
  is_archived: boolean
  processing_state: string
  parser_type?: string
  preview_urls: string[]
  created_at: string
  updated_at: string
}

export interface DashboardStats {
  total_organizations: number
  total_users: number
  total_documents: number
  total_departments: number
  recent_activity: DashboardActivity[]
}

export interface DashboardActivity {
  id: string
  action: string
  details?: string
  document_id: string
  document_subject?: string
  file_number?: string
  user_id?: string
  user_name?: string
  created_at?: string
}

export interface SearchResultItem {
  document_id: string
  document_subject?: string
  chunk_id: string
  content: string
  score: number
  page_number?: number
  match_type: string
  department?: string
  document_type?: string
  file_number?: string
  file_date?: string
}

export interface SearchResponse {
  query: string
  language: string
  results: SearchResultItem[]
  total: number
  page: number
  has_more: boolean
  elapsed_ms: number
}

export interface DraftTemplate {
  id: string
  name: string
  label: string
  description: string
  icon: string
}

export interface DraftGenerateRequest {
  template_id: string
  reference_id: string
  instructions?: string
  language?: string
  tone?: string
  fresh_generation?: boolean
}

export interface DraftGenerateResponse {
  draft_text: string
  draft_html: string
  draft_json: string
  relevant_records: SearchResultItem[]
  subject: string
  template_id: string
  language: string
  tone: string
}

export interface DraftCheckResponse {
  exists: boolean
  draft_id?: string
  draft?: DraftGenerateResponse
}

export interface DraftSaveRequest {
  reference_id: string
  template_id: string
  language: string
  tone: string
  subject: string
  instructions: string
  draft_text: string
  draft_html: string
  draft_json: string
}

export interface ApiResponse<T> {
  data?: T
  error?: string
}
