from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from datapilot.config.settings import get_settings


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()

    database_url = (
        settings.database_readonly_url
        or settings.database_url
    )

    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
    )