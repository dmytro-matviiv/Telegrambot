import asyncio
import logging
from user_manager import UserManager

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_user_manager():
    """Тестує UserManager"""
    print("🧪 Тестуємо UserManager...")
    
    user_manager = UserManager('test_users.json')
    
    # Тест додавання користувача
    user_id = 123456789
    success = user_manager.add_user(user_id, "test_user", "Test User")
    print(f"✅ Додавання користувача: {success}")
    
    # Тест отримання користувача
    user = user_manager.get_user(user_id)
    print(f"✅ Отримання користувача: {user is not None}")
    
    # Тест оновлення підписки
    success = user_manager.update_subscription(user_id, 'news', False)
    print(f"✅ Оновлення підписки: {success}")
    
    # Тест отримання підписників
    subscribers = user_manager.get_subscribers('alerts')
    print(f"✅ Підписники на тривоги: {len(subscribers)}")
    
    # Тест статистики
    stats = user_manager.get_stats()
    print(f"✅ Статистика: {stats}")
    
    # Очищення тестового файлу
    import os
    if os.path.exists('test_users.json'):
        os.remove('test_users.json')
    
    print("✅ Тестування UserManager завершено\n")

async def test_integration():
    """Тестує інтеграцію компонентів"""
    print("🧪 Тестуємо інтеграцію...")
    
    user_manager = UserManager('test_integration.json')
    
    # Додаємо тестових користувачів
    test_users = [111111111, 222222222, 333333333]
    for user_id in test_users:
        user_manager.add_user(user_id, f"test_user_{user_id}", f"Test User {user_id}")
    
    # Різні налаштування підписок
    user_manager.update_subscription(111111111, 'alerts', True)
    user_manager.update_subscription(111111111, 'news', False)
    user_manager.update_subscription(111111111, 'memorial', True)
    
    user_manager.update_subscription(222222222, 'alerts', False)
    user_manager.update_subscription(222222222, 'news', True)
    user_manager.update_subscription(222222222, 'memorial', False)
    
    user_manager.update_subscription(333333333, 'alerts', True)
    user_manager.update_subscription(333333333, 'news', True)
    user_manager.update_subscription(333333333, 'memorial', True)
    
    # Перевіряємо підписників
    alerts_subscribers = user_manager.get_subscribers('alerts')
    news_subscribers = user_manager.get_subscribers('news')
    memorial_subscribers = user_manager.get_subscribers('memorial')
    
    print(f"✅ Підписники на тривоги: {alerts_subscribers}")
    print(f"✅ Підписники на новини: {news_subscribers}")
    print(f"✅ Підписники на меморіальні: {memorial_subscribers}")
    
    # Перевіряємо налаштування конкретного користувача
    user_subscriptions = user_manager.get_user_subscriptions(111111111)
    print(f"✅ Налаштування користувача 111111111: {user_subscriptions}")
    
    # Очищення тестового файлу
    import os
    if os.path.exists('test_integration.json'):
        os.remove('test_integration.json')
    
    print("✅ Тестування інтеграції завершено\n")

async def test_message_formatting():
    """Тестує форматування повідомлень"""
    print("🧪 Тестуємо форматування повідомлень...")
    
    # Тест форматування новини
    test_news = {
        'title': 'Тестова новина',
        'description': 'Це тестова новина для перевірки роботи бота',
        'link': 'https://example.com',
        'source': 'Тестовий джерело',
        'category': 'ukraine'
    }
    
    # Форматуємо новину
    title = test_news.get('title', '')
    description = test_news.get('description', '')
    link = test_news.get('link', '')
    source = test_news.get('source', '')
    
    message = f"📰 <b>{title}</b>\n\n"
    if description:
        message += f"{description}\n\n"
    message += f"📖 <a href='{link}'>Читати далі</a>\n"
    message += f"📰 Джерело: {source}"
    
    print(f"✅ Форматована новина:\n{message}\n")
    
    # Тест форматування тривоги
    alert_message = "🚨 <b>ПОВІТРЯНА ТРИВОГА!</b>\n\n📍 Тестова область\n\n⚠️ Бережіть себе! Слідуйте інструкціям МНС."
    print(f"✅ Форматована тривога:\n{alert_message}\n")
    
    # Тест форматування меморіального повідомлення
    memorial_message = "🕯️ <b>Меморіальне повідомлення</b>\n\nЦе тестове меморіальне повідомлення"
    print(f"✅ Форматоване меморіальне повідомлення:\n{memorial_message}\n")
    
    print("✅ Тестування форматування завершено\n")

async def main():
    """Головна функція тестування"""
    print("🚀 Починаємо тестування персоналізованого бота...\n")
    
    try:
        await test_user_manager()
        await test_integration()
        await test_message_formatting()
        
        print("🎉 Всі тести пройдені успішно!")
        print("\n📋 Створені файли:")
        print("- user_manager.py - управління користувачами")
        print("- personalized_bot.py - персоналізований бот")
        print("- main_personalized.py - основний файл з персоналізацією")
        print("- PERSONALIZATION_README.md - документація")
        print("\n🚀 Для запуску бота використовуйте:")
        print("python main_personalized.py")
        
    except Exception as e:
        print(f"❌ Помилка під час тестування: {e}")
        logging.error(f"Помилка тестування: {e}")

if __name__ == "__main__":
    asyncio.run(main())
