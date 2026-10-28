# Account assistant (MCP server) — demo

Lets a sales rep ask Claude about their accounts in plain language — *"Why is
Blue Ridge flagged?"*, *"Prep me for my Acme call"*, *"Log a follow-up for
Thursday"* — and get answers built from the live account data.

It is a small [Model Context Protocol](https://modelcontextprotocol.io) server
that turns the headless API's endpoints into tools Claude can call. It is
**another client of the API**, like the web app: it calls the same `/v1/...`
endpoints with an API key and never touches Snowflake, Postgres or S3.

```
Rep ──▶ Claude (Desktop, Code, claude.ai) ──MCP──▶ assistant/server.py ──HTTP + X-API-Key──▶ Customer Insights API
```

## Tools

| Tool | API call | What Claude uses it for |
|---|---|---|
| `find_accounts(query, owner)` | `GET /v1/customers` | "Which accounts does mpatel own?" |
| `get_account_360(account)` | `GET /v1/customers/{id}/360` | Any question about one account. Takes an ID (`C-1001`) or a name (`"acme"`). |
| `get_watchlist(kind, owner)` | `GET /v1/portfolio/at-risk` · `/expansion` | "Who in my book is most likely to churn?" |
| `log_next_step(account, …)` | `POST /v1/customers/{id}/actions` | "Log a meeting with Acme for Nov 6." The only tool that writes; Claude asks before calling it. |

There is also a prompt, **Account call brief** (`account_brief`), that asks
Claude for a one-page pre-call brief on an account.

The server's instructions tell Claude how to read the data: health bands
(70+ healthy, 40–69 watch, under 40 at risk), the 0.6 churn and expansion
thresholds behind the recommended motion, and to say when a section of the
360 came back in `errors[]` instead of treating it as empty.

## Run it

Start the API first (see the main README). Then install the assistant's two
dependencies:

```bash
pip install -r requirements-assistant.txt
```

| Variable | Default | |
|---|---|---|
| `CI_API_URL` | `http://localhost:8000` | Where the Customer Insights API runs |
| `CI_API_KEY` | none | One of the API's `CI_API_KEYS`, if it requires a key |

**Claude Code** (from the repo root):

```bash
claude mcp add customer-insights --env CI_API_URL=http://localhost:8000 --env CI_API_KEY=your-key -- python -m assistant.server
```

**Claude Desktop**: add this to `claude_desktop_config.json`, then restart the app:

```json
{
  "mcpServers": {
    "customer-insights": {
      "command": "python",
      "args": ["-m", "assistant.server"],
      "env": {
        "PYTHONPATH": "/path/to/Headless-Application-Design",
        "CI_API_URL": "http://localhost:8000",
        "CI_API_KEY": "your-key"
      }
    }
  }
}
```

**As a remote connector** (Streamable HTTP, served at `/mcp`):

```bash
python -m assistant.server --http --host 0.0.0.0 --port 8100
```

This demo has no sign-in of its own. Anyone who can reach that URL can use it
with the server's API key, so keep it on localhost or a private network until
SSO is in place (see the main README's roadmap).

## Try asking

- What's going on with Blue Ridge Health?
- Prep me for my call with Acme Aerospace.
- Which of jlee's accounts are expansion targets, and why?
- Which products are slipping across my book?
- Log a meeting on Acme for 6 Nov: book an OpenShift AI enablement workshop. I'm jlee.

## Tests

`tests/test_assistant.py` runs every tool against the in-process API with the
sample data:

```bash
pytest -q tests/test_assistant.py
```
