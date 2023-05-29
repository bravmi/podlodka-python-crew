import pytest
import yoyo
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine

import db

TTL_YOYO_MIGRATION = 300


@pytest.fixture(scope='session', autouse=True)
def apply_migrations(settings, root_dir):
    backend = yoyo.get_backend(settings.db_dsn('postgresql'), 'migrations')

    migrations = yoyo.read_migrations((root_dir / 'migrations').as_posix())

    with backend.lock(timeout=TTL_YOYO_MIGRATION):
        backend.apply_migrations(backend.to_apply(migrations))

    yield
    with backend.lock(timeout=TTL_YOYO_MIGRATION):
        backend.rollback_migrations(backend.to_rollback(migrations))


@pytest.fixture(scope='session')
async def db_engine(settings):
    engine = create_async_engine(url=settings.db_dsn())
    yield engine
    await engine.dispose()


@pytest.fixture(scope='session')
async def db_connection(db_engine: AsyncEngine):
    async with db_engine.connect() as connection:
        yield connection


@pytest.fixture()
async def db_session(db_connection: AsyncConnection):
    transaction = await db_connection.begin()
    async with db.Session(
        bind=db_connection, join_transaction_mode='create_savepoint'
    ) as session:
        yield session
    await transaction.rollback()
