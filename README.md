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
