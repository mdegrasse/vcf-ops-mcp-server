from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from mcp.server.fastmcp import Context, FastMCP

from vcf_ops_mcp.client import VCFOpsClient
from vcf_ops_mcp.config import load_settings
from vcf_ops_mcp.tools import alerts as alert_tools
from vcf_ops_mcp.tools import metrics as metric_tools
from vcf_ops_mcp.tools import resources as resource_tools


@dataclass
class AppContext:
    client: VCFOpsClient


@asynccontextmanager
async def app_lifespan(_server: FastMCP) -> AsyncIterator[AppContext]:
    client = VCFOpsClient(load_settings())
    try:
        yield AppContext(client=client)
    finally:
        await client.aclose()


mcp = FastMCP("vcf-operations", lifespan=app_lifespan)


def _client(ctx: Context) -> VCFOpsClient:
    return ctx.request_context.lifespan_context.client


@mcp.tool()
async def list_resources(
    ctx: Context,
    name: str | None = None,
    adapter_kind: str | None = None,
    resource_kind: str | None = None,
    resource_health: str | None = None,
    regex: bool = False,
    page: int = 0,
    page_size: int = 100,
) -> dict:
    """List monitored objects (VMs, hosts, clusters, datastores, etc.) in VCF Operations.

    Filter by name (substring or regex match, see `regex`), adapter_kind (e.g. VMWARE),
    resource_kind (e.g. VirtualMachine, HostSystem, ClusterComputeResource, Datastore),
    and/or resource_health (GREEN/YELLOW/ORANGE/RED/GREY).
    """
    return await resource_tools.list_resources(
        _client(ctx),
        name=name,
        adapter_kind=adapter_kind,
        resource_kind=resource_kind,
        resource_health=resource_health,
        regex=regex,
        page=page,
        page_size=page_size,
    )


@mcp.tool()
async def get_resource(ctx: Context, resource_id: str) -> dict:
    """Get full details for a single VCF Operations resource by its identifier."""
    return await resource_tools.get_resource(_client(ctx), resource_id)


@mcp.tool()
async def get_resource_properties(ctx: Context, resource_id: str) -> dict:
    """Get the configuration properties collected for a resource (e.g. CPU count, guest OS,
    vCenter cluster/host placement)."""
    return await resource_tools.get_resource_properties(_client(ctx), resource_id)


@mcp.tool()
async def get_resource_relationships(ctx: Context, resource_id: str) -> dict:
    """Get the parent and child resources related to a resource (e.g. the host and cluster a
    VM runs on, or the VMs running on a host)."""
    return await resource_tools.get_resource_relationships(_client(ctx), resource_id)


@mcp.tool()
async def list_metric_keys(ctx: Context, adapter_kind: str, resource_kind: str) -> dict:
    """List the metric keys (statKeys) available for a given adapter/resource kind pair,
    e.g. adapter_kind='VMWARE', resource_kind='VirtualMachine'. Use the returned keys with
    get_latest_stats / query_stats."""
    return await metric_tools.list_metric_keys(_client(ctx), adapter_kind, resource_kind)


@mcp.tool()
async def get_latest_stats(ctx: Context, resource_id: str, stat_keys: list[str] | None = None) -> dict:
    """Get the most recent value for one or more metrics on a resource. Omit stat_keys to
    return the latest value of every metric collected for the resource."""
    return await metric_tools.get_latest_stats(_client(ctx), resource_id, stat_keys)


@mcp.tool()
async def query_stats(
    ctx: Context,
    resource_ids: list[str],
    stat_keys: list[str],
    begin: str,
    end: str,
    roll_up_type: str | None = None,
    interval_type: str | None = None,
    interval_quantifier: int | None = None,
) -> dict:
    """Query historical metric time series for one or more resources over a time range.

    begin/end accept ISO 8601 timestamps (e.g. '2026-08-20T00:00:00Z') or epoch
    seconds/millis. Use roll_up_type (AVG/SUM/MIN/MAX/COUNT/LATEST) together with
    interval_type (SECONDS/MINUTES/HOURS/DAYS) and interval_quantifier to downsample,
    e.g. hourly averages over a day.
    """
    return await metric_tools.query_stats(
        _client(ctx),
        resource_ids,
        stat_keys,
        begin,
        end,
        roll_up_type=roll_up_type,
        interval_type=interval_type,
        interval_quantifier=interval_quantifier,
    )


@mcp.tool()
async def list_alerts(
    ctx: Context,
    resource_id: str | None = None,
    active_only: bool = True,
    criticality: str | None = None,
    page: int = 0,
    page_size: int = 100,
) -> dict:
    """List alerts, optionally scoped to a resource_id and/or criticality
    (INFORMATION/WARNING/IMMEDIATE/CRITICAL)."""
    return await alert_tools.list_alerts(
        _client(ctx),
        resource_id=resource_id,
        active_only=active_only,
        criticality=criticality,
        page=page,
        page_size=page_size,
    )


@mcp.tool()
async def get_alert(ctx: Context, alert_id: str) -> dict:
    """Get full details for a single alert by its identifier."""
    return await alert_tools.get_alert(_client(ctx), alert_id)


@mcp.tool()
async def list_alert_definitions(
    ctx: Context,
    adapter_kind: str | None = None,
    resource_kind: str | None = None,
    page: int = 0,
    page_size: int = 100,
) -> dict:
    """List alert definitions (the rules that trigger alerts), optionally filtered by
    adapter/resource kind."""
    return await alert_tools.list_alert_definitions(
        _client(ctx),
        adapter_kind=adapter_kind,
        resource_kind=resource_kind,
        page=page,
        page_size=page_size,
    )
