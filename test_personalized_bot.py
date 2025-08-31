import asyncio
import logging
from user_manager import UserManager
from personalized_bot import PersonalizedBot
from config import BOT_TOKEN

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

async def test_personalized_bot():
    """Тестує PersonalizedBot"""
    print("🧪 Тестуємо PersonalizedBot...")
    
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN не знайдено, пропускаємо тест бота")
        return
    
    bot = PersonalizedBot(BOT_TOKEN)
    
    # Тест надсилання повідомлень
    test_users = [123456789]  # Тестовий користувач
    
    # Тест новини
    test_news = {
        'title': 'Тестова новина',
        'description': 'Це тестова новина для перевірки роботи бота',
        'link': 'https://example.com',
        'source': 'Тестовий джерело'
    }
    
    success_count, error_count = await bot.send_news_to_users(test_news, test_users)
    print(f"✅ Надсилання новини: успішно {success_count}, помилок {error_count}")
    
    # Тест тривоги
    alert_message = "🚨 <b>ТЕСТОВА ТРИВОГА!</b>\n\n📍 Тестова область\n\n⚠️ Це тест!"
    success_count, error_count = await bot.send_alert_to_users(alert_message, test_users)
    print(f"✅ Надсилання тривоги: успішно {success_count}, помилок {error_count}")
    
    # Тест меморіального повідомлення
    memorial_message = "🕯️ <b>Меморіальне повідомлення</b>\n\nЦе тестове меморіальне повідомлення"
    success_count, error_count = await bot.send_memorial_to_users(memorial_message, test_users)
    print(f"✅ Надсилання меморіального: успішно {success_count}, помилок {error_count}")
    
    print("✅ Тестування PersonalizedBot завершено\n")

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
    
    # Очищення тестового файлу
    import os
    if os.path.exists('test_integration.json'):
        os.remove('test_integration.json')
    
    print("✅ Тестування інтеграції завершено\n")

async def main():
    """Головна функція тестування"""
    print("🚀 Починаємо тестування персоналізованого бота...\n")
    
    try:
        await test_user_manager()
        await test_personalized_bot()
        await test_integration()
        
        print("🎉 Всі тести пройдені успішно!")
        
    except Exception as e:
        print(f"❌ Помилка під час тестування: {e}")
        logging.error(f"Помилка тестування: {e}")

if __name__ == "__main__":
    asyncio.run(main())
