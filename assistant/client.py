"""A thin client for the Customer Insights API, shaped for an AI assistant.

The assistant is just another client of the headless API: it calls the same
`/v1/...` endpoints as the web app, with an API key, and never touches
Snowflake, Postgres or S3 itself.
"""

import re
from datetime import date
from typing import Any, Literal

import httpx

CUSTOMER_ID = re.compile(r"^C-\d+$", re.IGNORECASE)

Watchlist = Literal["at_risk", "expansion"]


class AccountNotFound(LookupError):
    pass


class AmbiguousAccount(LookupError):
    def __init__(self, query: str, matches: list[dict[str, Any]]) -> None:
        names = ", ".join(f"{m['name']} ({m['customer_id']})" for m in matches)
        super().__init__(f"'{query}' matches more than one account: {names}. Ask which one is meant.")
        self.matches = matches


class InsightsClient:
    def __init__(self, http: httpx.Client) -> None:
        self._http = http

    @classmethod
    def connect(cls, base_url: str, api_key: str | None, timeout: float = 15.0) -> "InsightsClient":
        headers = {"X-API-Key": api_key} if api_key else {}
        return cls(httpx.Client(base_url=base_url, headers=headers, timeout=timeout))

    def _get(self, path: str, **params: Any) -> Any:
        r = self._http.get(path, params={k: v for k, v in params.items() if v is not None})
        r.raise_for_status()
        return r.json()

    def find_accounts(self, query: str | None = None, owner: str | None = None, limit: int = 25) -> list[dict[str, Any]]:
        page = self._get("/v1/customers", search=query or None, owner=owner, limit=limit)
        return page["items"]

    def resolve(self, account: str) -> str:
        """Turn a customer ID or a (partial) account name into one customer ID."""
        account = account.strip()
        if CUSTOMER_ID.match(account):
            return account.upper()
        matches = self.find_accounts(account)
        if not matches:
            raise AccountNotFound(f"No account matches '{account}'.")
        exact = [m for m in matches if m["name"].lower() == account.lower()]
        if len(exact) == 1:
            return exact[0]["customer_id"]
        if len(matches) > 1:
            raise AmbiguousAccount(account, matches)
        return matches[0]["customer_id"]

    def account_360(self, account: str) -> dict[str, Any]:
        customer_id = self.resolve(account)
        r = self._http.get(f"/v1/customers/{customer_id}/360")
        if r.status_code == 404:
            raise AccountNotFound(f"No account with ID {customer_id}.")
        r.raise_for_status()
        return r.json()

    def watchlist(self, kind: Watchlist, owner: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
        path = "/v1/portfolio/at-risk" if kind == "at_risk" else "/v1/portfolio/expansion"
        return self._get(path, owner=owner, limit=limit)

    def log_next_step(
        self, account: str, action_type: str, note: str, created_by: str, due_date: date | None = None
    ) -> dict[str, Any]:
        customer_id = self.resolve(account)
        body = {"action_type": action_type, "note": note, "created_by": created_by}
        if due_date:
            body["due_date"] = due_date.isoformat()
        r = self._http.post(f"/v1/customers/{customer_id}/actions", json=body)
        r.raise_for_status()
        return r.json()
