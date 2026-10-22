from app.repositories.protocols import CustomerRepository
from app.schemas import ModelName, ScoredAccount
from app.services.insights import CachedInsights


class PortfolioService:
    def __init__(self, customers: CustomerRepository, insights: CachedInsights) -> None:
        self._customers = customers
        self._insights = insights

    async def ranked(
        self, model_name: ModelName, min_score: float, limit: int, owner: str | None = None
    ) -> list[ScoredAccount]:
        scored = await self._insights.top_scored(model_name, min_score, limit if owner is None else limit * 5)
        customers = {c.customer_id: c for c in await self._customers.get_customers([cid for cid, _ in scored])}
        accounts = [
            ScoredAccount(
                customer=customers[cid],
                model_name=s.model_name,
                score=s.score,
                scored_at=s.scored_at,
                top_drivers=s.top_drivers,
            )
            for cid, s in scored
            if cid in customers and (owner is None or customers[cid].account_owner == owner)
        ]
        return accounts[:limit]
