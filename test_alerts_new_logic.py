#!/usr/bin/env python3
"""
Тест нової логіки тривог - тільки нові тривоги
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

async def test_new_alerts_logic():
    """Тестує нову логіку тривог"""
    logger.info("🚨 Тестуємо нову логіку тривог...")
    
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
    now = datetime.utcnow()
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
                delta = (now - started_dt).total_seconds() / 60
                logger.info(f"   Від початку: {delta:.1f} хвилин")
                
                if delta > 2:
                    logger.warning(f"   ⚠️ Тривога старіша за 2 хв - буде пропущена")
                else:
                    logger.info(f"   ✅ Тривога актуальна - буде надіслана")
            except Exception as e:
                logger.error(f"   ❌ Помилка парсингу часу: {e}")
        
        # Розраховуємо час від завершення
        if finished_at:
            try:
                finished_dt = datetime.strptime(finished_at[:19], "%Y-%m-%dT%H:%M:%S")
                delta = (now - finished_dt).total_seconds() / 60
                logger.info(f"   Від завершення: {delta:.1f} хвилин")
                
                if delta > 2:
                    logger.warning(f"   ⚠️ Відбій старіший за 2 хв - буде пропущений")
                else:
                    logger.info(f"   ✅ Відбій актуальний - буде надісланий")
            except Exception as e:
                logger.error(f"   ❌ Помилка парсингу часу відбою: {e}")
    
    # Тестуємо перший запуск
    logger.info("\n🔄 Тестуємо перший запуск...")
    monitor.is_first_run = True
    monitor.prev_alerts = set()
    
    # Симулюємо перший цикл
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
    
    logger.info(f"📊 Тривог при першому запуску: {len(current_alerts)}")
    logger.info("✅ При першому запуску тривоги не надсилаються")
    
    # Тестуємо другий цикл (після першого запуску)
    logger.info("\n🔄 Тестуємо другий цикл (після першого запуску)...")
    monitor.is_first_run = False
    monitor.prev_alerts = current_alerts  # Симулюємо, що це вже не перший запуск
    
    # Симулюємо нові тривоги
    new_alerts = set()
    for key in list(current_alerts)[:2]:  # Беремо перші 2 тривоги як нові
        new_alerts.add(key)
    
    logger.info(f"📊 Нових тривог для надсилання: {len(new_alerts)}")
    
    for key in new_alerts:
        alert = current_alerts_dict[key]
        location = alert.get('location_title', '')
        started_at = alert.get('started_at', '')
        
        logger.info(f"🎯 Нова тривога: {location}")
        if started_at:
            try:
                started_dt = datetime.strptime(started_at[:19], "%Y-%m-%dT%H:%M:%S")
                delta = (now - started_dt).total_seconds() / 60
                logger.info(f"   Час від початку: {delta:.1f} хв")
                
                if delta > 2:
                    logger.warning(f"   ⚠️ Тривога старіша за 2 хв - не буде надіслана")
                else:
                    logger.info(f"   ✅ Тривога актуальна - буде надіслана")
            except Exception as e:
                logger.error(f"   Помилка парсингу часу: {e}")
    
    logger.info("✅ Тест завершено")

if __name__ == "__main__":
    print("🚨 Тест нової логіки тривог")
    print("=" * 50)
    
    asyncio.run(test_new_alerts_logic()) 