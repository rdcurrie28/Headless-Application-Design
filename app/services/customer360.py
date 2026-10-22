import asyncio
import logging
from collections.abc import Awaitable
from datetime import datetime, timezone
from typing import Any

from app.repositories.protocols import CustomerRepository
from app.schemas import (
    Customer360,
    Customer360Summary,
    Motion,
    ProductHealth,
    PropensityScore,
    SectionError,
    SkuEntitlement,
)
from app.services.errors import CustomerNotFound
from app.services.insights import CachedInsights

log = logging.getLogger(__name__)


def recommend_motion(churn: float | None, expansion: float | None, churn_t: float, expansion_t: float) -> Motion:
    if churn is None and expansion is None:
        return "unknown"
    high_churn = churn is not None and churn >= churn_t
    high_expansion = expansion is not None and expansion >= expansion_t
    if high_churn and high_expansion:
        return "retain_and_expand"
    if high_churn:
        return "retain"
    if high_expansion:
        return "expand"
    return "nurture"


def summarize(
    skus: list[SkuEntitlement] | None,
    health: list[ProductHealth] | None,
    scores: list[PropensityScore] | None,
    churn_t: float,
    expansion_t: float,
) -> Customer360Summary:
    by_model = {s.model_name: s.score for s in scores or []}
    churn = by_model.get("churn")
    expansion = by_model.get("expansion")
    return Customer360Summary(
        total_arr=round(sum(s.arr for s in skus), 2) if skus is not None else None,
        sku_count=len(skus) if skus is not None else None,
        avg_health_score=round(sum(h.health_score for h in health) / len(health), 1) if health else None,
        at_risk_skus=sum(1 for h in health if h.status == "at_risk") if health is not None else None,
        churn_score=churn,
        expansion_score=expansion,
        recommended_motion=recommend_motion(churn, expansion, churn_t, expansion_t),
    )


class Customer360Service:
    def __init__(
        self,
        customers: CustomerRepository,
        insights: CachedInsights,
        timeout_seconds: float,
        churn_threshold: float,
        expansion_threshold: float,
    ) -> None:
        self._customers = customers
        self._insights = insights
        self._timeout = timeout_seconds
        self._churn_t = churn_threshold
        self._expansion_t = expansion_threshold

    async def _guard(self, section: str, source: str, call: Awaitable[Any]) -> tuple[Any, SectionError | None]:
        try:
            return await asyncio.wait_for(call, timeout=self._timeout), None
        except asyncio.TimeoutError:
            return None, SectionError(section=section, source=source, message="timed out")
        except Exception as exc:
            log.exception("360 section %s failed", section)
            return None, SectionError(section=section, source=source, message=type(exc).__name__)

    async def build(self, customer_id: str) -> Customer360:
        customer = await self._customers.get_customer(customer_id)
        if customer is None:
            raise CustomerNotFound(customer_id)

        plan = [
            ("skus", "snowflake", self._insights.skus(customer_id)),
            ("product_health", "snowflake", self._insights.health(customer_id)),
            ("propensity", "snowflake", self._insights.propensity(customer_id)),
            ("documents", "s3", self._insights.documents(customer_id)),
            ("recent_actions", "postgres", self._customers.list_actions(customer_id, 10)),
        ]
        results = await asyncio.gather(*(self._guard(s, src, c) for s, src, c in plan))

        sections = {name: value for (name, _, _), (value, _) in zip(plan, results)}
        errors = [err for _, err in results if err is not None]

        return Customer360(
            customer=customer,
            summary=summarize(
                sections["skus"], sections["product_health"], sections["propensity"],
                self._churn_t, self._expansion_t,
            ),
            errors=errors,
            generated_at=datetime.now(timezone.utc),
            **sections,
        )
