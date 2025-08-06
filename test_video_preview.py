#!/usr/bin/env python3
"""
Тестовий файл для перевірки створення відео превью
"""

import asyncio
import logging
import sys
import os
from typing import Optional

# Додаємо шлях до поточної директорії для імпорту модулів
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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

async def test_video_preview():
    """Тестує створення відео превью"""
    try:
        logger.info("🎬 Тестуємо створення відео превью...")
        
        publisher = TelegramPublisher()
        
        # Тестовий iframe URL
        test_video_url = "https://tsn.ua/b-iframe-widgets/9e81fa4e-ebbc-4687-ae3d-2f730c1dd210"
        
        logger.info(f"📹 Тестуємо URL: {test_video_url}")
        
        # Створюємо відео превью
        preview_video = await publisher.create_video_preview(test_video_url)
        
        if preview_video:
            logger.info(f"✅ Відео превью створено успішно: {len(preview_video)} bytes")
            
            # Зберігаємо для перевірки
            with open('test_preview.mp4', 'wb') as f:
                f.write(preview_video)
            logger.info("💾 Відео превью збережено як test_preview.mp4")
            
            return True
        else:
            logger.warning("⚠️ Не вдалося створити відео превью")
            return False
            
    except Exception as e:
        logger.error(f"❌ Помилка при тестуванні відео превью: {e}")
        return False

async def main():
    """Головна функція тесту"""
    logger.info("🚀 Запуск тесту відео превью")
    
    try:
        success = await test_video_preview()
        
        if success:
            logger.info("✅ Тест відео превью пройшов успішно")
        else:
            logger.warning("⚠️ Тест відео превью не пройшов")
            
    except Exception as e:
        logger.error(f"❌ Критична помилка в тесті: {e}")
    finally:
        logger.info("👋 Тест завершив роботу")

if __name__ == "__main__":
    asyncio.run(main()) 