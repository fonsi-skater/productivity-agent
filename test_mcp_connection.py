
import asyncio
from pathlib import Path

from langchain.mcp import MCPAdapter


async def main():
    project_dir = Path(__file__).resolve().parent
    server_path = project_dir / "mcp_servers" / "hello_server.py"

    if not server_path.is_file():
        raise FileNotFoundError(
            f"MCP server file not found: {server_path}"
        )

    async with MCPAdapter(server_path) as adapter:
        tools = await adapter.list_tools()

        print("\nDiscovered MCP tools:")
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")

        greet_tool = next(
            (tool for tool in tools if tool.name == "greet_user"),
            None,
        )

        if greet_tool is None:
            raise RuntimeError(
                "The greet_user tool was not discovered."
            )

        result = await greet_tool.ainvoke(
            {"name": "Developer"}
        )

        print("\nTool result:")
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
