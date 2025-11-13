"""CLI tool for testing individual RSS feeds."""
import argparse
import asyncio
import sys
from datetime import datetime, timedelta, timezone
from typing import Optional
from src.feed_parser import fetch_feed, is_from_yesterday


async def test_feed(feed_url: str, show_latest: bool = False, test_date: Optional[str] = None) -> None:
    """
    Test an RSS feed and display its contents.

    Args:
        feed_url: URL of the RSS feed to test
        show_latest: If True, show latest posts regardless of date
        test_date: Optional date string (YYYY-MM-DD) to test against
    """
    print(f"Testing feed: {feed_url}")
    print("=" * 80)
    print()

    # Fetch the feed
    result = await fetch_feed("Test Feed", feed_url, timeout=15)

    if result["status"] == "error":
        print(f"❌ Error fetching feed: {result['error_message']}")
        sys.exit(1)

    # Show feed metadata
    print(f"Feed Name: {result['name']}")
    if result.get("site_url"):
        print(f"Site URL: {result['site_url']}")
    print()

    # Re-fetch to get all entries (not just yesterday's)
    import aiohttp
    import feedparser

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(feed_url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                content = await response.text()

        feed = feedparser.parse(content)

        if not feed.entries:
            print("⚠️  No entries found in feed")
            sys.exit(0)

        print(f"Total entries in feed: {len(feed.entries)}")
        print()

        # Determine what date to check against
        if test_date:
            try:
                check_date = datetime.strptime(test_date, "%Y-%m-%d").date()
                print(f"Testing against date: {check_date}")
            except ValueError:
                print(f"❌ Invalid date format: {test_date}. Use YYYY-MM-DD")
                sys.exit(1)
        else:
            yesterday = datetime.now(timezone.utc) - timedelta(days=1)
            check_date = yesterday.date()
            print(f"Testing against yesterday's date: {check_date}")

        print()
        print("Latest Posts (up to 10):")
        print("-" * 80)

        matches = 0
        for i, entry in enumerate(feed.entries[:10]):
            print(f"\n{i + 1}. {entry.title}")
            print(f"   Link: {entry.link}")

            # Get publication date
            pub_date = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
            if pub_date:
                pub_datetime = datetime(*pub_date[:6], tzinfo=timezone.utc)
                print(f"   Published: {pub_datetime.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                print(f"   Raw date: {pub_date}")

                # Check if it matches our filter
                if show_latest:
                    print(f"   ✓ Shown (--latest mode)")
                    matches += 1
                elif pub_datetime.date() == check_date:
                    print(f"   ✓ Matches date filter")
                    matches += 1
                else:
                    print(f"   ✗ Does not match date filter")
            else:
                print(f"   ⚠️  No publication date found")

            # Show excerpt preview
            excerpt = ""
            if hasattr(entry, "summary"):
                excerpt = entry.summary
            elif hasattr(entry, "content"):
                excerpt = entry.content[0].value

            if excerpt:
                # Strip HTML and truncate for preview
                import re
                excerpt = re.sub(r'<[^>]+>', '', excerpt).strip()
                preview = excerpt[:100] + "..." if len(excerpt) > 100 else excerpt
                print(f"   Excerpt: {preview}")

        print()
        print("=" * 80)
        if show_latest:
            print(f"Total posts shown: {min(10, len(feed.entries))}")
        else:
            print(f"Posts matching filter: {matches} out of {min(10, len(feed.entries))} shown")
            print(f"Date filter: {check_date}")

    except Exception as e:
        print(f"❌ Error processing feed: {str(e)}")
        sys.exit(1)


def main():
    """Main entry point for CLI tool."""
    parser = argparse.ArgumentParser(
        description="Test an RSS feed and display its contents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show latest posts regardless of date
  python -m src.test_feed "https://example.com/feed.xml" --latest

  # Test for a specific date
  python -m src.test_feed "https://example.com/feed.xml" --date 2025-11-11

  # Test with default (yesterday's posts)
  python -m src.test_feed "https://example.com/feed.xml"
        """
    )

    parser.add_argument(
        "feed_url",
        help="URL of the RSS feed to test"
    )

    parser.add_argument(
        "--latest",
        action="store_true",
        help="Show latest posts regardless of date"
    )

    parser.add_argument(
        "--date",
        type=str,
        help="Test for a specific date (YYYY-MM-DD format)"
    )

    args = parser.parse_args()

    # Run the async test function
    asyncio.run(test_feed(args.feed_url, args.latest, args.date))


if __name__ == "__main__":
    main()
