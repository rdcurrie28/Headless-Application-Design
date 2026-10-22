import asyncio

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.container import build_container
from app.main import create_app
from app.repositories.fake import FakeInsightsRepository
from app.services.customer360 import recommend_motion

HEADERS = {"X-API-Key": "test-key"}


def make_client(**overrides) -> TestClient:
    settings = Settings(_env_file=None, api_keys="test-key", cache_ttl_seconds=60, section_timeout_seconds=0.5)
    container = build_container(settings, **overrides)
    return TestClient(create_app(settings, container))


@pytest.fixture
def client():
    with make_client() as c:
        yield c


def test_liveness_and_readiness(client):
    assert client.get("/healthz").json() == {"status": "ok"}
    ready = client.get("/readyz")
    assert ready.status_code == 200
    assert {s["name"] for s in ready.json()} == {"snowflake", "postgres", "s3"}


def test_api_key_required(client):
    assert client.get("/v1/customers").status_code == 401
    assert client.get("/v1/customers", headers={"X-API-Key": "wrong"}).status_code == 401


def test_list_and_search_customers(client):
    page = client.get("/v1/customers", headers=HEADERS).json()
    assert page["total"] == 5
    hits = client.get("/v1/customers", params={"search": "delta"}, headers=HEADERS).json()
    assert [c["customer_id"] for c in hits["items"]] == ["C-1004"]
    by_partial_id = client.get("/v1/customers", params={"search": " c-1005 "}, headers=HEADERS).json()
    assert [c["customer_id"] for c in by_partial_id["items"]] == ["C-1005"]
    by_id_fragment = client.get("/v1/customers", params={"search": "1005"}, headers=HEADERS).json()
    assert [c["customer_id"] for c in by_id_fragment["items"]] == ["C-1005"]


def test_customer_has_contact_details(client):
    c = client.get("/v1/customers/C-1004", headers=HEADERS).json()
    assert c["contact_name"] == "Sofia Lindqvist"
    assert c["contact_phone"] == "+44 20 7946 0321"
    assert c["address"] == "30 Finsbury Square, London EC2A 1AG, UK"
    listed = client.get("/v1/customers", params={"search": "C-1004"}, headers=HEADERS).json()["items"][0]
    assert listed["contact_name"] == "Sofia Lindqvist"


def test_unknown_customer_404(client):
    assert client.get("/v1/customers/NOPE", headers=HEADERS).status_code == 404
    assert client.get("/v1/customers/NOPE/360", headers=HEADERS).status_code == 404


def test_section_endpoints(client):
    skus = client.get("/v1/customers/C-1001/skus", headers=HEADERS).json()
    assert skus[0]["sku"] == "OCP-PREM"
    health = client.get("/v1/customers/C-1001/product-health", headers=HEADERS).json()
    assert health[0]["status"] == "at_risk"
    scores = client.get("/v1/customers/C-1001/propensity", headers=HEADERS).json()
    assert {s["model_name"] for s in scores} == {"churn", "expansion"}
    docs = client.get("/v1/customers/C-1001/documents", headers=HEADERS).json()
    assert docs[0]["name"] == "qbr-2026-q3.pdf"


def test_customer_360_full(client):
    body = client.get("/v1/customers/C-1005/360", headers=HEADERS).json()
    assert body["errors"] == []
    assert body["summary"]["recommended_motion"] == "retain"
    assert body["summary"]["sku_count"] == 1
    assert body["summary"]["at_risk_skus"] == 1


def test_actions_roundtrip_shows_in_360(client):
    payload = {"action_type": "call", "note": "Exec sponsor check-in", "created_by": "jlee"}
    created = client.post("/v1/customers/C-1002/actions", json=payload, headers=HEADERS)
    assert created.status_code == 201
    body = client.get("/v1/customers/C-1002/360", headers=HEADERS).json()
    assert body["recent_actions"][0]["note"] == "Exec sponsor check-in"


def test_portfolio_rankings(client):
    at_risk = client.get("/v1/portfolio/at-risk", headers=HEADERS).json()
    assert [a["customer"]["customer_id"] for a in at_risk] == ["C-1005", "C-1002"]
    mine = client.get("/v1/portfolio/expansion", params={"owner": "jlee"}, headers=HEADERS).json()
    assert [a["customer"]["customer_id"] for a in mine] == ["C-1003", "C-1001"]


class BrokenInsights(FakeInsightsRepository):
    async def product_health(self, customer_id):
        raise ConnectionError("warehouse suspended")

    async def propensity(self, customer_id):
        await asyncio.sleep(2)
        return []


def test_customer_360_degrades_per_section():
    with make_client(insights=BrokenInsights()) as c:
        body = c.get("/v1/customers/C-1001/360", headers=HEADERS).json()
    assert body["skus"] is not None
    assert body["product_health"] is None
    assert body["propensity"] is None
    errors = {e["section"]: e["message"] for e in body["errors"]}
    assert errors == {"product_health": "ConnectionError", "propensity": "timed out"}
    assert body["summary"]["recommended_motion"] == "unknown"


@pytest.mark.parametrize(
    "churn,expansion,expected",
    [(0.7, 0.7, "retain_and_expand"), (0.7, 0.1, "retain"), (0.1, 0.7, "expand"), (0.1, 0.1, "nurture"), (None, None, "unknown")],
)
def test_recommend_motion(churn, expansion, expected):
    assert recommend_motion(churn, expansion, 0.6, 0.6) == expected
