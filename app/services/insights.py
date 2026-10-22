from app.cache import TTLCache
from app.repositories.protocols import DocumentRepository, InsightsRepository
from app.schemas import Document, ModelName, ProductHealth, PropensityScore, SkuEntitlement


class CachedInsights:
    def __init__(self, insights: InsightsRepository, documents: DocumentRepository, cache: TTLCache) -> None:
        self._insights = insights
        self._documents = documents
        self._cache = cache

    async def skus(self, customer_id: str) -> list[SkuEntitlement]:
        return await self._cache.get_or_load(f"skus:{customer_id}", lambda: self._insights.skus_for_customer(customer_id))

    async def health(self, customer_id: str) -> list[ProductHealth]:
        return await self._cache.get_or_load(f"health:{customer_id}", lambda: self._insights.product_health(customer_id))

    async def propensity(self, customer_id: str) -> list[PropensityScore]:
        return await self._cache.get_or_load(f"propensity:{customer_id}", lambda: self._insights.propensity(customer_id))

    async def top_scored(self, model_name: ModelName, min_score: float, limit: int) -> list[tuple[str, PropensityScore]]:
        key = f"top:{model_name}:{min_score}:{limit}"
        return await self._cache.get_or_load(key, lambda: self._insights.top_scored(model_name, min_score, limit))

    async def documents(self, customer_id: str) -> list[Document]:
        return await self._documents.list_documents(customer_id)
