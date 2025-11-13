from datetime import datetime, timedelta, timezone
import os
from src.email_generator import generate_plain_text, generate_html, create_email_message


def test_generate_plain_text_with_posts():
    """Test plain text email generation with feed updates."""
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    date_str = yesterday.strftime("%B %d, %Y")

    feed_results = [
        {
            "name": "Tech Blog",
            "status": "success",
            "site_url": "https://techblog.com",
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
            "site_url": "https://news.com",
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
            "site_url": "",
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
        {"name": "Feed 1", "status": "no_updates", "site_url": "", "posts": []},
        {"name": "Feed 2", "status": "no_updates", "site_url": "", "posts": []}
    ]

    plain_text = generate_plain_text(feed_results)

    assert "No updates yesterday" in plain_text


def test_generate_html_with_posts():
    """Test HTML email generation with feed updates."""
    feed_results = [
        {
            "name": "Tech Blog",
            "status": "success",
            "site_url": "",
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
    assert "<h2>Tech Blog</h2>" in html
    assert '<a href="https://example.com/python">New Python Release</a>' in html
    assert "Python 3.12 released..." in html


def test_generate_html_escapes_special_chars():
    """Test that HTML generator escapes special characters."""
    feed_results = [
        {
            "name": "Blog & News",
            "status": "success",
            "site_url": "",
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


def test_html_entity_decoding_plain_text():
    """Test that HTML entities are decoded in plain text output."""
    feed_results = [
        {
            "name": "Test Feed",
            "status": "success",
            "site_url": "",
            "posts": [
                {
                    "title": "The company&#8217;s new API",
                    "link": "https://example.com/test",
                    "excerpt": "Here&#8217;s what&#8217;s new: &quot;improved&quot; features"
                }
            ]
        }
    ]

    plain_text = generate_plain_text(feed_results)

    # Check that entities are decoded to their actual characters
    # &#8217; decodes to ' (right single quotation mark U+2019)
    # &quot; decodes to " (straight double quote)
    assert "\u2019" in plain_text  # Right single quotation mark should be present
    assert "The company" in plain_text and "s new API" in plain_text
    assert "improved" in plain_text
    # Should not contain the raw entities
    assert "&#8217;" not in plain_text
    assert "&quot;" not in plain_text


def test_html_entity_decoding_html():
    """Test that HTML entities are decoded in HTML output."""
    feed_results = [
        {
            "name": "Test Feed",
            "status": "success",
            "site_url": "",
            "posts": [
                {
                    "title": "The company&#8217;s new API",
                    "link": "https://example.com/test",
                    "excerpt": "Here&#8217;s what&#8217;s new: &quot;improved&quot; features"
                }
            ]
        }
    ]

    html = generate_html(feed_results)

    # Check that entities are decoded to their actual characters
    # &#8217; decodes to ' (right single quotation mark U+2019)
    # After re-escaping for HTML, this stays as the actual character
    assert "\u2019" in html  # Right single quotation mark should be present
    assert "The company" in html and "s new API" in html
    assert "improved" in html
    # Should not contain the original numeric entities
    assert "&#8217;" not in html


def test_html_entity_decoding_preserves_xss_protection():
    """Test that XSS protection is maintained after entity decoding."""
    feed_results = [
        {
            "name": "Test Feed",
            "status": "success",
            "site_url": "",
            "posts": [
                {
                    "title": "&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;",
                    "link": "https://example.com/test",
                    "excerpt": "Safe &amp; secure"
                }
            ]
        }
    ]

    html = generate_html(feed_results)

    # After unescape, the < and > will be there, but then re-escaped
    # Should not contain executable script tags
    assert "<script>" not in html
    assert "alert('xss')" not in html or "alert(&#x27;xss&#x27;)" in html
    # Should contain escaped versions
    assert "&lt;" in html or "&#x3C;" in html


def test_clickable_feed_titles_html():
    """Test that feed titles are clickable links in HTML output when site_url is present."""
    feed_results = [
        {
            "name": "Example Blog",
            "status": "success",
            "site_url": "https://example.com",
            "posts": [
                {
                    "title": "Test Post",
                    "link": "https://example.com/post",
                    "excerpt": "Test excerpt"
                }
            ]
        }
    ]

    html = generate_html(feed_results)

    # Feed title should be wrapped in a link
    assert '<h2><a href="https://example.com">Example Blog</a></h2>' in html


def test_non_clickable_feed_titles_html():
    """Test that feed titles are not clickable when site_url is empty."""
    feed_results = [
        {
            "name": "Example Blog",
            "status": "success",
            "site_url": "",
            "posts": [
                {
                    "title": "Test Post",
                    "link": "https://example.com/post",
                    "excerpt": "Test excerpt"
                }
            ]
        }
    ]

    html = generate_html(feed_results)

    # Feed title should NOT be a link
    assert "<h2>Example Blog</h2>" in html


def test_clickable_feed_titles_plain_text():
    """Test that site URL is shown in plain text output when present."""
    feed_results = [
        {
            "name": "Example Blog",
            "status": "success",
            "site_url": "https://example.com",
            "posts": [
                {
                    "title": "Test Post",
                    "link": "https://example.com/post",
                    "excerpt": "Test excerpt"
                }
            ]
        }
    ]

    plain_text = generate_plain_text(feed_results)

    # Should show the visit line
    assert "Visit: https://example.com" in plain_text


def test_create_email_message():
    """Test multipart email message creation."""
    feed_results = [
        {
            "name": "Test Feed",
            "status": "success",
            "site_url": "https://example.com",
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
