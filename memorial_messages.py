import asyncio
import logging
import json
import random
from datetime import datetime, time
import pytz
from telegram_publisher import TelegramPublisher

logger = logging.getLogger(__name__)

class MemorialMessageScheduler:
    def __init__(self, publisher: TelegramPublisher):
        self.publisher = publisher
        self.last_sent_date = self.load_last_sent_date()
        
        # Шаблони меморіальних повідомлень
        self.memorial_templates = [
            "🕯️ Хвилина мовчання на згадку про загиблих героїв України",
            "🕯️ Вшануємо пам'ять тих, хто віддав життя за Україну",
            "🕯️ Хвилина мовчання на згадку про захисників України",
            "🕯️ Вшануємо пам'ять героїв, які захищали нашу землю",
            "🕯️ Хвилина мовчання на згадку про всіх загиблих за Україну"
        ]

    def load_last_sent_date(self) -> str:
        """Завантажує дату останнього надісланого повідомлення"""
        try:
            with open('memorial_last_sent.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('last_sent_date', '')
        except FileNotFoundError:
            return ''
        except Exception as e:
            logger.error(f"Помилка завантаження дати: {e}")
            return ''

    def save_last_sent_date(self, date: str):
        """Зберігає дату останнього надісланого повідомлення"""
        try:
            with open('memorial_last_sent.json', 'w', encoding='utf-8') as f:
                json.dump({'last_sent_date': date}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Помилка збереження дати: {e}")

    def get_random_memorial_message(self) -> str:
        """Повертає випадкове меморіальне повідомлення"""
        return random.choice(self.memorial_templates)

    def should_send_memorial_message(self) -> bool:
        """Перевіряє чи потрібно надіслати меморіальне повідомлення"""
        # Встановлюємо часовий пояс Києва
        kiev_tz = pytz.timezone('Europe/Kiev')
        current_time = datetime.now(kiev_tz)
        current_date = current_time.strftime('%Y-%m-%d')
        
        # Перевіряємо чи поточний час 9:00
        target_time = time(9, 0)
        current_time_only = current_time.time()
        
        # Перевіряємо чи вже надсилали сьогодні
        if self.last_sent_date == current_date:
            logger.info(f"[Minute of Silence] Сьогодні ({current_date}) вже надсилали меморіальне повідомлення")
            return False
        
        # Перевіряємо чи поточний час 9:00 (з допуском ±1 хвилина)
        time_diff = abs((current_time_only.hour * 60 + current_time_only.minute) - 
                       (target_time.hour * 60 + target_time.minute))
        
        if time_diff <= 1:
            logger.info(f"[Minute of Silence] Поточний час: {current_time_only}, дата: {current_date}")
            logger.info(f"[Minute of Silence] Остання дата відправки: {self.last_sent_date}")
            logger.info("[Minute of Silence] Умови для відправки виконані!")
            return True
        
        return False

    async def send_memorial_message(self) -> bool:
        """Надсилає меморіальне повідомлення"""
        try:
            message = self.get_random_memorial_message()
            logger.info(f"[Minute of Silence] Надсилаю меморіальне повідомлення: {message}")
            
            success = await self.publisher.send_simple_message(message)
            
            if success:
                # Зберігаємо дату надсилання
                kiev_tz = pytz.timezone('Europe/Kiev')
                current_date = datetime.now(kiev_tz).strftime('%Y-%m-%d')
                self.save_last_sent_date(current_date)
                self.last_sent_date = current_date
                logger.info(f"[Minute of Silence] ✅ Меморіальне повідомлення успішно надіслано")
                return True
            else:
                logger.error("[Minute of Silence] ❌ Помилка надсилання меморіального повідомлення")
                return False
                
        except Exception as e:
            logger.error(f"[Minute of Silence] ❌ Помилка: {e}")
            return False

    async def check_and_send_memorial(self):
        """Перевіряє та надсилає меморіальне повідомлення якщо потрібно"""
        logger.info("[Minute of Silence] Перевіряю умови для меморіального повідомлення...")
        
        if self.should_send_memorial_message():
            await self.send_memorial_message()

    async def monitor_memorial_schedule(self, check_interval: int = 60):
        """Моніторить розклад меморіальних повідомлень"""
        logger.info(f"[Minute of Silence] 🚀 Запуск моніторингу меморіальних повідомлень (перевірка кожні {check_interval} сек)")
        
        while True:
            try:
                await self.check_and_send_memorial()
                await asyncio.sleep(check_interval)
            except Exception as e:
                logger.error(f"[Minute of Silence] Помилка моніторингу: {e}")
                await asyncio.sleep(check_interval)
