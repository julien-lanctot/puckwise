"""Database connection pool and utilities."""

from contextlib import contextmanager
from typing import Generator, Any

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .config import config

_pool: ConnectionPool | None = None


def get_pool() -> ConnectionPool:
    """Get or create the connection pool."""
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            config.database_url,
            min_size=2,
            max_size=10,
            kwargs={"row_factory": dict_row},
        )
    return _pool


def close_pool() -> None:
    """Close the connection pool."""
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


@contextmanager
def get_connection() -> Generator[psycopg.Connection, None, None]:
    """Get a connection from the pool."""
    pool = get_pool()
    with pool.connection() as conn:
        yield conn


@contextmanager
def get_cursor() -> Generator[psycopg.Cursor, None, None]:
    """Get a cursor from a pooled connection."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            yield cur


def execute_batch(
    query: str,
    params_list: list[tuple],
    batch_size: int = 1000,
) -> int:
    """Execute a query in batches, returning total rows affected."""
    total = 0
    with get_connection() as conn:
        with conn.cursor() as cur:
            for i in range(0, len(params_list), batch_size):
                batch = params_list[i : i + batch_size]
                cur.executemany(query, batch)
                total += len(batch)
        conn.commit()
    return total


def execute_values(
    table: str,
    columns: list[str],
    values: list[tuple],
    on_conflict: str | None = None,
    batch_size: int = 1000,
) -> int:
    """Bulk insert using execute_values pattern."""
    if not values:
        return 0

    cols = ", ".join(columns)
    placeholders = ", ".join(["%s"] * len(columns))
    query = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"

    if on_conflict:
        query += f" {on_conflict}"

    total = 0
    with get_connection() as conn:
        with conn.cursor() as cur:
            for i in range(0, len(values), batch_size):
                batch = values[i : i + batch_size]
                cur.executemany(query, batch)
                total += len(batch)
        conn.commit()
    return total


def fetch_all(query: str, params: tuple | None = None) -> list[dict[str, Any]]:
    """Fetch all rows as dictionaries."""
    with get_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


def fetch_one(query: str, params: tuple | None = None) -> dict[str, Any] | None:
    """Fetch a single row as dictionary."""
    with get_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchone()
