"""Email generation module."""
from datetime import datetime, timedelta, timezone
from typing import List, Dict


def generate_plain_text(feed_results: List[Dict]) -> str:
    """
    Generate plain text email body from feed results.

    Args:
        feed_results: List of feed result dicts

    Returns:
        Plain text email body
    """
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    date_str = yesterday.strftime("%B %d, %Y")

    lines = [
        f"RSS Digest for {date_str}",
        "",
    ]

    # Sort feeds alphabetically
    sorted_feeds = sorted(feed_results, key=lambda f: f["name"])

    # Separate feeds with updates from others
    feeds_with_posts = [f for f in sorted_feeds if f["posts"]]
    feeds_failed = [f for f in sorted_feeds if f["status"] == "error"]

    if feeds_with_posts:
        lines.append("--- Feeds with Updates ---")
        lines.append("")

        for feed in feeds_with_posts:
            lines.append(feed["name"])
            for post in feed["posts"]:
                lines.append(f"• {post['title']}")
                lines.append(f"  {post['link']}")
                if post["excerpt"]:
                    lines.append(f"  {post['excerpt']}")
                lines.append("")
            lines.append("")
    else:
        lines.append("No updates yesterday")
        lines.append("")

    # Summary section
    lines.append("--- Summary ---")
    total_feeds = len(feed_results)
    updated_count = len(feeds_with_posts)
    lines.append(f"{updated_count} of {total_feeds} feeds updated")

    if feeds_failed:
        plural = "feed" if len(feeds_failed) == 1 else "feeds"
        lines.append(f"{len(feeds_failed)} {plural} failed to load:")
        for feed in feeds_failed:
            error_msg = feed.get("error_message", "Unknown error")
            lines.append(f"• {feed['name']} ({error_msg})")

    return "\n".join(lines)
