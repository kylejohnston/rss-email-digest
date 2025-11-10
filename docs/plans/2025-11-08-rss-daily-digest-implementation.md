# RSS Daily Digest Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python-based RSS feed aggregator that runs on GitHub Actions, fetches feeds daily, and emails a digest of yesterday's posts.

**Architecture:** Three-component system: (1) Feed Parser reads OPML and fetches RSS feeds in parallel using aiohttp/asyncio, filtering for yesterday's posts, (2) Email Generator creates multipart HTML/text emails grouped by feed, (3) GitHub Actions workflow runs daily at 2pm UTC with SMTP credentials from secrets.

**Tech Stack:** Python 3.11, feedparser, aiohttp, asyncio, smtplib, GitHub Actions

---

## Task 1: Project Structure & Dependencies

**Files:**
- Create: `src/requirements.txt`
- Create: `.gitignore`
- Create: `README.md`

**Step 1: Write .gitignore file**

Create `.gitignore` to exclude Python artifacts and local environment files:

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.env

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

**Step 2: Write requirements.txt**

Create `src/requirements.txt` with exact dependency versions:

```
feedparser==6.0.10
aiohttp==3.9.1
python-dateutil==2.8.2
```

**Step 3: Write README.md**

Create basic README with setup instructions:

```markdown
# RSS Daily Digest

Automated daily email digest of RSS feed updates, powered by GitHub Actions.

## Setup

1. Add your RSS feeds to `feeds.opml` (export from any RSS reader)
2. Configure GitHub Secrets:
   - `SMTP_HOST` - SMTP server (e.g., `smtp.gmail.com`)
   - `SMTP_PORT` - Port number (e.g., `587`)
   - `SMTP_USER` - Your email address
   - `SMTP_PASSWORD` - App-specific password
   - `RECIPIENT_EMAIL` - Email to receive digest
3. Enable GitHub Actions in repository settings
4. Trigger manually via Actions tab to test

## Local Testing

```bash
pip install -r src/requirements.txt
export SMTP_HOST=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USER=your@email.com
export SMTP_PASSWORD=your-app-password
export RECIPIENT_EMAIL=recipient@email.com
python src/main.py
```

## Schedule

Runs daily at 2pm UTC (8am Central, 7am during DST)
```

**Step 4: Commit initial project structure**

```bash
git add .gitignore src/requirements.txt README.md
git commit -m "feat: add project structure and dependencies"
```

---

## Task 2: OPML Parser (TDD)

**Files:**
- Create: `tests/test_feed_parser.py`
- Create: `src/feed_parser.py`
- Create: `tests/fixtures/sample.opml`

**Step 1: Write test fixture OPML file**

Create `tests/fixtures/sample.opml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <head>
    <title>Test Feeds</title>
  </head>
  <body>
    <outline text="Tech" title="Tech">
      <outline type="rss" text="Daring Fireball" title="Daring Fireball" xmlUrl="https://daringfireball.net/feeds/main"/>
      <outline type="rss" text="Hacker News" title="Hacker News" xmlUrl="https://news.ycombinator.com/rss"/>
    </outline>
  </body>
</opml>
```

**Step 2: Write failing test for OPML parsing**

Create `tests/test_feed_parser.py`:

```python
import pytest
from pathlib import Path
from src.feed_parser import parse_opml


def test_parse_opml_returns_feed_list():
    """Test that parse_opml extracts feed URLs and titles from OPML file."""
    opml_path = Path(__file__).parent / "fixtures" / "sample.opml"

    feeds = parse_opml(opml_path)

    assert len(feeds) == 2
    assert feeds[0]["title"] == "Daring Fireball"
    assert feeds[0]["url"] == "https://daringfireball.net/feeds/main"
    assert feeds[1]["title"] == "Hacker News"
    assert feeds[1]["url"] == "https://news.ycombinator.com/rss"


def test_parse_opml_handles_missing_file():
    """Test that parse_opml raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        parse_opml(Path("nonexistent.opml"))
```

**Step 3: Run test to verify it fails**

