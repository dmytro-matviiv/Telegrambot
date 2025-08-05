# Copilot Instructions for Telegrambot

## Project Overview
This project is a Telegram bot for automatically collecting and publishing official Ukrainian news to a Telegram channel. It consists of several main modules:
- `main.py`: Entry point, orchestrates scheduling, news collection, and publishing.
- `news_collector.py`: Collects news from multiple sources (RSS and custom), deduplicates, and prepares news items.
- `telegram_publisher.py`: Handles formatting and publishing news (with images and videos) to Telegram.
- `memorial_messages.py`: Schedules and sends daily memorial messages (e.g., minute of silence at 9:00).
- `config.py`: Central configuration for sources, intervals, and limits.
- `published_news.json`: Tracks published news to avoid duplicates.

## Key Patterns & Conventions
- **News Collection**: News sources are defined in `config.py`. The collector shuffles sources and news items to ensure diversity. Deduplication is enforced via `published_news.json`.
- **Publishing**: News is formatted with emojis, hashtags, and source info. Images are attached if available; a default image is used otherwise. Videos are downloaded and uploaded to Telegram if possible.
- **Scheduling**: Uses async tasks for periodic news checks and for daily memorial messages (9:00 minute of silence).
- **Logging**: All actions and errors are logged to `bot.log`.
- **Environment**: Secrets (bot token, channel ID) are loaded from `.env` (see `env_example.txt`).

## Developer Workflows
- **Install dependencies**: `pip install -r requirements.txt`
- **Run bot**: `python main.py` or use `run_bot.bat`
- **Run tests**: Execute test files directly, e.g. `python test_alerts.py`. No unified test runner is provided.
- **Debugging**: Check `bot.log` for errors and status.
- **Add news sources**: Edit `NEWS_SOURCES` in `config.py`.
- **Change intervals/limits**: Edit `CHECK_INTERVAL`, `MAX_POSTS_PER_CHECK` in `config.py`.

## Project-Specific Details
- **Minute of Silence**: Implemented in `memorial_messages.py`, scheduled at 9:00 daily. If not working, check async scheduling in `main.py` and time window logic.
- **News Diversity**: News and sources are shuffled before publishing. If only one source dominates, check post-selection logic in `news_collector.py`.
- **Video Handling**: Videos are downloaded and uploaded to Telegram. For YouTube/Facebook/Vimeo, direct download may fail; consider using a third-party service for mp4 extraction.
- **No hardcoded secrets**: All sensitive data must be in `.env`.

## Integration Points
- **Telegram API**: Used for publishing messages, images, and videos.
- **RSS/HTTP**: For news collection from official sources.

## Example: Adding a New News Source
Edit `config.py`:
```python
NEWS_SOURCES['new_source'] = {
    'name': 'Новий ресурс',
    'rss': 'https://example.com/rss',
    'website': 'https://example.com'
}
```

## Example: Custom News Formatting
Edit `format_news_text` in `telegram_publisher.py` to change message layout.

## References
- See `README.md` for user setup and troubleshooting.
- See `bot.log` for runtime issues.

---
For AI agents: Always preserve deduplication, shuffling, and logging logic. When in doubt, check `main.py` for orchestration and `config.py` for settings.
