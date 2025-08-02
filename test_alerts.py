#!/usr/bin/env python3
"""
Тестовий скрипт для перевірки нової логіки тривог
"""

import asyncio
import logging
from air_alerts_monitor import AirAlertsMonitor, OCCUPIED_AND_COMBAT_AREAS
from telegram_publisher import TelegramPublisher

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_alerts_logic():
    """Тестує нову логіку тривог"""
    publisher = TelegramPublisher()
    monitor = AirAlertsMonitor(publisher)
    
    logger.info("🔍 Тестуємо нову логіку тривог...")
    
    # Тестуємо з'єднання з Telegram
    telegram_ok = await publisher.test_connection()
    if not telegram_ok:
        logger.error("❌ Помилка з'єднання з Telegram")
        return
    
    logger.info("✅ Telegram з'єднання працює")
    
    # Показуємо окуповані території
    logger.info("🚫 Окуповані території та зони бойових дій (не показувати тривоги):")
    for area in OCCUPIED_AND_COMBAT_AREAS:
        logger.info(f"   - {area}")
    
    # Тестуємо фільтрацію тривог
    test_alerts = [
        # Валідні тривоги (повинні пройти)
        {
            'location_title': 'Київська область',
            'location_type': 'oblast',
            'alert_type': 'air_raid',
            'started_at': '2024-01-01T10:00:00Z',
            'finished_at': None
        },
        {
            'location_title': 'Львівська область',
            'location_type': 'oblast',
            'alert_type': 'air_raid',
            'started_at': '2024-01-01T10:00:00Z',
            'finished_at': None
        },
        # Невалідні тривоги (повинні бути відфільтровані)
        {
            'location_title': 'Донецька область',  # Окупована територія
            'location_type': 'oblast',
            'alert_type': 'air_raid',
            'started_at': '2024-01-01T10:00:00Z',
            'finished_at': None
        },
        {
            'location_title': 'Київ',  # Місто, не область
            'location_type': 'city',
            'alert_type': 'air_raid',
            'started_at': '2024-01-01T10:00:00Z',
            'finished_at': None
        },
        {
            'location_title': 'Київська область',
            'location_type': 'oblast',
            'alert_type': 'artillery',  # Не повітряна тривога
            'started_at': '2024-01-01T10:00:00Z',
            'finished_at': None
        }
    ]
    
    logger.info("🔍 Тестуємо фільтрацію тривог...")
    valid_count = 0
    for i, alert in enumerate(test_alerts):
        is_valid = monitor.is_valid_alert(alert)
        status = "✅ ПРОЙШОВ" if is_valid else "❌ ВІДФІЛЬТРОВАНО"
        logger.info(f"   Тривога {i+1}: {status}")
        logger.info(f"      Область: {alert['location_title']}")
        logger.info(f"      Тип: {alert['location_type']}")
        logger.info(f"      Тривога: {alert['alert_type']}")
        if is_valid:
            valid_count += 1
    
    logger.info(f"📊 Результат: {valid_count}/{len(test_alerts)} тривог пройшли фільтрацію")
    
    # Тестуємо отримання реальних даних з API
    logger.info("🔍 Тестуємо отримання реальних даних з API...")
    alerts_data = await monitor.fetch_alerts()
    if alerts_data:
        logger.info("✅ Отримано дані з API")
        
        # Аналізуємо всі типи локацій
        location_types = set()
        location_titles = set()
        for alert in alerts_data.get('alerts', []):
            location_type = alert.get('location_type', '')
            location_title = alert.get('location_title', '')
            location_types.add(location_type)
            location_titles.add(location_title)
        
        logger.info(f"📊 Знайдено {len(alerts_data.get('alerts', []))} тривог")
        logger.info(f"🔍 Типи локацій в API: {sorted(location_types)}")
        logger.info(f"🔍 Приклади назв локацій: {sorted(list(location_titles)[:10])}")
        
        # Перевіряємо чи є тривоги з "район" в назві
        district_alerts = []
        for alert in alerts_data.get('alerts', []):
            location_title = alert.get('location_title', '')
            location_type = alert.get('location_type', '')
            alert_type = alert.get('alert_type', '')
            if 'район' in location_title.lower():
                district_alerts.append({
                    'title': location_title,
                    'type': location_type,
                    'alert_type': alert_type
                })
        
        if district_alerts:
            logger.info(f"⚠️ Знайдено {len(district_alerts)} тривог з 'район' в назві:")
            for alert in district_alerts:
                logger.info(f"    - {alert['title']} (тип: {alert['type']}, тривога: {alert['alert_type']})")
        else:
            logger.info("✅ Тривог з 'район' в назві не знайдено")
        
        # Фільтруємо тривоги
        valid_alerts = []
        for alert in alerts_data.get('alerts', []):
            if monitor.is_valid_alert(alert):
                valid_alerts.append(alert)
        
        logger.info(f"📊 Знайдено {len(alerts_data.get('alerts', []))} тривог, {len(valid_alerts)} пройшли фільтрацію")
        if valid_alerts:
            logger.info("✅ Активні тривоги після фільтрації:")
            for alert in valid_alerts:
                location = alert.get('location_title', '')
                location_type = alert.get('location_type', '')
                alert_type = alert.get('alert_type', '')
                logger.info(f"    - {location} (тип: {location_type}, тривога: {alert_type})")
        else:
            logger.info("❌ Немає активних тривог після фільтрації")
    else:
        logger.error("❌ Не вдалося отримати дані з API")
    
    await publisher.close()

if __name__ == "__main__":
    asyncio.run(test_alerts_logic()) 