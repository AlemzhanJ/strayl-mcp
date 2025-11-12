"""Strayl MCP Server - Log search tools."""

import os
from typing import Annotated, Optional
import httpx
from mcp.server.fastmcp import FastMCP

from .utils import parse_time_period, format_log_result

# Initialize FastMCP server
mcp = FastMCP(
    "Strayl Log Search",
    dependencies=[
        "httpx>=0.27.0",
        "python-dateutil>=2.8.0",
    ]
)


# Strayl API base URL (hardcoded)
STRAYL_API_URL = "https://ougtygyvcgdnytkswier.supabase.co/functions/v1"


def get_api_key() -> str:
    """Get API key from environment variable."""
    api_key = os.getenv("STRAYL_API_KEY", "")

    if not api_key:
        raise ValueError(
            "STRAYL_API_KEY environment variable is required. "
            "Get your API key from https://strayl.dev"
        )

    return api_key


@mcp.tool()
async def search_logs_semantic(
    query: Annotated[str, "Search query in natural language or keywords"],
    time_period: Annotated[Optional[str], "Time filter: 5m, 1h, today, yesterday, 7d, 30d, etc."] = None,
    match_threshold: Annotated[float, "Minimum similarity score (0.0 to 1.0)"] = 0.5,
    match_count: Annotated[int, "Maximum number of results to return"] = 50,
) -> str:
    """Search logs using semantic (vector) search with optional time filtering.

    This tool performs AI-powered semantic search across your logs, finding relevant entries
    even if they don't contain exact keywords."""
    try:
        api_key = get_api_key()

        # Parse time period if provided
        start_time = None
        end_time = None
        if time_period:
            start_time, end_time = parse_time_period(time_period)
            if start_time is None:
                return f"Error: Invalid time period '{time_period}'. Supported values: 5m, 1h, today, yesterday, 7d, etc."

        # Prepare request payload
        payload = {
            "query": query,
            "match_threshold": match_threshold,
            "match_count": match_count,
        }

        # Add time filters if provided
        if start_time:
            payload["start_time"] = start_time.isoformat()
        if end_time:
            payload["end_time"] = end_time.isoformat()

        # Make API request
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{STRAYL_API_URL}/search-logs",
                json=payload,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
            )

            if response.status_code != 200:
                error_data = response.json() if response.headers.get("content-type") == "application/json" else {}
                return f"Error: API returned status {response.status_code}: {error_data.get('error', response.text)}"

            data = response.json()

            if not data.get("success"):
                return f"Error: {data.get('error', 'Unknown error')}"

            results = data.get("results", [])
            total = data.get("total_results", 0)
            metadata = data.get("search_metadata", {})

            if not results:
                time_info = f" in period '{time_period}'" if time_period else ""
                return f"No logs found for query '{query}'{time_info}"

            # Format results
            output = [
                f"Semantic Search Results for: '{query}'",
                f"Total results: {total}",
            ]

            if time_period:
                output.append(f"Time period: {time_period}")

            output.append(f"Similarity threshold: {match_threshold}")
            output.append(f"Logs with embeddings: {metadata.get('logs_with_embeddings', 0)}")
            output.append("\n" + "=" * 80 + "\n")

            for i, log in enumerate(results[:10], 1):
                output.append(f"{i}. {format_log_result(log)}")
                output.append("-" * 80)

            if total > 10:
                output.append(f"\n... and {total - 10} more results")

            return "\n".join(output)

    except ValueError as e:
        return f"Configuration error: {str(e)}"
    except httpx.TimeoutException:
        return "Error: Request timed out. Please try again."
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def search_logs_exact(
    query: Annotated[str, "Exact text to search for. Use '*' or empty string to see all logs"],
    time_period: Annotated[Optional[str], "Time filter: 5m, 1h, today, yesterday, 7d, 30d, etc."] = None,
    level: Annotated[Optional[str], "Log level filter: info, warn, error, debug"] = None,
    case_sensitive: Annotated[bool, "Whether to perform case-sensitive search"] = False,
    limit: Annotated[int, "Maximum number of results to return"] = 50,
) -> str:
    """Search logs using exact text matching with optional time and level filtering.

    This tool performs exact text search across your logs. Use '*' as query to view all logs
    with optional filters by time period and log level."""
    try:
        api_key = get_api_key()

        # Parse time period if provided
        start_time = None
        end_time = None
        if time_period:
            start_time, end_time = parse_time_period(time_period)
            if start_time is None:
                return f"Error: Invalid time period '{time_period}'"

        # Prepare request payload
        payload = {
            "query": query,
            "case_sensitive": case_sensitive,
            "limit": limit,
        }

        if level:
            if level.lower() not in ["info", "warn", "error", "debug"]:
                return f"Error: Invalid log level '{level}'. Must be one of: info, warn, error, debug"
            payload["level"] = level.lower()

        if start_time:
            payload["start_time"] = start_time.isoformat()
        if end_time:
            payload["end_time"] = end_time.isoformat()

        # Make API request to exact search endpoint
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{STRAYL_API_URL}/exact-search-logs",
                json=payload,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
            )

            if response.status_code != 200:
                error_data = response.json() if response.headers.get("content-type") == "application/json" else {}
                return f"Error: API returned status {response.status_code}: {error_data.get('error', response.text)}"

            data = response.json()

            if not data.get("success"):
                return f"Error: {data.get('error', 'Unknown error')}"

            results = data.get("results", [])
            total = data.get("total_results", 0)

            if not results:
                filters = []
                if time_period:
                    filters.append(f"period '{time_period}'")
                if level:
                    filters.append(f"level '{level}'")
                filter_str = f" with filters: {', '.join(filters)}" if filters else ""
                return f"No logs found for exact text '{query}'{filter_str}"

            # Format results
            output = [
                f"Exact Search Results for: '{query}'",
                f"Total results: {total}",
            ]

            if time_period:
                output.append(f"Time period: {time_period}")
            if level:
                output.append(f"Log level: {level}")

            output.append(f"Case sensitive: {case_sensitive}")
            output.append("\n" + "=" * 80 + "\n")

            for i, log in enumerate(results[:10], 1):
                output.append(f"{i}. {format_log_result(log)}")
                output.append("-" * 80)

            if total > 10:
                output.append(f"\n... and {total - 10} more results")

            return "\n".join(output)

    except ValueError as e:
        return f"Configuration error: {str(e)}"
    except httpx.TimeoutException:
        return "Error: Request timed out. Please try again."
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
def list_time_periods() -> str:
    """
    List all supported time period formats for log search.

    Returns:
        A formatted list of all supported time period values
    """
    return """Supported time periods for log search:

Minutes:
  - 5m, 5_minutes, 5_mins - Last 5 minutes
  - 10m, 10_minutes - Last 10 minutes
  - 15m, 15_minutes - Last 15 minutes
  - 30m, 30_minutes - Last 30 minutes

Hours:
  - 1h, 1_hour - Last 1 hour
  - 2h, 2_hours - Last 2 hours
  - 6h, 6_hours - Last 6 hours
  - 12h, 12_hours - Last 12 hours
  - 24h, last_24_hours - Last 24 hours

Days:
  - today - Today from 00:00 UTC
  - yesterday - Full yesterday (00:00 to 23:59)
  - 7d, last_7_days - Last 7 days
  - 30d, last_30_days - Last 30 days

Examples:
  - search_logs_semantic("error connecting to database", "1h")
  - search_logs_exact("timeout", "today", level="error")
"""
