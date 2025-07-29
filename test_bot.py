#!/usr/bin/env python3
"""
Тестовий скрипт для перевірки роботи українського новинного бота
"""

import asyncio
import logging
from news_collector import NewsCollector
from telegram_publisher import TelegramPublisher
from config import NEWS_SOURCES

# Налаштування логування для тестів
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_news_collection():
    """Тестує збір новин"""
    print("🔍 Тестуємо збір новин...")
    
    collector = NewsCollector()
    
    try:
        # Тестуємо збір з кожного джерела окремо
        for source_key, source_info in NEWS_SOURCES.items():
            print(f"\n📰 Тестуємо {source_info['name']}...")
            
            news = collector.get_news_from_rss(source_key, source_info)
            
            if news:
                print(f"✅ Знайдено {len(news)} новин")
                for i, item in enumerate(news[:3]):  # Показуємо перші 3
                    print(f"  {i+1}. {item.get('title', 'Без заголовка')[:50]}...")
            else:
                print("❌ Новин не знайдено")
        
        # Тестуємо загальний збір
        print(f"\n🔍 Тестуємо загальний збір новин...")
        all_news = collector.collect_all_news()
        print(f"✅ Всього знайдено {len(all_news)} новин")
        
        return all_news
        
    except Exception as e:
        print(f"❌ Помилка при зборі новин: {e}")
        return []

async def test_telegram_connection():
    """Тестує з'єднання з Telegram"""
    print("\n🤖 Тестуємо з'єднання з Telegram...")
    
    publisher = TelegramPublisher()
    
    try:
        success = await publisher.test_connection()
        if success:
            print("✅ Telegram з'єднання працює")
        else:
            print("❌ Помилка з'єднання з Telegram")
        
        await publisher.close()
        return success
        
    except Exception as e:
        print(f"❌ Помилка при тестуванні Telegram: {e}")
        return False

async def test_news_formatting():
    """Тестує форматування новин"""
    print("\n📝 Тестуємо форматування новин...")
    
    publisher = TelegramPublisher()
    
    # Створюємо тестову новину
    test_news = {
        'title': 'Тестова новина від українського бота',
        'description': 'Це тестовий опис новини для перевірки форматування.',
        'full_text': 'Це повний текст тестової новини. Він містить більше інформації та деталей для перевірки роботи бота.',
        'source': 'Тестове джерело',
        'link': 'https://example.com/test-news',
        'image_url': ''
    }
    
    try:
        formatted_text = publisher.format_news_text(test_news)
        print("✅ Форматування працює:")
        print("-" * 50)
        print(formatted_text)
        print("-" * 50)
        
        await publisher.close()
        return True
        
    except Exception as e:
        print(f"❌ Помилка при форматуванні: {e}")
        return False

async def test_single_news_publish():
    """Тестує публікацію однієї новини"""
    print("\n📤 Тестуємо публікацію новини...")
    
    publisher = TelegramPublisher()
    
    # Створюємо тестову новину
    test_news = {
        'title': '🧪 Тестова новина від бота',
        'description': 'Це тестова новина для перевірки роботи бота. Якщо ви бачите це повідомлення, бот працює правильно!',
        'full_text': 'Повний текст тестової новини. Бот успішно збирає, форматує та публікує новини з українських офіційних джерел.',
        'source': 'Тестовий бот',
        'link': 'https://t.me/your_channel',
        'image_url': ''
    }
    
    try:
        success = await publisher.publish_news(test_news)
        if success:
            print("✅ Тестова новина опублікована успішно")
        else:
            print("❌ Помилка при публікації тестової новини")
        
        await publisher.close()
        return success
        
    except Exception as e:
        print(f"❌ Помилка при публікації: {e}")
        return False

async def main():
    """Головна функція тестування"""
    print("🇺🇦 Тестування українського новинного бота")
    print("=" * 60)
    
    # Тестуємо збір новин
    news = await test_news_collection()
    
    # Тестуємо з'єднання з Telegram
    telegram_ok = await test_telegram_connection()
    
    # Тестуємо форматування
    formatting_ok = await test_news_formatting()
    
    # Тестуємо публікацію (тільки якщо Telegram працює)
    publish_ok = False
    if telegram_ok:
        publish_ok = await test_single_news_publish()
    
    # Підсумки
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТИ ТЕСТУВАННЯ:")
    print(f"🔍 Збір новин: {'✅' if news else '❌'}")
    print(f"🤖 Telegram з'єднання: {'✅' if telegram_ok else '❌'}")
    print(f"📝 Форматування: {'✅' if formatting_ok else '❌'}")
    print(f"📤 Публікація: {'✅' if publish_ok else '❌'}")
    
    if news and telegram_ok and formatting_ok:
        print("\n🎉 Всі тести пройшли успішно! Бот готовий до роботи.")
        print("💡 Запустіть main.py для початку роботи бота.")
    else:
        print("\n⚠️ Деякі тести не пройшли. Перевірте налаштування.")
        if not telegram_ok:
            print("   - Перевірте BOT_TOKEN та CHANNEL_ID в .env файлі")
        if not news:
            print("   - Перевірте інтернет-з'єднання та доступність джерел новин")

if __name__ == "__main__":
    asyncio.run(main()) 