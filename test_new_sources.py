import asyncio
import logging
from news_collector import NewsCollector
from telegram_publisher import TelegramPublisher
from config import CHANNEL_ID

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_new_sources():
    """Тестує нові джерела та категорії"""
    try:
        logger.info("🧪 Тестуємо нові джерела та категорії...")
        
        # Створюємо колектор
        collector = NewsCollector()
        
        # Збираємо новини
        all_news = collector.collect_all_news()
        
        if not all_news:
            logger.warning("❌ Не знайдено новин")
            return
        
        logger.info(f"✅ Знайдено {len(all_news)} новин")
        
        # Показуємо статистику по категоріях
        categories = {}
        for news in all_news:
            category = news.get('category', 'unknown')
            if category not in categories:
                categories[category] = []
            categories[category].append(news)
        
        for category, news_list in categories.items():
            logger.info(f"📊 Категорія '{category}': {len(news_list)} новин")
            for news in news_list[:2]:  # Показуємо перші 2 новини
                logger.info(f"  - {news['title'][:50]}...")
        
        # Тестуємо публікацію першої новини
        if all_news:
            publisher = TelegramPublisher()
            
            # Тестуємо з'єднання
            if await publisher.test_connection():
                logger.info("✅ З'єднання з Telegram успішне")
                
                # Публікуємо першу новину
                first_news = all_news[0]
                logger.info(f"📤 Публікуємо: {first_news['title'][:50]}...")
                
                success = await publisher.publish_news(first_news)
                if success:
                    logger.info("✅ Новина успішно опублікована")
                else:
                    logger.error("❌ Помилка при публікації")
            else:
                logger.error("❌ Помилка з'єднання з Telegram")
        
        await publisher.close()
        
    except Exception as e:
        logger.error(f"❌ Помилка тестування: {e}")

if __name__ == "__main__":
    asyncio.run(test_new_sources()) 