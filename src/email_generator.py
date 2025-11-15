"""Email generation module."""
from datetime import datetime, timedelta, timezone
from typing import List, Dict
import html
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import logging


logger = logging.getLogger(__name__)


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
        for feed in feeds_with_posts:
            lines.append(feed["name"])
            # Add site URL if available
            if feed.get("site_url"):
                lines.append(f"Visit: {feed['site_url']}")
            for post in feed["posts"]:
                # Decode HTML entities in plain text
                title = html.unescape(post['title'])
                lines.append(f"• {title}")
                lines.append(f"  {post['link']}")
                if post["excerpt"]:
                    excerpt = html.unescape(post['excerpt'])
                    lines.append(f"  {excerpt}")
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
        "body { font-family: Helvetica, Arial, sans-serif; font-size: 18px; line-height: 1.4; color: #121212; }",
        "h1 { font-size: 24px; }",
        "h2 { margin-top: 20px; font-size: 22px; }",
        "a { font-size: 18px; color: #0099CC; text-decoration: none; }",
        "a:hover { text-decoration: underline; }",
        ".post { margin-bottom: 15px; }",
        ".excerpt { font-size: 18px; }",
        ".summary { margin-top: 30px; padding-top: 18px; border-top: 2px solid #ABABAB; }",
        "</style>",
        "</head>",
        "<body>",
    ]

    if feeds_with_posts:
        for feed in feeds_with_posts:
            # Make feed title clickable if site URL is available
            if feed.get("site_url"):
                parts.append(f'<h2><a href="{html.escape(feed["site_url"])}">{html.escape(feed["name"])}</a></h2>')
            else:
                parts.append(f"<h2>{html.escape(feed['name'])}</h2>")
            for post in feed["posts"]:
                parts.append('<div class="post">')
                # Unescape HTML entities in content while keeping XSS protection
                title = html.unescape(post["title"])
                parts.append(f'<a href="{html.escape(post["link"])}">{html.escape(title)}</a>')
                if post["excerpt"]:
                    excerpt = html.unescape(post["excerpt"])
                    parts.append(f'<div class="excerpt">{html.escape(excerpt)}</div>')
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


def create_email_message(feed_results: List[Dict], from_email: str, to_email: str) -> MIMEMultipart:
    """
    Create multipart email message with plain text and HTML.

    Args:
        feed_results: List of feed result dicts
        from_email: Sender email address
        to_email: Recipient email address

    Returns:
        MIMEMultipart email message
    """
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    date_str = yesterday.strftime("%B %d, %Y")

    # Create message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"RSS Digest - {date_str}"
    msg["From"] = from_email
    msg["To"] = to_email

    # Generate both versions
    plain_text = generate_plain_text(feed_results)
    html_text = generate_html(feed_results)

    # Attach parts (plain text first, HTML second per RFC 2046)
    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html_text, "html"))

    return msg


def send_email(
    msg: MIMEMultipart,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str
) -> None:
    """
    Send email via SMTP.

    Args:
        msg: Email message to send
        smtp_host: SMTP server hostname
        smtp_port: SMTP server port
        smtp_user: SMTP username
        smtp_password: SMTP password

    Raises:
        smtplib.SMTPException: If SMTP authentication or sending fails
        OSError: If network connection to SMTP server fails
    """
    logger.info(f"Connecting to SMTP server {smtp_host}:{smtp_port}...")

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        logger.info(f"Email sent successfully to {msg['To']}")

    except (smtplib.SMTPException, OSError) as e:
        logger.error(f"Failed to send email: {str(e)}")
        raise
