import asyncio
import logging
from air_alerts_monitor import AirAlertsMonitor
from telegram_publisher import TelegramPublisher
import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_grouping_logic():
    """Тестує логіку групування відбоїв тривог"""
    try:
        # Створюємо мок publisher
        class MockPublisher:
            async def send_simple_message(self, text):
                logger.info(f"📤 Мок повідомлення: {text}")
        
        publisher = MockPublisher()
        monitor = AirAlertsMonitor(publisher)
        
        logger.info("🧪 Тестуємо логіку групування відбоїв тривог...")
        
        # Симулюємо відбої тривог в різних областях
        test_ended_alerts = [
            ('Київська область', 'air_raid'),
            ('Полтавська область', 'air_raid'),
            ('Рівненська область', 'air_raid')
        ]
        
        logger.info("📝 Додаємо відбої до буфера...")
        monitor.add_to_ended_alerts_buffer(test_ended_alerts, {})
        
        logger.info(f"📊 Буфер містить {len(monitor.ended_alerts_buffer)} відбоїв")
        for item in monitor.ended_alerts_buffer:
            logger.info(f"  - {item['location']} (час: {item['time']})")
        
        # Перевіряємо групування
        logger.info("🔍 Перевіряємо групування...")
        grouped = monitor.get_grouped_end_alerts()
        
        if grouped:
            logger.info(f"✅ Знайдено групу відбоїв: {', '.join(grouped)}")
        else:
            logger.info("❌ Група відбоїв не знайдена")
        
        # Симулюємо ще один відбій
        logger.info("📝 Додаємо ще один відбій...")
        additional_ended_alerts = [
            ('Харківська область', 'air_raid')
        ]
        monitor.add_to_ended_alerts_buffer(additional_ended_alerts, {})
        
        logger.info(f"📊 Буфер тепер містить {len(monitor.ended_alerts_buffer)} відбоїв")
        
        # Знову перевіряємо групування
        grouped = monitor.get_grouped_end_alerts()
        if grouped:
            logger.info(f"✅ Після додавання знайдено групу відбоїв: {', '.join(grouped)}")
        else:
            logger.info("❌ Група відбоїв все ще не знайдена")
        
        # Тестуємо сценарій з 2 відбоями (має групуватися)
        logger.info("📝 Додаємо ще 2 відбої для тесту групування...")
        two_more_ended_alerts = [
            ('Дніпропетровська область', 'air_raid'),
            ('Запорізька область', 'air_raid')
        ]
        monitor.add_to_ended_alerts_buffer(two_more_ended_alerts, {})
        
        logger.info(f"📊 Буфер тепер містить {len(monitor.ended_alerts_buffer)} відбоїв")
        
        # Перевіряємо групування 2 відбоїв
        grouped = monitor.get_grouped_end_alerts()
        if grouped:
            logger.info(f"✅ Знайдено групу з 2 відбоїв: {', '.join(grouped)}")
        else:
            logger.info("❌ Група з 2 відбоїв не знайдена")
        
        # Тестуємо сценарій з 1 відбоєм (не має групуватися)
        logger.info("📝 Додаємо 1 відбій (не має групуватися)...")
        single_ended_alert = [
            ('Одеська область', 'air_raid')
        ]
        monitor.add_to_ended_alerts_buffer(single_ended_alert, {})
        
        logger.info(f"📊 Буфер тепер містить {len(monitor.ended_alerts_buffer)} відбоїв")
        
        # Перевіряємо групування 1 відбою
        grouped = monitor.get_grouped_end_alerts()
        if grouped:
            logger.info(f"✅ Знайдено групу з 1 відбою: {', '.join(grouped)}")
        else:
            logger.info("❌ Група з 1 відбою не знайдена (це правильно)")
        
        # Показуємо фінальний стан буфера
        logger.info(f"📊 Фінальний стан буфера: {len(monitor.ended_alerts_buffer)} відбоїв")
        for item in monitor.ended_alerts_buffer:
            logger.info(f"  - {item['location']} (час: {item['time']})")
        
        logger.info("✅ Тест завершено")
        
        # Тестуємо реальне API
        logger.info("🌐 Тестуємо реальне API повітряних тривог...")
        try:
            alerts_data = await monitor.fetch_alerts()
            if alerts_data:
                logger.info(f"✅ API повернув дані: {type(alerts_data)}")
                if isinstance(alerts_data, dict) and 'alerts' in alerts_data:
                    alerts_list = alerts_data['alerts']
                elif isinstance(alerts_data, list):
                    alerts_list = alerts_data
                else:
                    alerts_list = []
                
                logger.info(f"📊 Знайдено {len(alerts_list)} тривог")
                
                # Показуємо кілька прикладів
                valid_count = 0
                for alert in alerts_list[:5]:
                    if monitor.is_valid_alert(alert):
                        valid_count += 1
                        location = alert.get('location_title', 'Невідомо')
                        alert_type = alert.get('alert_type', '')
                        logger.info(f"  - {location} ({alert_type})")
                
                logger.info(f"✅ Валідних тривог: {valid_count}")
            else:
                logger.warning("⚠️ API не повернув дані")
        except Exception as e:
            logger.error(f"❌ Помилка API: {e}")
            
    except Exception as e:
        logger.error(f"❌ Помилка тесту: {e}")
        import traceback
        logger.error(f"Деталі помилки: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(test_grouping_logic()) 