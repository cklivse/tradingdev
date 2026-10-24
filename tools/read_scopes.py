"""Read every trial scope of one run through the real MCP get_run_metrics tool."""
import asyncio, json, sys
from pathlib import Path
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

RUN = sys.argv[1]
OUT = Path(sys.argv[2])

async def main() -> None:
    params = StdioServerParameters(command="uv", args=["run", "--directory", "/workspaces/tradingdev", "tradingdev-mcp"])
    results = {}
    async with stdio_client(params) as streams, ClientSession(*streams) as session:
        await session.initialize()
        for scope in [f"trial/{i}/train" for i in range(15)] + ["test"]:
            r = await session.call_tool("get_run_metrics", {"run_id": RUN, "scope": scope})
            results[scope] = r.model_dump(mode="json", by_alias=True, exclude_none=True)
    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

asyncio.run(main())
