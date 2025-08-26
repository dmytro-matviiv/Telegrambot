import asyncio
import logging
from datetime import datetime, time, timedelta
import pytz
from typing import List
from telegram_publisher import TelegramPublisher
from news_collector import NewsCollector
from config import CHANNEL_ID

logger = logging.getLogger(__name__)


class ContentScheduler:
    def __init__(self, publisher: TelegramPublisher, news_collector: NewsCollector):
        self.publisher = publisher
        self.news_collector = news_collector
        self.channel_id = CHANNEL_ID
        self.tz = pytz.timezone('Europe/Kiev')

        # Розклад публікацій (Київ) - тільки з 05:00 до 21:00
        self.publish_slots = [
            (7, 45),   # Ранок
            (12, 30),  # Обід
            (16, 30),  # Вечір
            (20, 0),   # Вечір (останній пост)
        ]

    def now(self):
        return datetime.now(self.tz)

    def local_dt(self, h: int, m: int, day_offset: int = 0):
        d = (self.now().date() + timedelta(days=day_offset))
        return self.tz.localize(datetime.combine(d, time(h, m)))

    def next_fire(self) -> datetime:
        now = self.now()
        # Кандидати сьогодні і завтра
        candidates: List[datetime] = []
        for h, m in self.publish_slots:
            candidates.append(self.local_dt(h, m, 0))
            candidates.append(self.local_dt(h, m, 1))
        
        # Обрати найближчий у майбутньому
        for dt in sorted(candidates):
            if dt > now + timedelta(seconds=2):
                return dt
        # Запасний варіант — завтра перший слот
        h, m = self.publish_slots[0]
        return self.local_dt(h, m, 1)

    async def publish_scheduled_content(self):
        try:
            # Перевірити час - не публікувати з 21:00 до 05:00
            current_hour = self.now().hour
            if current_hour >= 21 or current_hour < 5:
                logger.info(f"🌙 Нічний час ({current_hour}:00) - новини не публікуються")
                return
            
            # Отримати свіжі новини
            news_items = self.news_collector.collect_all_news()
            
            if not news_items:
                logger.warning("📰 Немає свіжих новин для публікації")
                return

            # Опублікувати першу новину
            news_item = news_items[0]
            await self.publisher.publish_news(news_item)
            logger.info(f"📰 Опубліковано за розкладом: {news_item['title'][:50]}...")
            
        except Exception as e:
            logger.error(f"❌ Помилка публікації за розкладом: {e}")

    async def monitor_schedule(self):
        logger.info("🚀 Запущено ContentScheduler")
        while True:
            try:
                nxt = self.next_fire()
                now = self.now()
                sleep_s = max(1, int((nxt - now).total_seconds()))
                logger.info(f"📅 Next publish at {nxt.strftime('%Y-%m-%d %H:%M')}, sleep {sleep_s}s")
                await asyncio.sleep(sleep_s)

                # Перевірити, чи настав час публікації
                current = self.now()
                for h, m in self.publish_slots:
                    if current.hour == h and current.minute == m:
                        await self.publish_scheduled_content()
                        break
                        
            except Exception as e:
                logger.error(f"❌ Помилка в ContentScheduler: {e}")
                await asyncio.sleep(10)
