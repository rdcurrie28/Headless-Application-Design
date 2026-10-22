from datetime import date, datetime, timedelta, timezone
from itertools import count

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

NOW = datetime(2026, 10, 15, 6, 0, tzinfo=timezone.utc)
START = date(2026, 1, 1)
END = date(2027, 12, 31)

CUSTOMERS = [
    Customer(customer_id="C-1001", name="Acme Aerospace", segment="Enterprise", region="NA-East", account_owner="jlee", salesforce_id="001A000001",
             contact_name="Dana Whitfield", contact_phone="+1 (617) 555-0142", address="200 Harbor Way, Boston, MA 02210"),
    Customer(customer_id="C-1002", name="Blue Ridge Health", segment="Enterprise", region="NA-East", account_owner="mpatel", salesforce_id="001A000002",
             contact_name="Marcus Ellery", contact_phone="+1 (704) 555-0178", address="4100 Piedmont Row Dr, Charlotte, NC 28210"),
    Customer(customer_id="C-1003", name="Cardinal Logistics", segment="Mid-Market", region="NA-Central", account_owner="jlee", salesforce_id="001A000003",
             contact_name="Priya Raman", contact_phone="+1 (312) 555-0119", address="875 W Lake St, Chicago, IL 60607"),
    Customer(customer_id="C-1004", name="Delta Fintech", segment="Mid-Market", region="EMEA", account_owner="asmith", salesforce_id="001A000004",
             contact_name="Sofia Lindqvist", contact_phone="+44 20 7946 0321", address="30 Finsbury Square, London EC2A 1AG, UK"),
    Customer(customer_id="C-1005", name="Evergreen Retail", segment="Commercial", region="NA-West", account_owner="mpatel", salesforce_id="001A000005",
             contact_name="Tom Okafor", contact_phone="+1 (503) 555-0164", address="1220 NW Lovejoy St, Portland, OR 97209"),
]

CATALOG = {
    "OCP-PREM": ("OpenShift Platform Plus", "Hybrid Cloud"),
    "RHEL-SRV": ("RHEL Server Premium", "Platform"),
    "ANS-AAP": ("Ansible Automation Platform", "Automation"),
    "AI-PLAT": ("OpenShift AI", "AI"),
}

ENTITLEMENTS = {
    "C-1001": [("OCP-PREM", 400, 980000, 88.0, 6.0), ("RHEL-SRV", 1200, 410000, 74.0, -2.0), ("AI-PLAT", 32, 150000, 31.0, -18.0)],
    "C-1002": [("RHEL-SRV", 800, 260000, 45.0, -22.0), ("ANS-AAP", 300, 190000, 38.0, -30.0)],
    "C-1003": [("OCP-PREM", 120, 290000, 97.0, 12.0), ("ANS-AAP", 150, 95000, 102.0, 9.0)],
    "C-1004": [("RHEL-SRV", 250, 82000, 66.0, 1.0), ("AI-PLAT", 16, 70000, 92.0, 40.0)],
    "C-1005": [("RHEL-SRV", 100, 33000, 22.0, -41.0)],
}

SCORES = {
    "C-1001": {"churn": (0.21, ["stable_core_usage"]), "expansion": (0.74, ["ocp_capacity_near_limit", "ai_pilot_active"])},
    "C-1002": {"churn": (0.71, ["usage_decline_60d", "open_sev1_cases"]), "expansion": (0.18, ["flat_headcount"])},
    "C-1003": {"churn": (0.08, ["high_utilization"]), "expansion": (0.83, ["over_entitlement", "new_cluster_requests"])},
    "C-1004": {"churn": (0.33, ["renewal_in_90d"]), "expansion": (0.61, ["ai_usage_growth"])},
    "C-1005": {"churn": (0.86, ["usage_decline_60d", "champion_left", "renewal_in_60d"]), "expansion": (0.05, [])},
}


def _status(score: float) -> str:
    if score >= 70:
        return "healthy"
    if score >= 40:
        return "watch"
    return "at_risk"


