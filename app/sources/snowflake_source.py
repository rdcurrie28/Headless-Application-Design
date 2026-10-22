import asyncio
from pathlib import Path
from typing import Any

from app.config import Settings


class SnowflakeSource:
    name = "snowflake"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._conn: Any = None

    def _private_key(self) -> bytes:
        from cryptography.hazmat.primitives import serialization

        pem = Path(self._settings.snowflake_private_key_path).read_bytes()
        key = serialization.load_pem_private_key(pem, password=None)
        return key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

    def _connect_params(self) -> dict[str, Any]:
        s = self._settings
        params: dict[str, Any] = {
            "account": s.snowflake_account,
            "user": s.snowflake_user,
            "role": s.snowflake_role or None,
            "warehouse": s.snowflake_warehouse,
            "database": s.snowflake_database,
            "schema": s.snowflake_schema,
            "client_session_keep_alive": True,
            "application": "customer-insights-api",
        }
        if s.snowflake_private_key_path:
            params["private_key"] = self._private_key()
        else:
            params["password"] = s.snowflake_password
        return {k: v for k, v in params.items() if v is not None}

    async def connect(self) -> None:
        import snowflake.connector

        self._conn = await asyncio.to_thread(snowflake.connector.connect, **self._connect_params())

    async def close(self) -> None:
        if self._conn is not None:
            await asyncio.to_thread(self._conn.close)
            self._conn = None

    def _run(self, sql: str, params: dict[str, Any] | None) -> list[dict[str, Any]]:
        from snowflake.connector import DictCursor

        with self._conn.cursor(DictCursor) as cur:
            cur.execute(sql, params or {})
            return [{k.lower(): v for k, v in row.items()} for row in cur.fetchall()]

    async def fetch_all(self, sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if self._conn is None:
            raise RuntimeError("Snowflake source is not connected")
        return await asyncio.to_thread(self._run, sql, params)

    async def ping(self) -> bool:
        try:
            await self.fetch_all("SELECT 1 AS ok")
            return True
        except Exception:
            return False
