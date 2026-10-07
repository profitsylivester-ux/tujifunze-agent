"""
Minimal MCP client test: spawn custom_server.py as a subprocess,
initialize the MCP session, list tools, and call one tool.
"""

import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# Use the SAME python that is running this script (the venv python),
# so the subprocess inherits the venv's installed packages.
VENV_PYTHON = sys.executable


async def main():
    params = StdioServerParameters(
        command=VENV_PYTHON,
        args=["-m", "mcp_server.custom_server"],
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("=== Available tools ===")
            for t in tools.tools:
                print(f"  - {t.name}")

            print()
            print("=== Calling list_students ===")
            result = await session.call_tool("list_students", {})
            for item in result.content:
                if item.type == "text":
                    print(item.text)

            print()
            print("=== Calling get_student_historical_records for S002 (Brian) ===")
            result = await session.call_tool(
                "get_student_historical_records",
                {"student_id": "S002"},
            )
            for item in result.content:
                if item.type == "text":
                    import json
                    data = json.loads(item.text)
                    print("Student:", data["profile"]["full_name"])
                    print("Terms:  ", list(data["scores_by_term"].keys()))


if __name__ == "__main__":
    asyncio.run(main())
