"""Email generation module."""
from datetime import datetime, timedelta, timezone
from typing import List, Dict
import html


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


def generate_html(feed_results: List[Dict]) -> str:
    """
    Generate HTML email body from feed results.

    Args:
        feed_results: List of feed result dicts

    Returns:
        HTML email body
    """
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    date_str = yesterday.strftime("%B %d, %Y")

    # Sort feeds alphabetically
    sorted_feeds = sorted(feed_results, key=lambda f: f["name"])

    # Separate feeds with updates from others
    feeds_with_posts = [f for f in sorted_feeds if f["posts"]]
    feeds_failed = [f for f in sorted_feeds if f["status"] == "error"]

    # Build HTML
    parts = [
        "<html>",
        "<head>",
        "<style>",
        "body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }",
        "h1 { color: #2c3e50; }",
        "h2 { color: #34495e; margin-top: 20px; }",
        "a { color: #3498db; text-decoration: none; }",
        "a:hover { text-decoration: underline; }",
        ".post { margin-bottom: 15px; }",
        ".excerpt { color: #7f8c8d; margin-left: 20px; }",
        ".summary { margin-top: 30px; padding-top: 20px; border-top: 2px solid #ecf0f1; }",
        "</style>",
        "</head>",
        "<body>",
        f"<h1>RSS Digest for {html.escape(date_str)}</h1>",
    ]

    if feeds_with_posts:
        parts.append("<h2>Feeds with Updates</h2>")

        for feed in feeds_with_posts:
            parts.append(f"<h2>{html.escape(feed['name'])}</h2>")
            for post in feed["posts"]:
                parts.append('<div class="post">')
                parts.append(f'<a href="{html.escape(post["link"])}">{html.escape(post["title"])}</a>')
                if post["excerpt"]:
                    parts.append(f'<div class="excerpt">{html.escape(post["excerpt"])}</div>')
                parts.append("</div>")
    else:
        parts.append("<p>No updates yesterday</p>")

    # Summary section
    parts.append('<div class="summary">')
    parts.append("<h2>Summary</h2>")
    total_feeds = len(feed_results)
    updated_count = len(feeds_with_posts)
    parts.append(f"<p>{updated_count} of {total_feeds} feeds updated</p>")

    if feeds_failed:
        plural = "feed" if len(feeds_failed) == 1 else "feeds"
        parts.append(f"<p>{len(feeds_failed)} {plural} failed to load:</p>")
        parts.append("<ul>")
        for feed in feeds_failed:
            error_msg = feed.get("error_message", "Unknown error")
            parts.append(f"<li>{html.escape(feed['name'])} ({html.escape(error_msg)})</li>")
        parts.append("</ul>")

    parts.append("</div>")
    parts.append("</body>")
    parts.append("</html>")

    return "\n".join(parts)
