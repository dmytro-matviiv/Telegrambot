#!/usr/bin/env python3
"""
Тест швидкості реакції на тривоги
"""

import asyncio
import logging
from air_alerts_monitor import AirAlertsMonitor
from telegram_publisher import TelegramPublisher
from datetime import datetime

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_alerts_timing():
    """Тестує швидкість реакції на тривоги"""
    logger.info("🚨 Тестуємо швидкість реакції на тривоги...")
    
    publisher = TelegramPublisher()
    monitor = AirAlertsMonitor(publisher)
    
    # Тестуємо отримання даних
    alerts_data = await monitor.fetch_alerts()
    
    if not alerts_data:
        logger.error("❌ Не вдалося отримати дані тривог")
        return
    
    logger.info("✅ Отримано дані з API тривог")
    
    # Аналізуємо активні тривоги
    if isinstance(alerts_data, dict) and 'alerts' in alerts_data:
        alerts_list = alerts_data['alerts']
    elif isinstance(alerts_data, list):
        alerts_list = alerts_data
    else:
        logger.error("❌ Неочікуваний формат даних")
        return
    
    logger.info(f"📊 Знайдено {len(alerts_list)} тривог в API")
    
    # Перевіряємо валідні тривоги
    valid_alerts = []
    for alert in alerts_list:
        if monitor.is_valid_alert(alert):
            valid_alerts.append(alert)
    
    logger.info(f"✅ Валідних тривог: {len(valid_alerts)}")
    
    # Показуємо деталі кожної валідної тривоги
    for i, alert in enumerate(valid_alerts):
        location = alert.get('location_title', '')
        started_at = alert.get('started_at', '')
        finished_at = alert.get('finished_at', '')
        
        logger.info(f"\n{i+1}. Тривога: {location}")
        logger.info(f"   Початок: {started_at}")
        logger.info(f"   Завершення: {finished_at}")
        
        # Розраховуємо час від початку
        if started_at:
            try:
                started_dt = datetime.strptime(started_at[:19], "%Y-%m-%dT%H:%M:%S")
                now = datetime.utcnow()
                delta = (now - started_dt).total_seconds() / 60
                logger.info(f"   Від початку: {delta:.1f} хвилин")
                
                if delta > 10:
                    logger.warning(f"   ⚠️ Тривога старіша за 10 хв - буде пропущена")
                elif delta > 2:
                    logger.warning(f"   ⚠️ Тривога з затримкою {delta:.1f} хв - буде надіслана")
                else:
                    logger.info(f"   ✅ Тривога актуальна - буде надіслана")
            except Exception as e:
                logger.error(f"   ❌ Помилка парсингу часу: {e}")
    
    # Тестуємо один цикл моніторингу
    logger.info("\n🔄 Тестуємо один цикл моніторингу...")
    
    # Симулюємо початковий стан
    monitor.prev_alerts = set()
    
    # Запускаємо один цикл
    alerts_data = await monitor.fetch_alerts()
    if isinstance(alerts_data, dict) and 'alerts' in alerts_data:
        alerts_list = alerts_data['alerts']
    elif isinstance(alerts_data, list):
        alerts_list = alerts_data
    else:
        logger.error("❌ Помилка отримання даних для тесту")
        return
    
    # Групуємо тривоги
    current_alerts_dict = {}
    for alert in alerts_list:
        if not monitor.is_valid_alert(alert):
            continue
            
        location_title = alert.get('location_title', '')
        alert_type = alert.get('alert_type', '')
        finished_at = alert.get('finished_at')
        
        if location_title and not finished_at:
            current_alerts_dict[(location_title, alert_type)] = alert
    
    current_alerts = set(current_alerts_dict.keys())
    new_alerts = current_alerts - monitor.prev_alerts
    
    logger.info(f"📊 Нових тривог для надсилання: {len(new_alerts)}")
    
    for key in new_alerts:
        alert = current_alerts_dict[key]
        location = alert.get('location_title', '')
        started_at = alert.get('started_at', '')
        
        logger.info(f"🎯 Тривога: {location}")
        if started_at:
            try:
                started_dt = datetime.strptime(started_at[:19], "%Y-%m-%dT%H:%M:%S")
                now = datetime.utcnow()
                delta = (now - started_dt).total_seconds() / 60
                logger.info(f"   Час від початку: {delta:.1f} хв")
            except Exception as e:
                logger.error(f"   Помилка парсингу часу: {e}")
    
    logger.info("✅ Тест завершено")

if __name__ == "__main__":
    print("🚨 Тест швидкості реакції на тривоги")
    print("=" * 50)
    
    asyncio.run(test_alerts_timing()) 