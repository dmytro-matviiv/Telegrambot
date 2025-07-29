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
                    data = await resp.json()
                    logging.info(f"Отримано дані з API: {data}")
                    return data
                else:
                    logging.error(f"Помилка при запиті до alerts.in.ua: {resp.status}")
                    return []

    def group_alerts(self, alerts):
        # Повертає: (all_ukraine, {region: [області]})
        oblasts = []
        for alert in alerts:
            if isinstance(alert, dict):
                location_title = alert.get('location_title', '')
                location_type = alert.get('location_type', '')
                if location_type == 'oblast' and location_title:
                    oblasts.append(location_title)
        
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
                alerts_data = await self.fetch_alerts()
                
                # Перевіряємо формат даних
                if not isinstance(alerts_data, list):
                    logging.warning(f"Неочікуваний формат даних: {type(alerts_data)}")
                    await asyncio.sleep(interval)
                    continue
                
                # Фільтруємо тільки повітряні тривоги
                alerts = []
                for alert in alerts_data:
                    if isinstance(alert, dict):
                        alert_type = alert.get('alert_type', '')
                        if alert_type == 'air_raid':
                            alerts.append(alert)
                
                logging.info(f"Знайдено {len(alerts)} активних повітряних тривог")
                
                # Створюємо множину поточних тривог
                current_alerts = set()
                for alert in alerts:
                    if isinstance(alert, dict):
                        location_title = alert.get('location_title', '')
                        alert_type = alert.get('alert_type', '')
                        if location_title and alert_type:
                            current_alerts.add((location_title, alert_type))
                
                # Знаходимо нові та завершені тривоги
                new_alerts = current_alerts - self.prev_alerts
                ended_alerts = self.prev_alerts - current_alerts
                
                # Обробляємо нові тривоги
                for (location, alert_type) in new_alerts:
                    if alert_type == 'air_raid':
                        await self.send_alert(f"🔴🚨 Повітряна тривога! {location}")
                
                # Обробляємо завершені тривоги
                for (location, alert_type) in ended_alerts:
                    if alert_type == 'air_raid':
                        await self.send_alert(f"🟢✅ Відбій тривоги! {location}")
                
                # Оновлюємо попередній стан
                self.prev_alerts = current_alerts
                
            except Exception as e:
                logging.error(f"Помилка моніторингу тривог: {e}")
                import traceback
                logging.error(f"Деталі помилки: {traceback.format_exc()}")
            
            await asyncio.sleep(interval)

# Додати у TelegramPublisher метод для простого надсилання повідомлення
# async def send_simple_message(self, text: str):
#     await self.bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode='HTML') 