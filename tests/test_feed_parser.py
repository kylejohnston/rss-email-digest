import pytest
from pathlib import Path
from datetime import datetime, timedelta, timezone
from src.feed_parser import parse_opml, is_from_yesterday


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