Run: `pytest tests/test_feed_parser.py -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'src.feed_parser'"

**Step 4: Write minimal implementation**

Create `src/feed_parser.py`:

```python
"""RSS feed parser module."""
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict


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
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/test_feed_parser.py -v`

Expected: PASS (2 tests)

**Step 6: Commit OPML parser**

```bash
git add tests/test_feed_parser.py tests/fixtures/sample.opml src/feed_parser.py
git commit -m "feat: add OPML parser with tests"
```

---

## Task 3: Date Filtering Logic (TDD)

**Files:**
- Modify: `tests/test_feed_parser.py`
- Modify: `src/feed_parser.py`

**Step 1: Write failing test for date filtering**

Add to `tests/test_feed_parser.py`:

```python
from datetime import datetime, timedelta, timezone
from src.feed_parser import is_from_yesterday


def test_is_from_yesterday_with_yesterday_date():
    """Test that is_from_yesterday returns True for yesterday's date."""
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)

    # Test with datetime object
    assert is_from_yesterday(yesterday) is True

    # Test with struct_time (feedparser format)
    assert is_from_yesterday(yesterday.timetuple()) is True


def test_is_from_yesterday_with_today_date():
    """Test that is_from_yesterday returns False for today."""
    today = datetime.now(timezone.utc)

    assert is_from_yesterday(today) is False


def test_is_from_yesterday_with_old_date():
    """Test that is_from_yesterday returns False for older dates."""
    old_date = datetime.now(timezone.utc) - timedelta(days=5)

    assert is_from_yesterday(old_date) is False


def test_is_from_yesterday_with_none():
    """Test that is_from_yesterday returns False for None."""
    assert is_from_yesterday(None) is False
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_feed_parser.py::test_is_from_yesterday_with_yesterday_date -v`

Expected: FAIL with "ImportError: cannot import name 'is_from_yesterday'"

**Step 3: Write minimal implementation**

Add to `src/feed_parser.py`:

```python
from datetime import datetime, timedelta, timezone
import time
from typing import Union


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
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_feed_parser.py -v`

Expected: PASS (all tests)

**Step 5: Commit date filtering logic**

```bash
git add tests/test_feed_parser.py src/feed_parser.py
git commit -m "feat: add date filtering for yesterday's posts"
```

---

## Task 4: RSS Feed Fetcher (TDD)

**Files:**
- Modify: `tests/test_feed_parser.py`
- Modify: `src/feed_parser.py`

**Step 1: Write failing test for single feed fetch**

Add to `tests/test_feed_parser.py`:

```python
import asyncio
import pytest
from src.feed_parser import fetch_feed


@pytest.mark.asyncio
async def test_fetch_feed_success():
    """Test successful feed fetch returns posts from yesterday."""
    feed_url = "https://daringfireball.net/feeds/main"

    result = await fetch_feed("Daring Fireball", feed_url, timeout=15)

    assert result["name"] == "Daring Fireball"
    assert result["status"] in ["success", "no_updates"]
    assert isinstance(result["posts"], list)
    # Posts should be empty or contain valid post dicts
    for post in result["posts"]:
        assert "title" in post
        assert "link" in post
        assert "excerpt" in post


@pytest.mark.asyncio
async def test_fetch_feed_timeout():
    """Test that fetch_feed handles timeout gracefully."""
    # Use a URL that will timeout (non-routable IP)
    feed_url = "http://10.255.255.1/feed.xml"

    result = await fetch_feed("Timeout Feed", feed_url, timeout=1)

    assert result["name"] == "Timeout Feed"
    assert result["status"] == "error"
    assert result["posts"] == []
    assert "timeout" in result["error_message"].lower()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_feed_parser.py::test_fetch_feed_success -v`

Expected: FAIL with "ImportError: cannot import name 'fetch_feed'"

**Step 3: Write minimal implementation**

Add to `src/feed_parser.py`:

```python
import aiohttp
import feedparser
import asyncio
from typing import Dict, List
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
                import re
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
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_feed_parser.py -v -k fetch_feed`

Expected: PASS (test_fetch_feed_success may show no_updates if no posts from yesterday, which is acceptable)

**Step 5: Commit feed fetcher**

```bash
git add tests/test_feed_parser.py src/feed_parser.py
git commit -m "feat: add async RSS feed fetcher with error handling"
```

---

## Task 5: Parallel Feed Fetching (TDD)

**Files:**
- Modify: `tests/test_feed_parser.py`
- Modify: `src/feed_parser.py`

**Step 1: Write failing test for parallel fetching**

Add to `tests/test_feed_parser.py`:

```python
from src.feed_parser import fetch_all_feeds


