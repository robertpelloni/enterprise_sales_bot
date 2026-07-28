# Marketing Bot Agent Protocol

## Purpose

This module automates social media engagement across multiple platforms to drive awareness and traffic for HyperNexus/TormentNexus.

## Agent Roles

| Agent | Platform | Responsibility |
|-------|----------|----------------|
| RedditAgent | Reddit | Comment on discussions, build karma |
| TwitterAgent | Twitter/X | Reply to relevant threads |
| LinkedInAgent | LinkedIn | Company page posts + comments |
| BlueskyAgent | Bluesky | Cross-post content |
| HackerNewsAgent | HN | Show HN posts + comments |
| DevToAgent | dev.to | Cross-post articles |

## Workflow

### Comment Mode (Default)

1. **Search**: Find relevant discussions on platform
2. **Filter**: Select posts with 2-50 comments (active but not crowded)
3. **Generate**: Use MiMo v2.5 to create contextual reply
4. **Post**: Submit reply via CDP or API
5. **Wait**: Random delay (15-45 min) before next action
6. **Repeat**: Continue until stopped

### Article Mode

1. **Generate**: Create article content with MiMo v2.5
2. **Format**: Adapt for each platform's requirements
3. **Post**: Publish to dev.to, Hashnode, LinkedIn
4. **Share**: Post links on Twitter, Bluesky, Reddit
5. **Wait**: 4-6 hours between article posts

## Content Guidelines

### DO

- Be helpful and technical
- Share genuine insights
- Answer questions directly
- Include code examples when relevant
- Link to documentation (not just landing pages)

### DON'T

- Be salesy or pushy
- Post duplicate content
- Spam multiple subreddits
- Use link shorteners
- Ignore subreddit rules

## Karma Building Strategy

### Phase 1: Build Reputation (Week 1-2)

- Comment on 50+ posts
- Answer questions helpfully
- No promotional links
- Build to 100+ karma

### Phase 2: Soft Promotion (Week 3-4)

- Continue commenting (10:1 ratio)
- Share relevant blog posts
- Post to own profile first
- Target smaller subreddits

### Phase 3: Active Promotion (Week 5+)

- Post Show HN
- Share in relevant subreddits
- Cross-post articles
- Engage with comments

## Rate Limits

| Platform | Posts/Hour | Comments/Hour | Daily Max |
|----------|------------|---------------|-----------|
| Reddit | 1 | 4 | 10 |
| Twitter | 2 | 8 | 20 |
| LinkedIn | 1 | 4 | 10 |
| Bluesky | 2 | - | 10 |
| HN | 1 | 4 | 5 |
| dev.to | 2 | - | 5 |

## Error Handling

1. **Platform Error**: Log, wait 5 min, retry
2. **LLM Error**: Use fallback template
3. **Rate Limit**: Exponential backoff
4. **Auth Error**: Alert, skip platform
5. **Network Error**: Retry 3 times, then skip

## Monitoring

### Health Checks

- Browser connection (CDP platforms)
- API authentication (Bluesky, dev.to)
- LLM availability (Hermes API)
- Account status (karma, restrictions)

### Metrics

- Posts/comments per hour
- Success rate per platform
- LLM response time
- Error rate

## Files

| File | Purpose |
|------|---------|
| `config.py` | All configuration |
| `llm.py` | LLM integration |
| `cdp_utils.py` | Browser automation |
| `platforms/*.py` | Platform-specific logic |
| `content/*.py` | Content generation |
| `orchestrator.py` | Main loop |
| `run.py` | CLI entry point |