def _health_score(util: float, trend: float) -> float:
    return round(min(util, 100) * 0.7 + min(max(50 + trend, 0), 100) * 0.3, 0)


class FakeCustomerRepository:
    def __init__(self) -> None:
        self._customers = {c.customer_id: c for c in CUSTOMERS}
        self._actions: list[RepAction] = []
        self._ids = count(1)

    async def list_customers(
        self, search: str | None, region: str | None, owner: str | None, limit: int, offset: int
    ) -> CustomerPage:
        rows = sorted(self._customers.values(), key=lambda c: c.name)
        if search:
            s = search.lower()
            rows = [c for c in rows if s in c.name.lower() or s in c.customer_id.lower()]
        if region:
            rows = [c for c in rows if c.region == region]
        if owner:
            rows = [c for c in rows if c.account_owner == owner]
        return CustomerPage(items=rows[offset : offset + limit], total=len(rows), limit=limit, offset=offset)

    async def get_customer(self, customer_id: str) -> Customer | None:
        return self._customers.get(customer_id)

    async def get_customers(self, customer_ids: list[str]) -> list[Customer]:
        return [self._customers[i] for i in customer_ids if i in self._customers]

    async def list_actions(self, customer_id: str, limit: int) -> list[RepAction]:
        rows = [a for a in self._actions if a.customer_id == customer_id]
        return sorted(rows, key=lambda a: a.created_at, reverse=True)[:limit]

    async def create_action(self, customer_id: str, action: RepActionCreate) -> RepAction:
        created = RepAction(
            action_id=next(self._ids),
            customer_id=customer_id,
            created_at=datetime.now(timezone.utc),
            **action.model_dump(),
        )
        self._actions.append(created)
        return created


class FakeInsightsRepository:
    async def skus_for_customer(self, customer_id: str) -> list[SkuEntitlement]:
        rows = []
        for sku, qty, arr, util, _ in ENTITLEMENTS.get(customer_id, []):
            name, family = CATALOG[sku]
            rows.append(
                SkuEntitlement(
                    sku=sku, product_name=name, product_family=family, quantity=qty, arr=arr,
                    start_date=START, end_date=END, avg_units_30d=round(qty * util / 100, 2),
                    utilization_pct=util,
                )
            )
        return sorted(rows, key=lambda r: r.arr, reverse=True)

    async def product_health(self, customer_id: str) -> list[ProductHealth]:
        rows = []
        for sku, _, _, util, trend in ENTITLEMENTS.get(customer_id, []):
            score = _health_score(util, trend)
            rows.append(
                ProductHealth(
                    sku=sku, product_name=CATALOG[sku][0], health_score=score,
                    utilization_pct=util, trend_30d_pct=trend, status=_status(score),
                )
            )
        return sorted(rows, key=lambda r: r.health_score)

    async def propensity(self, customer_id: str) -> list[PropensityScore]:
        return [
            PropensityScore(model_name=m, model_version="v1", score=s, scored_at=NOW, top_drivers=d)
            for m, (s, d) in SCORES.get(customer_id, {}).items()
        ]

    async def top_scored(
        self, model_name: ModelName, min_score: float, limit: int
    ) -> list[tuple[str, PropensityScore]]:
        rows = []
        for cid, models in SCORES.items():
            s, d = models[model_name]
            if s >= min_score:
                rows.append((cid, PropensityScore(model_name=model_name, model_version="v1", score=s, scored_at=NOW, top_drivers=d)))
        return sorted(rows, key=lambda r: r[1].score, reverse=True)[:limit]


class FakeDocumentRepository:
    async def list_documents(self, customer_id: str) -> list[Document]:
        names = ["qbr-2026-q3.pdf", "order-form-2026.pdf", "success-plan.docx"]
        return [
            Document(
                key=f"customers/{customer_id}/{n}",
                name=n,
                size_bytes=250_000 + i * 10_000,
                last_modified=NOW - timedelta(days=30 * i),
                url=f"https://example.invalid/customers/{customer_id}/{n}",
            )
            for i, n in enumerate(names)
        ]
