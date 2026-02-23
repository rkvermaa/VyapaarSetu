"""SQLAlchemy async engine and declarative base."""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.orm import DeclarativeBase, MappedColumn
from sqlalchemy import MetaData

from src.config import settings
from src.core.logging import log

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.DATABASE_URL,
            pool_size=settings.get("DATABASE_POOL_SIZE", 10),
            max_overflow=settings.get("DATABASE_MAX_OVERFLOW", 20),
            echo=settings.get("DEBUG", False),
        )
        log.info("Database engine created")
    return _engine


async def init_db() -> None:
    """Create all tables (for development — use Alembic in prod)."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("Database tables created")
