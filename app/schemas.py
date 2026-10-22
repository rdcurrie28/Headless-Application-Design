from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

HealthStatus = Literal["healthy", "watch", "at_risk"]
ModelName = Literal["churn", "expansion"]
Motion = Literal["retain", "expand", "retain_and_expand", "nurture", "unknown"]
ActionType = Literal["call", "email", "meeting", "qbr", "renewal", "upsell", "escalation", "other"]


class Customer(BaseModel):
    customer_id: str
    name: str
    segment: str | None = None
    region: str | None = None
    account_owner: str | None = None
    salesforce_id: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    address: str | None = None


class CustomerPage(BaseModel):
    items: list[Customer]
    total: int
    limit: int
    offset: int


class SkuEntitlement(BaseModel):
    sku: str
    product_name: str
    product_family: str | None = None
    quantity: float
    arr: float
    start_date: date
    end_date: date
    avg_units_30d: float
    utilization_pct: float


class ProductHealth(BaseModel):
    sku: str
    product_name: str
    health_score: float
    utilization_pct: float
    trend_30d_pct: float | None = None
    status: HealthStatus


class PropensityScore(BaseModel):
    model_name: ModelName
    model_version: str | None = None
    score: float = Field(ge=0, le=1)
    scored_at: datetime
    top_drivers: list[str] = []


class Document(BaseModel):
    key: str
    name: str
    size_bytes: int
    last_modified: datetime
    url: str


class RepActionCreate(BaseModel):
    action_type: ActionType
    note: str = Field(min_length=1, max_length=4000)
    created_by: str
    due_date: date | None = None


class RepAction(RepActionCreate):
    action_id: int
    customer_id: str
    created_at: datetime


class SectionError(BaseModel):
    section: str
    source: str
    message: str


class Customer360Summary(BaseModel):
    total_arr: float | None = None
    sku_count: int | None = None
    avg_health_score: float | None = None
    at_risk_skus: int | None = None
    churn_score: float | None = None
    expansion_score: float | None = None
    recommended_motion: Motion = "unknown"


class Customer360(BaseModel):
    customer: Customer
    summary: Customer360Summary
    skus: list[SkuEntitlement] | None = None
    product_health: list[ProductHealth] | None = None
    propensity: list[PropensityScore] | None = None
    documents: list[Document] | None = None
    recent_actions: list[RepAction] | None = None
    errors: list[SectionError] = []
    generated_at: datetime


class ScoredAccount(BaseModel):
    customer: Customer
    model_name: ModelName
    score: float
    scored_at: datetime
    top_drivers: list[str] = []


class SourceStatus(BaseModel):
    name: str
    mode: str
    ok: bool
