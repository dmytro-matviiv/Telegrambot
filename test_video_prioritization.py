#!/usr/bin/env python3
"""
Тест пріоритизації новин з відео
"""

import asyncio
import logging
from news_collector import NewsCollector
from telegram_publisher import TelegramPublisher

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_video_prioritization():
    """Тестує пріоритизацію новин з відео"""
    logger.info("🎥 Тестуємо пріоритизацію новин з відео...")
    
    collector = NewsCollector()
    
    # Збираємо новини
    news_list = collector.collect_all_news()
    
    if not news_list:
        logger.info("📭 Новин не знайдено")
        return
    
    logger.info(f"📰 Знайдено {len(news_list)} новин")
    
    # Розділяємо новини на групи
    news_with_video = []
    news_without_video = []
    
    for news in news_list:
        if news.get('video_url', ''):
            news_with_video.append(news)
        else:
            news_without_video.append(news)
    
    # Виводимо статистику
    logger.info(f"🎥 Новин з відео: {len(news_with_video)}")
    logger.info(f"📰 Новин без відео: {len(news_without_video)}")
    
    # Показуємо приклади новин з відео
    if news_with_video:
        logger.info("\n=== ПРИКЛАДИ НОВИН З ВІДЕО ===")
        for i, news in enumerate(news_with_video[:3]):  # Показуємо перші 3
            logger.info(f"{i+1}. {news.get('title', '')[:60]}...")
            logger.info(f"   Джерело: {news.get('source', '')}")
            logger.info(f"   Відео: {news.get('video_url', '')[:50]}...")
            logger.info("")
    
    # Показуємо приклади новин без відео
    if news_without_video:
        logger.info("\n=== ПРИКЛАДИ НОВИН БЕЗ ВІДЕО ===")
        for i, news in enumerate(news_without_video[:3]):  # Показуємо перші 3
            logger.info(f"{i+1}. {news.get('title', '')[:60]}...")
            logger.info(f"   Джерело: {news.get('source', '')}")
            logger.info("")
    
    # Симулюємо пріоритизацію як в main.py
    import random
    
    # Перемішуємо кожну групу окремо
    random.shuffle(news_with_video)
    random.shuffle(news_without_video)
    
    # Об'єднуємо: спочатку новини з відео, потім без відео
    prioritized_news = news_with_video + news_without_video
    
    logger.info(f"\n=== ПРОРІОРИТИЗОВАНИЙ СПИСОК ===")
    logger.info(f"Перші {min(5, len(prioritized_news))} новин:")
    
    for i, news in enumerate(prioritized_news[:5]):
        has_video = "🎥" if news.get('video_url', '') else "📰"
        logger.info(f"{i+1}. {has_video} {news.get('title', '')[:60]}...")
        logger.info(f"   Джерело: {news.get('source', '')}")
        if news.get('video_url', ''):
            logger.info(f"   Відео: {news.get('video_url', '')[:50]}...")
        logger.info("")
    
    logger.info("✅ Тест пріоритизації завершено")

if __name__ == "__main__":
    print("🎥 Тест пріоритизації новин з відео")
    print("=" * 50)
    
    asyncio.run(test_video_prioritization()) 