@pytest.mark.asyncio
async def test_fetch_all_feeds():
    """Test parallel fetching of multiple feeds."""
    feeds = [
        {"title": "Daring Fireball", "url": "https://daringfireball.net/feeds/main"},
        {"title": "Hacker News", "url": "https://news.ycombinator.com/rss"}
    ]

    results = await fetch_all_feeds(feeds, batch_size=10)

    assert len(results) == 2
    assert all(r["status"] in ["success", "no_updates", "error"] for r in results)
    assert all("name" in r and "posts" in r for r in results)


@pytest.mark.asyncio
async def test_fetch_all_feeds_with_failures():
    """Test that fetch_all_feeds continues despite individual failures."""
    feeds = [
        {"title": "Valid Feed", "url": "https://daringfireball.net/feeds/main"},
        {"title": "Invalid Feed", "url": "http://10.255.255.1/feed.xml"}
    ]

    results = await fetch_all_feeds(feeds, batch_size=10, timeout=2)

    assert len(results) == 2
    # At least one should succeed, at least one should error
    statuses = [r["status"] for r in results]
    assert "error" in statuses
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_feed_parser.py::test_fetch_all_feeds -v`

Expected: FAIL with "ImportError: cannot import name 'fetch_all_feeds'"

**Step 3: Write minimal implementation**

Add to `src/feed_parser.py`:

```python
async def fetch_all_feeds(feeds: List[Dict[str, str]], batch_size: int = 10, timeout: int = 15) -> List[Dict]:
    """
    Fetch multiple RSS feeds in parallel batches.

    Args:
        feeds: List of feed dicts with 'title' and 'url' keys
        batch_size: Number of feeds to fetch concurrently
        timeout: Timeout per feed in seconds

    Returns:
        List of feed result dicts
    """
    results = []

    logger.info(f"Fetching {len(feeds)} feeds in batches of {batch_size}...")

    # Process feeds in batches to avoid overwhelming the system
    for i in range(0, len(feeds), batch_size):
        batch = feeds[i:i + batch_size]
        tasks = [fetch_feed(feed["title"], feed["url"], timeout) for feed in batch]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and add to results
        for result in batch_results:
            if isinstance(result, Exception):
                logger.error(f"Unexpected error: {result}")
            else:
                results.append(result)

    logger.info(f"Completed fetching {len(results)} feeds")
    return results
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_feed_parser.py -v -k fetch_all_feeds`

Expected: PASS (may be slow due to network requests)

**Step 5: Commit parallel fetching**

```bash
git add tests/test_feed_parser.py src/feed_parser.py
git commit -m "feat: add parallel feed fetching with batching"
```

---

## Task 6: Email Generator - Plain Text (TDD)

**Files:**
- Create: `tests/test_email_generator.py`
- Create: `src/email_generator.py`

**Step 1: Write failing test for plain text email**

Create `tests/test_email_generator.py`:

```python
from datetime import datetime, timedelta, timezone
from src.email_generator import generate_plain_text


