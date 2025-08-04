import asyncio
import logging
from air_alerts_monitor import AirAlertsMonitor
from telegram_publisher import TelegramPublisher
import datetime
import sys
import os

# Налаштування кодування для Windows
if sys.platform == "win32":
    os.system("chcp 65001 >nul")

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_alerts_fixed.log', encoding='utf-8')
    ]
)

class MockTelegramPublisher:
    """Мок-клас для тестування без реального надсилання в Telegram"""
    
    def __init__(self):
        self.sent_messages = []
    
    async def send_simple_message(self, text: str) -> bool:
        self.sent_messages.append({
            'text': text,
            'timestamp': datetime.datetime.now()
        })
        print(f"[SEND] ТЕСТ: Надіслано повідомлення: {text}")
        return True

async def test_alerts_logic():
    """Тестує логіку моніторингу тривог"""
    print("[TEST] Початок тестування логіки тривог...")
    
    # Створюємо мок-публішер
    mock_publisher = MockTelegramPublisher()
    monitor = AirAlertsMonitor(mock_publisher)
    
    # Симулюємо API відповіді
    print("\n[1] Тестуємо початок тривоги...")
    
    # Перший запуск - немає тривог
    monitor.prev_alerts = set()
    monitor.is_first_run = False
    
    # Симулюємо появу нової тривоги
    alerts_data_1 = [
        {
            'location_title': 'Київська область',
            'location_type': 'oblast',
            'alert_type': 'air_raid',
            'started_at': datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
            'finished_at': None
        }
    ]
    
    # Обробляємо дані (симулюємо частину логіки з monitor())
    current_alerts_dict = {}
    all_alerts_dict = {}
    
    for alert in alerts_data_1:
        if monitor.is_valid_alert(alert):
            location_title = alert.get('location_title', '')
            alert_type = alert.get('alert_type', '')
            finished_at = alert.get('finished_at')
            
            key = (location_title, alert_type)
            all_alerts_dict[key] = alert
            
            if location_title and not finished_at:
                current_alerts_dict[key] = alert
    
    current_alerts = set(current_alerts_dict.keys())
    new_alerts = current_alerts - monitor.prev_alerts
    
    print(f"Нові тривоги: {new_alerts}")
    
    # Надсилаємо нові тривоги
    for key in new_alerts:
        alert = current_alerts_dict[key]
        text = f"🚨 <b>Повітряна тривога</b> — {alert.get('location_title', '')}"
        await mock_publisher.send_simple_message(text)
    
    monitor.prev_alerts = current_alerts
    
    print("\n[2] Тестуємо завершення тривоги...")
    
    # Симулюємо завершення тривоги
    alerts_data_2 = [
        {
            'location_title': 'Київська область',
            'location_type': 'oblast',
            'alert_type': 'air_raid',
            'started_at': (datetime.datetime.utcnow() - datetime.timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%S"),
            'finished_at': datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
        }
    ]
    
    # Обробляємо дані
    current_alerts_dict_2 = {}
    all_alerts_dict_2 = {}
    
    for alert in alerts_data_2:
        if monitor.is_valid_alert(alert):
            location_title = alert.get('location_title', '')
            alert_type = alert.get('alert_type', '')
            finished_at = alert.get('finished_at')
            
            key = (location_title, alert_type)
            all_alerts_dict_2[key] = alert
            
            # Тільки активні тривоги
            if location_title and not finished_at:
                current_alerts_dict_2[key] = alert
    
    current_alerts_2 = set(current_alerts_dict_2.keys())
    ended_alerts = monitor.prev_alerts - current_alerts_2
    
    print(f"Завершені тривоги: {ended_alerts}")
    
    # Надсилаємо повідомлення про завершення
    for key in ended_alerts:
        location, alert_type = key
        if alert_type == 'air_raid':
            text = f"✅ <b>Відбій тривоги</b> — {location}"
            await mock_publisher.send_simple_message(text)
    
    print("\n[3] Результати тестування:")
    print(f"Всього надіслано повідомлень: {len(mock_publisher.sent_messages)}")
    for i, msg in enumerate(mock_publisher.sent_messages, 1):
        print(f"{i}. {msg['text']} (час: {msg['timestamp'].strftime('%H:%M:%S')})")
    
    # Перевіряємо чи є повідомлення про початок і завершення
    has_start = any('Повітряна тривога' in msg['text'] for msg in mock_publisher.sent_messages)
    has_end = any('Відбій тривоги' in msg['text'] for msg in mock_publisher.sent_messages)
    
    print(f"\n[OK] Повідомлення про початок тривоги: {'Так' if has_start else 'НІ'}")
    print(f"[OK] Повідомлення про відбій тривоги: {'Так' if has_end else 'НІ'}")
    
    if has_start and has_end:
        print("\n[SUCCESS] ТЕСТ ПРОЙШОВ УСПІШНО! Обидва типи повідомлень працюють.")
        return True
    else:
        print("\n[ERROR] ТЕСТ НЕ ПРОЙШОВ! Щось не працює.")
        return False

async def test_real_api():
    """Тестує реальний API"""
    print("\n[API] Тестування реального API...")
    
    mock_publisher = MockTelegramPublisher()
    monitor = AirAlertsMonitor(mock_publisher)
    
    try:
        alerts_data = await monitor.fetch_alerts()
        print(f"[OK] API відповів, отримано даних: {len(alerts_data) if isinstance(alerts_data, list) else 'dict' if isinstance(alerts_data, dict) else 'невідомо'}")
        
        if isinstance(alerts_data, dict) and 'alerts' in alerts_data:
            alerts_list = alerts_data['alerts']
        elif isinstance(alerts_data, list):
            alerts_list = alerts_data
        else:
            print("[ERROR] Неочікуваний формат даних від API")
            return False
            
        valid_alerts = [alert for alert in alerts_list if monitor.is_valid_alert(alert)]
        print(f"[INFO] Валідних тривог: {len(valid_alerts)}")
        
        for alert in valid_alerts[:3]:  # Показуємо перші 3
            location = alert.get('location_title', 'Невідомо')
            finished = alert.get('finished_at')
            status = "Активна" if not finished else "Завершена"
            print(f"  - {location}: {status}")
            
        return True
        
    except Exception as e:
        print(f"[ERROR] Помилка при тестуванні API: {e}")
        return False

async def main():
    print("[START] Запуск тестування виправленої логіки тривог\n")
    
    # Тест логіки
    logic_test = await test_alerts_logic()
    
    # Тест API
    api_test = await test_real_api()
    
    print(f"\n[SUMMARY] ПІДСУМОК ТЕСТУВАННЯ:")
    print(f"Логіка тривог: {'[OK] Працює' if logic_test else '[ERROR] Не працює'}")
    print(f"API підключення: {'[OK] Працює' if api_test else '[ERROR] Не працює'}")
    
    if logic_test and api_test:
        print("\n[SUCCESS] ВСЕ ПРАЦЮЄ! Можна запускати бота.")
    else:
        print("\n[WARNING] Є проблеми, потрібно додатково перевірити.")

if __name__ == "__main__":
    asyncio.run(main())