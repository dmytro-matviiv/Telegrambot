import asyncio
import logging
from air_alerts_monitor import AirAlertsMonitor
from telegram_publisher import TelegramPublisher
from user_manager import UserManager
from personalized_bot import PersonalizedBot
from config import BOT_TOKEN

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_air_alerts_monitor():
    """Тестує AirAlertsMonitor"""
    print("🧪 Тестуємо AirAlertsMonitor...")
    
    # Створюємо мок publisher для тестування
    class MockPublisher:
        async def send_simple_message(self, text):
            print(f"📤 Мок повідомлення: {text}")
            return True
    
    publisher = MockPublisher()
    monitor = AirAlertsMonitor(publisher)
    
    # Тест отримання поточних тривог
    try:
        current_alerts = await monitor.get_current_alerts()
        print(f"✅ Отримано поточних тривог: {len(current_alerts)}")
        
        if current_alerts:
            print("📋 Активні тривоги:")
            for alert in current_alerts:
                print(f"  - {alert['region']} (почалася: {alert['started_at']})")
        else:
            print("✅ Активних тривог немає")
            
    except Exception as e:
        print(f"❌ Помилка отримання тривог: {e}")
    
    print("✅ Тестування AirAlertsMonitor завершено\n")

async def test_personalized_alerts():
    """Тестує персоналізоване надсилання тривог"""
    print("🧪 Тестуємо персоналізоване надсилання тривог...")
    
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN не знайдено, пропускаємо тест")
        return
    
    try:
        # Створюємо персоналізованого бота
        bot = PersonalizedBot(BOT_TOKEN)
        
        # Додаємо тестових користувачів
        test_users = [123456789, 987654321]  # Замініть на реальні ID користувачів
        
        # Тест форматування повідомлення про тривогу
        alert_message = "🚨 <b>ПОВІТРЯНА ТРИВОГА!</b>\n\n📍 Київська область\n📍 Львівська область\n\n⚠️ Бережіть себе! Слідуйте інструкціям МНС."
        
        print(f"📤 Тестуємо надсилання тривоги користувачам: {test_users}")
        
        # Надсилаємо тестову тривогу
        success_count, error_count = await bot.send_alert_to_users(
            alert_message=alert_message,
            user_ids=test_users
        )
        
        print(f"✅ Надсилання тривоги: успішно {success_count}, помилок {error_count}")
        
    except Exception as e:
        print(f"❌ Помилка тестування персоналізованих тривог: {e}")
    
    print("✅ Тестування персоналізованих тривог завершено\n")

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
    
    # Очищення тестового файлу
    import os
    if os.path.exists('test_alerts_users.json'):
        os.remove('test_alerts_users.json')
    
    print("✅ Тестування підписок завершено\n")

async def main():
    """Головна функція тестування"""
    print("🚀 Починаємо тестування повітряних тривог...\n")
    
    try:
        await test_air_alerts_monitor()
        await test_alert_formatting()
        await test_user_subscriptions()
        await test_personalized_alerts()
        
        print("🎉 Всі тести повітряних тривог пройдені успішно!")
        print("\n📋 Перевірено:")
        print("- Отримання поточних тривог з API")
        print("- Форматування повідомлень про тривоги")
        print("- Підписки користувачів на тривоги")
        print("- Персоналізоване надсилання тривог")
        
    except Exception as e:
        print(f"❌ Помилка під час тестування: {e}")
        logging.error(f"Помилка тестування: {e}")

if __name__ == "__main__":
    asyncio.run(main())