def test_generate_plain_text_with_posts():
    """Test plain text email generation with feed updates."""
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    date_str = yesterday.strftime("%B %d, %Y")

    feed_results = [
        {
            "name": "Tech Blog",
            "status": "success",
            "posts": [
                {
                    "title": "New Python Release",
                    "link": "https://example.com/python",
                    "excerpt": "Python 3.12 released with new features..."
                }
            ]
        },
        {
            "name": "News Site",
            "status": "success",
            "posts": [
                {
                    "title": "Breaking News",
                    "link": "https://example.com/news",
                    "excerpt": "Important announcement today..."
                }
            ]
        },
        {
            "name": "Failed Feed",
            "status": "error",
            "posts": [],
            "error_message": "Timeout after 15s"
        }
    ]

    plain_text = generate_plain_text(feed_results)

    assert f"RSS Digest for {date_str}" in plain_text
    assert "Tech Blog" in plain_text
    assert "New Python Release" in plain_text
    assert "https://example.com/python" in plain_text
    assert "Python 3.12 released" in plain_text
    assert "2 of 3 feeds updated" in plain_text
    assert "1 feed failed to load:" in plain_text
    assert "Failed Feed (Timeout after 15s)" in plain_text


def test_generate_plain_text_empty():
    """Test plain text email when no feeds have updates."""
    feed_results = [
        {"name": "Feed 1", "status": "no_updates", "posts": []},
        {"name": "Feed 2", "status": "no_updates", "posts": []}
    ]

    plain_text = generate_plain_text(feed_results)

    assert "No updates yesterday" in plain_text
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_email_generator.py -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'src.email_generator'"

**Step 3: Write minimal implementation**

Create `src/email_generator.py`:

```python
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
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_email_generator.py -v`

Expected: PASS

**Step 5: Commit plain text generator**

```bash
git add tests/test_email_generator.py src/email_generator.py
git commit -m "feat: add plain text email generator"
```

---

## Task 7: Email Generator - HTML (TDD)

**Files:**
- Modify: `tests/test_email_generator.py`
- Modify: `src/email_generator.py`

**Step 1: Write failing test for HTML email**

Add to `tests/test_email_generator.py`:

```python
from src.email_generator import generate_html


def test_generate_html_with_posts():
    """Test HTML email generation with feed updates."""
    feed_results = [
        {
            "name": "Tech Blog",
            "status": "success",
            "posts": [
                {
                    "title": "New Python Release",
                    "link": "https://example.com/python",
                    "excerpt": "Python 3.12 released..."
                }
            ]
        }
    ]

    html = generate_html(feed_results)

    assert "<html>" in html
    assert "RSS Digest for" in html
    assert "<h2>Tech Blog</h2>" in html
    assert '<a href="https://example.com/python">New Python Release</a>' in html
    assert "Python 3.12 released..." in html


def test_generate_html_escapes_special_chars():
    """Test that HTML generator escapes special characters."""
    feed_results = [
        {
            "name": "Blog & News",
            "status": "success",
            "posts": [
                {
                    "title": "Post with <tags> & \"quotes\"",
                    "link": "https://example.com/test",
                    "excerpt": "Text with <script>alert('xss')</script>"
                }
            ]
        }
    ]

    html = generate_html(feed_results)

    assert "&amp;" in html  # & escaped
    assert "&lt;" in html or "&#x3C;" in html  # < escaped
    assert "&gt;" in html or "&#x3E;" in html  # > escaped
    assert "<script>" not in html  # Script tags escaped
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_email_generator.py::test_generate_html_with_posts -v`

Expected: FAIL with "ImportError: cannot import name 'generate_html'"

**Step 3: Write minimal implementation**

Add to `src/email_generator.py`:

```python
import html


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
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_email_generator.py -v`

Expected: PASS

**Step 5: Commit HTML generator**

```bash
git add tests/test_email_generator.py src/email_generator.py
git commit -m "feat: add HTML email generator with XSS protection"
```

---

## Task 8: Email Sender (TDD)

**Files:**
- Modify: `tests/test_email_generator.py`
- Modify: `src/email_generator.py`

**Step 1: Write failing test for email creation**

Add to `tests/test_email_generator.py`:

