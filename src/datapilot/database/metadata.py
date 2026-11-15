import json
from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from datapilot.config.settings import get_settings


@lru_cache
def get_metadata_engine() -> Engine:
    """Use the application database credentials for metadata writes."""

    settings = get_settings()

    # Important: use database_url, NOT the read-only URL.
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
    )


def initialize_metadata_tables():
    engine = get_metadata_engine()

    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS analysis_runs (
                run_id VARCHAR(36) PRIMARY KEY,
                user_question TEXT NOT NULL,
                status VARCHAR(30) NOT NULL,
                retry_count INTEGER NOT NULL DEFAULT 0,
                state_json JSONB NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """))

        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS agent_events (
                event_id BIGSERIAL PRIMARY KEY,
                run_id VARCHAR(36) NOT NULL
                    REFERENCES analysis_runs(run_id),
                stage VARCHAR(100) NOT NULL,
                event_type VARCHAR(100) NOT NULL,
                message TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """))


def save_analysis_run(state):
    engine = get_metadata_engine()

    state_json = json.dumps(
        state.model_dump(mode="json")
    )

    with engine.begin() as connection:
        connection.execute(
            text("""
                INSERT INTO analysis_runs (
                    run_id,
                    user_question,
                    status,
                    retry_count,
                    state_json
                )
                VALUES (
                    :run_id,
                    :question,
                    :status,
                    :retry_count,
                    CAST(:state_json AS JSONB)
                )
                ON CONFLICT (run_id)
                DO UPDATE SET
                    status = EXCLUDED.status,
                    retry_count = EXCLUDED.retry_count,
                    state_json = EXCLUDED.state_json,
                    updated_at = NOW()
            """),
            {
                "run_id": state.run_id,
                "question": state.user_question,
                "status": state.status,
                "retry_count": state.retry_count,
                "state_json": state_json,
            },
        )


def save_agent_event(
    run_id: str,
    stage: str,
    event_type: str,
    message: str,
):
    engine = get_metadata_engine()

    with engine.begin() as connection:
        connection.execute(
            text("""
                INSERT INTO agent_events (
                    run_id,
                    stage,
                    event_type,
                    message
                )
                VALUES (
                    :run_id,
                    :stage,
                    :event_type,
                    :message
                )
            """),
            {
                "run_id": run_id,
                "stage": stage,
                "event_type": event_type,
                "message": message,
            },
        )