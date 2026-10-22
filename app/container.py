from dataclasses import dataclass

from app.cache import TTLCache
from app.config import Settings
from app.repositories.fake import FakeCustomerRepository, FakeDocumentRepository, FakeInsightsRepository
from app.repositories.protocols import CustomerRepository, DocumentRepository, InsightsRepository
from app.sources.base import DataSource, NullSource
from app.services.customer360 import Customer360Service
from app.services.insights import CachedInsights
from app.services.portfolio import PortfolioService


@dataclass
class Container:
    settings: Settings
    sources: dict[str, DataSource]
    cache: TTLCache
    customers: CustomerRepository
    insights: CachedInsights
    customer360: Customer360Service
    portfolio: PortfolioService

    def modes(self) -> dict[str, str]:
        s = self.settings
        return {"snowflake": s.snowflake_mode, "postgres": s.postgres_mode, "s3": s.s3_mode}


def _snowflake(settings: Settings) -> tuple[DataSource, InsightsRepository]:
    if settings.snowflake_mode == "fake":
        return NullSource("snowflake"), FakeInsightsRepository()
    from app.repositories.snowflake_insights import SnowflakeInsightsRepository
    from app.sources.snowflake_source import SnowflakeSource

    source = SnowflakeSource(settings)
    return source, SnowflakeInsightsRepository(source)


def _postgres(settings: Settings) -> tuple[DataSource, CustomerRepository]:
    if settings.postgres_mode == "fake":
        return NullSource("postgres"), FakeCustomerRepository()
    from app.repositories.postgres_customers import PostgresCustomerRepository
    from app.sources.postgres_source import PostgresSource

    source = PostgresSource(settings)
    return source, PostgresCustomerRepository(source)


def _s3(settings: Settings) -> tuple[DataSource, DocumentRepository]:
    if settings.s3_mode == "fake":
        return NullSource("s3"), FakeDocumentRepository()
    from app.repositories.s3_documents import S3DocumentRepository
    from app.sources.s3_source import S3Source

    source = S3Source(settings)
    return source, S3DocumentRepository(source, settings.s3_prefix)


def build_container(
    settings: Settings,
    customers: CustomerRepository | None = None,
    insights: InsightsRepository | None = None,
    documents: DocumentRepository | None = None,
) -> Container:
    sf_source, sf_repo = _snowflake(settings)
    pg_source, pg_repo = _postgres(settings)
    s3_source, s3_repo = _s3(settings)

    customers = customers or pg_repo
    cache = TTLCache(settings.cache_ttl_seconds)
    cached = CachedInsights(insights or sf_repo, documents or s3_repo, cache)

    return Container(
        settings=settings,
        sources={"snowflake": sf_source, "postgres": pg_source, "s3": s3_source},
        cache=cache,
        customers=customers,
        insights=cached,
        customer360=Customer360Service(
            customers,
            cached,
            settings.section_timeout_seconds,
            settings.churn_threshold,
            settings.expansion_threshold,
        ),
        portfolio=PortfolioService(customers, cached),
    )


async def start(container: Container) -> None:
    for source in container.sources.values():
        await source.connect()


async def stop(container: Container) -> None:
    for source in container.sources.values():
        await source.close()