```python
import os
from src.email_generator import create_email_message


def test_create_email_message():
    """Test multipart email message creation."""
    feed_results = [
        {
            "name": "Test Feed",
            "status": "success",
            "posts": [
                {
                    "title": "Test Post",
                    "link": "https://example.com/test",
                    "excerpt": "Test excerpt"
                }
            ]
        }
    ]

    msg = create_email_message(
        feed_results=feed_results,
        from_email="sender@example.com",
        to_email="recipient@example.com"
    )

    assert msg["Subject"].startswith("RSS Digest - ")
    assert msg["From"] == "sender@example.com"
    assert msg["To"] == "recipient@example.com"
    assert msg.is_multipart()

    # Check both parts exist
    parts = list(msg.walk())
    content_types = [part.get_content_type() for part in parts]
    assert "text/plain" in content_types
    assert "text/html" in content_types
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_email_generator.py::test_create_email_message -v`

Expected: FAIL with "ImportError: cannot import name 'create_email_message'"

**Step 3: Write minimal implementation**

Add to `src/email_generator.py`:

```python
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


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
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_email_generator.py -v`

Expected: PASS

**Step 5: Commit email message creation**

```bash
git add tests/test_email_generator.py src/email_generator.py
git commit -m "feat: add multipart email message creation"
```

---

## Task 9: SMTP Email Sender

**Files:**
- Modify: `src/email_generator.py`

**Step 1: Write SMTP send function**

Add to `src/email_generator.py`:

```python
import smtplib
import logging


logger = logging.getLogger(__name__)


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
        Exception: If email sending fails
    """
    logger.info(f"Connecting to SMTP server {smtp_host}:{smtp_port}...")

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        logger.info(f"Email sent successfully to {msg['To']}")

    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        raise
```

**Step 2: Manual test (skip automated test for SMTP)**

Note: SMTP tests require real credentials and are better tested manually. The function follows standard patterns and will be tested end-to-end.

**Step 3: Commit SMTP sender**

```bash
git add src/email_generator.py
git commit -m "feat: add SMTP email sender"
```

---

## Task 10: Main Entry Point

**Files:**
- Create: `src/main.py`

**Step 1: Write main entry point**

Create `src/main.py`:

```python
"""Main entry point for RSS Daily Digest."""
import asyncio
import logging
import os
import sys
from pathlib import Path

from feed_parser import parse_opml, fetch_all_feeds
from email_generator import create_email_message, send_email


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main function to run RSS digest."""
    # Validate environment variables
    required_vars = ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD", "RECIPIENT_EMAIL"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)

    # Get configuration from environment
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    recipient_email = os.getenv("RECIPIENT_EMAIL")

    # Parse OPML file
    opml_path = Path(__file__).parent.parent / "feeds.opml"

    if not opml_path.exists():
        logger.error(f"OPML file not found: {opml_path}")
        logger.info("Create a feeds.opml file in the repository root with your RSS feeds")
        sys.exit(1)

    logger.info(f"Parsing OPML file: {opml_path}")
    feeds = parse_opml(opml_path)
    logger.info(f"Found {len(feeds)} feeds")

    # Fetch all feeds
    feed_results = await fetch_all_feeds(feeds, batch_size=10, timeout=15)

    # Create and send email
    logger.info("Generating email...")
    msg = create_email_message(
        feed_results=feed_results,
        from_email=smtp_user,
        to_email=recipient_email
    )

    logger.info("Sending email...")
    send_email(
        msg=msg,
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_user=smtp_user,
        smtp_password=smtp_password
    )

    logger.info("RSS digest sent successfully!")


if __name__ == "__main__":
    asyncio.run(main())
```

**Step 2: Test main.py with environment variables**

Run: Create a `.env` file (git-ignored) with test credentials and run:
```bash
export $(cat .env | xargs)
python src/main.py
```

Expected: Script runs, fetches feeds, sends email (or fails with helpful error if OPML missing)

**Step 3: Commit main entry point**

```bash
git add src/main.py
git commit -m "feat: add main entry point with environment validation"
```

---

## Task 11: Sample OPML File

**Files:**
- Create: `feeds.opml`

**Step 1: Create sample OPML file**

Create `feeds.opml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <head>
    <title>RSS Daily Digest Feeds</title>
  </head>
  <body>
    <outline text="Tech">
      <outline type="rss" text="Hacker News" title="Hacker News" xmlUrl="https://news.ycombinator.com/rss"/>
      <outline type="rss" text="Daring Fireball" title="Daring Fireball" xmlUrl="https://daringfireball.net/feeds/main"/>
    </outline>
  </body>
</opml>
```

