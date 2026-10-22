from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader

from app.container import Container

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_container(request: Request) -> Container:
    return request.app.state.container


def require_api_key(
    key: str | None = Depends(api_key_header),
    container: Container = Depends(get_container),
) -> None:
    allowed = container.settings.api_key_set
    if allowed and key not in allowed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")
