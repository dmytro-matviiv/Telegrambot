#!/usr/bin/env python3
"""
Тест функціональності перекладу та відео
"""

import asyncio
import logging
from news_collector import NewsCollector
from telegram_publisher import TelegramPublisher

# Налаштування логування
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_translation_and_video():
    """Тестує функціональність перекладу та відео"""
    
    # Створюємо екземпляри
    collector = NewsCollector()
    publisher = TelegramPublisher()
    
    # Тестуємо з'єднання з Telegram
    logger.info("🔍 Тестуємо з'єднання з Telegram...")
    if not await publisher.test_connection():
        logger.error("❌ Не вдалося підключитися до Telegram")
        return
    
    logger.info("✅ Telegram з'єднання працює")
    
    # Тестуємо переклад
    logger.info("🔍 Тестуємо функцію перекладу...")
    
    test_texts = [
        "Ukraine war latest news",
        "Russia attacks Ukrainian cities",
        "Zelensky says Ukraine will win",
        "Breaking news from Kyiv",
        "Ukrainian military reports success"
    ]
    
    for text in test_texts:
        translated = collector.translate_text(text)
        logger.info(f"Оригінал: {text}")
        logger.info(f"Переклад: {translated}")
        logger.info("---")
    
    # Тестуємо визначення англійської мови
    logger.info("🔍 Тестуємо визначення англійської мови...")
    
    test_language_texts = [
        ("Ukraine war latest news", True),
        ("Україна веде війну з Росією", False),
        ("Breaking news from Kyiv", True),
        ("Новини з Києва", False),
        ("Russia attacks Ukrainian cities", True)
    ]
    
    for text, expected in test_language_texts:
        is_english = collector.is_english_text(text)
        status = "✅" if is_english == expected else "❌"
        logger.info(f"{status} '{text}' -> англійська: {is_english} (очікувано: {expected})")
    
    # Тестуємо витягування відео URL
    logger.info("🔍 Тестуємо витягування відео URL...")
    
    # Мок дані для тестування
    mock_entry = {
        'summary': '<iframe src="https://www.youtube.com/embed/abc123"></iframe>',
        'link': 'https://example.com/article'
    }
    
    video_url = collector.extract_video_url(mock_entry, 'https://example.com/article')
    if video_url:
        logger.info(f"✅ Знайдено відео URL: {video_url}")
    else:
        logger.info("❌ Відео URL не знайдено")
    
    await publisher.close()
    logger.info("✅ Тест завершено")

if __name__ == "__main__":
    asyncio.run(test_translation_and_video()) 