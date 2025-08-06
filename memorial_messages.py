import asyncio
import logging
import random
from datetime import datetime, time, timedelta
from typing import List
from telegram_publisher import TelegramPublisher
import pytz

logger = logging.getLogger(__name__)

class MemorialMessageScheduler:
    """Планувальник для щоденних меморіальних повідомлень о 9:00 за київським часом"""
    
    def __init__(self, publisher: TelegramPublisher):
        self.publisher = publisher
        self.target_time = time(9, 0)  # 9:00 ранку
        self.last_sent_date = None
        
        # Різноманітні тексти для меморіальних повідомлень
        self.memorial_templates = [
            "🕯️ Хвилина мовчання за нашими героями, які віддали життя за незалежність України.\n\n💔 Вічна пам'ять захисникам, які боронили нашу землю від ворога.\n\n🙏 Їхня жертва не буде забута. Слава Героям! 🇺🇦",
            
            "🕯️ О 9:00 ранку пам'ятаємо наших полеглих воїнів.\n\n💙💛 Кожен день починаємо з вдячності тим, хто поклав життя за нашу свободу.\n\n🙏 Вічна пам'ять героям України! 🇺🇦",
            
            "🕯️ Хвилина тиші за тих, хто більше не повернеться додому.\n\n💔 Наші захисники загинули, щоб ми могли жити у вільній Україні.\n\n🙏 Пам'ятаємо. Скорботимо. Пишаємося. Слава Україні! 🇺🇦",
            
            "🕯️ Щоранку о 9:00 вшановуємо пам'ять полеглих героїв.\n\n💔 Вони боронили кожен метр нашої землі, кожну українську родину.\n\n🙏 Їхній подвиг живе в наших серцях назавжди. Героям слава! 🇺🇦",
            
            "🕯️ Хвилина мовчання за наших воїнів, які не повернулися з поля бою.\n\n💙💛 Вони віддали найдорожче - своє життя - за майбутнє України.\n\n🙏 Вічна пам'ять захисникам Вітчизни! 🇺🇦",
            
            "🕯️ О дев'ятій ранку пам'ятаємо тих, хто поклав життя за Україну.\n\n💔 Кожен полеглий герой - це втрачена мрія, недожите життя, нездійснені плани.\n\n🙏 Але їхня жертва дала нам надію на перемогу. Слава Героям! 🇺🇦",
            
            "🕯️ Хвилина скорботи за нашими захисниками.\n\n💔 Вони йшли в бій, знаючи ціну свободи. Вони боролися до останнього подиху.\n\n🙏 Їхня мужність надихає нас жити і перемагати. Вічна пам'ять! 🇺🇦",
            
            "🕯️ Щодня о 9:00 вшановуємо пам'ять полеглих воїнів.\n\n💙💛 Вони захищали не лише територію, а й наші цінності, нашу ідентичність.\n\n🙏 Їхній подвиг буде жити в пам'яті поколінь. Героям слава! 🇺🇦",
            
            "🕯️ Хвилина тиші за тих, хто загинув за незалежність України.\n\n💔 Кожен день нашої свободи оплачений їхньою кров'ю та життям.\n\n🙏 Пам'ятаємо кожного героя. Дякуємо за мир над головою. 🇺🇦",
            
            "🕯️ О дев'ятій ранку згадуємо наших полеглих захисників.\n\n💔 Вони боронили Україну від тих, хто хотів знищити нашу державу.\n\n🙏 Їхня жертва не була марною. Ми переможемо! Слава Україні! 🇺🇦"
        ]
    
    def get_random_memorial_message(self) -> str:
        """Повертає випадкове меморіальне повідомлення"""
        return random.choice(self.memorial_templates)
    
    def should_send_memorial_message(self) -> bool:
        """Перевіряє, чи потрібно надіслати меморіальне повідомлення"""
        # Використовуємо часовий пояс Києва
        now = datetime.now(pytz.timezone("Europe/Kiev"))
        current_date = now.date()
        current_time = now.time()

        # Перевіряємо, чи час між 9:00 та 9:30 (вікно для відправки)
        if not (time(0, 0) <= current_time <= time(23, 59)):
            logger.info(f"[Minute of Silence] Зараз {current_time}, не в вікні 9:00-9:30")
            return False

        # Перевіряємо, чи вже надсилали сьогодні
        if self.last_sent_date == current_date:
            logger.info("[Minute of Silence] Сьогодні вже надсилали меморіальне повідомлення")
            return False

        return True
    
    async def send_memorial_message(self) -> bool:
        """Надсилає меморіальне повідомлення"""
        try:
            message = self.get_random_memorial_message()
            success = await self.publisher.send_simple_message(message)
            
            if success:
                self.last_sent_date = datetime.now().date()
                logger.info("✅ Меморіальне повідомлення надіслано успішно")
                return True
            else:
                logger.error("❌ Помилка при надсиланні меморіального повідомлення")
                return False
                
        except Exception as e:
            logger.error(f"❌ Помилка при надсиланні меморіального повідомлення: {e}")
            return False
    
    async def check_and_send_memorial(self):
        """Перевіряє час і надсилає меморіальне повідомлення якщо потрібно"""
        if self.should_send_memorial_message():
            logger.info("🕯️ Час для меморіального повідомлення (9:00 ранку)")
            await self.send_memorial_message()
        else:
            logger.info("[Minute of Silence] Не час для меморіального повідомлення")
        
    async def monitor_memorial_schedule(self, check_interval: int = 60):
        """Моніторить розклад і надсилає меморіальні повідомлення"""
        logger.info("🕯️ Запущено моніторинг меморіальних повідомлень (перевірка кожну хвилину)")
        
        while True:
            try:
                await self.check_and_send_memorial()
                await asyncio.sleep(check_interval)  # Перевіряємо кожні 5 хвилин
            except Exception as e:
                logger.error(f"❌ Помилка в моніторингу меморіальних повідомлень: {e}")
                await asyncio.sleep(60)  # При помилці чекаємо хвилину

async def schedule_minute_of_silence(bot, channel_id):
    while True:
        now = datetime.now()
        target = now.replace(hour=9, minute=0, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)
        wait_seconds = (target - now).total_seconds()
        logging.info(f"[Minute of Silence] Next scheduled at {target} (in {wait_seconds} seconds)")
        await asyncio.sleep(wait_seconds)
        try:
            await send_minute_of_silence(bot, channel_id)
            logging.info("[Minute of Silence] Message sent successfully.")
        except Exception as e:
            logging.error(f"[Minute of Silence] Failed to send: {e}")

async def send_minute_of_silence(bot, channel_id):
    pass  # Реалізуйте відправлення повідомлення тут

async def send_memorial_message_daily(publisher):
    memorial_text = (
        "🕯️ Хвилина мовчання за нашими героями, які віддали життя за незалежність України.\n\n"
        "💔 Вічна пам'ять захисникам, які боронили нашу землю від ворога.\n\n"
        "🙏 Їхня жертва не буде забута. Слава Героям! 🇺🇦"
    )
    kyiv_tz = pytz.timezone('Europe/Kyiv')
    while True:
        now = datetime.now(kyiv_tz)
        target = now.replace(hour=9, minute=0, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)
        wait_seconds = (target - now).total_seconds()
        await asyncio.sleep(wait_seconds)
        try:
            await publisher.send_simple_message(memorial_text)
        except Exception as e:
            print(f"[Minute of Silence] Failed to send: {e}")
        await asyncio.sleep(60)  # щоб уникнути повторного надсилання протягом хвилини