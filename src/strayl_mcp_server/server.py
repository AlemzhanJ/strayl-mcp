"""Strayl MCP Server - Log search tools."""

import os
from typing import Annotated, Optional
import httpx
from mcp.server.fastmcp import FastMCP

from .utils import parse_time_period, format_log_result, format_documentation_result

# Initialize FastMCP server
mcp = FastMCP(
    "Strayl Search",
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
    match_threshold: Annotated[float, "Minimum similarity score (0.0 to 1.0)"] = 0.2,
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
async def search_documentation(
    query: Annotated[str, "Search query in natural language to find relevant documentation"],
    chat_id: Annotated[Optional[str], "Optional chat ID to save conversation history"] = None,
    source_id: Annotated[Optional[str], "Optional source ID to search within specific documentation source"] = None,
    use_ai: Annotated[bool, "Use AI (Gemini) to structure the answer"] = True,
) -> str:
    """Search documentation using semantic (vector) search with AI-powered answer structuring.
    
    If chat_id is provided, the query and response will be saved to the chat history.
    Use manage_documentation_chats to create and manage chat sessions."""
    try:
        api_key = get_api_key()

        payload = {
            "query": query,
            "limit": 15,  # Фиксированный лимит (не передается пользователем)
            "similarity_threshold": 0.22,
            "use_ai": use_ai,
        }

        if chat_id:
            payload["chat_id"] = chat_id
            
        if source_id:
            payload["source_id"] = source_id

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{STRAYL_API_URL}/search-documentation",
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

            if "error" in data:
                return f"Error: {data.get('error', 'Unknown error')}"

            results = data.get("results", [])
            structured_answer = data.get("structured_answer")
            metadata = data.get("metadata", {})

            if not results and not structured_answer:
                source_info = f" in source '{source_id}'" if source_id else ""
                return f"No documentation found for query '{query}'{source_info}"

            # Минималистичный вывод - только AI ответ или краткие результаты
            if structured_answer and str(structured_answer).strip():
                # Просто AI ответ, без заголовков и метаданных
                return str(structured_answer).strip()
            
            # Fallback: краткие результаты если нет AI ответа
            output = []
            output.append(f"📚 {len(results)} результат(ов) по запросу: {query}\n")
            
            for i, result in enumerate(results, 1):
                source = result.get("source", {})
                content = result.get("content", "")[:300]  # Первые 300 символов
                source_name = source.get("name", "Unknown")
                
                output.append(f"{i}. **{source_name}**")
                output.append(f"   {content}...\n")

            return "\n".join(output)

    except ValueError as e:
        return f"Configuration error: {str(e)}"
    except httpx.TimeoutException:
        return "Error: Request timed out (Gemini processing can take up to 60s). Please try again."
    except Exception as e:
        import traceback
        return f"Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"


@mcp.tool()
async def list_documentation_sources(
    include_public: Annotated[bool, "Include public sources accessible to all users"] = True,
    include_private: Annotated[bool, "Include your private sources"] = True,
) -> str:
    """List documentation sources available to you.
    
    Returns a formatted list of documentation sources with their IDs, names, URLs, 
    and status. Shows only sources you have access to:
    - Your private sources (if include_private=True)
    - Public sources (if include_public=True)
    
    Use source_id to search within a specific documentation source."""
    try:
        api_key = get_api_key()
        
        payload = {
            "include_public": include_public,
            "include_private": include_private,
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{STRAYL_API_URL}/list-documentation-sources",
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
            
            if "error" in data:
                return f"Error: {data.get('error', 'Unknown error')}"
            
            sources = data.get("sources", [])
            count = data.get("count", 0)
            
            if not sources:
                filter_info = []
                if not include_public:
                    filter_info.append("excluding public")
                if not include_private:
                    filter_info.append("excluding private")
                filter_str = f" ({', '.join(filter_info)})" if filter_info else ""
                return f"No documentation sources found{filter_str}."
            
            output = [
                "=" * 80,
                "AVAILABLE DOCUMENTATION SOURCES",
                "=" * 80,
                f"Total sources: {count}",
                f"Filters: Public={'Yes' if include_public else 'No'}, Private={'Yes' if include_private else 'No'}",
                "",
            ]
            
            for i, source in enumerate(sources, 1):
                source_id = source.get("id", "Unknown")
                name = source.get("name", "Unnamed")
                url = source.get("url", "N/A")
                status = source.get("status", "unknown")
                chunks_count = source.get("chunks_count", 0)
                indexed_at = source.get("indexed_at", "")
                is_public = source.get("is_public", False)
                
                date_str = ""
                if indexed_at:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(indexed_at.replace('Z', '+00:00'))
                        date_str = dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        date_str = indexed_at[:10]
                
                output.append(f"{i}. {name}")
                output.append(f"   ID: {source_id}")
                output.append(f"   URL: {url}")
                output.append(f"   Status: {status.upper()}")
                output.append(f"   Public: {'Yes' if is_public else 'No (Your private source)'}")
                if chunks_count:
                    output.append(f"   Chunks: {chunks_count}")
                if date_str:
                    output.append(f"   Indexed: {date_str}")
                output.append("")
            
            output.append("=" * 80)
            output.append("\nTip: Use source_id to search within a specific documentation source")
            output.append("   Example: search_documentation('query', source_id='uuid-here')")
            
            return "\n".join(output)
            
    except ValueError as e:
        return f"Configuration error: {str(e)}"
    except httpx.TimeoutException:
        return "Error: Request timed out. Please try again."
    except Exception as e:
        import traceback
        return f"Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"


@mcp.tool()
async def index_documentation(
    url: Annotated[str, "URL of the documentation to index (e.g., https://docs.example.com)"],
    is_public: Annotated[bool, "Whether this documentation should be public (visible to all users who add it)"] = True,
    force: Annotated[bool, "Force re-indexing even if already indexed"] = False,
) -> str:
    """Add and index documentation from a URL.
    
    This tool will:
    1. Check if the documentation already exists (for public docs)
    2. Add it to your documentation list
    3. Crawl the website and extract content
    4. Generate embeddings for semantic search
    5. Make it searchable via search_documentation
    
    If the documentation is public and already indexed by another user, it will be added
    to your list without re-indexing (unless you use force=True).
    
    Note: Indexing can take several minutes depending on the size of the documentation.
    Backend will use default values: max_pages=50000, max_depth=10."""
    try:
        api_key = get_api_key()
        
        payload = {
            "url": url,
            "is_public": is_public,
            "force": force,
        }
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{STRAYL_API_URL}/index-documentation",
                json=payload,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
            )
            
            if response.status_code != 200:
                error_data = response.json() if response.headers.get("content-type") == "application/json" else {}
                error_msg = error_data.get('error', response.text)
                return f"Error: API returned status {response.status_code}: {error_msg}"
            
            data = response.json()
            
            if "error" in data:
                return f"Error: {data.get('error', 'Unknown error')}"
            
            if data.get("success"):
                source_id_returned = data.get("source_id", "")
                pages_crawled = data.get("pages_crawled", 0)
                chunks_indexed = data.get("chunks_indexed", 0)
                total_tokens = data.get("total_tokens", 0)
                performance = data.get("performance", {})
                
                output = [
                    "=" * 80,
                    "DOCUMENTATION ADDED & INDEXED",
                    "=" * 80,
                    f"URL: {url}",
                    f"Source ID: {source_id_returned}",
                    f"Public: {'Yes' if is_public else 'No (Private)'}",
                    f"Pages crawled: {pages_crawled}",
                    f"Chunks indexed: {chunks_indexed}",
                    f"Total tokens: {total_tokens:,}",
                ]
                
                if performance:
                    total_duration = performance.get("total_duration_ms", 0)
                    stages = performance.get("stages", {})
                    
                    output.append(f"\nTotal duration: {total_duration / 1000:.2f}s")
                    
                    if stages:
                        output.append("\nStage timings:")
                        for stage, duration in stages.items():
                            output.append(f"  - {stage}: {duration / 1000:.2f}s")
                
                output.append("\n" + "=" * 80)
                output.append("The documentation is now searchable!")
                output.append(f"   Use: search_documentation('your query here')")
                output.append(f"   Or: search_documentation('your query', source_id='{source_id_returned}')")
                
                return "\n".join(output)
            else:
                return f"Error: Indexing failed. {data.get('error', 'Unknown error')}"
            
    except ValueError as e:
        return f"Configuration error: {str(e)}"
    except httpx.TimeoutException:
        return "Error: Request timed out. Indexing can take several minutes. Please check the status later."
    except Exception as e:
        import traceback
        return f"Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"


@mcp.tool()
async def manage_documentation_chats(
    action: Annotated[str, "Action to perform: 'list', 'create', 'get', or 'delete'"],
    title: Annotated[Optional[str], "Chat title (required for 'create')"] = None,
    chat_id: Annotated[Optional[str], "Chat ID (required for 'get' and 'delete')"] = None,
    source_id: Annotated[Optional[str], "Optional source ID to associate with chat (for 'create')"] = None,
) -> str:
    """Manage documentation chat sessions.
    
    Actions:
    - 'list': Get all your chats
    - 'create': Create a new chat session (requires title)
    - 'get': Get chat history (requires chat_id)
    - 'delete': Delete a chat (requires chat_id)
    
    Use chat_id with search_documentation to save conversation history."""
    try:
        api_key = get_api_key()
        
        # Валидация параметров
        if action == 'create' and not title:
            return "Error: 'title' is required for creating a chat"
        
        if action in ['get', 'delete'] and not chat_id:
            return f"Error: 'chat_id' is required for action '{action}'"
        
        # Формируем URL с параметрами
        url = f"{STRAYL_API_URL}/manage-documentation-chats?action={action}"
        
        if action == 'get' or action == 'delete':
            url += f"&chat_id={chat_id}"
        
        # Подготавливаем body для POST запроса (для create)
        body = None
        if action == 'create':
            body = {"title": title}
            if source_id:
                body["source_id"] = source_id
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            if body:
                response = await client.post(
                    url,
                    json=body,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                )
            else:
                # Для list, get, delete используем GET (можно POST с пустым body)
                response = await client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                )
            
            if response.status_code != 200:
                error_data = response.json() if response.headers.get("content-type") == "application/json" else {}
                return f"Error: API returned status {response.status_code}: {error_data.get('error', response.text)}"
            
            data = response.json()
            
            if "error" in data:
                return f"Error: {data.get('error', 'Unknown error')}"
            
            # Форматируем ответ в зависимости от действия
            if action == 'list':
                chats = data.get("chats", [])
                count = data.get("count", 0)
                
                if not chats:
                    return "No chats found. Create a new chat with action='create'."
                
                output = [
                    "=" * 80,
                    "YOUR DOCUMENTATION CHATS",
                    "=" * 80,
                    f"Total chats: {count}",
                    "",
                ]
                
                for i, chat in enumerate(chats, 1):
                    chat_id_val = chat.get("id", "Unknown")
                    title_val = chat.get("title", "Untitled")
                    updated = chat.get("updated_at", "")
                    source = chat.get("documentation_sources")
                    
                    date_str = ""
                    if updated:
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                            date_str = dt.strftime("%Y-%m-%d %H:%M")
                        except:
                            date_str = updated[:16]
                    
                    output.append(f"{i}. {title_val}")
                    output.append(f"   ID: {chat_id_val}")
                    if source:
                        output.append(f"   Source: {source.get('name', 'N/A')}")
                    if date_str:
                        output.append(f"   Updated: {date_str}")
                    output.append("")
                
                output.append("=" * 80)
                output.append("\nTip: Use chat_id with search_documentation to continue conversation")
                output.append("   Example: search_documentation('query', chat_id='uuid-here')")
                
                return "\n".join(output)
            
            elif action == 'create':
                chat = data.get("chat", {})
                chat_id_val = chat.get("id", "Unknown")
                title_val = chat.get("title", "Untitled")
                
                return f"""✅ Chat created successfully!

Title: {title_val}
Chat ID: {chat_id_val}

Use this chat_id with search_documentation to save conversation history:
  search_documentation('your query', chat_id='{chat_id_val}')
"""
            
            elif action == 'get':
                chat = data.get("chat", {})
                messages = data.get("messages", [])
                count = data.get("count", 0)
                
                title_val = chat.get("title", "Untitled")
                
                output = [
                    "=" * 80,
                    f"CHAT: {title_val}",
                    "=" * 80,
                    f"Messages: {count}",
                    "",
                ]
                
                if not messages:
                    output.append("No messages in this chat yet.")
                else:
                    for i, msg in enumerate(messages, 1):
                        role = msg.get("role", "unknown")
                        content = msg.get("content", "")
                        created = msg.get("created_at", "")
                        
                        date_str = ""
                        if created:
                            try:
                                from datetime import datetime
                                dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                                date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                            except:
                                date_str = created[:19]
                        
                        role_emoji = "👤" if role == "user" else "🤖"
                        output.append(f"{role_emoji} {role.upper()} [{date_str}]")
                        output.append(f"{content}")
                        output.append("-" * 80)
                
                return "\n".join(output)
            
            elif action == 'delete':
                return f"✅ Chat deleted successfully (ID: {chat_id})"
            
            else:
                return f"Unknown action: {action}"
                
    except ValueError as e:
        return f"Configuration error: {str(e)}"
    except httpx.TimeoutException:
        return "Error: Request timed out. Please try again."
    except Exception as e:
        import traceback
        return f"Error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"


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