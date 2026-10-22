import asyncio
from typing import Any

from app.config import Settings


class S3Source:
    name = "s3"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: Any = None

    @property
    def bucket(self) -> str:
        return self._settings.s3_bucket

    async def connect(self) -> None:
        import boto3

        self._client = await asyncio.to_thread(
            boto3.client,
            "s3",
            region_name=self._settings.s3_region,
            endpoint_url=self._settings.s3_endpoint_url,
        )

    async def close(self) -> None:
        self._client = None

    def _require_client(self) -> Any:
        if self._client is None:
            raise RuntimeError("S3 source is not connected")
        return self._client

    def _list(self, prefix: str) -> list[dict[str, Any]]:
        paginator = self._require_client().get_paginator("list_objects_v2")
        items: list[dict[str, Any]] = []
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                if obj["Key"].endswith("/"):
                    continue
                items.append(
                    {"key": obj["Key"], "size": obj["Size"], "last_modified": obj["LastModified"]}
                )
        return items

    async def list_objects(self, prefix: str) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self._list, prefix)

    async def presign(self, key: str) -> str:
        return await asyncio.to_thread(
            self._require_client().generate_presigned_url,
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=self._settings.s3_presign_seconds,
        )

    async def ping(self) -> bool:
        try:
            await asyncio.to_thread(self._require_client().head_bucket, Bucket=self.bucket)
            return True
        except Exception:
            return False