**Step 2: Commit sample OPML**

```bash
git add feeds.opml
git commit -m "feat: add sample OPML file with default feeds"
```

---

## Task 12: GitHub Actions Workflow

**Files:**
- Create: `.github/workflows/daily-digest.yml`

**Step 1: Create workflow file**

Create `.github/workflows/daily-digest.yml`:

```yaml
name: Daily RSS Digest

on:
  schedule:
    # Run at 2pm UTC (8am Central, 7am during DST)
    - cron: '0 14 * * *'
  workflow_dispatch:  # Allow manual triggering

jobs:
  send-digest:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r src/requirements.txt

      - name: Run RSS digest
        env:
          SMTP_HOST: ${{ secrets.SMTP_HOST }}
          SMTP_PORT: ${{ secrets.SMTP_PORT }}
          SMTP_USER: ${{ secrets.SMTP_USER }}
          SMTP_PASSWORD: ${{ secrets.SMTP_PASSWORD }}
          RECIPIENT_EMAIL: ${{ secrets.RECIPIENT_EMAIL }}
        run: python src/main.py
```

**Step 2: Commit GitHub Actions workflow**

```bash
git add .github/workflows/daily-digest.yml
git commit -m "feat: add GitHub Actions workflow for daily digest"
```

---

## Task 13: Update README with Complete Instructions

**Files:**
- Modify: `README.md`

**Step 1: Update README with complete documentation**

Replace `README.md` contents:

```markdown
# RSS Daily Digest

Automated daily email digest of RSS feed updates, powered by GitHub Actions.

## Features

- Fetches 100-200 RSS feeds in parallel
- Filters for posts published yesterday
- Sends formatted HTML + plain text email
- Runs automatically every day at 2pm UTC (8am Central, 7am during DST)
- Graceful error handling for failed feeds
- Zero infrastructure required (runs on GitHub Actions)

## Setup

### 1. Fork or Clone this Repository

```bash
git clone https://github.com/yourusername/rss-digest.git
cd rss-digest
```

### 2. Add Your RSS Feeds

Edit `feeds.opml` with your feeds. You can:
- Export OPML from your RSS reader (Feedly, Inoreader, etc.)
- Manually add feeds following the example structure

### 3. Configure GitHub Secrets

Go to your repository → Settings → Secrets and variables → Actions → New repository secret

Add the following secrets:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `SMTP_HOST` | SMTP server hostname | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port (usually 587) | `587` |
| `SMTP_USER` | Your email address | `your@email.com` |
| `SMTP_PASSWORD` | App-specific password | `abcd efgh ijkl mnop` |
| `RECIPIENT_EMAIL` | Email to receive digest | `recipient@email.com` |

#### Gmail Setup

1. Enable 2-Factor Authentication on your Google account
2. Go to [Google Account → Security → App Passwords](https://myaccount.google.com/apppasswords)
3. Generate new app password for "Mail"
4. Use the 16-character password in `SMTP_PASSWORD` secret

### 4. Enable GitHub Actions

Go to your repository → Actions tab → Enable workflows

### 5. Test the Workflow

Go to Actions → Daily RSS Digest → Run workflow (manual trigger)

Check the logs to verify it works correctly.

## Local Testing

```bash
# Install dependencies
pip install -r src/requirements.txt

# Set environment variables
export SMTP_HOST=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USER=your@email.com
export SMTP_PASSWORD=your-app-password
export RECIPIENT_EMAIL=recipient@email.com

