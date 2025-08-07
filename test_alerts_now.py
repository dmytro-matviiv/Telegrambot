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

async def test_alerts_api():
    """Тестує API тривог"""
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
                    
                    logger.info(f"Кількість тривог: {len(alerts_list)}")
                    
                    # Показуємо активні повітряні тривоги
                    air_raid_alerts = []
                    for alert in alerts_list:
                        if isinstance(alert, dict):
                            alert_type = alert.get('alert_type', '')
                            location_title = alert.get('location_title', '')
                            location_type = alert.get('location_type', '')
                            finished_at = alert.get('finished_at')
                            started_at = alert.get('started_at', '')
                            
                            if alert_type == 'air_raid' and location_type == 'oblast' and not finished_at:
                                air_raid_alerts.append({
                                    'location': location_title,
                                    'started_at': started_at
                                })
                    
                    if air_raid_alerts:
                        logger.info("🚨 Активні повітряні тривоги:")
                        for alert in air_raid_alerts:
                            logger.info(f"   {alert['location']} (почалася: {alert['started_at']})")
                    else:
                        logger.info("✅ Активних повітряних тривог немає")
                        
                else:
                    logger.error(f"❌ Помилка при запиті до alerts.in.ua: {resp.status}")
                    
    except Exception as e:
        logger.error(f"Помилка: {e}")

if __name__ == "__main__":
    print("🧪 Тестування API тривог...")
    asyncio.run(test_alerts_api())
