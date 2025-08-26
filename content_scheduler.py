import asyncio
import logging
from datetime import datetime, time, timedelta
from typing import List, Dict, Optional, Tuple
import pytz

from telegram_publisher import TelegramPublisher
from news_collector import NewsCollector
from video_sources import fetch_recent_videos


logger = logging.getLogger(__name__)


class ContentScheduler:
    """
    Schedules warm‑tone, slot‑based posting for the channel (Kyiv timezone).
    Keeps logic simple: at each slot, fetch fresh mixed news and publish
    1–2 items with hashtags and CTA, avoiding duplicates via NewsCollector.
    """

    def __init__(self, publisher: TelegramPublisher, collector: NewsCollector):
        self.publisher = publisher
        self.collector = collector
        self.kyiv_tz = pytz.timezone('Europe/Kiev')
        # Default slot schedule: (hour, minute, label)
        self.slots: List[Tuple[int, int, str]] = [
            (7, 45, 'morning_digest'),
            (12, 30, 'midday_updates'),
            (16, 30, 'world_economy'),
            (20, 30, 'evening_summary'),
        ]
        # How many news to publish per slot
        self.items_per_slot = 1

    def _now_kyiv(self) -> datetime:
        return datetime.now(self.kyiv_tz)

    def _next_slot_dt(self) -> datetime:
        now = self._now_kyiv()
        today = now.date()
        # Build candidate datetimes for today
        candidates = []
        for h, m, _ in self.slots:
            candidates.append(self.kyiv_tz.localize(datetime.combine(today, time(h, m))))
        # Find the next slot time >= now; if none, choose first slot tomorrow
        for dt in sorted(candidates):
            if dt >= now - timedelta(seconds=5):
                return dt
        # Tomorrow first slot
        h, m, _ = sorted(self.slots)[0]
        tomorrow = today + timedelta(days=1)
        return self.kyiv_tz.localize(datetime.combine(tomorrow, time(h, m)))

    def _slot_for_time(self, dt: datetime) -> Optional[str]:
        for h, m, label in self.slots:
            if dt.hour == h and dt.minute == m:
                return label
        return None

    def _build_hashtags(self, label: str, news_item: Dict) -> str:
        category = news_item.get('category', 'unknown')
        mapping = {
            'world': '#світ',
            'ukraine': '#україна',
            'inventions': '#техно',
            'celebrity': '#суспільство',
            'war': '#фронт',
        }
        slot_tag = {
            'morning_digest': '#ранковий_дайджест',
            'midday_updates': '#апдейт',
            'world_economy': '#економіка',
            'evening_summary': '#вечірній_підсумок',
        }.get(label, '')
        cat_tag = mapping.get(category, '#новини')
        tags = ' '.join(t for t in [slot_tag, cat_tag] if t)
        return tags

    def _append_warm_cta(self, news_item: Dict, label: str) -> Dict:
        # Clone and enrich description with hashtags and CTA
        item = dict(news_item)
        description = item.get('description') or ''
        tags = self._build_hashtags(label, item)
        cta = "\n\nЯкщо було корисно — перешліть другу. Це допомагає нам рости."
        extra = f"\n\n{tags}\n{cta}" if tags else f"\n\n{cta}"
        # Keep description concise; publisher handles truncation too
        item['description'] = (description or '').strip() + extra
        return item

    def _pick_news_for_slot(self, all_news: List[Dict], label: str) -> List[Dict]:
        if not all_news:
            return []
        # Відео пріоритет прибрано
        # Prefer categories based on slot
        preferred_order = {
            'morning_digest': ['ukraine', 'war', 'world'],
            'midday_updates': ['ukraine', 'world', 'war'],
            'world_economy': ['world', 'inventions', 'ukraine'],
            'evening_summary': ['ukraine', 'world', 'war'],
        }.get(label, ['ukraine', 'world', 'war', 'inventions', 'celebrity'])

        # Stable selection: first items matching preferred categories
        selected: List[Dict] = []
        for category in preferred_order:
            for item in all_news:
                if item.get('category') == category and item not in selected:
                    selected.append(item)
                    if len(selected) >= self.items_per_slot:
                        return selected
        # Fallback: take first available
        return selected or all_news[: self.items_per_slot]

    async def _publish_slot(self, label: str) -> None:
        try:
            logger.info(f"[Scheduler] ⏱️ Slot '{label}': collecting news…")
            news = self.collector.collect_all_news()
            picks = self._pick_news_for_slot(news, label)
            # Fallback на YouTube прибрано
            if not picks:
                logger.info(f"[Scheduler] No news to publish for slot '{label}'")
                return

            for item in picks:
                enriched = self._append_warm_cta(item, label)
                success = await self.publisher.publish_news(enriched)
                if success:
                    news_id = f"{item['source_key']}_{item['id']}"
                    self.collector.mark_as_published(news_id, item['source_key'])
                    logger.info(f"[Scheduler] ✅ Published for slot '{label}': {item.get('title','')[:80]}…")
                else:
                    logger.warning(f"[Scheduler] ❌ Failed to publish for slot '{label}'")
        except Exception as e:
            logger.error(f"[Scheduler] Exception in slot '{label}': {e}")

    async def monitor_schedule(self) -> None:
        logger.info("[Scheduler] 🚀 ContentScheduler started (Kyiv timezone)")
        while True:
            try:
                next_dt = self._next_slot_dt()
                now = self._now_kyiv()
                sleep_seconds = max(1, int((next_dt - now).total_seconds()))
                logger.info(f"[Scheduler] Next slot at {next_dt.strftime('%Y-%m-%d %H:%M')} (sleep {sleep_seconds}s)")
                await asyncio.sleep(sleep_seconds)

                # Small alignment window to avoid drift
                current = self._now_kyiv()
                label = self._slot_for_time(current)
                if label:
                    await self._publish_slot(label)
                else:
                    logger.debug("[Scheduler] Woke up outside a labeled slot; continuing…")
                    await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"[Scheduler] Monitor loop error: {e}")
                await asyncio.sleep(10)


