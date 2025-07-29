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
                # Перевіряємо формат даних - API повертає {'alerts': [...]} або список
                if isinstance(alerts_data, dict) and 'alerts' in alerts_data:
                    alerts_list = alerts_data['alerts']
                elif isinstance(alerts_data, list):
                    alerts_list = alerts_data
                else:
                    logging.warning(f"Неочікуваний формат даних: {type(alerts_data)}")
                    await asyncio.sleep(interval)
                    continue

                # --- Групування по типу події та області/місту ---
                # Ключ: (location_title, alert_type), значення: alert (dict)
                current_alerts_dict = {}
                for alert in alerts_list:
                    if not isinstance(alert, dict):
                        continue
                    alert_type = alert.get('alert_type', '')
                    location_title = alert.get('location_title', '')
                    finished_at = alert.get('finished_at')
                    # Враховуємо тільки активні події
                    if alert_type and location_title and not finished_at:
                        current_alerts_dict[(location_title, alert_type)] = alert

                current_alerts = set(current_alerts_dict.keys())
                new_alerts = current_alerts - self.prev_alerts
                ended_alerts = self.prev_alerts - current_alerts

                # --- Формування інформативних повідомлень ---
                def format_alert_message(alert, is_end=False):
                    alert_type = alert.get('alert_type', '')
                    location = alert.get('location_title', '')
                    started_at = alert.get('started_at', '')
                    notes = alert.get('notes', '')
                    # Короткі назви для типів подій
                    type_map = {
                        'air_raid': ('🚨', 'Повітряна тривога'),
                        'mig_takeoff': ('✈️', 'Зліт МіГа'),
                        'missile_launch': ('🚀', 'Запуск ракети'),
                        'artillery_shelling': ('💥', 'Артобстріл'),
                        'urban_fights': ('⚔️', 'Бої в місті'),
                        # Додати інші типи за потреби
                    }
                    emoji, label = type_map.get(alert_type, ('❗', alert_type))
                    if is_end:
                        if alert_type == 'air_raid':
                            emoji, label = '✅', 'Відбій тривоги'
                        else:
                            emoji = '✅'
                            label = f'Кінець події: {label}'
                    msg = f"{emoji} <b>{label}</b> — {location}"
                    if started_at and not is_end:
                        msg += f"\nПочаток: {started_at[:16].replace('T',' ')}"
                    if notes:
                        msg += f"\n<i>{notes}</i>"
                    return msg

                # --- Надсилання нових подій ---
                for key in new_alerts:
                    alert = current_alerts_dict[key]
                    text = format_alert_message(alert, is_end=False)
                    await self.send_alert(text)

                # --- Надсилання завершених подій ---
                for key in ended_alerts:
                    # Для ended_alerts у нас немає повного alert, але є (location, alert_type)
                    location, alert_type = key
                    fake_alert = {'alert_type': alert_type, 'location_title': location}
                    text = format_alert_message(fake_alert, is_end=True)
                    await self.send_alert(text)

                self.prev_alerts = current_alerts

            except Exception as e:
                logging.error(f"Помилка моніторингу тривог: {e}")
                import traceback
                logging.error(f"Деталі помилки: {traceback.format_exc()}")
            await asyncio.sleep(interval)

# Додати у TelegramPublisher метод для простого надсилання повідомлення
# async def send_simple_message(self, text: str):
#     await self.bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode='HTML') 