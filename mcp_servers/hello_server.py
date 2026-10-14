from mcp.server.mcpserver import MCPServer

# Create the MCP server
mcp = MCPServer("Productivity Helper")


@mcp.tool()
def greet_user(name: str) -> str:
    """Greet a user by name."""
    return f"Hello, {name}! Your MCP server is working."


if __name__ == "__main__":
    mcp.run(transport="stdio")
