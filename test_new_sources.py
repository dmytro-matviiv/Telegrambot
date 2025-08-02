#!/usr/bin/env python3
"""
Тестовий скрипт для перевірки нових джерел новин
"""

import asyncio
import logging
from news_collector import NewsCollector
from telegram_publisher import TelegramPublisher
from config import NEWS_SOURCES

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_news_sources():
    """Тестує нові джерела новин"""
    collector = NewsCollector()
    publisher = TelegramPublisher()
    
    logger.info("🔍 Тестуємо нові джерела новин...")
    
    # Тестуємо з'єднання з Telegram
    telegram_ok = await publisher.test_connection()
    if not telegram_ok:
        logger.error("❌ Помилка з'єднання з Telegram")
        return
    
    logger.info("✅ Telegram з'єднання працює")
    
    # Тестуємо кожне джерело окремо
    for source_key, source_info in NEWS_SOURCES.items():
        logger.info(f"📰 Тестуємо {source_info['name']}...")
        
        try:
            news = collector.get_news_from_rss(source_key, source_info)
            if news:
                logger.info(f"✅ {source_info['name']}: знайдено {len(news)} новин")
                # Показуємо першу новину як приклад
                if news:
                    first_news = news[0]
                    logger.info(f"   Приклад: {first_news.get('title', '')[:100]}...")
            else:
                logger.warning(f"⚠️ {source_info['name']}: новин не знайдено")
        except Exception as e:
            logger.error(f"❌ {source_info['name']}: помилка - {e}")
    
    # Тестуємо загальний збір новин
    logger.info("🔍 Тестуємо загальний збір новин...")
    try:
        all_news = collector.collect_all_news()
        logger.info(f"✅ Загалом знайдено {len(all_news)} новин")
        
        # Показуємо статистику по джерелах
        source_stats = {}
        for news in all_news:
            source = news.get('source', 'Невідомо')
            source_stats[source] = source_stats.get(source, 0) + 1
        
        logger.info("📊 Статистика по джерелах:")
        for source, count in source_stats.items():
            logger.info(f"   {source}: {count} новин")
            
    except Exception as e:
        logger.error(f"❌ Помилка при загальному зборі новин: {e}")
    
    await publisher.close()

if __name__ == "__main__":
    asyncio.run(test_news_sources()) 