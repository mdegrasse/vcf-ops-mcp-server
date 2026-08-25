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

Server transport/auth configuration (also via `.env` or real environment variables):

| Variable                  | Description                                                              |
|---------------------------|---------------------------------------------------------------------------|
| `VCFOPS_MCP_TRANSPORT`    | `streamable-http` (default) or `stdio`                                    |
| `VCFOPS_MCP_HOST`         | Bind host for streamable-http (default `127.0.0.1`)                       |
| `VCFOPS_MCP_PORT`         | Bind port for streamable-http (default `8000`)                            |
| `VCFOPS_MCP_BEARER_TOKEN` | Required for streamable-http. Clients must send `Authorization: Bearer <value>` |

## Running

By default this runs as a standalone **remote server** over streamable-http,
bound to `127.0.0.1:8000`, requiring a bearer token on every request:

```bash
export VCFOPS_MCP_BEARER_TOKEN="$(openssl rand -hex 32)"
vcf-ops-mcp
# or
python -m vcf_ops_mcp
```

`GET /healthz` is unauthenticated (for load balancer/orchestrator liveness checks);
everything else requires the bearer token. `127.0.0.1` only listens locally — to
actually reach it from another host, bind `VCFOPS_MCP_HOST=0.0.0.0` (or run it
behind a reverse proxy) and make sure the bearer token is the only thing standing
between the network and credentials capable of querying your whole monitored
environment, so treat it like any other secret and prefer TLS termination (e.g. a
reverse proxy) in front of it rather than plaintext HTTP over an untrusted network.

Point an MCP client at it as a streamable-http server, e.g. in Claude Code:

```bash
claude mcp add --transport http vcf-operations http://<host>:8000/mcp \
  --header "Authorization: Bearer <your-token>"
```

### Running over stdio instead

For local use where an MCP client spawns the server itself as a subprocess (no
network exposure needed), set `VCFOPS_MCP_TRANSPORT=stdio` — the bearer token is
not required in this mode. Example Claude Desktop config:

```json
{
  "mcpServers": {
    "vcf-operations": {
      "command": "/absolute/path/to/.venv/bin/vcf-ops-mcp",
      "env": {
        "VCFOPS_MCP_TRANSPORT": "stdio",
        "VCFOPS_BASE_URL": "https://ops.example.com",
        "VCFOPS_USERNAME": "admin",
        "VCFOPS_PASSWORD": "changeme"
      }
    }
  }
}
```

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
