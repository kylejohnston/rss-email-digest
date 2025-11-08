"""RSS feed parser module."""
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Union
from datetime import datetime, timedelta, timezone
import time
import aiohttp
import feedparser
import asyncio
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


async def fetch_feed(feed_name: str, feed_url: str, timeout: int = 15) -> Dict:
    """
    Fetch RSS feed and extract yesterday's posts.

    Args:
        feed_name: Display name for the feed
        feed_url: RSS feed URL
        timeout: Request timeout in seconds

    Returns:
        Dict with keys: name, status, posts, error_message (if error)
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(feed_url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                content = await response.text()

        # Parse feed content
        feed = feedparser.parse(content)

        if feed.bozo:  # feedparser sets bozo=1 for malformed feeds
            return {
                "name": feed_name,
                "status": "error",
                "posts": [],
                "error_message": f"Invalid feed format: {feed.bozo_exception}"
            }

        # Filter for yesterday's posts
        yesterday_posts = []
        for entry in feed.entries:
            # Try published date first, fall back to updated
            pub_date = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)

            if pub_date and is_from_yesterday(pub_date):
                # Extract excerpt from summary or content
                excerpt = ""
                if hasattr(entry, "summary"):
                    excerpt = entry.summary
                elif hasattr(entry, "content"):
                    excerpt = entry.content[0].value

                # Strip HTML tags and truncate
                excerpt = re.sub(r'<[^>]+>', '', excerpt)
                excerpt = excerpt.strip()
                if len(excerpt) > 300:
                    excerpt = excerpt[:300] + "..."

                yesterday_posts.append({
                    "title": entry.title,
                    "link": entry.link,
                    "excerpt": excerpt
                })

        status = "success" if yesterday_posts else "no_updates"
        logger.info(f"{feed_name}: {len(yesterday_posts)} posts from yesterday")

        return {
            "name": feed_name,
            "status": status,
            "posts": yesterday_posts
        }

    except asyncio.TimeoutError:
        logger.warning(f"{feed_name}: Timeout after {timeout}s")
        return {
            "name": feed_name,
            "status": "error",
            "posts": [],
            "error_message": f"Timeout after {timeout}s"
        }
    except Exception as e:
        logger.error(f"{feed_name}: Error - {str(e)}")
        return {
            "name": feed_name,
            "status": "error",
            "posts": [],
            "error_message": str(e)
        }


async def fetch_all_feeds(feeds: List[Dict[str, str]], batch_size: int = 10, timeout: int = 15) -> List[Dict]:
    """
    Fetch multiple RSS feeds in parallel batches.

    Args:
        feeds: List of feed dicts with 'title' and 'url' keys
        batch_size: Number of feeds to fetch concurrently
        timeout: Timeout per feed in seconds

    Returns:
        List of feed result dicts. Length matches input feeds list,
        with error results for feeds that fail.
    """
    results = []

    logger.info(f"Fetching {len(feeds)} feeds in batches of {batch_size}...")

    # Process feeds in batches to avoid overwhelming the system
    for i in range(0, len(feeds), batch_size):
        batch = feeds[i:i + batch_size]
        tasks = [fetch_feed(feed["title"], feed["url"], timeout) for feed in batch]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and add to results
        for i, result in enumerate(batch_results):
            if isinstance(result, Exception):
                feed = batch[i]
                logger.error(f"{feed['title']}: Unexpected error - {result}")
                results.append({
                    "name": feed["title"],
                    "status": "error",
                    "posts": [],
                    "error_message": f"Unexpected error: {str(result)}"
                })
            else:
                results.append(result)

    logger.info(f"Completed fetching {len(results)} feeds")
    return results
