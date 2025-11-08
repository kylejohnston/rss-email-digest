"""RSS feed parser module."""
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Union
from datetime import datetime, timedelta, timezone
import time


def parse_opml(opml_path: Path) -> List[Dict[str, str]]:
    """
    Parse OPML file and extract RSS feed URLs and titles.

    Args:
        opml_path: Path to OPML file

    Returns:
        List of dicts with 'title' and 'url' keys

    Raises:
        FileNotFoundError: If OPML file doesn't exist
    """
    if not opml_path.exists():
        raise FileNotFoundError(f"OPML file not found: {opml_path}")

    tree = ET.parse(opml_path)
    root = tree.getroot()

    feeds = []
    # Find all outline elements with xmlUrl attribute (RSS feeds)
    for outline in root.findall(".//outline[@xmlUrl]"):
        feeds.append({
            "title": outline.get("text") or outline.get("title"),
            "url": outline.get("xmlUrl")
        })

    return feeds


def is_from_yesterday(date_value: Union[datetime, time.struct_time, None]) -> bool:
    """
    Check if a date is from yesterday (UTC calendar date).

    Args:
        date_value: datetime object, struct_time, or None

    Returns:
        True if date is from yesterday's calendar date, False otherwise
    """
    if date_value is None:
        return False

    # Convert struct_time to datetime if needed
    if isinstance(date_value, time.struct_time):
        date_value = datetime(*date_value[:6], tzinfo=timezone.utc)

    # Ensure datetime has timezone info
    if date_value.tzinfo is None:
        date_value = date_value.replace(tzinfo=timezone.utc)

    # Get yesterday's date (calendar date only, ignore time)
    now = datetime.now(timezone.utc)
    yesterday = (now - timedelta(days=1)).date()

    # Compare calendar dates only
    return date_value.date() == yesterday
