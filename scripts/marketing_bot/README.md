# Marketing Bot Documentation

## Overview

The Marketing Bot is an autonomous multi-platform social media engagement system that posts comments, replies, and articles across Reddit, Twitter/X, LinkedIn, Bluesky, Hacker News, GitHub, and dev.to.

## Architecture

```
scripts/marketing_bot/
├── README.md                  # This file
├── AGENTS.md                  # Agent protocol documentation
├── __init__.py                # Package init
├── config.py                  # Centralized configuration
├── llm.py                     # MiMo v2.5 LLM integration
├── cdp_utils.py               # Chrome DevTools Protocol utilities
├── platforms/
│   ├── __init__.py
│   ├── reddit.py              # Reddit posting & commenting
│   ├── twitter.py             # Twitter/X posting & commenting
│   ├── linkedin.py            # LinkedIn posting & commenting
│   ├── bluesky.py             # Bluesky posting (API-based)
│   ├── hackernews.py          # Hacker News posting
│   ├── devto.py               # dev.to article publishing
│   └── github.py              # GitHub engagement (stars, issues)
├── content/
│   ├── __init__.py
│   ├── generator.py           # Content generation with LLM
│   ├── templates.py           # Fallback templates
│   ├── articles.py            # Article content for cross-posting
│   ├── thread_generator.py    # Twitter/LinkedIn thread generator
│   ├── comment_responder.py   # Auto-respond to comments
│   ├── newsletter_generator.py # Weekly newsletter generator
│   └── analytics_tracker.py   # Engagement analytics tracker
├── orchestrator.py            # Main orchestrator (runs all platforms)
└── run.py                     # CLI entry point
```

## Quick Start

```bash
# Run all platforms
python scripts/marketing_bot/run.py

# Run specific platform
python scripts/marketing_bot/run.py --platform reddit
python scripts/marketing_bot/run.py --platform twitter
python scripts/marketing_bot/run.py --platform linkedin
python scripts/marketing_bot/run.py --platform github

# Run in article mode (cross-post articles)
python scripts/marketing_bot/run.py --mode articles

# Run in comment mode (engage with discussions)
python scripts/marketing_bot/run.py --mode comments
```

## Configuration

All configuration is in `config.py`. Key settings:

| Setting | Default | Description |
|---------|---------|-------------|
| `MIMO_API_URL` | Hermes API | MiMo v2.5 endpoint |
| `MIMO_API_KEY` | - | API key |
| `REDDIT_SUBREDDITS` | 8 subreddits | Target subreddits |
| `TWITTER_SEARCH_TERMS` | 5 terms | Search queries |
| `DELAY_BETWEEN_POSTS` | 15-45 min | Anti-spam delay |
| `MAX_POSTS_PER_HOUR` | 4 | Rate limiting |
| `GITHUB_TOKEN` | - | GitHub API token |

## Platform Details

### Reddit

- Uses old.reddit.com for CDP automation
- Targets smaller, less moderated subreddits first
- Follows 10:1 rule (10 comments per post)
- Builds karma before promotional posts

### Twitter/X

- Searches for relevant discussions
- Posts replies with helpful context
- Rate-limited to avoid API costs

### LinkedIn

- Posts as HyperNexus company page
- Comments on relevant industry posts
- Uses headless browser automation

### Bluesky

- API-based posting (no CDP needed)
- Posts to both @tormentnexus and @hypernexus
- Cross-posts blog content

### Hacker News

- "Show HN" posts for major releases
- Comment engagement on relevant threads

### dev.to

- Cross-posts blog articles
- Uses API with stored credentials

### GitHub

- Stars relevant repositories
- Comments on issues
- Finds repos by topic (MCP, AI agents, LLM)

## Content Modules

### Thread Generator

Converts blog posts into Twitter/LinkedIn threads:

```python
from marketing_bot.content.thread_generator import ThreadGenerator

generator = ThreadGenerator()
tweets = generator.generate_thread_from_blog(
    blog_title="How Progressive Tool Routing Works",
    blog_content="...",
    platform="twitter",
    num_tweets=6,
)
```

### Comment Responder

Monitors and responds to comments on our posts:

```python
from marketing_bot.content.comment_responder import CommentResponder

responder = CommentResponder()
response = responder.generate_response(
    comment_text="How does this compare to LangChain?",
    original_post_text="...",
    platform="reddit",
)
```

### Newsletter Generator

Generates weekly newsletter content:

```python
from marketing_bot.content.newsletter_generator import NewsletterGenerator

generator = NewsletterGenerator()
newsletter = generator.generate_weekly_digest(
    blog_posts=[{"title": "...", "url": "..."}],
    social_highlights=["...", "..."],
)
html = generator.format_newsletter_html(newsletter)
```

### Analytics Tracker

Tracks engagement metrics across all platforms:

```python
from marketing_bot.content.analytics_tracker import AnalyticsTracker

tracker = AnalyticsTracker()
tracker.track_event("reddit", "comment", success=True)
summary = tracker.get_summary(days=7)
report = tracker.export_report(format="text")
```

## Anti-Spam Measures

1. **Rate Limiting**: Max 4 posts/hour per platform
2. **Random Delays**: 15-45 min between posts
3. **Content Variation**: LLM-generated unique content
4. **Karma Building**: Comments before promotional posts
5. **Account Rotation**: Multiple accounts per platform

## LLM Integration

Uses MiMo v2.5 (Hermes API) for:

- Generating contextual replies
- Creating article content
- Adapting tone per platform
- Avoiding repetitive content
- Generating threads from blog posts

## Monitoring

Logs are written to stdout with format:

```
[HH:MM:SS] [Platform] Message
```

Analytics data is stored in `analytics_data.json`.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Browser not connected | Start Edge with `--remote-debugging-port=9222` |
| LLM not responding | Check `MIMO_API_KEY` in config |
| Posts getting removed | See anti-spam measures |
| Rate limited | Increase `DELAY_BETWEEN_POSTS` |
| GitHub API errors | Check `GITHUB_TOKEN` in config |
