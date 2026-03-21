from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.settings import DB_Settings

engine = None
async_session_factory = None


def init_db(db_settings: DB_Settings):
    global engine, async_session_factory

    if engine is not None:
        return

    engine = create_async_engine(
        db_settings.url_async,
        # Connection pool configuration
        pool_size=db_settings.connection_pool_size,  # Permanent connections in pool
        max_overflow=db_settings.connection_max_overflow,  # Temporary connections during spikes
        pool_timeout=db_settings.connection_pool_timeout,  # Wait time for connection
        pool_recycle=db_settings.connection_pool_recycle,  # Prevent stale connections
        pool_pre_ping=True,  # Verify connection before use
        # SQL logging for debugging
        echo=db_settings.echo,
    )
    # Create async session factory
    # expire_on_commit=False prevents attribute access errors after commit
    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,  # Keep data accessible after commit
        autocommit=False,  # Require explicit commits
        autoflush=False,  # Manual control over flushing
    )


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    if async_session_factory is None:
        raise RuntimeError("Database not initialized. Run init_db() first.")

    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
