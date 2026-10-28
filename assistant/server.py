"""Customer Insights as an MCP server: ask Claude about any account.

Runs over stdio for Claude Desktop or Claude Code, or over Streamable HTTP
(`--http`) so it can be added as a remote connector. Configure with
CI_API_URL (default http://localhost:8000) and CI_API_KEY.
"""

import argparse
import logging
import os
from collections.abc import Callable
from datetime import date
from functools import wraps
from typing import Any, Literal, ParamSpec, TypeVar

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp_types import ToolAnnotations

from assistant.client import InsightsClient

P = ParamSpec("P")
R = TypeVar("R")

ActionType = Literal["call", "email", "meeting", "qbr", "renewal", "upsell", "escalation", "other"]

INSTRUCTIONS = """\
Customer Insights answers questions about a sales rep's accounts. Every tool
reads the same headless API the web app uses.

- Start with get_account_360 for any question about one account; it accepts
  a customer ID (C-1001) or a name ("Acme"). It returns owned SKUs with ARR
  and utilization, product health per SKU, churn and expansion scores with
  their top drivers, documents, the rep's recent next steps, and a summary
  with the recommended motion.
- Health is 0-100: 70+ healthy, 40-69 watch, under 40 at risk.
- Churn and expansion scores are 0-1 from ML models; 0.6 or more counts as
  high. The motion is retain (high churn), expand (high expansion),
  retain_and_expand (both) or nurture (neither).
- If the response lists errors[], say which sections were unavailable rather
  than treating them as empty.
- Use get_watchlist for questions across the book ("who is at risk?").
- Only call log_next_step when the user asks to record an action.
"""

mcp = MCPServer(name="customer-insights", title="Customer Insights", instructions=INSTRUCTIONS)
_client: InsightsClient | None = None


def client() -> InsightsClient:
    global _client
    if _client is None:
        _client = InsightsClient.connect(
            os.environ.get("CI_API_URL", "http://localhost:8000"), os.environ.get("CI_API_KEY")
        )
    return _client


def tool_errors(fn: Callable[P, R]) -> Callable[P, R]:
    """Report lookup and API failures to the model as readable tool errors."""

    @wraps(fn)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return fn(*args, **kwargs)
        except LookupError as exc:
            raise ToolError(str(exc)) from exc
        except httpx.HTTPStatusError as exc:
            raise ToolError(f"Customer Insights API returned {exc.response.status_code}: {exc.response.text}") from exc
        except httpx.HTTPError as exc:
            raise ToolError(f"Customer Insights API is unreachable: {exc}") from exc

    return wrapper


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
@tool_errors
def find_accounts(query: str = "", owner: str | None = None) -> list[dict[str, Any]]:
    """Search accounts by name or customer ID (partial, case-insensitive), optionally for one owner.

    Leave query empty to list every account. Returns ID, name, segment, region,
    owner and primary contact for each.
    """
    return client().find_accounts(query or None, owner)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
@tool_errors
def get_account_360(account: str) -> dict[str, Any]:
    """Everything about one account in one call: the Customer 360 view.

    `account` is a customer ID such as C-1001 or an account name, in full or in
    part ("Blue Ridge").
    """
    return client().account_360(account)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
@tool_errors
def get_watchlist(kind: Literal["at_risk", "expansion"], owner: str | None = None) -> list[dict[str, Any]]:
    """Accounts ranked by churn score (at_risk) or expansion score (expansion), at or above 0.6.

    Optionally only one owner's accounts. Each entry has the account and its score with top drivers.
    """
    return client().watchlist(kind, owner)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False))
@tool_errors
def log_next_step(
    account: str, action_type: ActionType, note: str, created_by: str, due_date: date | None = None
) -> dict[str, Any]:
    """Record a rep's next step on an account. Only when the user asks to log or save one.

    `created_by` is the rep's username (for example jlee). `due_date` is optional, as YYYY-MM-DD.
    """
    return client().log_next_step(account, action_type, note, created_by, due_date)


@mcp.prompt(title="Account call brief")
def account_brief(account: str) -> str:
    """Prepare a one-page brief before a customer call."""
    return (
        f"Prepare me for a call with {account}. Use get_account_360, then write a short brief: "
        "what they own and its ARR, which products are healthy or slipping and why, "
        "churn and expansion scores with their drivers, the recommended motion, "
        "what we promised last time (recent next steps), and three talking points."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--http", action="store_true", help="serve Streamable HTTP instead of stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8100)
    args = parser.parse_args()
    logging.getLogger("httpx").setLevel(logging.WARNING)
    if args.http:
        mcp.run("streamable-http", host=args.host, port=args.port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
