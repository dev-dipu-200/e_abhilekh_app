# Abhilekh Application Details

## 1. Application Overview

Abhilekh is a Django-based document management and AI-assisted drafting platform. It is designed for multi-organization use, where each organization manages its own users, departments, document types, folders, uploaded files, and AI-generated drafts. The application combines traditional document workflows with Retrieval-Augmented Generation (RAG), OCR, semantic search, and formal draft generation.

Core business capabilities:

- User authentication and password reset
- Organization, role, and user administration
- Role-based access control
- Department and document type management
- Folder-based document storage
- File upload and metadata tracking
- Notes and attachments on documents
- Activity history for document actions
- OCR and text extraction from uploaded files
- Semantic search over indexed documents
- AI draft generation and export
- Hindi and English UI support

## 2. Technology Stack

Backend stack:

- Python 3.11 runtime in Docker
- Django 4.2
- PostgreSQL for relational data
- Celery for background processing
- Redis as Celery broker/result backend
- Qdrant as vector store for semantic retrieval

AI and OCR stack:

- OpenAI for embeddings and LLM generation
- Ollama as an optional local alternative for embeddings and generation
- Google Document AI for structured OCR/layout extraction
- EasyOCR as an alternate OCR provider
- `pypdf` and `pypdfium2` for PDF reading and rendering

Document export stack:

- ReportLab for PDF export
- `python-docx` for DOCX export

Frontend:

- Django template rendering
- Shared templates in `templates/`
- Static CSS in `static/css/style.css`
- Devanagari font support via `static/fonts/Lohit-Devanagari.ttf`

## 3. High-Level Architecture

The repository is organized into one Django project and three main apps:

- `abhilekh_project/`: project settings, root URL configuration, Celery bootstrap
- `accounts/`: authentication, organizations, roles, users, email flows
- `core/`: document management, dashboard, file operations, AI drafting
- `rag/`: OCR, extraction, indexing, semantic search, ingestion tracking

Application flow at a high level:

1. A user logs in and is scoped to an organization.
2. The user uploads a PDF document into the file management system.
3. The upload creates a `Document` record and stores the file in `files/`.
4. A Django signal queues a Celery ingestion task when the file is marked for processing.
5. The RAG service extracts text and metadata, chunks the text, generates embeddings, and stores vectors in Qdrant.
6. Users can use Smart Search to retrieve matching records by semantic and lexical relevance.
7. Users can generate official drafts using reference content from indexed documents and save, export, or attach the generated draft.

## 4. Project Structure

Important paths in the repository:

- `manage.py`: Django command entrypoint
- `abhilekh_project/settings.py`: central configuration
- `abhilekh_project/urls.py`: root routing
- `abhilekh_project/celery.py`: Celery app setup
- `accounts/`: user and access management
- `core/`: main business workflows
- `rag/`: search and ingestion pipeline
- `templates/`: HTML templates
- `static/`: CSS and fonts
- `docker/`: startup scripts and Nginx config
- `docker-compose.yml`: development container setup
- `docker-compose.prod.yml`: production container setup

## 5. Configuration and Environment

The application loads environment variables from `.env` using `python-dotenv`.

Required environment variables:

