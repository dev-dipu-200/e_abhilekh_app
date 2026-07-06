"""add ai settings columns

Revision ID: 20260706_01
Revises:
Create Date: 2026-07-06 12:00:00
"""

from alembic import op


revision = "20260706_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS designation VARCHAR(255)")
    op.execute("ALTER TABLE organizations ADD COLUMN IF NOT EXISTS ai_provider VARCHAR(50) NOT NULL DEFAULT 'ollama'")
    op.execute("ALTER TABLE organizations ADD COLUMN IF NOT EXISTS openai_api_key TEXT")
    op.execute("ALTER TABLE organizations ADD COLUMN IF NOT EXISTS openai_embedding_model VARCHAR(255)")
    op.execute("ALTER TABLE organizations ADD COLUMN IF NOT EXISTS openai_llm_model VARCHAR(255)")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS ai_provider VARCHAR(50) NOT NULL DEFAULT 'ollama'")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS openai_api_key TEXT")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS openai_embedding_model VARCHAR(255)")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS openai_llm_model VARCHAR(255)")


def downgrade() -> None:
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS openai_llm_model")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS openai_embedding_model")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS openai_api_key")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS ai_provider")
    op.execute("ALTER TABLE organizations DROP COLUMN IF EXISTS openai_llm_model")
    op.execute("ALTER TABLE organizations DROP COLUMN IF EXISTS openai_embedding_model")
    op.execute("ALTER TABLE organizations DROP COLUMN IF EXISTS openai_api_key")
    op.execute("ALTER TABLE organizations DROP COLUMN IF EXISTS ai_provider")
    op.execute("ALTER TABLE documents DROP COLUMN IF EXISTS designation")
