#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тестовий скрипт для перевірки нової логіки збору новин та меморіальних повідомлень
"""

import asyncio
import logging
from datetime import datetime, time
from news_collector import NewsCollector
from telegram_publisher import TelegramPublisher
from memorial_messages import MemorialMessageScheduler

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_news_collection():
    """Тестує нову логіку збору новин"""
    logger.info("🧪 Тестування нової логіки збору новин...")
    
    collector = NewsCollector()
    
    # Збираємо новини з новою логікою
    news_list = collector.collect_all_news()
    
    if not news_list:
        logger.warning("⚠️ Новин не знайдено")
        return
    
    # Аналізуємо результати
    sources_count = {}
    video_count = 0
    
    for news in news_list:
        source = news.get('source', 'Unknown')
        sources_count[source] = sources_count.get(source, 0) + 1
        
        if news.get('video_url', ''):
            video_count += 1
    
    logger.info("📊 Результати тестування збору новин:")
    logger.info(f"   📰 Всього новин: {len(news_list)}")
    logger.info(f"   🎥 Новин з відео: {video_count}")
    logger.info(f"   📋 Розподіл по джерелах:")
    
    for source, count in sources_count.items():
        logger.info(f"      - {source}: {count} новин")
    
    # Перевіряємо чи новини з відео йдуть першими
    first_5_with_video = sum(1 for news in news_list[:5] if news.get('video_url', ''))
    logger.info(f"   🎯 З перших 5 новин мають відео: {first_5_with_video}")
    
    return news_list

async def test_memorial_messages():
    """Тестує систему меморіальних повідомлень"""
    logger.info("🧪 Тестування системи меморіальних повідомлень...")
    
    # Створюємо фейковий publisher для тестування
    class FakePublisher:
        async def send_simple_message(self, text):
            logger.info(f"📤 Тестове повідомлення:\n{text}")
            return True
    
    fake_publisher = FakePublisher()
    scheduler = MemorialMessageScheduler(fake_publisher)
    
    # Тестуємо генерацію повідомлень
    for i in range(3):
        message = scheduler.get_random_memorial_message()
        logger.info(f"🕯️ Приклад меморіального повідомлення #{i+1}:")
        logger.info(f"   {message[:100]}...")
    
    # Тестуємо логіку часу
    current_time = datetime.now().time()
    should_send = scheduler.should_send_memorial_message()
    
    logger.info(f"⏰ Поточний час: {current_time}")
    logger.info(f"🕯️ Чи потрібно надсилати меморіальне повідомлення: {should_send}")
    
    # Примусово надсилаємо тестове повідомлення
    logger.info("📤 Надсилаємо тестове меморіальне повідомлення...")
    await scheduler.send_memorial_message()

async def test_source_diversity():
    """Тестує різноманітність джерел"""
    logger.info("🧪 Тестування різноманітності джерел...")
    
    collector = NewsCollector()
    
    # Збираємо новини кілька разів
    all_sources = []
    
    for i in range(3):
        logger.info(f"🔄 Збір новин #{i+1}...")
        news_list = collector.collect_all_news()
        
        if news_list:
            sources_in_order = [news.get('source', 'Unknown') for news in news_list[:5]]
            all_sources.append(sources_in_order)
            logger.info(f"   📋 Порядок джерел: {sources_in_order}")
        
        await asyncio.sleep(2)  # Невелика пауза між зборами
    
    # Аналізуємо різноманітність
    if all_sources:
        logger.info("📊 Аналіз різноманітності:")
        for i, sources in enumerate(all_sources):
            unique_sources = len(set(sources))
            logger.info(f"   Збір #{i+1}: {unique_sources} унікальних джерел з {len(sources)}")

async def main():
    """Головна функція тестування"""
    logger.info("🚀 Запуск тестування нової логіки бота")
    logger.info("=" * 60)
    
    try:
        # Тест 1: Збір новин
        await test_news_collection()
        logger.info("=" * 60)
        
        # Тест 2: Меморіальні повідомлення
        await test_memorial_messages()
        logger.info("=" * 60)
        
        # Тест 3: Різноманітність джерел
        await test_source_diversity()
        logger.info("=" * 60)
        
        logger.info("✅ Всі тести завершено успішно!")
        
    except Exception as e:
        logger.error(f"❌ Помилка під час тестування: {e}")
        raise

if __name__ == "__main__":
    print("🇺🇦 Тестування покращеної логіки новинного бота")
    print("=" * 60)
    
    # Запускаємо тести
    asyncio.run(main())