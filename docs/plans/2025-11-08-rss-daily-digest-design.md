# RSS Daily Digest - Design Document

**Date:** November 8, 2025
**Project:** RSS Daily Digest
**Purpose:** Automated daily email digest of RSS feed updates

## Overview

A Python-based tool running on GitHub Actions that fetches RSS feeds daily, identifies yesterday's posts, and sends a formatted email digest. Designed to handle 100-200 feeds efficiently with graceful error handling.

## Architecture

### Core Components

1. **Feed Parser** - Reads OPML, fetches RSS feeds, filters for yesterday's posts
2. **Email Generator** - Creates multipart email (HTML + plain text) with posts grouped by feed
3. **GitHub Actions Workflow** - Schedules daily runs, manages secrets

### File Structure

```
rss-digest/
├── .github/
│   └── workflows/
│       └── daily-digest.yml
├── feeds.opml
├── src/
│   ├── main.py
│   ├── feed_parser.py
│   ├── email_generator.py
│   └── requirements.txt
├── docs/
│   └── plans/
│       └── 2025-11-08-rss-daily-digest-design.md
└── README.md
```

## Technical Decisions

### Language & Runtime
- **Python 3.11** - Excellent RSS parsing libraries, good async support, easy email handling
- **GitHub Actions** - Free for public repos, no server needed, cron scheduling built-in

### Feed Management
- **OPML format** - Standard RSS export format from any reader
- **Location** - `feeds.opml` in repo root
- **Parsing** - Python's built-in `xml.etree` library

### Scheduling
- **Time:** 2pm UTC (8am Central Time)
- **Frequency:** Daily via GitHub Actions cron
- **Note:** Time will shift to 7am during DST (GitHub Actions uses UTC only)

### Email Delivery
- **Method:** SMTP (for initial testing/personal use)
- **Format:** Multipart (HTML + plain text fallback)
- **Credentials:** Stored in GitHub Secrets

## Feed Parser Component

### OPML Parsing
- Read `feeds.opml` from repo root
- Extract feed URLs and titles from `<outline>` tags
- Parse `xmlUrl` and `title` attributes

### RSS Fetching (Parallel)
- **Library:** `feedparser` for parsing RSS/Atom feeds
- **Concurrency:** `aiohttp` + `asyncio` for parallel fetching
- **Batch size:** 10-20 feeds at a time
- **Timeout:** 15 seconds per feed
- **Error handling:** Track failures, continue with remaining feeds

### Date Filtering
- Determine "yesterday" based on UTC calendar date
- Check each entry's `published` or `updated` timestamp
- Include entries published on yesterday's date (ignore time-of-day)
- Skip feeds with no publish dates (log warning)

### Output Structure
```python
{
  'feeds': [
    {
      'name': 'Daring Fireball',
      'posts': [
        {
          'title': 'Post Title',
          'link': 'https://...',
          'excerpt': 'First 300 chars...'
        }
      ],
      'status': 'success'
    },
    {
      'name': 'Broken Feed',
      'posts': [],
      'status': 'error',
      'error_message': 'Timeout after 15s'
    }
  ]
}
```

## Email Generator Component

### Email Structure

**Subject:** `RSS Digest - [Date]`

**Body:**
```
RSS Digest for [Date]

--- Feeds with Updates ---

Feed Name 1
• Post title (linked)
  Excerpt (truncated to 300 chars)...
• Post title (linked)
  Excerpt...

Feed Name 2
• Post title (linked)
  Excerpt...

--- Summary ---
12 of 25 feeds updated
3 feeds failed to load:
• Feed Name (Timeout after 15s)
• Feed Name (Invalid XML)
```

### Email Generation Details
- **Library:** Python's `email.mime.multipart` for multipart messages
- **HTML version:** Basic styling (readable fonts, spacing, blue links)
- **Plain text version:** Same structure, simpler formatting
- **Excerpt handling:**
  - Truncate at 300 characters
  - Add "..." if truncated
  - Strip HTML tags if present in feed
- **Feed ordering:** Alphabetical by feed name
- **Empty digest:** Send email with "No updates yesterday" if no posts

### SMTP Configuration
- **Library:** `smtplib` (built-in Python)
- **Credentials from GitHub Secrets:**
  - `SMTP_HOST` (e.g., `smtp.gmail.com`)
  - `SMTP_PORT` (e.g., `587` for TLS)
  - `SMTP_USER` (email address)
  - `SMTP_PASSWORD` (app-specific password)
  - `RECIPIENT_EMAIL` (recipient address)

## GitHub Actions Workflow

### Workflow Configuration

**File:** `.github/workflows/daily-digest.yml`

```yaml
name: Daily RSS Digest

on:
  schedule:
    - cron: '0 14 * * *'  # 2pm UTC = 8am Central
  workflow_dispatch:  # Manual trigger for testing

jobs:
  send-digest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r src/requirements.txt
      - name: Run digest
        env:
          SMTP_HOST: ${{ secrets.SMTP_HOST }}
          SMTP_PORT: ${{ secrets.SMTP_PORT }}
          SMTP_USER: ${{ secrets.SMTP_USER }}
          SMTP_PASSWORD: ${{ secrets.SMTP_PASSWORD }}
          RECIPIENT_EMAIL: ${{ secrets.RECIPIENT_EMAIL }}
        run: python src/main.py
```

