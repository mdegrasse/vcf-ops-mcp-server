# vcf-ops-mcp

An MCP server that wraps the VCF Operations (vROps) `suite-api` REST API, exposing
resources, metrics, and alerts as MCP tools so an LLM client can query monitored
infrastructure directly.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # then fill in your VCF Operations details
```

Required configuration (via `.env` or real environment variables):

| Variable              | Description                                                        |
|-----------------------|----------------------------------------------------------------------|
| `VCFOPS_BASE_URL`     | Base URL of the VCF Operations instance, e.g. `https://ops.example.com` |
| `VCFOPS_USERNAME`     | User to authenticate as                                              |
| `VCFOPS_PASSWORD`     | Password for that user                                               |
| `VCFOPS_AUTH_SOURCE`  | Auth source name (default `LOCAL`)                                   |
| `VCFOPS_VERIFY_SSL`   | Set `false` to skip TLS verification against self-signed lab instances |
| `VCFOPS_TIMEOUT`      | Per-request timeout in seconds (default `30`)                        |

The server acquires a token from `/suite-api/api/auth/token/acquire` on first use,
caches it, and transparently re-acquires it when it's near expiry or rejected with
401.

## Running

```bash
vcf-ops-mcp
# or
python -m vcf_ops_mcp
```

This runs over **stdio**, so register it with an MCP client (Claude Desktop, Claude
Code, etc.) as a local command, e.g. in Claude Desktop's config:

```json
{
  "mcpServers": {
    "vcf-operations": {
      "command": "/absolute/path/to/.venv/bin/vcf-ops-mcp",
      "env": {
        "VCFOPS_BASE_URL": "https://ops.example.com",
        "VCFOPS_USERNAME": "admin",
        "VCFOPS_PASSWORD": "changeme"
      }
    }
  }
}
```

### Going remote later

The tool definitions in [`server.py`](src/vcf_ops_mcp/server.py) don't depend on the
transport. To expose this over the network instead of stdio, change the `mcp.run()`
call in [`__main__.py`](src/vcf_ops_mcp/__main__.py) to
`mcp.run(transport="streamable-http")` (FastMCP listens on `127.0.0.1:8000` by
default; configure host/port via `mcp.settings`). Do **not** put this on an
untrusted network as-is — the server holds credentials capable of querying your
whole monitored environment, and streamable-http has no built-in access control.
Put it behind a reverse proxy that enforces bearer-token or mTLS auth first.

## Tools

**Resources**
- `list_resources` — search monitored objects by name/adapter kind/resource kind/health
- `get_resource` — full detail for one resource
- `get_resource_properties` — collected configuration properties
- `get_resource_relationships` — parent/child objects

**Metrics**
- `list_metric_keys` — available statKeys for an adapter/resource kind pair
- `get_latest_stats` — most recent metric value(s) for a resource
- `query_stats` — historical time series across resources, with rollup/interval

**Alerts**
- `list_alerts` — active/all alerts, optionally scoped to a resource or criticality
- `get_alert` — full detail for one alert
- `list_alert_definitions` — the rule definitions behind alerts

## Testing

```bash
pip install -e ".[dev]"
pytest
```

Tests mock the VCF Operations HTTP API with `respx` — no live instance required.

## Notes

- Pinned to `mcp<2.0.0`: the MCP Python SDK's 2.x line renamed `FastMCP` to
  `MCPServer` and moved it to `mcp.server.mcpserver`. This project targets the
  well-established 1.x `mcp.server.fastmcp.FastMCP` API.
