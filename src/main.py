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
