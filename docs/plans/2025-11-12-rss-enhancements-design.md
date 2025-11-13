# RSS Digest Enhancements Design

**Date:** 2025-11-12
**Status:** Approved

## Overview

Three enhancements to improve the RSS digest user experience:
1. Decode HTML entities in feed content
2. Add CLI tool for testing individual feeds locally
3. Make feed titles clickable links to main sites

## Feature 1: HTML Entity Decoding

### Problem
Feed content contains HTML entities (`&#8220;`, `&#8221;`, `&quot;`, `&amp;`, etc.) that render literally instead of as their actual characters, making the digest less readable.

### Solution
Use Python's `html.unescape()` to decode entities in both HTML and plain text email outputs.

### Implementation
- **Location:** `src/email_generator.py`
- **Apply to:** Post titles and excerpts (user-facing content)
- **Don't apply to:** Feed names (from OPML, should be clean)

**HTML mode:**
1. Continue using `html.escape()` first for XSS protection
2. Apply `html.unescape()` to post titles and excerpts after escaping
3. This ensures structure is safe while content is readable

**Plain text mode:**
1. Apply `html.unescape()` directly to post titles and excerpts
2. No escaping needed in plain text

**Example transformation:**
- Input: `"The company&#8217;s new API"`
- Output: `"The company's new API"`

### Security Consideration
XSS protection via `html.escape()` is maintained in HTML mode. Unescape is only applied to content portions, not HTML structure or attributes.

## Feature 2: Feed Testing CLI Tool

### Problem
Some feeds should return updates but are missing from the digest. Need a way to test individual feeds locally to troubleshoot date filtering, parsing issues, or connectivity problems.

### Solution
Create new CLI module `src/test_feed.py` that fetches and displays feed data with optional date filtering.

### Command Interface
```bash
# Show latest posts regardless of date
python -m src.test_feed "https://example.com/feed.xml" --latest

# Test for a specific date
python -m src.test_feed "https://example.com/feed.xml" --date 2025-11-11

# Test with default (yesterday's posts only)
python -m src.test_feed "https://example.com/feed.xml"
```

### Output Format
- Feed title and homepage link (from feed metadata)
- Number of total entries found
- For each post (limited to 10 most recent):
  - Title
  - Published date (both raw and parsed format)
  - Link
  - Excerpt preview (first 100 chars)
  - ✓ or ✗ indicator if it matches the date filter
- Summary: "X posts match the filter, Y total posts found"

### Implementation
- **Location:** New file `src/test_feed.py`
- **Reuses:** `fetch_feed()` and `is_from_yesterday()` from `feed_parser.py`
- **Argument parsing:** Use `argparse` for CLI interface
- **Date override:** Bypass date filter when `--latest` flag is used

## Feature 3: Clickable Feed Titles

### Problem
Some posts don't have links, and feed titles currently aren't clickable. Linking titles to the main site provides a workaround for accessing content.

### Solution
Extract site homepage URL from feed metadata and make feed titles clickable links in both HTML and plain text formats.

### Data Flow Changes

**1. Feed Parser (`src/feed_parser.py`)**
- In `fetch_feed()`, extract site URL from `parsed_feed.feed.link`
- Add `site_url` field to returned feed dictionary
- Handle missing URLs gracefully (use empty string or None)

**2. Email Generator (`src/email_generator.py`)**

**HTML mode:**
- Wrap `<h2>` feed names in `<a href="...">` tags if site_url exists
- Example: `<h2><a href="https://daringfireball.net">Daring Fireball</a></h2>`

**Plain text mode:**
- Add URL on separate line under feed name
- Example:
  ```
  Daring Fireball
  Visit: https://daringfireball.net
  ```

### Edge Cases
- If feed doesn't have `feed.link` metadata, title remains as plain text (no link)
- No breaking changes if URL is missing

## Implementation Order

1. **HTML Entity Decoding** - Simplest change, immediate UX improvement
2. **Clickable Feed Titles** - Moderate complexity, enhances navigation
3. **Feed Testing CLI** - Most complex, requires new module and CLI interface

## Testing Requirements

- Add tests for HTML entity decoding in `tests/test_email_generator.py`
- Add tests for site URL extraction in `tests/test_feed_parser.py`
- Manual testing of CLI tool with various feeds and date scenarios
- Verify existing tests still pass after changes

## Success Criteria

- HTML entities render as proper characters in both email formats
- CLI tool successfully identifies why feeds are/aren't appearing in digest
- Feed titles link to homepages in HTML emails
- All existing tests pass
- No breaking changes to current functionality
