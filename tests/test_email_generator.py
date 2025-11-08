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
