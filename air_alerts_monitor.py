import asyncio
import aiohttp
import logging
import os
from config import ALERTS_API_TOKEN
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
        alert_type = alert.get('alert_type', '')
        finished_at = alert.get('finished_at')
        
        # Показувати тільки повітряні тривоги
        if alert_type != 'air_raid':
            return False
            
        # Показувати тільки активні тривоги (без finished_at)
        if finished_at:
            return False
            
        # Не показувати тривоги в окупованих територіях
        occupied_areas = {
            'Луганська область', 'АР Крим', 'Автономна Республіка Крим'
        }
        
        if location_title in occupied_areas:
            return False
            
        return True


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
                
                # Фільтруємо та обробляємо тривоги
                current_alerts = set()
                current_alerts_dict = {}
                
                for alert in alerts_list:
                    if not self.is_valid_alert(alert):
                        continue
                        
                    location_title = alert.get('location_title', '')
                    alert_type = alert.get('alert_type', '')
                    
                    key = (location_title, alert_type)
                    current_alerts.add(key)
                    current_alerts_dict[key] = alert
                
                # При першому запуску просто зберігаємо поточні тривоги
                if self.is_first_run:
                    logging.info("🚀 Перший запуск - зберігаємо поточні тривоги без надсилання")
                    self.prev_alerts = current_alerts
                    self.is_first_run = False
                    
                    # Логуємо поточні тривоги
                    if current_alerts:
                        locations = [key[0] for key in current_alerts]
                        logging.info(f"📊 Поточні активні тривоги: {', '.join(locations)}")
                    else:
                        logging.info("📊 Активних тривог немає")
                    
                    await asyncio.sleep(interval)
                    continue
                
                # Знаходимо нові та завершені тривоги
                new_alerts = current_alerts - self.prev_alerts
                ended_alerts = self.prev_alerts - current_alerts
                
                # Логуємо статистику
                if new_alerts:
                    locations = [key[0] for key in new_alerts]
                    logging.info(f"🚨 Знайдено {len(new_alerts)} нових тривог: {', '.join(locations)}")
                
                if ended_alerts:
                    locations = [key[0] for key in ended_alerts]
                    logging.info(f"✅ Знайдено {len(ended_alerts)} завершених тривог: {', '.join(locations)}")
                
                # Надсилаємо повідомлення про нові тривоги
                for key in new_alerts:
                    alert = current_alerts_dict[key]
                    location = alert.get('location_title', '')
                    started_at = alert.get('started_at', '')
                    
                    # Формуємо повідомлення
                    message = f"🚨 <b>Повітряна тривога</b> — {location}"
                    
                    # Додаємо час початку, якщо є
                    if started_at:
                        try:
                            started_dt = datetime.datetime.strptime(started_at[:19], "%Y-%m-%dT%H:%M:%S")
                            time_str = started_dt.strftime("%H:%M")
                            message += f" (з {time_str})"
                        except:
                            pass
                    
                    await self.send_alert(message)
                
                # Надсилаємо повідомлення про завершені тривоги
                for key in ended_alerts:
                    location, alert_type = key
                    if alert_type == 'air_raid':
                        message = f"✅ <b>Відбій повітряної тривоги</b> — {location}"
                        await self.send_alert(message)
                
                # Оновлюємо попередні тривоги
                self.prev_alerts = current_alerts
                
                # Логуємо загальну статистику
                if current_alerts:
                    locations = [key[0] for key in current_alerts]
                    logging.info(f"📊 Загалом активних тривог: {len(current_alerts)} ({', '.join(locations)})")
                else:
                    logging.info("📊 Активних тривог немає")
                
            except Exception as e:
                logging.error(f"❌ Помилка моніторингу тривог: {e}")
                import traceback
                logging.error(f"Деталі помилки: {traceback.format_exc()}")
            
            await asyncio.sleep(interval)

