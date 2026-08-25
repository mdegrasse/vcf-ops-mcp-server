from __future__ import annotations

from typing import Any

from ..client import VCFOpsClient


async def list_alerts(
    client: VCFOpsClient,
    *,
    resource_id: str | None = None,
    active_only: bool = True,
    criticality: str | None = None,
    page: int = 0,
    page_size: int = 100,
) -> dict[str, Any]:
    """List alerts, optionally scoped to a resource and/or criticality
    (INFORMATION/WARNING/IMMEDIATE/CRITICAL)."""
    data = await client.get(
        "/alerts",
        params={
            "resourceId": resource_id,
            "activeOnly": active_only,
            "alertCriticality": criticality,
            "page": page,
            "pageSize": page_size,
        },
    )
    return {"alerts": data.get("alerts", []), "pageInfo": data.get("pageInfo")}


async def get_alert(client: VCFOpsClient, alert_id: str) -> Any:
    """Get full details for a single alert by its identifier."""
    return await client.get(f"/alerts/{alert_id}")


async def list_alert_definitions(
    client: VCFOpsClient,
    *,
    adapter_kind: str | None = None,
    resource_kind: str | None = None,
    page: int = 0,
    page_size: int = 100,
) -> dict[str, Any]:
    """List alert definitions, optionally filtered by adapter/resource kind."""
    data = await client.get(
        "/alertdefinitions",
        params={
            "adapterKindKey": adapter_kind,
            "resourceKindKey": resource_kind,
            "page": page,
            "pageSize": page_size,
        },
    )
    return {"alertDefinitions": data.get("alertDefinitions", []), "pageInfo": data.get("pageInfo")}
