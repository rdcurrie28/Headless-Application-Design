from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_container, require_api_key
from app.container import Container
from app.schemas import (
    Customer,
    Customer360,
    CustomerPage,
    Document,
    ProductHealth,
    PropensityScore,
    RepAction,
    RepActionCreate,
    SkuEntitlement,
)
from app.services.errors import CustomerNotFound

router = APIRouter(prefix="/v1/customers", tags=["customers"], dependencies=[Depends(require_api_key)])


async def existing_customer(customer_id: str, c: Container = Depends(get_container)) -> Customer:
    customer = await c.customers.get_customer(customer_id)
    if customer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Customer {customer_id} not found")
    return customer


@router.get("", response_model=CustomerPage)
async def list_customers(
    search: str | None = None,
    region: str | None = None,
    owner: str | None = None,
    limit: int = Query(25, ge=1, le=200),
    offset: int = Query(0, ge=0),
    c: Container = Depends(get_container),
) -> CustomerPage:
    search = (search or "").strip() or None
    return await c.customers.list_customers(search, region, owner, limit, offset)


@router.get("/{customer_id}", response_model=Customer)
async def get_customer(customer: Customer = Depends(existing_customer)) -> Customer:
    return customer


@router.get("/{customer_id}/360", response_model=Customer360)
async def customer_360(customer_id: str, c: Container = Depends(get_container)) -> Customer360:
    try:
        return await c.customer360.build(customer_id)
    except CustomerNotFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{customer_id}/skus", response_model=list[SkuEntitlement])
async def customer_skus(
    customer: Customer = Depends(existing_customer), c: Container = Depends(get_container)
) -> list[SkuEntitlement]:
    return await c.insights.skus(customer.customer_id)


@router.get("/{customer_id}/product-health", response_model=list[ProductHealth])
async def customer_health(
    customer: Customer = Depends(existing_customer), c: Container = Depends(get_container)
) -> list[ProductHealth]:
    return await c.insights.health(customer.customer_id)


@router.get("/{customer_id}/propensity", response_model=list[PropensityScore])
async def customer_propensity(
    customer: Customer = Depends(existing_customer), c: Container = Depends(get_container)
) -> list[PropensityScore]:
    return await c.insights.propensity(customer.customer_id)


@router.get("/{customer_id}/documents", response_model=list[Document])
async def customer_documents(
    customer: Customer = Depends(existing_customer), c: Container = Depends(get_container)
) -> list[Document]:
    return await c.insights.documents(customer.customer_id)


@router.get("/{customer_id}/actions", response_model=list[RepAction])
async def list_actions(
    limit: int = Query(25, ge=1, le=200),
    customer: Customer = Depends(existing_customer),
    c: Container = Depends(get_container),
) -> list[RepAction]:
    return await c.customers.list_actions(customer.customer_id, limit)


@router.post("/{customer_id}/actions", response_model=RepAction, status_code=status.HTTP_201_CREATED)
async def create_action(
    body: RepActionCreate,
    customer: Customer = Depends(existing_customer),
    c: Container = Depends(get_container),
) -> RepAction:
    return await c.customers.create_action(customer.customer_id, body)
