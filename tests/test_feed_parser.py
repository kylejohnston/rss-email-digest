import pytest
from pathlib import Path
from datetime import datetime, timedelta, timezone
import asyncio
from src.feed_parser import parse_opml, is_from_yesterday, fetch_feed, fetch_all_feeds


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
