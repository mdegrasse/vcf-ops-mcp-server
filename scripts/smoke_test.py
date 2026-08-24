"""Quick manual check against a real VCF Operations server.

Bypasses the MCP protocol entirely - just exercises the client and tool
functions directly, using whatever VCFOPS_* config is set (.env or real
env vars). Useful for confirming auth and basic API calls work before
wiring up an MCP client.

Usage:
    python scripts/smoke_test.py
"""

import asyncio

from vcf_ops_mcp.client import VCFOpsClient
from vcf_ops_mcp.config import load_settings
from vcf_ops_mcp.tools import alerts, resources


async def main() -> None:
    client = VCFOpsClient(load_settings())
    try:
        print("Acquiring token and listing resources...")
        result = await resources.list_resources(client, page_size=5)
        for r in result["resources"]:
            key = r.get("resourceKey", {})
            print(f"  - {key.get('name')} ({key.get('resourceKindKey')})")

        print("\nListing active alerts...")
        alert_result = await alerts.list_alerts(client, page_size=5)
        for a in alert_result["alerts"]:
            print(f"  - {a.get('alertLevel')} {a.get('alertDefinitionName')}")
    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
