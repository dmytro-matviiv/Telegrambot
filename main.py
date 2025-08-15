import asyncio
import logging
import schedule
import time
import random
from datetime import datetime, timedelta, timezone
from news_collector import NewsCollector, parse_published_date
from telegram_publisher import TelegramPublisher
from air_alerts_monitor import AirAlertsMonitor
from memorial_messages import MemorialMessageScheduler

from config import CHECK_INTERVAL, MAX_POSTS_PER_CHECK, CHANNEL_ID
import os

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NewsBot:
    def __init__(self):
        self.collector = NewsCollector()
        self.publisher = TelegramPublisher()
        self.alerts_monitor = AirAlertsMonitor(self.publisher)
        self.memorial_scheduler = MemorialMessageScheduler(self.publisher)
        self.is_running = False
        self.last_published_sources = []  # Трекимо останні опубліковані джерела

    def select_diverse_news(self, all_news: list, max_count: int = 3) -> list:
        """Вибір новин з різних джерел для різноманітності"""
        if not all_news:
            return []
        
        # Групуємо новини за джерелами
        news_by_source = {}
        for news in all_news:
            source = news['source_key']
            if source not in news_by_source:
                news_by_source[source] = []
            news_by_source[source].append(news)
        
        # Сортуємо джерела за пріоритетом (менше опублікованих = вищий пріоритет)
        source_priority = []
        for source, news_list in news_by_source.items():
            # Рахуємо скільки разів це джерело було опубліковано останнім
            recent_count = self.last_published_sources.count(source)
            source_priority.append((source, news_list, recent_count))
        
        # Сортуємо за пріоритетом (менше недавніх публікацій = вищий пріоритет)
        source_priority.sort(key=lambda x: x[2])
        
        # Вибір новин з різних джерел
        selected_news = []
        used_sources = set()
        
        for source, news_list, _ in source_priority:
            if len(selected_news) >= max_count:
                break
            
            # Беремо першу новину з цього джерела
            if news_list and source not in used_sources:
                selected_news.append(news_list[0])
                used_sources.add(source)
        
        # Якщо не набрали достатньо новин, додаємо з інших джерел
        if len(selected_news) < max_count:
            for source, news_list, _ in source_priority:
                if len(selected_news) >= max_count:
                    break
                
                # Додаємо додаткові новини з цього джерела
                for news in news_list[1:]:  # Починаємо з другої новини
                    if len(selected_news) >= max_count:
                        break
                    selected_news.append(news)
        
        # Оновлюємо список останніх опублікованих джерел
        for news in selected_news:
            self.last_published_sources.append(news['source_key'])
        
        # Зберігаємо тільки останні 10 джерел для пам'яті
        if len(self.last_published_sources) > 10:
            self.last_published_sources = self.last_published_sources[-10:]
        
        logger.info(f"🎯 Вибрані новини з джерел: {list(used_sources)}")
        return selected_news

    async def check_and_publish_news(self):
        """Перевіряє та публікує новини"""
        try:
            logger.info("🔍 Перевіряємо нові новини...")
            
            # Збираємо новини
            all_news = self.collector.collect_all_news()
            
            if all_news:
                logger.info(f"📰 Знайдено {len(all_news)} нових новин")
                
                # Вибір новин з різних джерел для різноманітності
                news_to_publish = self.select_diverse_news(all_news, max_count=3)
                logger.info(f"📤 Публікуємо {len(news_to_publish)} новин з різних джерел...")
                
                success = await self.publisher.publish_multiple_news(news_to_publish)
                
                if success:
                    # Позначаємо новини як опубліковані
                    for news in news_to_publish:
                        news_id = f"{news['source_key']}_{news['id']}"
                        self.collector.mark_as_published(news_id, news['source_key'])
                    
                    logger.info("✅ Новини успішно опубліковані")
                else:
                    logger.error("❌ Помилка при публікації новин")
            else:
                logger.info("📭 Нові новини не знайдено")
                
        except Exception as e:
            logger.error(f"❌ Помилка при перевірці новин: {e}")
            import traceback
            logger.error(f"Деталі помилки: {traceback.format_exc()}")

    async def run(self):
        """Запускає бота"""
        logger.info("🚀 Запуск бота новин...")
        
        # Тестуємо з'єднання
        if not await self.publisher.test_connection():
            logger.error("❌ Помилка підключення до Telegram")
            return
        
        logger.info("✅ Бот успішно запущено")
        
        # Запускаємо монітор повітряних тривог як окрему задачу
        alerts_task = asyncio.create_task(
            self.alerts_monitor.monitor(interval=60)
        )
        
        # Запускаємо меморіальний планувальник як окрему задачу
        memorial_task = asyncio.create_task(
            self.memorial_scheduler.monitor_memorial_schedule(check_interval=60)
        )
        
        while True:
            try:
                # Перевіряємо та публікуємо новини
                await self.check_and_publish_news()
                logger.info(f"⏰ Очікую {CHECK_INTERVAL} секунд до наступної перевірки...")
                await asyncio.sleep(CHECK_INTERVAL)
            except KeyboardInterrupt:
                logger.info("🛑 Бот зупинено користувачем")
                break
            except Exception as e:
                logger.error(f"❌ Помилка: {e}")
                await asyncio.sleep(60)  # Чекаємо хвилину перед повторною спробою
        
        # Скасовуємо задачі
        alerts_task.cancel()
        memorial_task.cancel()
        
        # Закриваємо з'єднання
        await self.publisher.close()
        logger.info("👋 Бот зупинено")

async def main():
    """Головна функція"""
    bot = NewsBot()
    loop = asyncio.get_event_loop()
    
    # channel_id має бути визначено тут
    channel_id = os.getenv("CHANNEL_ID")  # або інший спосіб отримання
    
    try:
        # Тестуємо з'єднання
        if not await bot.publisher.test_connection():
            logger.error("❌ Тестування з'єднань не пройшло. Перевірте налаштування.")
            return
        
        # Меморіальні повідомлення обробляються в run_continuous()
        
        # Запускаємо бота
        await bot.run()
        
    except KeyboardInterrupt:
        logger.info("🛑 Бот зупинено користувачем")
    except Exception as e:
        logger.error(f"❌ Помилка: {e}")
    finally:
        # Закриваємо з'єднання
        await bot.publisher.close()
        logger.info("👋 Бот зупинено")

if __name__ == "__main__":
    print("🇺🇦 Український новинний бот")
    print("=" * 50)
    print("Бот буде автоматично збирати новини з офіційних джерел")
    print("та публікувати їх у ваш Telegram канал.")
    print("=" * 50)
    
    # Запускаємо головну функцію
    asyncio.run(main())