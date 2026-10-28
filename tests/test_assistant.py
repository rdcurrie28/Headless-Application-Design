import asyncio

import pytest
from mcp import Client

from assistant import server
from assistant.client import AmbiguousAccount, InsightsClient
from tests.test_api import HEADERS, make_client


@pytest.fixture
def insights():
    with make_client() as api:
        api.headers.update(HEADERS)
        server._client = InsightsClient(api)
        yield server._client
    server._client = None


def call(tool: str, **arguments):
    async def run():
        async with Client(server.mcp) as c:
            return await c.call_tool(tool, arguments)

    return asyncio.run(run())


def test_tools_are_listed_with_read_only_hints():
    async def run():
        async with Client(server.mcp) as c:
            return {t.name: t.annotations.read_only_hint for t in (await c.list_tools()).tools}

    assert asyncio.run(run()) == {
        "find_accounts": True,
        "get_account_360": True,
        "get_watchlist": True,
        "log_next_step": False,
    }


def test_resolve_by_id_name_and_partial_name(insights):
    assert insights.resolve("c-1002") == "C-1002"
    assert insights.resolve("Blue Ridge Health") == "C-1002"
    assert insights.resolve("cardinal") == "C-1003"


def test_resolve_ambiguous_names_the_matches(insights):
    with pytest.raises(AmbiguousAccount) as exc:
        insights.resolve("e")
    assert "Acme Aerospace (C-1001)" in str(exc.value)


def test_account_360_by_name(insights):
    result = call("get_account_360", account="Evergreen")
    assert not result.is_error
    body = result.structured_content
    assert body["customer"]["customer_id"] == "C-1005"
    assert body["summary"]["recommended_motion"] == "retain"
    assert body["errors"] == []


def test_unknown_account_is_a_readable_tool_error(insights):
    result = call("get_account_360", account="Zenith Mining")
    assert result.is_error
    assert "No account matches 'Zenith Mining'" in result.content[0].text


def test_watchlist_ranks_by_score(insights):
    result = call("get_watchlist", kind="at_risk")
    ids = [row["customer"]["customer_id"] for row in result.structured_content["result"]]
    assert ids == ["C-1005", "C-1002"]


def test_log_next_step_shows_up_in_the_360(insights):
    logged = call(
        "log_next_step", account="Acme", action_type="call", note="Walk through OpenShift AI adoption", created_by="jlee"
    )
    assert not logged.is_error
    actions = call("get_account_360", account="C-1001").structured_content["recent_actions"]
    assert actions[0]["note"] == "Walk through OpenShift AI adoption"


def test_account_brief_prompt_names_the_account():
    async def run():
        async with Client(server.mcp) as c:
            return await c.get_prompt("account_brief", {"account": "Delta Fintech"})

    text = asyncio.run(run()).messages[0].content.text
    assert "Delta Fintech" in text and "get_account_360" in text
