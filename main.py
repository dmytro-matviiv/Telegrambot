import asyncio
import logging
import schedule
import time
import random
from datetime import datetime, timedelta, timezone
from news_collector import NewsCollector, parse_published_date
from telegram_publisher import TelegramPublisher
from air_alerts_monitor import AirAlertsMonitor
from memorial_messages import MemorialMessageScheduler, schedule_minute_of_silence
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

    async def check_and_publish_news(self):
        """Перевіряє та публікує новини"""
        try:
            logger.info("🔍 Перевіряємо нові новини...")
            
            # Збираємо новини
            all_news = self.collector.collect_all_news()
            
            if all_news:
                logger.info(f"📰 Знайдено {len(all_news)} нових новин")
                
                # Публікуємо перші кілька новин (максимум 3)
                news_to_publish = all_news[:3]
                logger.info(f"📤 Публікуємо {len(news_to_publish)} новин...")
                
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
        
        while True:
            try:
                await self.check_and_publish_news()
                logger.info(f"⏰ Очікую {CHECK_INTERVAL} секунд до наступної перевірки...")
                await asyncio.sleep(CHECK_INTERVAL)
            except KeyboardInterrupt:
                logger.info("🛑 Бот зупинено користувачем")
                break
            except Exception as e:
                logger.error(f"❌ Помилка: {e}")
                await asyncio.sleep(60)  # Чекаємо хвилину перед повторною спробою
        
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