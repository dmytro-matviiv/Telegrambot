import asyncio
import logging
from datetime import datetime, time, timedelta
import pytz
from typing import List
from telegram import Bot
from config import BOT_TOKEN, GROUP_CHAT_ID

logger = logging.getLogger(__name__)


class GroupEngagementScheduler:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.group_chat = GROUP_CHAT_ID
        self.tz = pytz.timezone('Europe/Kiev')

        # Розклад (Київ): спілкування + розіграш
        self.daily_slots = [
            (8, 15, 'qotd'),         # Питання дня (опитування)
            (12, 45, 'mini_discuss'),# Міні-дискусія
            (17, 30, 'ugc_prompt'),  # UGC-збір
        ]
        # Розіграш через день о 20:00
        self.raffle_slot = (20, 0)
        self.weekly_slot = (19, 30, 6, 'top_comment')  # Нд 19:30

    def now(self):
        return datetime.now(self.tz)

    def local_dt(self, h: int, m: int, day_offset: int = 0):
        d = (self.now().date() + timedelta(days=day_offset))
        return self.tz.localize(datetime.combine(d, time(h, m)))

    def next_fire(self) -> datetime:
        now = self.now()
        # Кандидати щоденних слотів сьогодні і завтра
        candidates: List[datetime] = []
        for h, m, _ in self.daily_slots:
            candidates.append(self.local_dt(h, m, 0))
            candidates.append(self.local_dt(h, m, 1))
        # Щотижневий (день тижня 0=Пн..6=Нд)
        wh, wm, wday, _ = self.weekly_slot
        # знайдемо найближчу дату з цим днем тижня
        delta_days = (wday - now.weekday()) % 7
        candidates.append(self.local_dt(wh, wm, delta_days))
        # обрати найближчий у майбутньому
        for dt in sorted(candidates):
            if dt > now + timedelta(seconds=2):
                return dt
        # запасний варіант — завтра перший слот
        h, m, _ = self.daily_slots[0]
        return self.local_dt(h, m, 1)

    async def send_qotd_poll(self):
        question = "Питання дня: що для вас сьогодні головне?"
        options = ["Безпека", "Економіка", "Міжнародні новини", "Інше"]
        try:
            await self.bot.send_poll(chat_id=self.group_chat, question=question, options=options, is_anonymous=False, allows_multiple_answers=False)
            logger.info("[Group] ✅ Надіслано опитування QOTD")
        except Exception as e:
            logger.error(f"[Group] ❌ Помилка QOTD: {e}")

    async def send_mini_discussion(self):
        text = (
            "Міні‑дискусія: дві тези — яку підтримуєте і чому?\n"
            "1) Посилювати внутрішні реформи зараз\n"
            "2) Зосередитись на зовнішній підтримці\n\n"
            "Залиште реакцію й 1 думку в коментарях — важливо почути вас."
        )
        try:
            await self.bot.send_message(chat_id=self.group_chat, text=text)
            logger.info("[Group] ✅ Надіслано міні‑дискусію")
        except Exception as e:
            logger.error(f"[Group] ❌ Помилка міні‑дискусії: {e}")

    async def send_ugc_prompt(self):
        text = (
            "UGC: надішліть фото/історію/посилання по темі дня — відмітимо автора у підсумку.\n"
            "Формат: 1–2 речення що і чому важливо."
        )
        try:
            await self.bot.send_message(chat_id=self.group_chat, text=text)
            logger.info("[Group] ✅ Надіслано UGC‑збір")
        except Exception as e:
            logger.error(f"[Group] ❌ Помилка UGC: {e}")

    async def send_raffle_reminder(self):
        text = "🎁 РОЗІГРАШ 500 ГРН! 1 раз на місяць! Лишайте коментарі під постами — переможця оголосимо в кінці місяця!"
        try:
            await self.bot.send_message(chat_id=self.group_chat, text=text)
            logger.info("[Group] ✅ Надіслано нагадування про розіграш")
        except Exception as e:
            logger.error(f"[Group] ❌ Помилка розіграшу: {e}")

    async def send_top_comment_weekly(self):
        text = (
            "ТОП‑коментар тижня: лишайте корисні думки під постами — щонеділі відзначимо найкращий коментар у групі."
        )
        try:
            await self.bot.send_message(chat_id=self.group_chat, text=text)
            logger.info("[Group] ✅ Надіслано нагадування про ТОП‑коментар")
        except Exception as e:
            logger.error(f"[Group] ❌ Помилка ТОП‑коментаря: {e}")

    async def fire_label(self, label: str):
        if label == 'qotd':
            await self.send_qotd_poll()
        elif label == 'mini_discuss':
            await self.send_mini_discussion()
        elif label == 'ugc_prompt':
            await self.send_ugc_prompt()

    async def monitor(self):
        logger.info("[Group] 🚀 Запущено GroupEngagementScheduler")
        while True:
            try:
                nxt = self.next_fire()
                now = self.now()
                sleep_s = max(1, int((nxt - now).total_seconds()))
                logger.info(f"[Group] Next at {nxt.strftime('%Y-%m-%d %H:%M')}, sleep {sleep_s}s")
                await asyncio.sleep(sleep_s)

                # Визначаємо, що саме стріляє
                current = self.now()
                # Щотижневий
                wh, wm, wday, wlabel = self.weekly_slot
                if current.weekday() == wday and current.hour == wh and current.minute == wm:
                    await self.send_top_comment_weekly()
                    continue
                # Розіграш через день о 20:00
                rh, rm = self.raffle_slot
                if current.hour == rh and current.minute == rm and current.day % 2 == 0:
                    await self.send_raffle_reminder()
                    continue
                # Щоденні
                for h, m, label in self.daily_slots:
                    if current.hour == h and current.minute == m:
                        await self.fire_label(label)
                        break
            except Exception as e:
                logger.error(f"[Group] ❌ Помилка в моніторі: {e}")
                await asyncio.sleep(10)


