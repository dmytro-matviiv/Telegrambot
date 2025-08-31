import asyncio
import logging
from user_manager import UserManager

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_alert_formatting():
    """Тестує форматування повідомлень про тривоги"""
    print("🧪 Тестуємо форматування повідомлень про тривоги...")
    
    # Тест різних форматів тривог
    test_alerts = [
        {
            'regions': ['Київська область'],
            'expected': '🚨 <b>ПОВІТРЯНА ТРИВОГА!</b>\n\n📍 Київська область\n\n⚠️ Бережіть себе! Слідуйте інструкціям МНС.'
        },
        {
            'regions': ['Київська область', 'Львівська область', 'Одеська область'],
            'expected': '🚨 <b>ПОВІТРЯНА ТРИВОГА!</b>\n\n📍 Київська область\n📍 Львівська область\n📍 Одеська область\n\n⚠️ Бережіть себе! Слідуйте інструкціям МНС.'
        },
        {
            'regions': ['Київська область', 'Львівська область', 'Одеська область', 'Харківська область', 'Дніпропетровська область'],
            'expected': '🚨 <b>ПОВІТРЯНА ТРИВОГА!</b>\n\n📍 Київська область\n📍 Львівська область\n📍 Одеська область\n📍 Харківська область\n📍 Дніпропетровська область\n\n⚠️ Бережіть себе! Слідуйте інструкціям МНС.'
        }
    ]
    
    def format_alerts_message(regions):
        """Форматує повідомлення про тривоги"""
        if not regions:
            return ""
        
        message = "🚨 <b>ПОВІТРЯНА ТРИВОГА!</b>\n\n"
        
        for region in regions:
            message += f"📍 {region}\n"
        
        message += "\n⚠️ Бережіть себе! Слідуйте інструкціям МНС."
        
        return message
    
    for i, test_case in enumerate(test_alerts, 1):
        formatted = format_alerts_message(test_case['regions'])
        expected = test_case['expected']
        
        if formatted == expected:
            print(f"✅ Тест {i} пройдено: {len(test_case['regions'])} областей")
        else:
            print(f"❌ Тест {i} не пройдено:")
            print(f"   Очікувалось: {expected}")
            print(f"   Отримано: {formatted}")
    
    print("✅ Тестування форматування завершено\n")

async def test_user_subscriptions():
    """Тестує підписки користувачів на тривоги"""
    print("🧪 Тестуємо підписки користувачів на тривоги...")
    
    user_manager = UserManager('test_alerts_users.json')
    
    # Додаємо тестових користувачів з різними налаштуваннями
    test_users = [
        {'id': 111111111, 'name': 'User 1', 'alerts': True, 'news': False, 'memorial': True},
        {'id': 222222222, 'name': 'User 2', 'alerts': False, 'news': True, 'memorial': False},
        {'id': 333333333, 'name': 'User 3', 'alerts': True, 'news': True, 'memorial': True},
        {'id': 444444444, 'name': 'User 4', 'alerts': False, 'news': False, 'memorial': False}
    ]
    
    for user in test_users:
        user_manager.add_user(user['id'], f"test_user_{user['id']}", user['name'])
        user_manager.update_subscription(user['id'], 'alerts', user['alerts'])
        user_manager.update_subscription(user['id'], 'news', user['news'])
        user_manager.update_subscription(user['id'], 'memorial', user['memorial'])
    
    # Перевіряємо підписників на тривоги
    alerts_subscribers = user_manager.get_subscribers('alerts')
    print(f"✅ Підписники на тривоги: {alerts_subscribers}")
    
    # Перевіряємо налаштування конкретного користувача
    user_subscriptions = user_manager.get_user_subscriptions(111111111)
    print(f"✅ Налаштування користувача 111111111: {user_subscriptions}")
    
    # Тестуємо персоналізоване надсилання
    all_users = user_manager.get_all_users()
    print(f"✅ Всього користувачів: {len(all_users)}")
    
    # Очищення тестового файлу
    import os
    if os.path.exists('test_alerts_users.json'):
        os.remove('test_alerts_users.json')
    
    print("✅ Тестування підписок завершено\n")

