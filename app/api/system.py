import asyncio

from fastapi import APIRouter, Depends, Response, status

from app.api.deps import get_container, require_api_key
from app.container import Container
from app.schemas import SourceStatus

router = APIRouter(tags=["system"])


@router.get("/healthz")
async def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz", response_model=list[SourceStatus])
async def readiness(response: Response, c: Container = Depends(get_container)) -> list[SourceStatus]:
    names = list(c.sources)
    results = await asyncio.gather(*(c.sources[n].ping() for n in names))
    modes = c.modes()
    statuses = [SourceStatus(name=n, mode=modes[n], ok=ok) for n, ok in zip(names, results)]
    if not all(results):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return statuses


@router.post("/v1/admin/cache/clear", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_api_key)])
async def clear_cache(prefix: str = "", c: Container = Depends(get_container)) -> Response:
    c.cache.invalidate(prefix)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
