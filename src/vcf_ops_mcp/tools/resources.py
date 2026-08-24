from __future__ import annotations

from typing import Any

from ..client import VCFOpsClient


async def list_resources(
    client: VCFOpsClient,
    *,
    name: str | None = None,
    adapter_kind: str | None = None,
    resource_kind: str | None = None,
    resource_health: str | None = None,
    regex: bool = False,
    page: int = 0,
    page_size: int = 100,
) -> dict[str, Any]:
    """List monitored objects (VMs, hosts, clusters, datastores, etc.)."""
    params = {
        "name": name,
        "adapterKind": adapter_kind,
        "resourceKind": resource_kind,
        "resourceHealth": resource_health,
        "regex": regex,
        "page": page,
        "pageSize": page_size,
    }
    data = await client.get("/resources", params=params)
    return {
        "resources": data.get("resourceList", []),
        "pageInfo": data.get("pageInfo"),
    }


async def get_resource(client: VCFOpsClient, resource_id: str) -> Any:
    """Get full details for a single resource by its identifier."""
    return await client.get(f"/resources/{resource_id}")


async def get_resource_properties(client: VCFOpsClient, resource_id: str) -> Any:
    """Get the configuration properties collected for a resource."""
    data = await client.get(f"/resources/{resource_id}/properties")
    return data.get("property", data)


async def get_resource_relationships(client: VCFOpsClient, resource_id: str) -> Any:
    """Get the parent and child resources related to a resource."""
    return await client.get(f"/resources/{resource_id}/relationships")
