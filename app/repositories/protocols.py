from typing import Protocol

from app.schemas import (
    Customer,
    CustomerPage,
    Document,
    ModelName,
    ProductHealth,
    PropensityScore,
    RepAction,
    RepActionCreate,
    SkuEntitlement,
)


class CustomerRepository(Protocol):
    async def list_customers(
        self, search: str | None, region: str | None, owner: str | None, limit: int, offset: int
    ) -> CustomerPage: ...

    async def get_customer(self, customer_id: str) -> Customer | None: ...

    async def get_customers(self, customer_ids: list[str]) -> list[Customer]: ...

    async def list_actions(self, customer_id: str, limit: int) -> list[RepAction]: ...

    async def create_action(self, customer_id: str, action: RepActionCreate) -> RepAction: ...


class InsightsRepository(Protocol):
    async def skus_for_customer(self, customer_id: str) -> list[SkuEntitlement]: ...

    async def product_health(self, customer_id: str) -> list[ProductHealth]: ...

    async def propensity(self, customer_id: str) -> list[PropensityScore]: ...

    async def top_scored(
        self, model_name: ModelName, min_score: float, limit: int
    ) -> list[tuple[str, PropensityScore]]: ...


class DocumentRepository(Protocol):
    async def list_documents(self, customer_id: str) -> list[Document]: ...
