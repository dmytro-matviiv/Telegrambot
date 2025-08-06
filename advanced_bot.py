#!/usr/bin/env python3
"""
Розширений український новинний бот з додатковими можливостями
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from advanced_collector import AdvancedNewsCollector
from telegram_publisher import TelegramPublisher
from config import CHECK_INTERVAL, MAX_POSTS_PER_CHECK

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('advanced_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AdvancedNewsBot:
    def __init__(self):
        self.collector = AdvancedNewsCollector()
        self.publisher = TelegramPublisher()
        self.is_running = False
        
        # Ключові слова для фільтрації важливих новин
        self.important_keywords = [
            'президент', 'зеленський', 'кабінет міністрів', 'верховна рада',
            'міністерство', 'уряд', 'закон', 'постанова', 'указу',
            'економіка', 'фінанси', 'оборона', 'безпека', 'коронавірус',
            'вакцина', 'карантин', 'медицина', 'освіта', 'культура'
        ]

    async def check_and_publish_news(self):
        """Основна функція перевірки та публікації новин"""
        try:
            logger.info("🔍 Починаємо розширений збір новин...")
            
            # Збираємо новини з усіх джерел
            news_list = self.collector.collect_all_news_advanced()
            
            if not news_list:
                logger.info("📭 Новин не знайдено")
                return
            
            logger.info(f"📰 Знайдено {len(news_list)} нових новин")
            
            # Видаляємо дублікати
            unique_news = self.collector.remove_duplicates(news_list)
            logger.info(f"🔄 Після видалення дублікатів: {len(unique_news)} новин")
            logger.debug(f"🔄 Унікальні новини для публікації: {[n['title'] for n in unique_news]}")
            
            # Фільтруємо важливі новини
            important_news = self.collector.filter_news_by_keywords(
                unique_news, self.important_keywords
            )
            logger.info(f"⭐ Знайдено {len(important_news)} важливих новин")
            logger.debug(f"⭐ Важливі новини: {[n['title'] for n in important_news]}")
            
            if important_news:
                news_to_publish = important_news[:MAX_POSTS_PER_CHECK]
            else:
                news_to_publish = unique_news[:MAX_POSTS_PER_CHECK]
            
            logger.info(f"📤 Готуємо до публікації {len(news_to_publish)} новин")
            logger.debug(f"📤 Новини для публікації: {[n['title'] for n in news_to_publish]}")
            
            # Публікуємо новини
            published_count = await self.publisher.publish_multiple_news(news_to_publish)
            logger.info(f"✅ Опубліковано {published_count} новин")
            
            # Позначаємо як опубліковані
            for news_item in news_to_publish:
                self.collector.mark_as_published(news_item['id'])
            
            # Виводимо статистику
            stats = self.collector.get_news_statistics()
            logger.info(f"📊 Статистика: {stats['total_sources']} джерел, "
                       f"{stats['published_news_count']} опублікованих новин")
            
        except Exception as e:
            logger.error(f"❌ Помилка при зборі/публікації новин: {e}")

    async def test_connections(self):
        """Тестує з'єднання з усіма сервісами"""
        logger.info("🔧 Тестуємо розширене з'єднання...")
        
        # Тестуємо Telegram
        telegram_ok = await self.publisher.test_connection()
        if telegram_ok:
            logger.info("✅ Telegram з'єднання працює")
        else:
            logger.error("❌ Помилка з'єднання з Telegram")
            return False
        
        # Тестуємо розширений збір новин
        try:
            test_news = self.collector.collect_all_news_advanced()
            logger.info(f"✅ Розширений збір новин працює (знайдено {len(test_news)} новин)")
            
            # Тестуємо фільтрацію
            important_news = self.collector.filter_news_by_keywords(
                test_news, self.important_keywords
            )
            logger.info(f"✅ Фільтрація працює (знайдено {len(important_news)} важливих новин)")
            
        except Exception as e:
            logger.error(f"❌ Помилка розширеного збору новин: {e}")
            return False
        
        return True

    async def run_once(self):
        """Запускає один цикл збору та публікації"""
        await self.check_and_publish_news()

    async def run_continuous(self):
        """Запускає безперервний цикл роботи бота"""
        self.is_running = True
        logger.info("🚀 Розширений бот запущений в режимі безперервної роботи")
        
        while self.is_running:
            try:
                await self.check_and_publish_news()
                logger.info(f"⏰ Очікуємо {CHECK_INTERVAL} секунд до наступної перевірки...")
                await asyncio.sleep(CHECK_INTERVAL)
            except KeyboardInterrupt:
                logger.info("🛑 Отримано сигнал зупинки")
                break
            except Exception as e:
                logger.error(f"❌ Помилка в основному циклі: {e}")
                await asyncio.sleep(60)  # Чекаємо хвилину перед повторною спробою

    def stop(self):
        """Зупиняє бота"""
        self.is_running = False
        logger.info("🛑 Розширений бот зупинено")

async def main():
    """Головна функція розширеного бота"""
    bot = AdvancedNewsBot()
    
    try:
        # Тестуємо з'єднання
        if not await bot.test_connections():
            logger.error("❌ Тестування з'єднань не пройшло. Перевірте налаштування.")
            return
        
        # Запускаємо бота
        await bot.run_continuous()
        
    except KeyboardInterrupt:
        logger.info("🛑 Отримано сигнал зупинки")
    except Exception as e:
        logger.error(f"❌ Критична помилка: {e}")
    finally:
        bot.stop()
        await bot.publisher.close()
        logger.info("👋 Розширений бот завершив роботу")

if __name__ == "__main__":
    print("🇺🇦 Розширений український новинний бот")
    print("=" * 60)
    print("Бот збирає новини з більшої кількості джерел")
    print("та фільтрує важливі новини для пріоритетної публікації.")
    print("=" * 60)
    
    # Запускаємо головну функцію
    asyncio.run(main())