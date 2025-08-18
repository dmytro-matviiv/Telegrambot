import asyncio
import aiohttp
import logging
import os
from config import ALERTS_API_TOKEN, CHANNEL_ID, MASS_END_THRESHOLD, MASS_END_TIME_WINDOW, MASS_ALERT_THRESHOLD, MASS_ALERT_TIME_WINDOW
from telegram_publisher import TelegramPublisher
import datetime

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

# Окуповані території та зони бойових дій (не показувати тривоги)
OCCUPIED_AND_COMBAT_AREAS = {
    'Донецька область', 'Луганська область', 'АР Крим', 'Автономна Республіка Крим',
    'Херсонська область', 'Запорізька область', 'Харківська область'
}

API_URL = "https://api.alerts.in.ua/v1/alerts/active.json"

class AirAlertsMonitor:
    def __init__(self, publisher: TelegramPublisher):
        self.publisher = publisher
        self.prev_alerts = set()  # {(location_title, alert_type)}
        self.is_first_run = True  # Прапорець для першого запуску
        self.ended_alerts_buffer = []  # Буфер для зберігання відбоїв для групування
        self.last_mass_end_time = None  # Час останнього масового відбою

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
                    logging.info(f"✅ Отримано дані з API (статус: {resp.status})")
                    return data
                else:
                    logging.error(f"❌ Помилка при запиті до alerts.in.ua: {resp.status}")
                    return []

    def is_valid_alert(self, alert):
        """Перевіряє чи тривога повинна бути показана"""
        if not isinstance(alert, dict):
            return False
            
        location_title = alert.get('location_title', '')
        location_type = alert.get('location_type', '')
        alert_type = alert.get('alert_type', '')
        
        # Показувати тільки повітряні тривоги
        if alert_type != 'air_raid':
            return False
            
        # Показувати тільки тривоги по областях (не по громадах, містах, тощо)
        if location_type != 'oblast':
            return False
            
        # Не показувати тривоги в окупованих територіях та зонах бойових дій
        if location_title in OCCUPIED_AND_COMBAT_AREAS:
            return False
            
        return True

    def group_alerts(self, alerts):
        """Групує тривоги для оптимізації повідомлень"""
        oblasts = []
        for alert in alerts:
            if self.is_valid_alert(alert):
                location_title = alert.get('location_title', '')
                if location_title:
                    oblasts.append(location_title)
        
        # Якщо тривога в більшості областей - показуємо загальну тривогу
        if len(oblasts) >= 15:  # Більше половини областей
            return True, {}
        
        region_map = {k: [] for k in REGIONS}
        for oblast in oblasts:
            for region, oblast_list in REGIONS.items():
                if oblast in oblast_list:
                    region_map[region].append(oblast)
        return False, region_map

    def should_group_alerts(self, new_alerts, current_alerts_dict):
        """Перевіряє чи потрібно групувати тривоги"""
        if len(new_alerts) >= MASS_ALERT_THRESHOLD:
            # Перевіряємо чи тривоги почалися в проміжку 1-2 хвилини
            now = datetime.datetime.now(datetime.timezone.utc)
            alert_times = []
            
            for key in new_alerts:
                alert = current_alerts_dict.get(key)
                if alert and alert.get('started_at'):
                    try:
                        started_dt = datetime.datetime.strptime(alert['started_at'][:19], "%Y-%m-%dT%H:%M:%S")
                        alert_times.append(started_dt)
                    except:
                        continue
            
            if len(alert_times) >= MASS_ALERT_THRESHOLD:
                # Перевіряємо чи всі тривоги в межах налаштованого часового вікна
                min_time = min(alert_times)
                max_time = max(alert_times)
                time_diff = (max_time - min_time).total_seconds() / 60
                
                if time_diff <= MASS_ALERT_TIME_WINDOW:
                    return True
        
        return False

    def should_group_end_alerts(self, ended_alerts, all_alerts_dict):
        """Перевіряє чи потрібно групувати відбої тривоги"""
        if len(ended_alerts) >= MASS_END_THRESHOLD:  # Мінімум 2 області мають відбій
            now = datetime.datetime.now(datetime.timezone.utc)
            end_times = []
            
            for key in ended_alerts:
                location, alert_type = key
                if alert_type != 'air_raid':
                    continue
                    
                alert = all_alerts_dict.get(key)
                if alert and alert.get('finished_at'):
                    try:
                        finished_dt = datetime.datetime.strptime(alert['finished_at'][:19], "%Y-%m-%dT%H:%M:%S")
                        end_times.append(finished_dt)
                    except:
                        continue
            
            if len(end_times) >= MASS_END_THRESHOLD:
                # Перевіряємо чи всі відбої в межах налаштованого часового вікна
                min_time = min(end_times)
                max_time = max(end_times)
                time_diff = (max_time - min_time).total_seconds() / 60
                
                if time_diff <= MASS_END_TIME_WINDOW:
                    return True
        
        return False

    def add_to_ended_alerts_buffer(self, ended_alerts, all_alerts_dict):
        """Додає відбої до буфера для групування"""
        now = datetime.datetime.now(datetime.timezone.utc)
        
        for key in ended_alerts:
            location, alert_type = key
            if alert_type != 'air_raid':
                continue
                
            # Додаємо до буфера з поточним часом
            self.ended_alerts_buffer.append({
                'location': location,
                'time': now,
                'key': key
            })
        
        # Очищаємо старий буфер (старше 2 хвилин)
        cutoff_time = now - datetime.timedelta(minutes=2)
        self.ended_alerts_buffer = [
            item for item in self.ended_alerts_buffer 
            if item['time'] > cutoff_time
        ]

    def get_grouped_end_alerts(self):
        """Отримує групу відбоїв для публікації"""
        if len(self.ended_alerts_buffer) < MASS_END_THRESHOLD:
            return []
        
        # Групуємо відбої за часовим вікном
        now = datetime.datetime.now(datetime.timezone.utc)
        cutoff_time = now - datetime.timedelta(minutes=MASS_END_TIME_WINDOW)
        
        recent_ends = [
            item for item in self.ended_alerts_buffer 
            if item['time'] > cutoff_time
        ]
        
        if len(recent_ends) >= MASS_END_THRESHOLD:
            # Видаляємо ці відбої з буфера
            locations = [item['location'] for item in recent_ends]
            keys_to_remove = [item['key'] for item in recent_ends]
            
            # Видаляємо з буфера
            self.ended_alerts_buffer = [
                item for item in self.ended_alerts_buffer 
                if item['key'] not in keys_to_remove
            ]
            
            return locations
        
        return []

    async def send_alert(self, text):
        await self.publisher.send_simple_message(text)

    async def monitor(self, interval=60):
        logging.info(f"🚨 Моніторинг тривог запущений з інтервалом {interval} сек")
        while True:
            try:
                logging.info("🔍 Перевіряємо тривоги...")
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
                all_alerts_dict = {}  # Всі тривоги (включно з завершеними)
                
                for alert in alerts_list:
                    if not self.is_valid_alert(alert):
                        continue
                        
                    location_title = alert.get('location_title', '')
                    alert_type = alert.get('alert_type', '')
                    finished_at = alert.get('finished_at')
                    started_at = alert.get('started_at', '')
                    
                    key = (location_title, alert_type)
                    all_alerts_dict[key] = alert
                    
                    # Враховуємо тільки активні події air_raid для поточних тривог
                    if location_title and not finished_at:
                        current_alerts_dict[key] = alert

                current_alerts = set(current_alerts_dict.keys())
                
                # При першому запуску просто зберігаємо поточні тривоги без надсилання
                if self.is_first_run:
                    logging.info("🚀 Перший запуск - зберігаємо поточні тривоги без надсилання")
                    self.prev_alerts = current_alerts
                    self.is_first_run = False
                    await asyncio.sleep(interval)
                    continue
                
                new_alerts = current_alerts - self.prev_alerts
                ended_alerts = self.prev_alerts - current_alerts
                
                # Логуємо статистику
                if new_alerts:
                    logging.info(f"🚨 Знайдено {len(new_alerts)} нових тривог")
                if ended_alerts:
                    logging.info(f"✅ Знайдено {len(ended_alerts)} завершених тривог")

                # --- Формування інформативних повідомлень ---
                def format_alert_message(alert, is_end=False):
                    location = alert.get('location_title', '')
                    started_at = alert.get('started_at', '')
                    if is_end:
                        return f"✅ <b>Відбій повітряної тривоги</b> — {location}"
                    msg = f"🚨 <b>Повітряна тривога</b> — {location}"
                    return msg

                # --- Надсилання нових подій ---
                now = datetime.datetime.now(datetime.timezone.utc)
                
                # Перевіряємо чи потрібно групувати тривоги
                if self.should_group_alerts(new_alerts, current_alerts_dict):
                    logging.info(f"📤 Надсилаємо загальну тривогу для України")
                    await self.send_alert("🚨 <b>Повітряна тривога</b> — Україна")
                else:
                    # Надсилаємо окремі тривоги
                    for key in new_alerts:
                        alert = current_alerts_dict[key]
                        started_at = alert.get('started_at', '')
                        
                        # Перевіряємо час початку тривоги
                        if started_at:
                            try:
                                started_dt = datetime.datetime.strptime(started_at[:19], "%Y-%m-%dT%H:%M:%S")
                                delta = (now - started_dt).total_seconds() / 60
                                
                                # Надсилаємо тільки тривоги, які почалися не більше 10 хвилин тому
                                if delta > 10:
                                    logging.info(f"⏩ Пропускаємо стару тривогу: {alert.get('location_title', '')} (почалася {delta:.1f} хв тому)")
                                    continue
                            except Exception as e:
                                logging.warning(f"Помилка парсингу часу тривоги: {e}")
                                continue
                        
                        text = format_alert_message(alert, is_end=False)
                        logging.info(f"📤 Надсилаємо нову тривогу: {alert.get('location_title', '')}")
                        await self.send_alert(text)

                # --- Надсилання завершених подій ---
                # Додаємо відбої до буфера
                if ended_alerts:
                    self.add_to_ended_alerts_buffer(ended_alerts, all_alerts_dict)
                
                # Перевіряємо чи є група відбоїв для публікації
                grouped_end_locations = self.get_grouped_end_alerts()
                
                if grouped_end_locations:
                    # Публікуємо групу відбоїв
                    message = f"✅ <b>Відбій повітряної тривоги</b> — {', '.join(grouped_end_locations)}"
                    logging.info(f"📤 Надсилаємо групу відбоїв тривоги для {len(grouped_end_locations)} областей: {', '.join(grouped_end_locations)}")
                    await self.send_alert(message)
                else:
                    # Надсилаємо окремі відбої тільки якщо їх немає в буфері
                    for key in ended_alerts:
                        location, alert_type = key
                        if alert_type != 'air_raid':
                            continue
                        
                        # Перевіряємо, чи цей відбій вже в буфері
                        if any(item['key'] == key for item in self.ended_alerts_buffer):
                            logging.info(f"⏩ Відбій {location} в буфері, чекаємо групування")
                            continue
                        
                        # Перевіряємо, чи є завершена тривога в поточних даних API
                        finished_alert = all_alerts_dict.get(key)
                        if finished_alert and finished_alert.get('finished_at'):
                            # Є завершена тривога в API - перевіряємо час завершення
                            finished_at = finished_alert.get('finished_at')
                            try:
                                finished_dt = datetime.datetime.strptime(finished_at[:19], "%Y-%m-%dT%H:%M:%S")
                                delta = (now - finished_dt).total_seconds() / 60
                                
                                # Надсилаємо тільки відбої, які відбулися не більше 5 хвилин тому
                                if delta > 5:
                                    logging.info(f"⏩ Пропускаємо старий відбій: {location} (відбувся {delta:.1f} хв тому)")
                                    continue
                            except Exception as e:
                                logging.warning(f"Помилка парсингу часу відбою: {e}")
                                # Якщо не можемо парсити час - все одно надсилаємо відбій
                        else:
                            # Немає завершеної тривоги в API - тривога просто зникла з активних
                            # Це означає що вона завершилася, надсилаємо відбій
                            logging.info(f"🔍 Тривога зникла з активних (API не повертає finished_at): {location}")
                        
                        # Надсилаємо повідомлення про відбій
                        fake_alert = {'location_title': location}
                        text = format_alert_message(fake_alert, is_end=True)
                        logging.info(f"📤 Надсилаємо відбій тривоги: {location}")
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