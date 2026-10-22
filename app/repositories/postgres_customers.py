from app.schemas import Customer, CustomerPage, RepAction, RepActionCreate
from app.sources.postgres_source import PostgresSource

CUSTOMER_COLUMNS = (
    "customer_id, name, segment, region, account_owner, salesforce_id, contact_name, contact_phone, address"
)

LIST_CUSTOMERS_SQL = f"""
SELECT {CUSTOMER_COLUMNS}, count(*) OVER () AS total
FROM customers
WHERE ($1::text IS NULL OR name ILIKE '%' || $1 || '%' OR customer_id ILIKE '%' || $1 || '%')
  AND ($2::text IS NULL OR region = $2)
  AND ($3::text IS NULL OR account_owner = $3)
ORDER BY name
LIMIT $4 OFFSET $5
"""

GET_CUSTOMER_SQL = f"SELECT {CUSTOMER_COLUMNS} FROM customers WHERE customer_id = $1"

GET_CUSTOMERS_SQL = f"SELECT {CUSTOMER_COLUMNS} FROM customers WHERE customer_id = ANY($1::text[])"

LIST_ACTIONS_SQL = """
SELECT action_id, customer_id, action_type, note, created_by, due_date, created_at
FROM rep_actions
WHERE customer_id = $1
ORDER BY created_at DESC
LIMIT $2
"""

CREATE_ACTION_SQL = """
INSERT INTO rep_actions (customer_id, action_type, note, created_by, due_date)
VALUES ($1, $2, $3, $4, $5)
RETURNING action_id, customer_id, action_type, note, created_by, due_date, created_at
"""


class PostgresCustomerRepository:
    def __init__(self, source: PostgresSource) -> None:
        self._db = source

    async def list_customers(
        self, search: str | None, region: str | None, owner: str | None, limit: int, offset: int
    ) -> CustomerPage:
        rows = await self._db.fetch_all(LIST_CUSTOMERS_SQL, search, region, owner, limit, offset)
        total = rows[0]["total"] if rows else 0
        items = [Customer(**{k: v for k, v in r.items() if k != "total"}) for r in rows]
        return CustomerPage(items=items, total=total, limit=limit, offset=offset)

    async def get_customer(self, customer_id: str) -> Customer | None:
        row = await self._db.fetch_one(GET_CUSTOMER_SQL, customer_id)
        return Customer(**row) if row else None

    async def get_customers(self, customer_ids: list[str]) -> list[Customer]:
        if not customer_ids:
            return []
        rows = await self._db.fetch_all(GET_CUSTOMERS_SQL, customer_ids)
        return [Customer(**r) for r in rows]

    async def list_actions(self, customer_id: str, limit: int) -> list[RepAction]:
        rows = await self._db.fetch_all(LIST_ACTIONS_SQL, customer_id, limit)
        return [RepAction(**r) for r in rows]

    async def create_action(self, customer_id: str, action: RepActionCreate) -> RepAction:
        row = await self._db.fetch_one(
            CREATE_ACTION_SQL,
            customer_id,
            action.action_type,
            action.note,
            action.created_by,
            action.due_date,
        )
        return RepAction(**row)
