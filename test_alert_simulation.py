import asyncio
import logging
from telegram_publisher import TelegramPublisher
from datetime import datetime, timezone
import datetime as dt

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def simulate_alert_at_2057():
    """Симулює тривогу яка почалася о 20:57"""
    try:
        publisher = TelegramPublisher()
        
        # Симулюємо тривогу в Чернігівській області о 20:57
        alert_time = datetime(2025, 8, 7, 20, 57, 0, tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        
        # Розраховуємо різницю в хвилинах
        delta = (now - alert_time).total_seconds() / 60
        
        logger.info(f"⏰ Час тривоги: {alert_time}")
        logger.info(f"⏰ Поточний час: {now}")
        logger.info(f"⏰ Різниця: {delta:.1f} хвилин")
        
        # Перевіряємо чи тривога в межах 10 хвилин
        if delta <= 10:
            logger.info("✅ Тривога в межах 10 хвилин - повинна показуватися")
            message = "🚨 <b>Повітряна тривога</b> — Чернігівська область"
            if await publisher.send_simple_message(message):
                logger.info("✅ Тестова тривога надіслана успішно")
            else:
                logger.error("❌ Помилка при надсиланні тестової тривоги")
        else:
            logger.info(f"⏩ Тривога застаріла ({delta:.1f} хв) - не показується")
        
        await publisher.close()
        
    except Exception as e:
        logger.error(f"Помилка: {e}")

if __name__ == "__main__":
    print("🧪 Симуляція тривоги о 20:57...")
    asyncio.run(simulate_alert_at_2057())
