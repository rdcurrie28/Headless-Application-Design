import json
from typing import Any

from app.schemas import ModelName, ProductHealth, PropensityScore, SkuEntitlement
from app.sources.snowflake_source import SnowflakeSource

SKUS_SQL = """
WITH usage_30d AS (
    SELECT customer_id, sku, AVG(consumed_units) AS avg_units_30d
    FROM USAGE_DAILY
    WHERE customer_id = %(customer_id)s
      AND usage_date >= DATEADD(day, -30, CURRENT_DATE())
    GROUP BY customer_id, sku
)
SELECT e.sku, e.product_name, e.product_family, e.quantity, e.arr, e.start_date, e.end_date,
       ROUND(COALESCE(u.avg_units_30d, 0), 2) AS avg_units_30d,
       ROUND(DIV0(COALESCE(u.avg_units_30d, 0), e.quantity) * 100, 1) AS utilization_pct
FROM ENTITLEMENTS e
LEFT JOIN usage_30d u ON u.customer_id = e.customer_id AND u.sku = e.sku
WHERE e.customer_id = %(customer_id)s
  AND e.end_date >= CURRENT_DATE()
ORDER BY e.arr DESC
"""

HEALTH_SQL = """
SELECT sku, product_name, health_score, utilization_pct, trend_30d_pct, status
FROM PRODUCT_HEALTH
WHERE customer_id = %(customer_id)s
ORDER BY health_score ASC
"""

PROPENSITY_SQL = """
SELECT model_name, model_version, score, scored_at, top_drivers
FROM PROPENSITY_LATEST
WHERE customer_id = %(customer_id)s
"""

TOP_SCORED_SQL = """
SELECT customer_id, model_name, model_version, score, scored_at, top_drivers
FROM PROPENSITY_LATEST
WHERE model_name = %(model_name)s
  AND score >= %(min_score)s
ORDER BY score DESC
LIMIT %(limit)s
"""


def _drivers(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = json.loads(value)
    return [str(v) for v in value]


def _score(row: dict[str, Any]) -> PropensityScore:
    return PropensityScore(
        model_name=row["model_name"].lower(),
        model_version=row.get("model_version"),
        score=float(row["score"]),
        scored_at=row["scored_at"],
        top_drivers=_drivers(row.get("top_drivers")),
    )


class SnowflakeInsightsRepository:
    def __init__(self, source: SnowflakeSource) -> None:
        self._sf = source

    async def skus_for_customer(self, customer_id: str) -> list[SkuEntitlement]:
        rows = await self._sf.fetch_all(SKUS_SQL, {"customer_id": customer_id})
        return [SkuEntitlement(**r) for r in rows]

    async def product_health(self, customer_id: str) -> list[ProductHealth]:
        rows = await self._sf.fetch_all(HEALTH_SQL, {"customer_id": customer_id})
        return [ProductHealth(**r) for r in rows]

    async def propensity(self, customer_id: str) -> list[PropensityScore]:
        rows = await self._sf.fetch_all(PROPENSITY_SQL, {"customer_id": customer_id})
        return [_score(r) for r in rows]

    async def top_scored(
        self, model_name: ModelName, min_score: float, limit: int
    ) -> list[tuple[str, PropensityScore]]:
        rows = await self._sf.fetch_all(
            TOP_SCORED_SQL, {"model_name": model_name, "min_score": min_score, "limit": limit}
        )
        return [(r["customer_id"], _score(r)) for r in rows]
