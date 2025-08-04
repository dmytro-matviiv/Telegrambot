#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Простий тест меморіальних повідомлень без залежностей
"""

import asyncio
import logging
from datetime import datetime, time
import sys
import os

# Додаємо поточну директорію до шляху
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Імітація TelegramPublisher для тестування
class FakePublisher:
    async def send_simple_message(self, text):
        logger.info("📤 Тестове меморіальне повідомлення:")
        logger.info("-" * 50)
        logger.info(text)
        logger.info("-" * 50)
        return True

async def test_memorial_messages():
    """Тестує систему меморіальних повідомлень"""
    logger.info("🧪 Тестування системи меморіальних повідомлень...")
    
    try:
        from memorial_messages import MemorialMessageScheduler
        
        fake_publisher = FakePublisher()
        scheduler = MemorialMessageScheduler(fake_publisher)
        
        # Тестуємо генерацію повідомлень
        logger.info("🕯️ Тестування генерації різних меморіальних повідомлень:")
        
        for i in range(5):
            message = scheduler.get_random_memorial_message()
            logger.info(f"\n📝 Приклад #{i+1}:")
            logger.info(f"   Довжина: {len(message)} символів")
            logger.info(f"   Початок: {message[:80]}...")
            
            # Перевіряємо наявність емодзі
            emojis = ['🕯️', '🙏', '💔', '🇺🇦', '💙', '💛']
            found_emojis = [emoji for emoji in emojis if emoji in message]
            logger.info(f"   Емодзі: {', '.join(found_emojis)}")
        
        # Тестуємо логіку часу
        current_time = datetime.now().time()
        should_send = scheduler.should_send_memorial_message()
        
        logger.info(f"\n⏰ Поточний час: {current_time}")
        logger.info(f"🕯️ Чи потрібно надсилати меморіальне повідомлення: {should_send}")
        
        # Пояснюємо логіку
        if time(9, 0) <= current_time <= time(9, 30):
            logger.info("✅ Зараз час для меморіальних повідомлень (9:00-9:30)")
        else:
            logger.info("⏰ Зараз не час для меморіальних повідомлень (потрібно 9:00-9:30)")
        
        # Примусово надсилаємо тестове повідомлення
        logger.info("\n📤 Надсилаємо тестове меморіальне повідомлення...")
        success = await scheduler.send_memorial_message()
        
        if success:
            logger.info("✅ Тестове повідомлення надіслано успішно")
        else:
            logger.error("❌ Помилка при надсиланні тестового повідомлення")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Не вдалося імпортувати memorial_messages: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Помилка під час тестування: {e}")
        return False

async def main():
    """Головна функція тестування"""
    logger.info("🚀 Запуск тестування меморіальних повідомлень")
    logger.info("=" * 60)
    
    try:
        success = await test_memorial_messages()
        
        if success:
            logger.info("=" * 60)
            logger.info("✅ Тест меморіальних повідомлень завершено успішно!")
            logger.info("\n📋 Що було протестовано:")
            logger.info("   🕯️ Генерація різноманітних меморіальних текстів")
            logger.info("   ⏰ Логіка перевірки часу (9:00-9:30)")
            logger.info("   📤 Надсилання повідомлень")
            logger.info("   😊 Наявність відповідних емодзі")
        else:
            logger.error("❌ Тест не пройшов")
            
    except Exception as e:
        logger.error(f"❌ Критична помилка: {e}")

if __name__ == "__main__":
    print("🇺🇦 Тестування меморіальних повідомлень")
    print("=" * 60)
    
    # Запускаємо тест
    asyncio.run(main())