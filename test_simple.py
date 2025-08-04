#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Простий тест без емодзі для перевірки логіки
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
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Імітація TelegramPublisher для тестування
class FakePublisher:
    async def send_simple_message(self, text):
        logger.info("Testove memorialne povidomlennya:")
        logger.info("-" * 50)
        logger.info(text)
        logger.info("-" * 50)
        return True

async def test_memorial_messages():
    """Тестує систему меморіальних повідомлень"""
    logger.info("Testuvannya systemy memorialnyh povidomlen...")
    
    try:
        from memorial_messages import MemorialMessageScheduler
        
        fake_publisher = FakePublisher()
        scheduler = MemorialMessageScheduler(fake_publisher)
        
        # Тестуємо генерацію повідомлень
        logger.info("Testuvannya generaciyi riznyh memorialnyh povidomlen:")
        
        for i in range(3):
            message = scheduler.get_random_memorial_message()
            logger.info(f"Pryklad #{i+1}:")
            logger.info(f"   Dovzhyna: {len(message)} symvoliv")
            logger.info(f"   Pochatok: {message[:80]}...")
        
        # Тестуємо логіку часу
        current_time = datetime.now().time()
        should_send = scheduler.should_send_memorial_message()
        
        logger.info(f"Potochnyj chas: {current_time}")
        logger.info(f"Chy potribno nadsylaty memorialne povidomlennya: {should_send}")
        
        # Пояснюємо логіку
        if time(9, 0) <= current_time <= time(9, 30):
            logger.info("Zaraz chas dlya memorialnyh povidomlen (9:00-9:30)")
        else:
            logger.info("Zaraz ne chas dlya memorialnyh povidomlen (potribno 9:00-9:30)")
        
        # Примусово надсилаємо тестове повідомлення
        logger.info("Nadsylayemo testove memorialne povidomlennya...")
        success = await scheduler.send_memorial_message()
        
        if success:
            logger.info("Testove povidomlennya nadislano uspishno")
        else:
            logger.error("Pomylka pry nadsylanni testovogo povidomlennya")
        
        return True
        
    except ImportError as e:
        logger.error(f"Ne vdalosya importuvaty memorial_messages: {e}")
        return False
    except Exception as e:
        logger.error(f"Pomylka pid chas testuvannya: {e}")
        return False

async def main():
    """Головна функція тестування"""
    logger.info("Zapusk testuvannya memorialnyh povidomlen")
    logger.info("=" * 60)
    
    try:
        success = await test_memorial_messages()
        
        if success:
            logger.info("=" * 60)
            logger.info("Test memorialnyh povidomlen zaversheno uspishno!")
        else:
            logger.error("Test ne projshov")
            
    except Exception as e:
        logger.error(f"Krytychna pomylka: {e}")

if __name__ == "__main__":
    print("Testuvannya memorialnyh povidomlen")
    print("=" * 60)
    
    # Запускаємо тест
    asyncio.run(main())