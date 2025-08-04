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
from config import CHECK_INTERVAL, MAX_POSTS_PER_CHECK

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
        """Основна функція перевірки та публікації новин"""
        try:
            logger.info("🔍 Починаємо збір новин...")
            
            # Збираємо новини
            news_list = self.collector.collect_all_news()
            
            if not news_list:
                logger.info("📭 Новин не знайдено")
                return
            
            logger.info(f"📰 Знайдено {len(news_list)} нових новин")

            # Фільтрація за часом: публікуємо лише ті, яким вже 10-20 хвилин
            now = datetime.now(timezone.utc)
            filtered_news = []
            for news in news_list:
                published_str = news.get('published', '')
                published_time = None
                if published_str:
                    published_time = parse_published_date(published_str)
                if published_time:
                    # Переконуємося, що обидві дати мають однакову timezone-aware/naive природу
                    if published_time.tzinfo is None:
                        # Якщо published_time timezone-naive, робимо її UTC
                        published_time = published_time.replace(tzinfo=timezone.utc)
                    elif now.tzinfo is None:
                        # Якщо now timezone-naive (не повинно статися), робимо її UTC
                        now = now.replace(tzinfo=timezone.utc)
                    
                    age = (now - published_time).total_seconds() / 60
                    if 10 <= age <= 30:
                        filtered_news.append(news)
                else:
                    # Якщо немає дати — додаємо, але в кінець списку
                    filtered_news.append(news)

            # Обмежуємо кількість публікацій за раз
            # Пріоритизація відео та перемішування джерел тепер відбувається в NewsCollector
            news_to_publish = filtered_news[:MAX_POSTS_PER_CHECK]
            
            # Публікуємо новини
            published_count = await self.publisher.publish_multiple_news(news_to_publish)
            
            # Позначаємо як опубліковані
            for news_item in news_to_publish:
                self.collector.mark_as_published(news_item['id'])
            
            logger.info(f"✅ Опубліковано {published_count} новин")
            
        except Exception as e:
            logger.error(f"❌ Помилка при зборі/публікації новин: {e}")

    async def test_connections(self):
        """Тестує з'єднання з усіма сервісами"""
        logger.info("🔧 Тестуємо з'єднання...")
        
        # Тестуємо Telegram
        telegram_ok = await self.publisher.test_connection()
        if telegram_ok:
            logger.info("✅ Telegram з'єднання працює")
        else:
            logger.error("❌ Помилка з'єднання з Telegram")
            return False
        
        # Тестуємо збір новин
        try:
            test_news = self.collector.collect_all_news()
            logger.info(f"✅ Збір новин працює (знайдено {len(test_news)} новин)")
        except Exception as e:
            logger.error(f"❌ Помилка збору новин: {e}")
            return False
        
        # Тестуємо API тривог
        try:
            test_alerts = await self.alerts_monitor.fetch_alerts()
            logger.info(f"✅ API тривог працює (отримано {len(test_alerts)} активних тривог)")
        except Exception as e:
            logger.error(f"❌ Помилка API тривог: {e}")
            return False
        
        return True

    async def run_once(self):
        """Запускає один цикл збору та публікації"""
        await self.check_and_publish_news()

    async def run_continuous(self):
        """Запускає безперервний цикл роботи бота"""
        self.is_running = True
        logger.info("🚀 Бот запущений в режимі безперервної роботи")
        
        # Запускаємо моніторинг тривог в окремому завданні
        alerts_task = asyncio.create_task(self.alerts_monitor.monitor(interval=60))
        logger.info("🚨 Моніторинг повітряних тривог запущений (перевірка кожні 60 сек)")
        
        # Запускаємо моніторинг меморіальних повідомлень в окремому завданні
        memorial_task = asyncio.create_task(self.memorial_scheduler.monitor_memorial_schedule(check_interval=300))
        logger.info("🕯️ Моніторинг меморіальних повідомлень запущений (перевірка кожні 5 хвилин)")
        
        while self.is_running:
            try:
                await self.check_and_publish_news()
                logger.info(f"⏰ Очікуємо {CHECK_INTERVAL} секунд до наступної перевірки...")
                await asyncio.sleep(CHECK_INTERVAL)
            except KeyboardInterrupt:
                logger.info("🛑 Отримано сигнал зупинки")
                break
            except Exception as e:
                logger.error(f"❌ Помилка в основному циклі: {e}")
                await asyncio.sleep(60)  # Чекаємо хвилину перед повторною спробою
        
        # Зупиняємо моніторинг тривог та меморіальних повідомлень
        alerts_task.cancel()
        memorial_task.cancel()
        try:
            await alerts_task
        except asyncio.CancelledError:
            logger.info("🚨 Моніторинг тривог зупинено")
        try:
            await memorial_task
        except asyncio.CancelledError:
            logger.info("🕯️ Моніторинг меморіальних повідомлень зупинено")

    def stop(self):
        """Зупиняє бота"""
        self.is_running = False
        logger.info("🛑 Бот зупинено")

async def main():
    """Головна функція"""
    bot = NewsBot()
    
    try:
        # Тестуємо з'єднання
        if not await bot.test_connections():
            logger.error("❌ Тестування з'єднань не пройшло. Перевірте налаштування.")
            return
        
        # Запускаємо бота
        await bot.run_continuous()
        
    except KeyboardInterrupt:
        logger.info("🛑 Отримано сигнал зупинки")
    except Exception as e:
        logger.error(f"❌ Критична помилка: {e}")
    finally:
        bot.stop()
        await bot.publisher.close()
        logger.info("👋 Бот завершив роботу")

if __name__ == "__main__":
    print("🇺🇦 Український новинний бот")
    print("=" * 50)
    print("Бот буде автоматично збирати новини з офіційних джерел")
    print("та публікувати їх у ваш Telegram канал.")
    print("=" * 50)
    
    # Запускаємо головну функцію
    asyncio.run(main()) 