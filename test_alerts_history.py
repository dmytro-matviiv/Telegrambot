import asyncio
import aiohttp
import logging
from config import ALERTS_API_TOKEN
import datetime

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

API_URL = "https://api.alerts.in.ua/v1/alerts/active.json"

# Окуповані території та зони бойових дій (не показувати тривоги)
OCCUPIED_AND_COMBAT_AREAS = {
    'Донецька область', 'Луганська область', 'АР Крим', 'Автономна Республіка Крим',
    'Херсонська область', 'Запорізька область', 'Харківська область'
}

def is_valid_alert(alert):
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

async def test_alerts_history():
    """Тестує API тривог та аналізує фільтри"""
    headers = {}
    params = {}
    token = ALERTS_API_TOKEN
    if not token:
        logger.error("ALERTS_API_TOKEN не заданий!")
        return
    
    headers['Authorization'] = f'Bearer {token}'
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL, headers=headers, params=params, timeout=15) as resp:
                logger.info(f"Статус відповіді: {resp.status}")
                
                if resp.status == 200:
                    data = await resp.json()
                    logger.info(f"✅ Отримано дані з API")
                    
                    # Перевіряємо формат даних
                    if isinstance(data, dict) and 'alerts' in data:
                        alerts_list = data['alerts']
                    elif isinstance(data, list):
                        alerts_list = data
                    else:
                        logger.error(f"Неочікуваний формат даних: {type(data)}")
                        return
                    
                    logger.info(f"Кількість всіх тривог: {len(alerts_list)}")
                    
                    # Аналізуємо всі тривоги
                    all_air_raid = []
                    filtered_air_raid = []
                    occupied_air_raid = []
                    
                    for alert in alerts_list:
                        if isinstance(alert, dict):
                            alert_type = alert.get('alert_type', '')
                            location_title = alert.get('location_title', '')
                            location_type = alert.get('location_type', '')
                            finished_at = alert.get('finished_at')
                            started_at = alert.get('started_at', '')
                            
                            if alert_type == 'air_raid' and location_type == 'oblast' and not finished_at:
                                all_air_raid.append({
                                    'location': location_title,
                                    'started_at': started_at
                                })
                                
                                # Перевіряємо фільтри
                                if location_title in OCCUPIED_AND_COMBAT_AREAS:
                                    occupied_air_raid.append({
                                        'location': location_title,
                                        'started_at': started_at
                                    })
                                else:
                                    filtered_air_raid.append({
                                        'location': location_title,
                                        'started_at': started_at
                                    })
                    
                    logger.info(f"🚨 Всі активні повітряні тривоги ({len(all_air_raid)}):")
                    for alert in all_air_raid:
                        logger.info(f"   {alert['location']} (почалася: {alert['started_at']})")
                    
                    if occupied_air_raid:
                        logger.info(f"🚫 Тривоги в окупованих територіях ({len(occupied_air_raid)}):")
                        for alert in occupied_air_raid:
                            logger.info(f"   {alert['location']} (почалася: {alert['started_at']})")
                    
                    if filtered_air_raid:
                        logger.info(f"✅ Тривоги які бот покаже ({len(filtered_air_raid)}):")
                        for alert in filtered_air_raid:
                            logger.info(f"   {alert['location']} (почалася: {alert['started_at']})")
                    else:
                        logger.info("✅ Активних тривог для показу немає")
                        
                else:
                    logger.error(f"❌ Помилка при запиті до alerts.in.ua: {resp.status}")
                    
    except Exception as e:
        logger.error(f"Помилка: {e}")

if __name__ == "__main__":
    print("🧪 Аналіз тривог та фільтрів...")
    asyncio.run(test_alerts_history())