### Required GitHub Secrets
- `SMTP_HOST` - SMTP server hostname
- `SMTP_PORT` - SMTP port (usually 587)
- `SMTP_USER` - SMTP username
- `SMTP_PASSWORD` - SMTP password (app-specific for Gmail)
- `RECIPIENT_EMAIL` - Email address to receive digest

### Key Features
- `workflow_dispatch` enables manual testing
- All logs visible in Actions tab
- Free for public repos
- Minimal cost for private repos (~5 minutes per day)

## Error Handling

### Feed Fetch Failures
- Catch timeouts, network errors, invalid XML
- Track error type and feed name
- Continue processing remaining feeds
- Include error details in email summary

### OPML Parse Errors
- Exit with clear error message if OPML is malformed
- Validate OPML structure before processing

### SMTP Failures
- Log detailed error message
- Exit with non-zero code (visible in Actions logs)
- GitHub Actions will mark workflow as failed

### Missing Configuration
- Validate all required environment variables exist
- Exit early with helpful message if any are missing

### Empty Digest
- Send email even if no feeds have updates
- Include message: "No updates yesterday"
- Still show error summary if feeds failed

## Logging

### Progress Tracking
- Print to stdout (visible in GitHub Actions logs)
- Log examples:
  - "Fetching 25 feeds..."
  - "Feed X: 3 new posts"
  - "Feed Y: timeout after 15s"
  - "Sending email..."
- Helps debug issues when reviewing workflow runs

## Testing Strategy

### Local Testing
- Run script locally with `.env` file for secrets
- Test with small OPML file (5-10 feeds) first
- Verify email format and content

### GitHub Actions Testing
- Use `workflow_dispatch` to trigger manually
- Test without waiting for scheduled run
- Review logs in Actions tab

### Test Scenarios
- All feeds successful
- Some feeds fail (timeout, invalid XML)
- No updates (empty digest)
- Large feed list (100+ feeds)

## Dependencies

### requirements.txt
```
feedparser==6.0.10
aiohttp==3.9.1
python-dateutil==2.8.2
```

### Rationale
- **feedparser** - Industry standard RSS/Atom parser, handles malformed feeds
- **aiohttp** - Async HTTP client for parallel fetching
- **python-dateutil** - Robust date parsing and timezone handling

## Performance Considerations

### Scalability (100-200 feeds)
- **Parallel fetching:** 10-20 concurrent requests
- **Expected runtime:** 2-5 minutes for 200 feeds
- **Timeout per feed:** 15 seconds
- **GitHub Actions limits:** 6 hours max (plenty of headroom)

### Email Size
- With 200 feeds, potentially 500+ items
- Truncated excerpts keep size manageable
- Consider adding `max_posts_per_feed` config if needed

## Known Issues & Considerations

### Gmail SMTP
- Requires App Password (2FA must be enabled)
- May receive security alert for new IP (GitHub's servers)
- Must approve login attempt via email

### Feed Behavior Quirks
- Some feeds update timestamps when posts are edited
- Some feeds lack timestamps entirely (will be skipped)
- 301 redirects are common (feedparser handles automatically)
- Some sites may block automated requests

### GitHub Actions Caveats
- Schedule not guaranteed (5-10 minute delay possible during high load)
- Won't run if repo inactive for 60 days (make a commit to reactivate)
- No built-in failure notifications (check Actions tab periodically)

### Daylight Saving Time
- Schedule uses UTC only
- Digest will arrive at 7am during DST, 8am during standard time
- Must manually update cron schedule to maintain consistent time

### Repository Visibility
- **Public repo:** Free unlimited Actions minutes, but OPML reveals your reading list
- **Private repo:** OPML is private, uses free tier minutes (2,000/month - sufficient for daily 5-minute runs)

## Future Enhancements

### Potential Features (Not in Initial Implementation)
- AI-powered summaries using LLM APIs
- Feed categorization/grouping
- Per-feed configuration (max items, summarize on/off)
- Multiple recipient support
- Email service API (SendGrid, Mailgun) for better deliverability
- JSON feed format support alongside OPML
- Web preview of digest before sending
- RSS feed health monitoring dashboard

## Success Criteria

### Minimum Viable Product
- ✓ Reads OPML file from repo
- ✓ Fetches 100-200 feeds in parallel
- ✓ Filters for yesterday's posts
- ✓ Sends formatted multipart email
- ✓ Handles errors gracefully
- ✓ Runs daily on schedule
- ✓ Includes feed excerpts (300 chars)
- ✓ Summary stats at bottom

### User Experience Goals
- Email arrives reliably each morning
- Easy to scan (alphabetical, grouped by feed)
- Clear indication of feed errors
- Simple to add/remove feeds (edit OPML)
- Low maintenance (runs automatically)

## Implementation Notes

### Getting Started
1. Create GitHub repository
2. Set up directory structure
3. Add `feeds.opml` with initial feed list
4. Configure GitHub Secrets for SMTP
5. Implement feed parser
6. Implement email generator
7. Create GitHub Actions workflow
8. Test with manual trigger
9. Verify scheduled runs

### Gmail App Password Setup
1. Enable 2FA on Google account
2. Go to Google Account → Security → App Passwords
3. Generate new app password for "Mail"
4. Use generated password in `SMTP_PASSWORD` secret

---

**End of Design Document**
