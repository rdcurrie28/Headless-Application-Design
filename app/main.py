import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import customers, portfolio, system
from app.config import Settings, get_settings
from app.container import Container, build_container, start, stop


def create_app(settings: Settings | None = None, container: Container | None = None) -> FastAPI:
    settings = settings or get_settings()
    container = container or build_container(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await start(container)
        app.state.container = container
        try:
            yield
        finally:
            await stop(container)

    app = FastAPI(title="Customer Insights API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["GET", "POST"],
        allow_headers=["X-API-Key", "Content-Type"],
    )
    app.include_router(system.router)
    app.include_router(customers.router)
    app.include_router(portfolio.router)
    return app


logging.basicConfig(level=logging.INFO)
app = create_app()
