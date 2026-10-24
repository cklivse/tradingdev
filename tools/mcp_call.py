"""Call one tool on the real tradingdev MCP server over stdio.

Usage: python mcp_call.py <tool> <args.json | '{}'> [out.json]
Spawns the server exactly as .mcp.json does and prints the tool result.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def main() -> None:
    tool, raw = sys.argv[1], sys.argv[2]
    arguments = json.loads(Path(raw).read_text() if raw.endswith(".json") else raw)
    params = StdioServerParameters(
        command="uv",
        args=["run", "--directory", "/workspaces/tradingdev", "tradingdev-mcp"],
    )
    async with stdio_client(params) as streams, ClientSession(*streams) as session:
        await session.initialize()
        result = await session.call_tool(tool, arguments, read_timeout_seconds=900)
    dumped = result.model_dump(mode="json", by_alias=True, exclude_none=True)
    text = json.dumps(dumped, ensure_ascii=False, indent=2)
    if len(sys.argv) > 3:
        Path(sys.argv[3]).write_text(text, encoding="utf-8")
    print(text)


asyncio.run(main())