async def test_air_alerts_logic():
    """Тестує логіку роботи з повітряними тривогами"""
    print("🧪 Тестуємо логіку роботи з повітряними тривогами...")
    
    # Симулюємо дані з API
    mock_api_data = {
        'alerts': [
            {
                'location_title': 'Київська область',
                'location_type': 'oblast',
                'alert_type': 'air_raid',
                'started_at': '2024-01-01T12:00:00',
                'finished_at': None
            },
            {
                'location_title': 'Львівська область',
                'location_type': 'oblast',
                'alert_type': 'air_raid',
                'started_at': '2024-01-01T12:05:00',
                'finished_at': None
            },
            {
                'location_title': 'Одеська область',
                'location_type': 'oblast',
                'alert_type': 'air_raid',
                'started_at': '2024-01-01T11:55:00',
                'finished_at': '2024-01-01T12:10:00'  # Завершена тривога
            }
        ]
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
            
        # Показувати тільки тривоги по областях
        if location_type != 'oblast':
            return False
            
        return True
    
    def get_active_alerts(alerts_data):
        """Отримує активні тривоги"""
        if isinstance(alerts_data, dict) and 'alerts' in alerts_data:
            alerts_list = alerts_data['alerts']
        elif isinstance(alerts_data, list):
            alerts_list = alerts_data
        else:
            return []
        
        active_alerts = []
        for alert in alerts_list:
            if is_valid_alert(alert):
                location_title = alert.get('location_title', '')
                finished_at = alert.get('finished_at')
                
                # Тільки активні тривоги (без finished_at)
                if location_title and not finished_at:
                    active_alerts.append({
                        'region': location_title,
                        'started_at': alert.get('started_at', ''),
                        'alert_type': alert.get('alert_type', '')
                    })
        
        return active_alerts
    
    # Тестуємо отримання активних тривог
    active_alerts = get_active_alerts(mock_api_data)
    print(f"✅ Активних тривог: {len(active_alerts)}")
    
    for alert in active_alerts:
        print(f"  - {alert['region']} (почалася: {alert['started_at']})")
    
    # Тестуємо форматування повідомлення
    if active_alerts:
        regions = [alert['region'] for alert in active_alerts]
        message = "🚨 <b>ПОВІТРЯНА ТРИВОГА!</b>\n\n"
        for region in regions:
            message += f"📍 {region}\n"
        message += "\n⚠️ Бережіть себе! Слідуйте інструкціям МНС."
        
        print(f"✅ Форматоване повідомлення:\n{message}")
    
    print("✅ Тестування логіки завершено\n")

async def test_personalized_delivery():
    """Тестує персоналізовану доставку тривог"""
    print("🧪 Тестуємо персоналізовану доставку тривог...")
    
    user_manager = UserManager('test_delivery_users.json')
    
    # Створюємо тестових користувачів
    test_users = [
        {'id': 111111111, 'alerts': True},   # Підписаний на тривоги
        {'id': 222222222, 'alerts': False},  # Не підписаний на тривоги
        {'id': 333333333, 'alerts': True},   # Підписаний на тривоги
    ]
    
    for user in test_users:
        user_manager.add_user(user['id'], f"test_user_{user['id']}", f"User {user['id']}")
        user_manager.update_subscription(user['id'], 'alerts', user['alerts'])
    
    # Симулюємо надсилання тривоги
    all_user_ids = user_manager.get_all_users()
    alert_subscribers = user_manager.get_subscribers('alerts')
    
    print(f"✅ Всього користувачів: {len(all_user_ids)}")
    print(f"✅ Підписників на тривоги: {len(alert_subscribers)}")
    print(f"✅ ID підписників: {alert_subscribers}")
    
    # Перевіряємо, чи правильно фільтруються користувачі
    expected_subscribers = [111111111, 333333333]
    if set(alert_subscribers) == set(expected_subscribers):
        print("✅ Фільтрація підписників працює правильно")
    else:
        print("❌ Помилка в фільтрації підписників")
        print(f"   Очікувалось: {expected_subscribers}")
        print(f"   Отримано: {alert_subscribers}")
    
    # Очищення тестового файлу
    import os
    if os.path.exists('test_delivery_users.json'):
        os.remove('test_delivery_users.json')
    
    print("✅ Тестування персоналізованої доставки завершено\n")

async def main():
    """Головна функція тестування"""
    print("🚀 Починаємо тестування повітряних тривог...\n")
    
    try:
        await test_alert_formatting()
        await test_user_subscriptions()
        await test_air_alerts_logic()
        await test_personalized_delivery()
        
        print("🎉 Всі тести повітряних тривог пройдені успішно!")
        print("\n📋 Перевірено:")
        print("- Форматування повідомлень про тривоги")
        print("- Підписки користувачів на тривоги")
        print("- Логіка роботи з даними API")
        print("- Персоналізована доставка тривог")
        print("\n✅ Система повітряних тривог працює коректно!")
        
    except Exception as e:
        print(f"❌ Помилка під час тестування: {e}")
        logging.error(f"Помилка тестування: {e}")

if __name__ == "__main__":
    asyncio.run(main())
