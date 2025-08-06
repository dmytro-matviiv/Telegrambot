#!/usr/bin/env python3
"""
Тимчасовий тестовий обробник для публікації новин з відео
Знаходить новини і публікує першу з відео, потім завершує роботу
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timezone
from typing import List, Dict, Optional

# Додаємо шлях до поточної директорії для імпорту модулів
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import BOT_TOKEN, CHANNEL_ID, NEWS_SOURCES
from news_collector import NewsCollector
from telegram_publisher import TelegramPublisher

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class TestVideoHandler:
    def __init__(self):
        self.news_collector = NewsCollector()
        self.telegram_publisher = TelegramPublisher()
        
    async def find_and_publish_video_news(self):
        """Знаходить новини і публікує першу з відео"""
        try:
            logger.info("🔍 Починаю пошук новин...")
            
            # Збираємо всі новини без фільтрації
            all_news = []
            sources_with_news = []
            
            # Збираємо новини з кожного джерела
            for source_key, source_info in NEWS_SOURCES.items():
                try:
                    news = self.news_collector.get_news_from_rss(source_key, source_info)
                    if news:
                        sources_with_news.append((source_key, source_info, news))
                        all_news.extend(news)
                        logger.info(f"✅ {source_info['name']}: знайдено {len(news)} новин")
                except Exception as e:
                    logger.error(f"❗ Помилка при зборі новин з {source_key}: {e}")
            
            logger.info(f"📰 Знайдено {len(all_news)} новин загалом")
            
            if not all_news:
                logger.warning("⚠️ Новини не знайдено")
                return False
            
            # Шукаємо новини з відео
            news_with_video = []
            for news in all_news:
                video_url = news.get('video_url', '')
                if video_url:
                    news_with_video.append(news)
                    logger.info(f"🎥 Знайдено новину з відео: {news.get('title', '')[:50]}...")
            
            if not news_with_video:
                logger.warning("⚠️ Новини з відео не знайдено")
                return False
            
            # Беремо першу новину з відео
            first_video_news = news_with_video[0]
            logger.info(f"📤 Публікую першу новину з відео: {first_video_news.get('title', '')[:50]}...")
            
            # Публікуємо новину
            success = await self.telegram_publisher.publish_news(first_video_news)
            
            if success:
                logger.info("✅ Новину з відео успішно опубліковано!")
                return True
            else:
                logger.error("❌ Помилка при публікації новини з відео")
                return False
                
        except Exception as e:
            logger.error(f"❌ Помилка в тестовому обробнику: {e}")
            return False

async def main():
    """Головна функція тестового обробника"""
    logger.info("🚀 Запуск тестового обробника для новин з відео")
    
    handler = TestVideoHandler()
    
    try:
        success = await handler.find_and_publish_video_news()
        
        if success:
            logger.info("✅ Тестовий обробник успішно завершив роботу")
        else:
            logger.warning("⚠️ Тестовий обробник завершив роботу без публікації")
            
    except KeyboardInterrupt:
        logger.info("🛑 Тестовий обробник зупинено користувачем")
    except Exception as e:
        logger.error(f"❌ Критична помилка в тестовому обробнику: {e}")
    finally:
        # Закриваємо сесії
        try:
            if hasattr(handler.news_collector, 'session') and handler.news_collector.session:
                await handler.news_collector.session.close()
        except:
            pass
        try:
            if hasattr(handler.telegram_publisher, 'session') and handler.telegram_publisher.session:
                await handler.telegram_publisher.session.close()
        except:
            pass
        logger.info("👋 Тестовий обробник завершив роботу")

if __name__ == "__main__":
    asyncio.run(main()) 