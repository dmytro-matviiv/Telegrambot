import asyncio
import aiohttp
import logging
import os
from config import ALERTS_API_TOKEN, MASS_ALERT_THRESHOLD, MASS_END_THRESHOLD, MASS_ALERT_TIME_WINDOW, MASS_END_TIME_WINDOW
from telegram_publisher import TelegramPublisher
import datetime

# API URL для отримання активних тривог
API_URL = "https://api.alerts.in.ua/v1/alerts/active.json"

class AirAlertsMonitor:
    def __init__(self, publisher: TelegramPublisher):
        self.publisher = publisher
        self.prev_alerts = set()  # {(location_title, alert_type)}
        self.is_first_run = True
        self.last_check_time = None
        
        # Для відстеження масових тривог та відбоїв
        self.pending_alerts = []  # Список нових тривог в часовому вікні
        self.pending_ends = []    # Список відбоїв в часовому вікні
        self.last_mass_alert_time = None
        self.last_mass_end_time = None

    async def fetch_alerts(self):
        """Отримує дані про тривоги з API"""
        headers = {}
        params = {}
        token = ALERTS_API_TOKEN or os.getenv('ALERTS_API_TOKEN')
        
        if not token:
            logging.warning("⚠️ ALERTS_API_TOKEN не заданий!")
            return []
            
        headers['Authorization'] = f'Bearer {token}'
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(API_URL, headers=headers, params=params, timeout=15) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        logging.info(f"✅ Отримано дані з API (статус: {resp.status})")
                        return data
                    else:
                        logging.error(f"❌ Помилка при запиті до alerts.in.ua: {resp.status}")
                        return []
        except Exception as e:
            logging.error(f"❌ Помилка при запиті до API: {e}")
            return []

    def is_valid_alert(self, alert):
        """Перевіряє чи тривога повинна бути показана"""
        if not isinstance(alert, dict):
            return False
            
        location_title = alert.get('location_title', '')
        location_type = alert.get('location_type', '')
        alert_type = alert.get('alert_type', '')
        finished_at = alert.get('finished_at')
        
        # Показувати тільки повітряні тривоги
        if alert_type != 'air_raid':
            return False
            
        # Показувати тільки тривоги по областях (містах), не по районах
        if location_type != 'oblast':
            return False
            
        # Не показувати тривоги в окупованих територіях
        occupied_areas = {
            'Луганська область', 'АР Крим', 'Автономна Республіка Крим'
        }
        
        if location_title in occupied_areas:
            return False
            
        return True
    
    def extract_city_name(self, location_title):
        """Витягує назву міста/області з повної назви"""
        # Якщо це вже область, повертаємо як є
        if 'область' in location_title:
            return location_title
        
        # Якщо це місто, додаємо "область" або залишаємо як є
        return location_title
    
    def group_alerts_by_city(self, alerts):
        """Групує тривоги по містах/областях"""
        city_alerts = {}
        
        for alert in alerts:
            if not self.is_valid_alert(alert):
                continue
                
            location_title = alert.get('location_title', '')
            city_name = self.extract_city_name(location_title)
            finished_at = alert.get('finished_at')
            
            if city_name not in city_alerts:
                city_alerts[city_name] = {
                    'active_alerts': [],
                    'finished_alerts': []
                }
            
            if finished_at:
                city_alerts[city_name]['finished_alerts'].append(alert)
            else:
                city_alerts[city_name]['active_alerts'].append(alert)
        
        return city_alerts

    def add_to_pending_alerts(self, cities):
        """Додає нові тривоги до списку очікуючих"""
        current_time = datetime.datetime.now()
        for city in cities:
            self.pending_alerts.append({
                'city': city,
                'time': current_time
            })
        logging.info(f"📝 Додано {len(cities)} тривог до очікуючих. Всього: {len(self.pending_alerts)}")

    def add_to_pending_ends(self, cities):
        """Додає відбої до списку очікуючих"""
        current_time = datetime.datetime.now()
        for city in cities:
            self.pending_ends.append({
                'city': city,
                'time': current_time
            })
        logging.info(f"📝 Додано {len(cities)} відбоїв до очікуючих. Всього: {len(self.pending_ends)}")

    def cleanup_old_pending(self):
        """Видаляє застарілі записи з списків очікуючих"""
        current_time = datetime.datetime.now()
        
        # Очищаємо застарілі тривоги
        self.pending_alerts = [
            alert for alert in self.pending_alerts
            if (current_time - alert['time']).total_seconds() <= MASS_ALERT_TIME_WINDOW * 60
        ]
        
        # Очищаємо застарілі відбої
        self.pending_ends = [
            end for end in self.pending_ends
            if (current_time - end['time']).total_seconds() <= MASS_END_TIME_WINDOW * 60
        ]

    def get_pending_alert_cities(self):
        """Повертає унікальні міста з очікуючих тривог"""
        return list(set(alert['city'] for alert in self.pending_alerts))

    def get_pending_end_cities(self):
        """Повертає унікальні міста з очікуючих відбоїв"""
        return list(set(end['city'] for end in self.pending_ends))

    def clear_pending_alerts(self):
        """Очищає список очікуючих тривог"""
        self.pending_alerts.clear()
        self.last_mass_alert_time = datetime.datetime.now()

    def clear_pending_ends(self):
        """Очищає список очікуючих відбоїв"""
        self.pending_ends.clear()
        self.last_mass_end_time = datetime.datetime.now()

    async def send_alert(self, text):
        """Надсилає повідомлення про тривогу"""
        try:
            await self.publisher.send_simple_message(text)
            logging.info(f"📤 Надіслано повідомлення: {text}")
        except Exception as e:
            logging.error(f"❌ Помилка надсилання повідомлення: {e}")

    async def monitor(self, interval=30):
        """Основний цикл моніторингу тривог"""
        logging.info(f"🚨 Моніторинг тривог запущений з інтервалом {interval} сек")
        
        while True:
            try:
                logging.info("🔍 Перевіряємо тривоги...")
                self.last_check_time = datetime.datetime.now(datetime.timezone.utc)
                
                # Отримуємо дані з API
                alerts_data = await self.fetch_alerts()
                
                if not alerts_data:
                    logging.warning("⚠️ Не отримано дані з API")
                    await asyncio.sleep(interval)
                    continue
                
                # Обробляємо формат даних
                if isinstance(alerts_data, dict) and 'alerts' in alerts_data:
                    alerts_list = alerts_data['alerts']
                elif isinstance(alerts_data, list):
                    alerts_list = alerts_data
                else:
                    logging.warning(f"⚠️ Неочікуваний формат даних: {type(alerts_data)}")
                    await asyncio.sleep(interval)
                    continue
                
                # Групуємо тривоги по містах
                city_alerts = self.group_alerts_by_city(alerts_list)
                
                # Формуємо поточні активні міста
                current_cities = set()
                for city_name, city_data in city_alerts.items():
                    if city_data['active_alerts']:  # Є активні тривоги
                        current_cities.add(city_name)
                
                # При першому запуску просто зберігаємо поточні тривоги
                if self.is_first_run:
                    logging.info("🚀 Перший запуск - зберігаємо поточні тривоги без надсилання")
                    self.prev_alerts = current_cities
                    self.is_first_run = False
                    
                    # Логуємо поточні тривоги
                    if current_cities:
                        logging.info(f"📊 Поточні активні міста: {', '.join(current_cities)}")
                    else:
                        logging.info("📊 Активних тривог немає")
                    
                    await asyncio.sleep(interval)
                    continue
                
                # Знаходимо нові та завершені тривоги по містах
                new_cities = current_cities - self.prev_alerts
                ended_cities = self.prev_alerts - current_cities
                
                # Логуємо статистику
                if new_cities:
                    logging.info(f"🚨 Знайдено {len(new_cities)} нових міст з тривогою: {', '.join(new_cities)}")
                
                if ended_cities:
                    logging.info(f"✅ Знайдено {len(ended_cities)} міст з відбоєм тривоги: {', '.join(ended_cities)}")
                
                # Очищаємо застарілі записи
                self.cleanup_old_pending()
                
                # Додаємо нові тривоги та відбої до очікуючих
                if new_cities:
                    self.add_to_pending_alerts(list(new_cities))
                
                if ended_cities:
                    self.add_to_pending_ends(list(ended_cities))
                
                # Перевіряємо чи потрібно відправити масові повідомлення
                pending_alert_cities = self.get_pending_alert_cities()
                pending_end_cities = self.get_pending_end_cities()
                
                # Масові тривоги
                if len(pending_alert_cities) >= MASS_ALERT_THRESHOLD:
                    cities_list = ', '.join(sorted(pending_alert_cities))
                    message = f"🚨 <b>Повітряна тривога</b> — {cities_list}"
                    await self.send_alert(message)
                    logging.info(f"📤 Надіслано масову тривогу для {len(pending_alert_cities)} міст")
                    self.clear_pending_alerts()
                elif new_cities:
                    # Окремі тривоги (тільки якщо не було масової)
                    for city in new_cities:
                        message = f"🚨 <b>Повітряна тривога</b> — {city}"
                        await self.send_alert(message)
                
                # Масові відбої
                if len(pending_end_cities) >= MASS_END_THRESHOLD:
                    cities_list = ', '.join(sorted(pending_end_cities))
                    message = f"✅ <b>Відбій повітряної тривоги</b> — {cities_list}"
                    await self.send_alert(message)
                    logging.info(f"📤 Надіслано масовий відбій для {len(pending_end_cities)} міст")
                    self.clear_pending_ends()
                elif ended_cities:
                    # Окремі відбої (тільки якщо не було масового)
                    for city in ended_cities:
                        message = f"✅ <b>Відбій повітряної тривоги</b> — {city}"
                        await self.send_alert(message)
                
                # Оновлюємо попередні тривоги
                self.prev_alerts = current_cities
                
                # Логуємо загальну статистику
                if current_cities:
                    logging.info(f"📊 Загалом активних міст: {len(current_cities)} ({', '.join(current_cities)})")
                else:
                    logging.info("📊 Активних тривог немає")
                
            except Exception as e:
                logging.error(f"❌ Помилка моніторингу тривог: {e}")
                import traceback
                logging.error(f"Деталі помилки: {traceback.format_exc()}")
            
            await asyncio.sleep(interval)

