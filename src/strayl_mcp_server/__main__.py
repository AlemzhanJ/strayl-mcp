"""Entry point for the Strayl MCP server."""

from .server import mcp


def main():
    """Run the Strayl MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
