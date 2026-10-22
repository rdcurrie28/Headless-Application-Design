import asyncio

from app.schemas import Document
from app.sources.s3_source import S3Source


class S3DocumentRepository:
    def __init__(self, source: S3Source, prefix: str) -> None:
        self._s3 = source
        self._prefix = prefix.strip("/")

    def _customer_prefix(self, customer_id: str) -> str:
        return f"{self._prefix}/{customer_id}/"

    async def list_documents(self, customer_id: str) -> list[Document]:
        objects = await self._s3.list_objects(self._customer_prefix(customer_id))
        objects.sort(key=lambda o: o["last_modified"], reverse=True)
        urls = await asyncio.gather(*(self._s3.presign(o["key"]) for o in objects))
        return [
            Document(
                key=o["key"],
                name=o["key"].rsplit("/", 1)[-1],
                size_bytes=o["size"],
                last_modified=o["last_modified"],
                url=url,
            )
            for o, url in zip(objects, urls)
        ]
