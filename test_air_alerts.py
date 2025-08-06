import asyncio
import logging
from air_alerts_monitor import AirAlertsMonitor
from telegram_publisher import TelegramPublisher
from config import ALERTS_API_TOKEN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_air_alerts():
    """Тестує роботу повітряної тривоги"""
    try:
        logger.info("🧪 Тестуємо повітряну тривогу...")
        
        # Створюємо publisher
        publisher = TelegramPublisher()
        
        # Тестуємо з'єднання з Telegram
        if not await publisher.test_connection():
            logger.error("❌ Помилка з'єднання з Telegram")
            return
        
        logger.info("✅ З'єднання з Telegram успішне")
        
        # Створюємо монітор тривог
        monitor = AirAlertsMonitor(publisher)
        
        # Тестуємо отримання даних з API
        logger.info("📡 Отримуємо дані з API повітряних тривог...")
        alerts_data = await monitor.fetch_alerts()
        
        if alerts_data:
            logger.info(f"✅ Отримано дані з API: {len(alerts_data) if isinstance(alerts_data, list) else 'dict'}")
            
            # Показуємо статистику тривог
            if isinstance(alerts_data, dict) and 'alerts' in alerts_data:
                alerts_list = alerts_data['alerts']
            elif isinstance(alerts_data, list):
                alerts_list = alerts_data
            else:
                alerts_list = []
            
            air_raid_count = 0
            valid_alerts = []
            
            for alert in alerts_list:
                if monitor.is_valid_alert(alert):
                    air_raid_count += 1
                    valid_alerts.append(alert)
            
            logger.info(f"📊 Статистика тривог:")
            logger.info(f"   📡 Всього тривог: {len(alerts_list)}")
            logger.info(f"   🚨 Повітряних тривог: {air_raid_count}")
            logger.info(f"   ✅ Валідних тривог: {len(valid_alerts)}")
            
            if valid_alerts:
                logger.info("📍 Активні повітряні тривоги:")
                for alert in valid_alerts[:5]:  # Показуємо перші 5
                    location = alert.get('location_title', 'Невідомо')
                    started_at = alert.get('started_at', '')
                    logger.info(f"   - {location} (почалася: {started_at})")
            
            # Тестуємо надсилання повідомлення
            logger.info("📤 Тестуємо надсилання повідомлення...")
            test_message = "🧪 Тест повітряної тривоги - це тестове повідомлення"
            success = await publisher.send_simple_message(test_message)
            
            if success:
                logger.info("✅ Тестове повідомлення успішно надіслано")
            else:
                logger.error("❌ Помилка при надсиланні тестового повідомлення")
        else:
            logger.warning("⚠️ Не вдалося отримати дані з API")
        
        await publisher.close()
        
    except Exception as e:
        logger.error(f"❌ Помилка тестування: {e}")
        import traceback
        logger.error(f"Деталі помилки: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_air_alerts()) 