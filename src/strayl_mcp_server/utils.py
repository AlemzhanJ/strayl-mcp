"""Utility functions for the Strayl MCP server."""

from datetime import datetime, timedelta
from typing import Optional, Tuple


def parse_time_period(period: str) -> Tuple[Optional[datetime], Optional[datetime]]:
    """
    Parse time period strings and return start/end datetime.

    Supported periods:
    - "5_minutes", "5_mins", "5m" - last 5 minutes
    - "1_hour", "1h" - last 1 hour
    - "today" - today from 00:00
    - "yesterday" - yesterday's full day
    - "last_24_hours", "24h" - last 24 hours
    - "last_7_days", "7d" - last 7 days
    - "last_30_days", "30d" - last 30 days

    Returns:
        Tuple of (start_time, end_time) as datetime objects, or (None, None) if invalid
    """
    now = datetime.utcnow()
    period = period.lower().strip()

    # Minutes
    if period in ["5_minutes", "5_mins", "5m"]:
        return now - timedelta(minutes=5), now
    elif period in ["10_minutes", "10_mins", "10m"]:
        return now - timedelta(minutes=10), now
    elif period in ["15_minutes", "15_mins", "15m"]:
        return now - timedelta(minutes=15), now
    elif period in ["30_minutes", "30_mins", "30m"]:
        return now - timedelta(minutes=30), now

    # Hours
    elif period in ["1_hour", "1h"]:
        return now - timedelta(hours=1), now
    elif period in ["2_hours", "2h"]:
        return now - timedelta(hours=2), now
    elif period in ["6_hours", "6h"]:
        return now - timedelta(hours=6), now
    elif period in ["12_hours", "12h"]:
        return now - timedelta(hours=12), now
    elif period in ["last_24_hours", "24h"]:
        return now - timedelta(hours=24), now

    # Days
    elif period == "today":
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return start_of_day, now
    elif period == "yesterday":
        yesterday = now - timedelta(days=1)
        start_of_yesterday = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_yesterday = start_of_yesterday + timedelta(days=1) - timedelta(microseconds=1)
        return start_of_yesterday, end_of_yesterday
    elif period in ["last_7_days", "7d"]:
        return now - timedelta(days=7), now
    elif period in ["last_30_days", "30d"]:
        return now - timedelta(days=30), now

    # Invalid period
    return None, None


def format_log_result(log: dict) -> str:
    """Format a log entry for display."""
    timestamp = log.get("created_at", "Unknown time")
    level = log.get("level", "info").upper()
    message = log.get("message", "")
    context = log.get("context", {})

    result = f"[{timestamp}] [{level}] {message}"

    if context:
        result += f"\nContext: {context}"

    if "similarity" in log:
        result += f"\nSimilarity: {log['similarity']:.4f}"

    return result
