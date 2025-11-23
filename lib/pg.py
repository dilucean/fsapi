import json
from contextlib import asynccontextmanager
from typing import Optional

import asyncpg
from asyncpg import Connection, Pool


# Global pool instance
_pool: Optional[Pool] = None


async def _configure_connection(conn: Connection) -> None:
    """
    Configure connection with custom type codecs.
    Registers JSON/JSONB types to auto-convert to/from Python dict/list.
    """
    await conn.set_type_codec(
        "json",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )
    await conn.set_type_codec(
        "jsonb",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )


async def init_pool(
    host: str,
    port: int,
    user: str,
    password: str,
    database: str,
    min_size: int = 10,
    max_size: int = 20,
    **kwargs,
) -> Pool:
    """
    Initialize PostgreSQL connection pool with JSON codec support.

    Args:
        host: Database host
        port: Database port
        user: Database user
        password: Database password
        database: Database name
        min_size: Minimum pool size (default: 10)
        max_size: Maximum pool size (default: 20)
        **kwargs: Additional asyncpg pool arguments

    Returns:
        asyncpg Pool instance
    """
    global _pool

    _pool = await asyncpg.create_pool(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        min_size=min_size,
        max_size=max_size,
        init=_configure_connection,  # Configure each connection
        **kwargs,
    )

    return _pool


def get_pool() -> Pool:
    """
    Get the current connection pool.

    Returns:
        asyncpg Pool instance

    Raises:
        RuntimeError: If pool has not been initialized
    """
    if _pool is None:
        raise RuntimeError("Database pool not initialized. Call init_pool() first.")
    return _pool


async def close_pool() -> None:
    """Close the connection pool."""
    global _pool

    if _pool is not None:
        await _pool.close()
        _pool = None


async def connect(
    host: str,
    port: int,
    user: str,
    password: str,
    database: str,
    **kwargs,
) -> Connection:
    """
    Create a direct database connection with JSON codec support.
    Useful for CLI tools and migrations.

    Args:
        host: Database host
        port: Database port
        user: Database user
        password: Database password
        database: Database name
        **kwargs: Additional asyncpg connection arguments

    Returns:
        asyncpg Connection instance
    """
    conn = await asyncpg.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        **kwargs,
    )

    # Configure JSON codecs
    await _configure_connection(conn)

    return conn


@asynccontextmanager
async def transaction():
    """
    Async context manager for database transactions using the pool.

    Usage:
        async with transaction() as conn:
            await conn.execute("INSERT INTO users (name) VALUES ($1)", "Alice")
            await conn.execute("INSERT INTO users (name) VALUES ($1)", "Bob")
        # Automatically commits on success, rolls back on exception

    Yields:
        asyncpg Connection in transaction context
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            yield conn
