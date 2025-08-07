import asyncio
import logging
from telegram_publisher import TelegramPublisher
from config import CHANNEL_ID

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_telegram_connection():
    """Тестує підключення до Telegram"""
    try:
        publisher = TelegramPublisher()
        
        # Тестуємо підключення
        logger.info("🔗 Тестуємо підключення до Telegram...")
        if await publisher.test_connection():
            logger.info("✅ Підключення до Telegram успішне")
            
            # Тестуємо надсилання повідомлення
            logger.info("📤 Тестуємо надсилання повідомлення...")
            test_message = "🧪 Тестове повідомлення від бота"
            if await publisher.send_simple_message(test_message):
                logger.info("✅ Тестове повідомлення надіслано успішно")
            else:
                logger.error("❌ Помилка при надсиланні тестового повідомлення")
        else:
            logger.error("❌ Помилка підключення до Telegram")
            
        await publisher.close()
        
    except Exception as e:
        logger.error(f"Помилка: {e}")

if __name__ == "__main__":
    print("🧪 Тестування підключення до Telegram...")
    asyncio.run(test_telegram_connection())
