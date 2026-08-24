from __future__ import annotations

from typing import Any

from ..client import VCFOpsClient
from ..timeutil import to_epoch_millis


async def list_metric_keys(client: VCFOpsClient, adapter_kind: str, resource_kind: str) -> Any:
    """List the metric keys (statKeys) available for a given adapter/resource kind,
    e.g. adapter_kind='VMWARE', resource_kind='VirtualMachine'."""
    data = await client.get(f"/adapterkinds/{adapter_kind}/resourcekinds/{resource_kind}/statkeys")
    return data.get("resourceTypeAttributes", data)


async def get_latest_stats(
    client: VCFOpsClient,
    resource_id: str,
    stat_keys: list[str] | None = None,
) -> Any:
    """Get the most recent value for one or more metrics on a resource.

    Leave stat_keys empty to return the latest value of every metric collected
    for the resource (can be a large response for busy resource kinds)."""
    params: dict[str, Any] = {"currentOnly": True}
    if stat_keys:
        params["statKey"] = stat_keys
    data = await client.get(f"/resources/{resource_id}/stats", params=params)
    return data.get("values", data)


async def query_stats(
    client: VCFOpsClient,
    resource_ids: list[str],
    stat_keys: list[str],
    begin: str,
    end: str,
    roll_up_type: str | None = None,
    interval_type: str | None = None,
    interval_quantifier: int | None = None,
) -> Any:
    """Query historical metric time series for one or more resources.

    begin/end accept ISO 8601 timestamps (e.g. '2026-08-20T00:00:00Z') or epoch
    seconds/millis. roll_up_type is one of AVG/SUM/MIN/MAX/COUNT/LATEST/etc.,
    interval_type is one of SECONDS/MINUTES/HOURS/DAYS, used together to
    downsample (e.g. interval_type='HOURS', interval_quantifier=1)."""
    body = {
        "resourceId": resource_ids,
        "statKey": stat_keys,
        "begin": to_epoch_millis(begin),
        "end": to_epoch_millis(end),
        "rollUpType": roll_up_type,
        "intervalType": interval_type,
        "intervalQuantifier": interval_quantifier,
    }
    body = {k: v for k, v in body.items() if v is not None}
    data = await client.post("/resources/stats/query", json=body)
    return data.get("values", data)
