"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-04-22
"""

import sqlalchemy as sa
from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sources",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("fetch_interval_hours", sa.Integer, server_default="6"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "cbr_rates",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("rate_date", sa.Date, unique=True, nullable=False),
        sa.Column("rate_value", sa.Numeric(5, 2), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "events",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("source_id", sa.Integer, sa.ForeignKey("sources.id"), nullable=True),
        sa.Column("external_id", sa.Text, nullable=True),
        sa.Column("content_hash", sa.String(64), unique=True, nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("url", sa.Text, nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("impact_score", sa.SmallInteger, nullable=True),
        sa.Column("price_direction", sa.String(10), nullable=True),
        sa.Column("is_key_event", sa.Boolean, server_default="false"),
        sa.Column("analysis_raw", sa.JSON, nullable=True),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), server_default="pending"),
    )

    op.create_index("ix_events_published_at", "events", ["published_at"])
    op.create_index("ix_events_category_impact", "events", ["category", "impact_score"])

    op.create_table(
        "collection_runs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("source_id", sa.Integer, sa.ForeignKey("sources.id"), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), server_default="running"),
        sa.Column("events_collected", sa.Integer, server_default="0"),
        sa.Column("events_analyzed", sa.Integer, server_default="0"),
        sa.Column("error_message", sa.Text, nullable=True),
    )

    # Начальные источники данных
    op.execute("""
        INSERT INTO sources (name, source_type, url, fetch_interval_hours) VALUES
        ('ЦБ РФ — Ключевая ставка', 'cbr', 'https://cbr.ru/hd_base/KeyRate/', 24),
        ('IRN.ru', 'rss', 'https://www.irn.ru/rss/', 6),
        ('РБК Недвижимость', 'rss', 'https://realty.rbc.ru/rss/news/', 6),
        ('ЦИАН Новости', 'rss', 'https://www.cian.ru/rss/news/', 6)
    """)


def downgrade() -> None:
    op.drop_table("collection_runs")
    op.drop_index("ix_events_category_impact", "events")
    op.drop_index("ix_events_published_at", "events")
    op.drop_table("events")
    op.drop_table("cbr_rates")
    op.drop_table("sources")