# Run the script
python src/main.py
```

## Schedule

- **Default:** 2pm UTC daily (8am Central Standard Time)
- **During DST:** Digest arrives at 7am Central (GitHub Actions uses UTC only)
- **To change:** Edit the cron schedule in `.github/workflows/daily-digest.yml`

## Email Format

**Subject:** RSS Digest - [Date]

**Body:**
- Feeds grouped alphabetically
- Each feed shows posts from yesterday
- Post title (linked) + 300-character excerpt
- Summary section with success/failure counts

## Troubleshooting

### No email received

1. Check GitHub Actions logs for errors
2. Verify all secrets are set correctly
3. Check spam folder
4. Ensure SMTP credentials are valid

### "Missing required environment variables"

All five secrets must be configured in GitHub repository settings.

### "OPML file not found"

Ensure `feeds.opml` exists in the repository root.

### Feed errors in email

Some feeds may timeout or have invalid XML. These are reported in the email summary section. Consider removing consistently failing feeds.

### GitHub Actions workflow not running

- Workflows in inactive repos (60+ days) are paused
- Make a commit to reactivate
- Check Actions tab for disabled workflows

## Architecture

- **Feed Parser** (`src/feed_parser.py`) - Parses OPML, fetches feeds in parallel, filters by date
- **Email Generator** (`src/email_generator.py`) - Creates multipart HTML/text emails
- **Main Script** (`src/main.py`) - Orchestrates the workflow
- **GitHub Actions** (`.github/workflows/daily-digest.yml`) - Schedules daily runs

## Dependencies

- `feedparser` - RSS/Atom feed parsing
- `aiohttp` - Async HTTP requests for parallel fetching
- `python-dateutil` - Date parsing and timezone handling

## License

MIT

## Contributing

Pull requests welcome! Please ensure tests pass before submitting.

## Privacy Note

If your repository is public, your `feeds.opml` will be visible to anyone. Use a private repository if you want to keep your feed list private (GitHub free tier includes 2,000 Actions minutes/month, sufficient for daily 5-minute runs).
```

**Step 2: Commit updated README**

```bash
git add README.md
git commit -m "docs: update README with complete setup instructions"
```

---

## Task 14: Add pytest Configuration

**Files:**
- Create: `pytest.ini`
- Modify: `src/requirements.txt`

**Step 1: Add pytest to requirements**

Add to `src/requirements.txt`:

```
feedparser==6.0.10
aiohttp==3.9.1
python-dateutil==2.8.2
pytest==7.4.3
pytest-asyncio==0.21.1
```

**Step 2: Create pytest configuration**

Create `pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
```

**Step 3: Verify tests run**

Run: `pip install -r src/requirements.txt && pytest -v`

Expected: All tests pass

**Step 4: Commit pytest configuration**

```bash
git add pytest.ini src/requirements.txt
git commit -m "test: add pytest configuration and dependencies"
```

---

## Task 15: Final Integration Test

**Files:**
- Review all components

**Step 1: Run full test suite**

Run: `pytest -v`

Expected: All tests pass

**Step 2: Test main.py with real feeds**

Run:
```bash
export SMTP_HOST=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USER=your@email.com
export SMTP_PASSWORD=your-app-password
export RECIPIENT_EMAIL=your@email.com
python src/main.py
```

Expected: Email received with digest

**Step 3: Verify GitHub Actions workflow syntax**

Run: `cat .github/workflows/daily-digest.yml`

Expected: Valid YAML with correct job structure

**Step 4: Review commit history**

Run: `git log --oneline`

Expected: Clean commit history with descriptive messages following conventional commits format

---

## Post-Implementation Checklist

After completing all tasks, verify:

- [ ] All tests pass locally (`pytest -v`)
- [ ] Script runs successfully with real OPML and SMTP credentials
- [ ] Email received with expected format (HTML + plain text)
- [ ] GitHub Actions workflow file is valid
- [ ] README contains complete setup instructions
- [ ] Repository has `.gitignore` to exclude sensitive files
- [ ] Sample `feeds.opml` includes working RSS feeds
- [ ] All commits follow conventional commit format
- [ ] Code includes proper error handling and logging

## Next Steps for Deployment

1. Push code to GitHub repository
2. Configure GitHub Secrets in repository settings
3. Enable GitHub Actions
4. Trigger manual workflow run to test
5. Verify email arrives successfully
6. Wait for scheduled run next day
7. Monitor GitHub Actions logs for any issues

---

**End of Implementation Plan**
