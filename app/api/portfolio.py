from fastapi import APIRouter, Depends, Query

from app.api.deps import get_container, require_api_key
from app.container import Container
from app.schemas import ScoredAccount

router = APIRouter(prefix="/v1/portfolio", tags=["portfolio"], dependencies=[Depends(require_api_key)])


@router.get("/at-risk", response_model=list[ScoredAccount])
async def at_risk(
    min_score: float | None = Query(None, ge=0, le=1),
    owner: str | None = None,
    limit: int = Query(25, ge=1, le=200),
    c: Container = Depends(get_container),
) -> list[ScoredAccount]:
    threshold = c.settings.churn_threshold if min_score is None else min_score
    return await c.portfolio.ranked("churn", threshold, limit, owner)


@router.get("/expansion", response_model=list[ScoredAccount])
async def expansion(
    min_score: float | None = Query(None, ge=0, le=1),
    owner: str | None = None,
    limit: int = Query(25, ge=1, le=200),
    c: Container = Depends(get_container),
) -> list[ScoredAccount]:
    threshold = c.settings.expansion_threshold if min_score is None else min_score
    return await c.portfolio.ranked("expansion", threshold, limit, owner)
