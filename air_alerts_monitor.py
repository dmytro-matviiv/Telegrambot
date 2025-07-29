import asyncio
import aiohttp
import logging
import os
from config import ALERTS_API_TOKEN, CHANNEL_ID
from telegram_publisher import TelegramPublisher

# Макрорегіони України
REGIONS = {
    'Захід': [
        'Львівська область', 'Волинська область', 'Рівненська область', 'Тернопільська область',
        'Івано-Франківська область', 'Закарпатська область', 'Чернівецька область'
    ],
    'Схід': [
        'Харківська область', 'Донецька область', 'Луганська область'
    ],
    'Північ': [
        'Київська область', 'Житомирська область', 'Чернігівська область', 'Сумська область'
    ],
    'Південь': [
        'Одеська область', 'Миколаївська область', 'Херсонська область', 'Запорізька область', 'АР Крим'
    ],
    'Центр': [
        'Кіровоградська область', 'Полтавська область', 'Черкаська область', 'Дніпропетровська область', 'м. Київ'
    ]
}

API_URL = "https://api.alerts.in.ua/v1/alerts/active.json"

class AirAlertsMonitor:
    def __init__(self, publisher: TelegramPublisher):
        self.publisher = publisher
        self.prev_alerts = set()  # {(location_title, alert_type)}

    async def fetch_alerts(self):
        headers = {}
        params = {}
        token = ALERTS_API_TOKEN or os.getenv('ALERTS_API_TOKEN')
        if not token:
            logging.warning("ALERTS_API_TOKEN не заданий!")
            return []
        headers['Authorization'] = f'Bearer {token}'
        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL, headers=headers, params=params, timeout=15) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    logging.error(f"Помилка при запиті до alerts.in.ua: {resp.status}")
                    return []

    def group_alerts(self, alerts):
        # Повертає: (all_ukraine, {region: [області]})
        oblasts = [a['location_title'] for a in alerts if a['location_type'] == 'oblast']
        if len(oblasts) >= 24:
            return True, {}
        region_map = {k: [] for k in REGIONS}
        for oblast in oblasts:
            for region, oblast_list in REGIONS.items():
                if oblast in oblast_list:
                    region_map[region].append(oblast)
        return False, region_map

    async def send_alert(self, text):
        await self.publisher.send_simple_message(text)

    async def monitor(self, interval=60):
        while True:
            try:
                alerts = await self.fetch_alerts()
                current_alerts = set((a['location_title'], a['alert_type']) for a in alerts)
                # Початок тривоги
                new_alerts = current_alerts - self.prev_alerts
                # Відбій
                ended_alerts = self.prev_alerts - current_alerts
                # Групування для масових тривог
                all_ukraine, region_map = self.group_alerts(alerts)
                # Повітряна тривога по всій Україні
                if all_ukraine and not any(('Україна', 'air_raid') in self.prev_alerts for _ in [0]):
                    await self.send_alert("🔴🚨 Повітряна тривога по всій Україні!")
                # Відбій по всій Україні
                if not all_ukraine and any(('Україна', 'air_raid') in self.prev_alerts for _ in [0]):
                    await self.send_alert("🟢✅ Відбій тривоги по всій Україні!")
                # По регіонах
                for region, oblasts in region_map.items():
                    if len(oblasts) == len(REGIONS[region]) and not any((region, 'air_raid') in self.prev_alerts for _ in [0]):
                        await self.send_alert(f"🔴🚨 Повітряна тривога на {region} України!")
                    if len(oblasts) < len(REGIONS[region]) and any((region, 'air_raid') in self.prev_alerts for _ in [0]):
                        await self.send_alert(f"🟢✅ Відбій тривоги на {region} України!")
                # Окремі області
                for (loc, typ) in new_alerts:
                    if typ == 'air_raid':
                        await self.send_alert(f"🔴 Повітряна тривога! {loc}")
                for (loc, typ) in ended_alerts:
                    if typ == 'air_raid':
                        await self.send_alert(f"🟢 Відбій тривоги! {loc}")
                self.prev_alerts = current_alerts
            except Exception as e:
                logging.error(f"Помилка моніторингу тривог: {e}")
            await asyncio.sleep(interval)

# Додати у TelegramPublisher метод для простого надсилання повідомлення
# async def send_simple_message(self, text: str):
#     await self.bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode='HTML') 