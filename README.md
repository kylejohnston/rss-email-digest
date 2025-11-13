# RSS Daily Digest

Automated daily email digest of RSS feed updates, powered by GitHub Actions.

## Features

- Fetches 100-200 RSS feeds in parallel
- Filters for posts published yesterday
- Sends formatted HTML + plain text email
- **HTML entity decoding** - Special characters (curly quotes, em dashes, etc.) render correctly
- **Clickable feed titles** - Feed names link to the main site in HTML emails
- **CLI testing tool** - Debug individual feeds locally without sending emails
- Runs automatically every day at 2pm UTC (8am Central, 7am during DST)
- Graceful error handling for failed feeds
- Zero infrastructure required (runs on GitHub Actions)

## Setup

### 1. Fork or Clone this Repository

```bash
git clone https://github.com/yourusername/rss-email-digest.git
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

### Running the Full Digest

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

### Testing Individual Feeds

Use the CLI testing tool to debug individual feeds without sending emails:

```bash
# Show latest posts regardless of date
python -m src.test_feed "https://example.com/feed.xml" --latest

# Test for a specific date (useful for debugging date filters)
python -m src.test_feed "https://example.com/feed.xml" --date 2025-11-11

# Test with default filter (yesterday's posts only)
python -m src.test_feed "https://example.com/feed.xml"
```

**What it shows:**
- Feed metadata (title, homepage URL)
- Latest 10 posts with publication dates
- Whether each post matches the date filter (✓ or ✗)
- Excerpt previews

**Use cases:**
- Debug why a feed isn't showing up in your digest
- Verify a feed has recent posts
- Check if date filtering is working correctly
- Test new feeds before adding them to `feeds.opml`

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
