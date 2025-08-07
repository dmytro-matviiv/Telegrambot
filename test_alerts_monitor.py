#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from air_alerts_monitor import AirAlertsMonitor
from telegram_publisher import TelegramPublisher

# Налаштування логування
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_alerts_monitor():
    """Тестує монітор повітряних тривог"""
    try:
        logger.info("🧪 Тестуємо монітор повітряних тривог...")
        
        # Створюємо publisher
        publisher = TelegramPublisher()
        
        # Тестуємо з'єднання
        if not await publisher.test_connection():
            logger.error("❌ Помилка підключення до Telegram")
            return
        
        logger.info("✅ Підключення до Telegram успішне")
        
        # Створюємо монітор
        monitor = AirAlertsMonitor(publisher)
        
        # Тестуємо отримання даних
        logger.info("📡 Отримуємо дані з API...")
        alerts_data = await monitor.fetch_alerts()
        
        if alerts_data:
            logger.info(f"✅ Отримано дані з API")
            
            # Показуємо статистику
            if isinstance(alerts_data, dict) and 'alerts' in alerts_data:
                alerts_list = alerts_data['alerts']
            elif isinstance(alerts_data, list):
                alerts_list = alerts_data
            else:
                alerts_list = []
            
            logger.info(f"📊 Всього тривог: {len(alerts_list)}")
            
            # Показуємо активні повітряні тривоги
            active_air_raids = []
            for alert in alerts_list:
                if monitor.is_valid_alert(alert):
                    active_air_raids.append(alert)
            
            logger.info(f"🚨 Активних повітряних тривог: {len(active_air_raids)}")
            
            if active_air_raids:
                logger.info("📍 Активні тривоги:")
                for alert in active_air_raids:
                    location = alert.get('location_title', 'Невідомо')
                    started_at = alert.get('started_at', '')
                    logger.info(f"   - {location} (почалася: {started_at})")
            
            # Тестуємо надсилання повідомлення
            logger.info("📤 Тестуємо надсилання повідомлення...")
            test_message = "🚨 <b>Повітряна тривога</b> — Чернігівська область"
            success = await publisher.send_simple_message(test_message)
            
            if success:
                logger.info("✅ Тестове повідомлення успішно надіслано")
            else:
                logger.error("❌ Помилка при надсиланні")
        else:
            logger.warning("⚠️ Не вдалося отримати дані з API")
        
        await publisher.close()
        
    except Exception as e:
        logger.error(f"❌ Помилка при тестуванні: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_alerts_monitor())
