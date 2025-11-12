# Strayl MCP Server

MCP server for semantic and exact log search powered by Strayl.

## Features

- **Semantic Search**: AI-powered search across your logs using vector embeddings
- **Exact Text Search**: Traditional text matching with case-sensitive options
- **Time Filtering**: Search logs by time periods (5m, 1h, today, yesterday, 7d, etc.)
- **Log Level Filtering**: Filter by log levels (info, warn, error, debug)
- **Easy Integration**: Works with Claude Desktop, Cline, and other MCP clients

## Installation

Install via pipx (recommended):

```bash
pipx install strayl-mcp-server
```

Or via pip:

```bash
pip install strayl-mcp-server
```

## Configuration

### Get Your API Key

1. Visit [https://strayl.dev](https://strayl.dev)
2. Generate an API key
3. Copy your API key (starts with `st_`)

### Claude Desktop Configuration

Add to your Claude Desktop config file:

**MacOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "strayl": {
      "command": "pipx",
      "args": ["run", "--no-cache", "strayl-mcp-server"],
      "env": {
        "STRAYL_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### Cline/Other MCP Clients

Add to your MCP settings file:

```json
{
  "mcpServers": {
    "strayl": {
      "command": "pipx",
      "args": ["run", "--no-cache", "strayl-mcp-server"],
      "env": {
        "STRAYL_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

## Available Tools

### 1. search_logs_semantic

Semantic (AI-powered) search across your logs.

**Parameters:**
- `query` (required): Search query in natural language
- `time_period` (optional): Time filter (e.g., "5m", "1h", "today", "7d")
- `match_threshold` (optional): Similarity threshold (0.0-1.0, default 0.5)
- `match_count` (optional): Max results (default 50)

**Example:**
```
Search for database connection errors in the last hour
```

### 2. search_logs_exact

Exact text matching search across your logs.

**Parameters:**
- `query` (required): Exact text to search for
- `time_period` (optional): Time filter
- `level` (optional): Log level filter ("info", "warn", "error", "debug")
- `case_sensitive` (optional): Case-sensitive search (default false)
- `limit` (optional): Max results (default 50)

**Example:**
```
Search for exact text "timeout" in error logs from today
```

### 3. list_time_periods

List all supported time period formats.

## Time Period Formats

### Minutes
- `5m`, `5_minutes`, `5_mins` - Last 5 minutes
- `10m`, `15m`, `30m` - Last 10, 15, 30 minutes

### Hours
- `1h`, `2h`, `6h`, `12h` - Last 1, 2, 6, 12 hours
- `24h`, `last_24_hours` - Last 24 hours

### Days
- `today` - Today from 00:00 UTC
- `yesterday` - Full yesterday
- `7d`, `last_7_days` - Last 7 days
- `30d`, `last_30_days` - Last 30 days

## Usage Examples

### With Claude Desktop

Simply ask Claude:

> "Search my logs for authentication errors in the last hour"

> "Find all database connection issues from today"

> "Show me exact text 'null pointer' in error logs"

### Development/Testing

Run the server directly:

```bash
export STRAYL_API_KEY="your_api_key_here"
strayl-mcp-server
```

## Logging Your Application

To send logs to Strayl, use the Strayl Log API:

```python
import httpx

api_key = "st_your_api_key"
api_url = "https://ougtygyvcgdnytkswier.supabase.co/functions/v1"

async def log_message(message: str, level: str = "info", context: dict = None):
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{api_url}/log",
            json={
                "message": message,
                "level": level,
                "context": context or {}
            },
            headers={"Authorization": f"Bearer {api_key}"}
        )

# Usage
await log_message("User logged in", "info", {"user_id": "123"})
await log_message("Database connection failed", "error", {"db": "postgres"})
```

## Troubleshooting

### API Key Issues

If you get authentication errors:
1. Verify your API key starts with `st_`
2. Check the API key is correctly set in your MCP config
3. Ensure there are no extra spaces or quotes around the key

### Connection Issues

If the server fails to connect:
1. Check your internet connection
2. Verify the Strayl API is accessible
3. Check for any firewall or proxy issues

### No Results

If searches return no results:
1. Verify you've sent logs to Strayl
2. Check the time period filter isn't too restrictive
3. For semantic search, wait a few seconds for embeddings to generate

## Support

- Documentation: [https://docs.strayl.dev](https://docs.strayl.dev)
- Issues: [https://github.com/strayl/strayl-mcp-server/issues](https://github.com/strayl/strayl-mcp-server/issues)
- Website: [https://strayl.dev](https://strayl.dev)

## License

MIT License
