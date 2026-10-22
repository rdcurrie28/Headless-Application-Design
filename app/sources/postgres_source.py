from typing import Any

from app.config import Settings


class PostgresSource:
    name = "postgres"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._pool: Any = None

    async def connect(self) -> None:
        import asyncpg

        self._pool = await asyncpg.create_pool(
            dsn=self._settings.postgres_dsn,
            min_size=self._settings.postgres_pool_min,
            max_size=self._settings.postgres_pool_max,
        )

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    def _require_pool(self) -> Any:
        if self._pool is None:
            raise RuntimeError("Postgres source is not connected")
        return self._pool

    async def fetch_all(self, sql: str, *args: Any) -> list[dict[str, Any]]:
        async with self._require_pool().acquire() as conn:
            rows = await conn.fetch(sql, *args)
        return [dict(r) for r in rows]

    async def fetch_one(self, sql: str, *args: Any) -> dict[str, Any] | None:
        async with self._require_pool().acquire() as conn:
            row = await conn.fetchrow(sql, *args)
        return dict(row) if row else None

    async def ping(self) -> bool:
        try:
            await self.fetch_one("SELECT 1 AS ok")
            return True
        except Exception:
            return False
