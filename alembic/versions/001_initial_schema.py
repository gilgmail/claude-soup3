"""Create initial database schema for financial wisdom platform

Revision ID: 001
Revises: 
Create Date: 2025-09-07 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""
    
    # Create data_sources table - let SQLAlchemy handle ENUM creation
    op.create_table('data_sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('base_url', sa.String(length=500), nullable=False),
        sa.Column('collection_config', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('last_collected_at', sa.DateTime(), nullable=True),
        sa.Column('collection_count', sa.Integer(), nullable=False),
        sa.Column('success_rate', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_data_sources_name'), 'data_sources', ['name'], unique=False)
    op.create_index(op.f('ix_data_sources_source_type'), 'data_sources', ['source_type'], unique=False)
    op.create_index(op.f('ix_data_sources_is_active'), 'data_sources', ['is_active'], unique=False)
    op.create_index(op.f('ix_data_sources_last_collected_at'), 'data_sources', ['last_collected_at'], unique=False)
    
    # Create raw_content table
    op.create_table('raw_content',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=1000), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('url', sa.String(length=2000), nullable=False),
        sa.Column('content_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('collected_at', sa.DateTime(), nullable=False),
        sa.Column('processed', sa.Boolean(), nullable=False),
        sa.Column('keywords', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('financial_terms', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('word_count', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['source_id'], ['data_sources.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_raw_content_source_id'), 'raw_content', ['source_id'], unique=False)
    op.create_index(op.f('ix_raw_content_collected_at'), 'raw_content', ['collected_at'], unique=False)
    op.create_index(op.f('ix_raw_content_processed'), 'raw_content', ['processed'], unique=False)
    op.create_index('idx_raw_content_source_date', 'raw_content', ['source_id', 'collected_at'], unique=False)
    op.create_index('idx_raw_content_processed', 'raw_content', ['processed', 'collected_at'], unique=False)
    
    # Create articles table
    op.create_table('articles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('content_json', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('topic_keywords', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('topic_category', sa.String(length=100), nullable=False),
        sa.Column('topic_context', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('content_style', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('quality_metrics', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('source_materials', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('word_count', sa.Integer(), nullable=True),
        sa.Column('readability_score', sa.Float(), nullable=True),
        sa.Column('engagement_score', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_articles_topic_category'), 'articles', ['topic_category'], unique=False)
    op.create_index(op.f('ix_articles_content_style'), 'articles', ['content_style'], unique=False)
    op.create_index(op.f('ix_articles_status'), 'articles', ['status'], unique=False)
    op.create_index(op.f('ix_articles_quality_score'), 'articles', ['quality_score'], unique=False)
    op.create_index(op.f('ix_articles_created_at'), 'articles', ['created_at'], unique=False)
    op.create_index(op.f('ix_articles_published_at'), 'articles', ['published_at'], unique=False)
    op.create_index('idx_articles_status_created', 'articles', ['status', 'created_at'], unique=False)
    op.create_index('idx_articles_category_style', 'articles', ['topic_category', 'content_style'], unique=False)
    
    # Create topics table
    op.create_table('topics',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('keywords', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('trend_score', sa.Float(), nullable=False),
        sa.Column('context', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('mention_count', sa.Integer(), nullable=False),
        sa.Column('first_seen', sa.DateTime(), nullable=False),
        sa.Column('last_updated', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('weekly_mentions', sa.Integer(), nullable=True),
        sa.Column('monthly_mentions', sa.Integer(), nullable=True),
        sa.Column('peak_trend_score', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_topics_category'), 'topics', ['category'], unique=False)
    op.create_index(op.f('ix_topics_trend_score'), 'topics', ['trend_score'], unique=False)
    op.create_index(op.f('ix_topics_last_updated'), 'topics', ['last_updated'], unique=False)
    op.create_index(op.f('ix_topics_is_active'), 'topics', ['is_active'], unique=False)
    op.create_index('idx_topics_trend_active', 'topics', ['is_active', 'trend_score'], unique=False)
    op.create_index('idx_topics_category_updated', 'topics', ['category', 'last_updated'], unique=False)
    
    # Create content_cache table
    op.create_table('content_cache',
        sa.Column('cache_key', sa.String(length=255), nullable=False),
        sa.Column('content_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('content_type', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('hit_count', sa.Integer(), nullable=False),
        sa.Column('last_accessed', sa.DateTime(), nullable=False),
        sa.Column('generation_cost', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('cache_key')
    )
    op.create_index(op.f('ix_content_cache_content_type'), 'content_cache', ['content_type'], unique=False)
    op.create_index(op.f('ix_content_cache_expires_at'), 'content_cache', ['expires_at'], unique=False)
    op.create_index('idx_cache_expiry_type', 'content_cache', ['expires_at', 'content_type'], unique=False)
    op.create_index('idx_cache_accessed', 'content_cache', ['last_accessed'], unique=False)
    
    # Create workflow_runs table
    op.create_table('workflow_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('run_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('article_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('topics_analyzed', sa.Integer(), nullable=True),
        sa.Column('content_generated', sa.Boolean(), nullable=True),
        sa.Column('quality_checks', sa.Integer(), nullable=True),
        sa.Column('cache_hits', sa.Integer(), nullable=True),
        sa.Column('total_cost', sa.Float(), nullable=True),
        sa.Column('metrics', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workflow_runs_run_type'), 'workflow_runs', ['run_type'], unique=False)
    op.create_index(op.f('ix_workflow_runs_status'), 'workflow_runs', ['status'], unique=False)
    op.create_index(op.f('ix_workflow_runs_started_at'), 'workflow_runs', ['started_at'], unique=False)
    op.create_index('idx_workflow_runs_type_status', 'workflow_runs', ['run_type', 'status'], unique=False)
    
    # Create usage_stats table
    op.create_table('usage_stats',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('service_name', sa.String(length=100), nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('usage_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_usage_stats_date'), 'usage_stats', ['date'], unique=False)
    op.create_index(op.f('ix_usage_stats_service_name'), 'usage_stats', ['service_name'], unique=False)
    op.create_index(op.f('ix_usage_stats_metric_name'), 'usage_stats', ['metric_name'], unique=False)
    op.create_index('idx_usage_stats_date_service', 'usage_stats', ['date', 'service_name'], unique=False)
    op.create_index('idx_usage_stats_metric', 'usage_stats', ['service_name', 'metric_name', 'date'], unique=False)

    # Create full-text search indexes (PostgreSQL specific)
    op.execute("CREATE INDEX IF NOT EXISTS idx_raw_content_title_fts ON raw_content USING gin(to_tsvector('english', title))")
    op.execute("CREATE INDEX IF NOT EXISTS idx_raw_content_content_fts ON raw_content USING gin(to_tsvector('english', content))")
    op.execute("CREATE INDEX IF NOT EXISTS idx_articles_title_fts ON articles USING gin(to_tsvector('english', title))")
    
    # Create partial indexes for active records
    op.execute("CREATE INDEX IF NOT EXISTS idx_data_sources_active ON data_sources (name, source_type) WHERE is_active = true")
    op.execute("CREATE INDEX IF NOT EXISTS idx_topics_active ON topics (trend_score DESC, last_updated DESC) WHERE is_active = true")
    
    # Create composite indexes for common query patterns
    op.execute("CREATE INDEX IF NOT EXISTS idx_articles_quality_published ON articles (quality_score DESC, published_at DESC) WHERE status = 'published'")
    op.execute("CREATE INDEX IF NOT EXISTS idx_raw_content_recent ON raw_content (collected_at DESC, processed) WHERE processed = false")


def downgrade() -> None:
    """Downgrade database schema."""
    
    # Drop tables in reverse order
    op.drop_table('usage_stats')
    op.drop_table('workflow_runs')
    op.drop_table('content_cache')
    op.drop_table('topics')
    op.drop_table('articles')
    op.drop_table('raw_content')
    op.drop_table('data_sources')
    
    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS contentstyle")
    op.execute("DROP TYPE IF EXISTS articlestatus")
    op.execute("DROP TYPE IF EXISTS sourcetype")