- `SECRET_KEY`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`

Important optional variables:

- `DEBUG`
- `DB_HOST`
- `DB_PORT`
- `CSRF_TRUSTED_ORIGINS`
- `USE_X_FORWARDED_HOST`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `RAG_CHUNK_SIZE`
- `RAG_CHUNK_OVERLAP`
- `RAG_SEARCH_LIMIT`
- `RAG_EMBEDDING_MODEL`
- `RAG_EMBEDDING_DIMENSION`
- `OPENAI_MODEL`
- `OLLAMA_HOST`
- `OLLAMA_EMBED_MODEL`
- `OLLAMA_MODEL`
- `OCR_PROVIDER_DEFAULT`
- `OCR_PROVIDER_FALLBACK_ENABLED`
- `DOCUMENT_AI_PROJECT_ID`
- `DOCUMENT_AI_LOCATION`
- `DOCUMENT_AI_PROCESSOR_ID`
- `DOCUMENT_AI_PROCESSOR_VERSION`
- `QDRANT_URL`
- `QDRANT_API_KEY`
- `QDRANT_COLLECTION_NAME`
- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `DEFAULT_FROM_EMAIL`

Key settings behavior:

- Custom user model is `accounts.User`
- Media files are stored under `files/`
- Static files are collected into `staticfiles/`
- Session expiry is browser-close based with a 30-minute cookie age
- RAG tasks are routed to queue `rag`
- Celery beat syncs processing statuses every 30 seconds
- `rag` uses a custom migration module path: `rag/db_migrations`

## 6. URL Structure

Top-level routes:

- `/admin/`: Django admin
- `/i18n/`: language switching
- `/accounts/`: login, password reset, user/org/role management
- `/rag/`: Smart Search workspace and RAG APIs
- `/`: dashboard, file management, document APIs, AI draft module

Language-aware URLs are mounted with `i18n_patterns`, so translated paths can be served with locale prefixes.

## 7. Accounts Module

The `accounts` app handles identity and administration.

Main models:

- `Organization`
  - Name, address, active flag, created timestamp
  - Used as the tenant boundary for most application data
- `Role`
  - Name, description, explicit Django permissions
  - Includes flags for all-access, read-only, superadmin, and org-admin behavior
- `User`
  - Extends Django `AbstractUser`
  - Uses unique email
  - Belongs to one role and one organization
  - Supports employee ID and deactivation flag

Notable behavior:

- `User.has_role_perm()` applies role-based permission logic
- Superuser and superadmin role bypass most checks
- Read-only roles are allowed `view_*` permissions only

Main views and capabilities:

- `login_view`: username/email login
- `HtmlPasswordResetView`: HTML email password reset
- `user_profile_api`: current user profile and permission payload
- Organization management APIs and forms
- Role management APIs and forms
- User management APIs and forms

Access control helpers:

- `is_admin()`: superuser, superadmin role, or org admin
- `is_superadmin()`: superuser or superadmin role

Email support:

- Password reset emails are sent asynchronously using a thread pool
- New user credentials and profile update emails are template-based

## 8. Core Module

The `core` app contains the main document and workflow logic.

### 8.1 Data Model

- `Department`
  - Belongs to an organization
  - Unique by name within organization

- `DocumentType`
  - Belongs to an organization
  - Unique by name within organization

- `Folder`
  - Supports parent-child hierarchy
  - Belongs to an organization
  - Created by a user

- `Document`
  - Central file record
  - Stores file, folder, organization, file number, subject, department, document type, dates, status, priority, amount, current holder, uploader, starred/archive state, processing state, parser type
  - Deletes the physical file on record deletion

- `Note`
  - User-authored note attached to a document

- `Attachment`
  - Extra file attached to a document
  - Deletes the physical attachment file on deletion

- `GeneratedDraft`
  - Stores AI output
  - Includes template type, language, tone, text, HTML, JSON, and optional attached/reference document relationships

- `ActivityLog`
  - Tracks actions against a document

### 8.2 Document Storage

Uploaded document path format:

- `files/<organization>/<folder hierarchy>/<filename>`
- If no folder exists, documents are stored under the organization `root/`

Attachment path format:

- `files/<organization>/attachments/<document_id>/<filename>`

### 8.3 Document Features

The document management feature set includes:

- Dashboard overview
- Upload page
- File management listing
- Folder creation, deletion, and file movement
- Department and document type CRUD
- Document detail view
- Secure document and attachment serving
- File download
- PDF preview page rendering
- Starred and archived toggles
- Note and attachment addition
- Assignment to current holder
- Metadata updates

Status and priority concepts:

- Status values: `new`, `pending`, `urgent`, `approved`, `rejected`, `in_review`, `forwarded`
- Priority values: `high`, `medium`, `low`
- Upload processing values: `pending`, `in_progress`, `done`, `failed`

Upload validation currently enforces:

- PDF-only uploads
- Maximum file size of 50 MB
- Maximum 30 pages
- Rejection of image uploads in the document upload endpoint

### 8.4 Dashboard

The dashboard aggregates organization-scoped information such as:

- Recent documents
- Department workload
- Recent activity
- Urgent notifications
- Pagination state
- Status badges and localized time labels

### 8.5 AI Draft Generator

The AI draft generator is a major feature inside `core/views.py`.

Supported draft formats:

- Official letter
- Circular
- Notice
- RTI reply
- Information

Capabilities:

- Build draft context from indexed records
- Use a reference document where available
- Generate normal or streamed responses
- Normalize generated JSON/text
- Detect and repair language mismatches
- Export generated output to PDF or DOCX
- Save generated drafts in the database
- Attach generated drafts back to documents

Important implementation characteristics:

- Prompt construction is heavily rule-based
- Hindi text normalization is explicitly handled
- Reference facts and semantic context are extracted before generation
- Export supports text-origin and image-origin draft content

## 9. RAG Module

The `rag` app provides ingestion tracking, OCR, vector indexing, and search.

### 9.1 Data Model

- `RAGIngestion`
  - One-to-one with `core.Document`
  - Tracks extraction status, text, metadata, error, Celery task ID, timing

- `RAGChunk`
  - Stores chunk text and embedding data per document
  - Unique by document and chunk index

- `OCRProviderConfiguration`
  - Singleton-style model
  - Stores the active OCR provider
  - Admin prevents multiple records

### 9.2 Ingestion Lifecycle

Document ingestion flow:

1. A `Document` is created with `file_uploaded='in_progress'`.
2. `rag.signals.enqueue_new_document_processing` schedules processing after transaction commit.
3. `rag.tasks.enqueue_document_processing()` creates or reuses the `RAGIngestion` record and delays the Celery task based on current backlog.
4. `process_document_for_rag()` marks the ingestion as started.
5. Text and metadata are extracted from the file.
6. Text is chunked and embedded.
7. Chunks and vectors are stored.
8. Processing state is updated to `done` or `failed`.

There is retry logic for transient OCR/provider failures, with exponential backoff controlled by settings.

### 9.3 Text Extraction

The extraction layer in `rag/services.py` supports:

- PDF text-layer extraction
- PDF page rendering and OCR
- Image OCR
- DOCX text extraction
- TXT text extraction
- Document AI layout parsing
- Metadata extraction for dates, tables, images, graphs, and page summaries

OCR/provider behavior:

- Default provider is environment-driven
- Admin can switch OCR provider through Django admin
- Google Document AI is preferred for structured layout extraction
- EasyOCR can be used as the main or fallback provider
- Digital PDFs can be read directly before OCR depending on configuration

### 9.4 Embeddings and Vector Indexing

The RAG service supports:

- OpenAI embeddings
- Ollama embeddings
- Fallback embedding generation logic
- Automatic Qdrant collection creation
- Payload indexing in Qdrant
- Dimension fitting to the active embedding configuration

Chunk indexing includes document metadata so results can be filtered by:

- Organization
- Department
- Document type
- Status
- Year
- Date range

### 9.5 Search

The Smart Search implementation combines:

- Semantic similarity from Qdrant
- Lexical token overlap scoring
- Database metadata matching

Search APIs support:

- Query text
- Department filter
- Document type filter
- Status filter
- Year filter
- Date range filter
- Pagination

Smart Search workspace also exposes processing status so users can see which files are still being indexed or failed.

## 10. Templates and UI

Template groups:

- `templates/base.html`: base layout
- `templates/includes/`: shared header, sidebar, pagination, styles
- `templates/accounts/`: auth and administration screens
- `templates/core/`: dashboard, upload, file management, AI draft pages
- `templates/rag/`: Smart Search workspace

Language support:

- English and Hindi are configured in settings
- Hindi translations are stored in `locale/hi/LC_MESSAGES/django.po`
- `core.context_processors.translation_processor` and translation helpers expose localized strings to templates

## 11. Admin Interface

Admin registrations currently include:

- `accounts.Role`
- `accounts.User`
- `accounts.Organization`
- `rag.RAGIngestion`
- `rag.RAGChunk`
- `rag.OCRProviderConfiguration`

The OCR provider configuration is intended to be edited in admin to control future OCR behavior.

## 12. Background Processing

Celery components:

- `worker`: default queue processing
- `rag-worker`: dedicated RAG queue worker
- `beat`: scheduled tasks

Important background behaviors:

- RAG ingestion tasks are routed to the `rag` queue
- Beat runs `sync_processing_statuses` every 30 seconds
- Worker startup waits for PostgreSQL and Redis

## 13. Deployment and Runtime

### 13.1 Development Compose

`docker-compose.yml` defines:

- `web`
- `worker`
- `rag-worker`
- `beat`
- `db`
- `redis`
- `qdrant`

Development web process:

- Runs migrations
- Starts Django `runserver` on port `8000`
- Host mapping exposes it on `8010`

### 13.2 Production Compose

`docker-compose.prod.yml` defines:

- `web`
- `worker`
- `rag-worker`
- `beat`
- `nginx`
- `db`
- `redis`

Production web process:

- Runs migrations
- Collects static files
- Starts Gunicorn

### 13.3 Docker Runtime Notes

Container entrypoint:

- Waits for PostgreSQL
- Optionally waits for Redis
- Runs migrations
- Executes the target command

Persistent volumes are used for:

- PostgreSQL data
- Redis data
- Qdrant data in development
- Media files
- Static files
- EasyOCR model cache

## 14. Security and Access Boundaries

Implemented controls include:

- Django authentication
- Organization scoping on many queries and views
- Role-based access checks
- CSRF support
- Secure cookie flags configurable via environment
- Password reset token expiration

Operational note:

- `ALLOWED_HOSTS` in settings currently includes `*`, which is convenient for flexible deployment but should be reviewed for stricter production hardening.

## 15. Key Operational Workflows

### Upload and Index Workflow

1. User uploads a PDF.
2. `Document` is saved with metadata.
3. Processing is queued.
4. OCR/text extraction runs asynchronously.
5. Chunks are embedded and stored in Qdrant.
6. Search and AI drafting become available once status is `done`.

### Search Workflow

1. User opens Smart Search.
2. UI sends query and filters to `/rag/api/search/`.
3. The backend combines vector and lexical results.
4. Paginated results are returned with status metadata.

### AI Draft Workflow

1. User opens the AI draft page.
2. A reference document and optional prompt instructions are selected.
3. The system builds semantic context from indexed documents.
4. The LLM generates structured draft output.
5. User can stream, save, export, or attach the draft.

## 16. Important Files for Future Maintenance

If you need to modify the application, these are the most important starting points:

- `abhilekh_project/settings.py`: all runtime configuration
- `accounts/models.py`: tenant, role, and user definitions
- `accounts/views.py`: auth and admin flows
- `core/models.py`: primary business entities
- `core/views.py`: dashboard, file management, AI draft system
- `rag/services.py`: extraction, indexing, embeddings, search logic
- `rag/tasks.py`: Celery orchestration for ingestion
- `rag/signals.py`: automatic queueing and cleanup

## 17. Summary

Abhilekh is a server-rendered Django application that combines document management, access control, OCR, vector search, and AI-assisted draft generation in one system. The application is multi-tenant at the organization level, relies on PostgreSQL for primary data, Celery and Redis for async work, and Qdrant for semantic retrieval. The most complex and business-critical parts of the codebase are the document lifecycle in `core` and the OCR/RAG pipeline in `rag`.
