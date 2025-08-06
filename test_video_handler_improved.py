#!/usr/bin/env python3
"""
Покращений тестовий обробник для публікації новин з відео
Знаходить новини і публікує першу з відео, використовуючи покращену логіку
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timezone
from typing import List, Dict, Optional

# Додаємо шлях до поточної директорії для імпорту модулів
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import BOT_TOKEN, CHANNEL_ID, NEWS_SOURCES
from news_collector import NewsCollector
from telegram_publisher import TelegramPublisher

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ImprovedVideoHandler:
    def __init__(self):
        self.news_collector = NewsCollector()
        self.telegram_publisher = TelegramPublisher()
        
    async def find_and_publish_video_news(self):
        """Знаходить новини і публікує першу з відео з покращеною логікою"""
        try:
            logger.info("🔍 Починаю пошук новин...")
            
            # Збираємо всі новини без фільтрації
            all_news = []
            sources_with_news = []
            
            # Збираємо новини з кожного джерела
            for source_key, source_info in NEWS_SOURCES.items():
                try:
                    news = self.news_collector.get_news_from_rss(source_key, source_info)
                    if news:
                        sources_with_news.append((source_key, source_info, news))
                        all_news.extend(news)
                        logger.info(f"✅ {source_info['name']}: знайдено {len(news)} новин")
                except Exception as e:
                    logger.error(f"❗ Помилка при зборі новин з {source_key}: {e}")
            
            logger.info(f"📰 Знайдено {len(all_news)} новин загалом")
            
            if not all_news:
                logger.warning("⚠️ Новини не знайдено")
                return False
            
            # Шукаємо новини з відео
            news_with_video = []
            for news in all_news:
                video_url = news.get('video_url', '')
                if video_url:
                    news_with_video.append(news)
                    logger.info(f"🎥 Знайдено новину з відео: {news.get('title', '')[:50]}...")
            
            if not news_with_video:
                logger.warning("⚠️ Новини з відео не знайдено")
                return False
            
            # Беремо першу новину з відео
            first_video_news = news_with_video[0]
            logger.info(f"📤 Публікую першу новину з відео: {first_video_news.get('title', '')[:50]}...")
            
            # Публікуємо новину з покращеною логікою
            success = await self.publish_news_with_video_preview(first_video_news)
            
            if success:
                logger.info("✅ Новину з відео успішно опубліковано!")
                return True
            else:
                logger.error("❌ Помилка при публікації новини з відео")
                return False
                
        except Exception as e:
            logger.error(f"❌ Помилка в покращеному обробнику: {e}")
            return False

    async def publish_news_with_video_preview(self, news_item: Dict) -> bool:
        """Публікує новину з покращеною обробкою відео"""
        try:
            from telegram_publisher import TelegramPublisher
            
            text = self.telegram_publisher.format_news_text(news_item)
            
            # Перевіряємо чи є відео
            video_url = news_item.get('video_url', '')
            video_published = False
            
            if video_url:
                logger.info(f"🎬 Обробляємо відео: {video_url[:50]}...")
                
                # Спробуємо завантажити та опублікувати відео
                try:
                    video_data = await self.telegram_publisher.extract_and_download_video(video_url)
                    if video_data:
                        await self.telegram_publisher.bot.send_video(
                            chat_id=CHANNEL_ID,
                            video=video_data,
                            caption=text,
                            parse_mode='HTML',
                            supports_streaming=True
                        )
                        logger.info(f"🎥 Опубліковано новину з відео: {news_item.get('title', '')[:50]}...")
                        video_published = True
                    else:
                        logger.warning(f"Не вдалося завантажити відео: {video_url}")
                        
                        # Для iframe відео спробуємо створити превью
                        if 'iframe' in video_url.lower():
                            logger.info("🎬 Створюємо відео превью для iframe...")
                            preview_video = await self.telegram_publisher.create_video_preview(video_url)
                            if preview_video:
                                try:
                                    await self.telegram_publisher.bot.send_video(
                                        chat_id=CHANNEL_ID,
                                        video=preview_video,
                                        caption=text,
                                        parse_mode='HTML',
                                        supports_streaming=True
                                    )
                                    logger.info(f"🎥 Опубліковано новину з відео превью: {news_item.get('title', '')[:50]}...")
                                    video_published = True
                                except Exception as e:
                                    logger.warning(f"Не вдалося надіслати відео превью: {e}")
                        
                except Exception as e:
                    logger.warning(f"Не вдалося надіслати відео файл: {e}")
                    # Спробуємо надіслати як документ якщо відео не підтримується
                    try:
                        if 'video_data' in locals() and video_data:
                            await self.telegram_publisher.bot.send_document(
                                chat_id=CHANNEL_ID,
                                document=video_data,
                                caption=text,
                                parse_mode='HTML'
                            )
                            logger.info(f"📎 Опубліковано новину з відео як документ: {news_item.get('title', '')[:50]}...")
                            video_published = True
                    except Exception as e2:
                        logger.warning(f"Не вдалося надіслати відео як документ: {e2}")
                
                # Якщо не вдалося завантажити відео, додаємо посилання до тексту
                if not video_published:
                    # Розширений список платформ з відповідними іконками
                    video_platforms = {
                        'youtube.com': ('🎬', 'YouTube'), 'youtu.be': ('🎬', 'YouTube'),
                        'vimeo.com': ('🎬', 'Vimeo'), 'facebook.com': ('📱', 'Facebook'),
                        'dailymotion.com': ('🎬', 'Dailymotion'), 'rutube.ru': ('🎬', 'Rutube'),
                        'vk.com': ('📱', 'VK'), 'ok.ru': ('📱', 'OK.ru'),
                        'tsn.ua': ('📺', 'ТСН'), 'espreso.tv': ('📺', 'Еспресо'),
                        '24tv.ua': ('📺', '24 Канал'), 'hromadske.ua': ('📺', 'Громадське'),
                        'suspilne.media': ('📺', 'Суспільне'), 'pravda.com.ua': ('📰', 'Правда'),
                        'ukrinform.ua': ('📰', 'Укрінформ'), 'fakty.com.ua': ('📺', 'Факти ICTV'),
                        'obozrevatel.com': ('📰', 'Обозреватель'), 'censor.net': ('📰', 'Цензор.НЕТ'),
                        'strana.ua': ('📰', 'Страна.ua'), 'lb.ua': ('📰', 'Левый берег')
                    }
                    
                    platform_found = False
                    for platform, (icon, name) in video_platforms.items():
                        if platform in video_url.lower():
                            text += f"\n\n{icon} <a href=\"{video_url}\">Дивитися на {name}</a>"
                            platform_found = True
                            break
                    
                    if not platform_found:
                        text += f"\n\n🎥 <a href=\"{video_url}\">Дивитися відео</a>"
                    
                    logger.info(f"Додано посилання на відео: {video_url[:50]}...")
            
            # Якщо відео не було опубліковано окремо, публікуємо з зображенням
            if not video_published:
                image_url = news_item.get('image_url', '')
                image_data = await self.telegram_publisher.download_image(image_url)

                # Якщо не вдалося завантажити фото, пробуємо стандартне
                if not image_data:
                    image_data = await self.telegram_publisher.download_image('default_ua_news.jpg')

                if image_data:
                    # Публікуємо з зображенням
                    await self.telegram_publisher.bot.send_photo(
                        chat_id=CHANNEL_ID,
                        photo=image_data,
                        caption=text,
                        parse_mode='HTML'
                    )
                    logger.info(f"Опубліковано новину з зображенням: {news_item.get('title', '')[:50]}...")
                else:
                    # Публікуємо без зображення
                    await self.telegram_publisher.bot.send_message(
                        chat_id=CHANNEL_ID,
                        text=text,
                        parse_mode='HTML',
                        disable_web_page_preview=False
                    )
                    logger.info(f"Опубліковано новину без зображення: {news_item.get('title', '')[:50]}...")
            
            return True
            
        except Exception as e:
            logger.error(f"Помилка при публікації новини: {e}")
            return False

async def main():
    """Головна функція покращеного тестового обробника"""
    logger.info("🚀 Запуск покращеного тестового обробника для новин з відео")
    
    handler = ImprovedVideoHandler()
    
    try:
        success = await handler.find_and_publish_video_news()
        
        if success:
            logger.info("✅ Покращений тестовий обробник успішно завершив роботу")
        else:
            logger.warning("⚠️ Покращений тестовий обробник завершив роботу без публікації")
            
    except KeyboardInterrupt:
        logger.info("🛑 Покращений тестовий обробник зупинено користувачем")
    except Exception as e:
        logger.error(f"❌ Критична помилка в покращеному тестовому обробнику: {e}")
    finally:
        # Закриваємо сесії
        try:
            if hasattr(handler.news_collector, 'session') and handler.news_collector.session:
                await handler.news_collector.session.close()
        except:
            pass
        try:
            if hasattr(handler.telegram_publisher, 'session') and handler.telegram_publisher.session:
                await handler.telegram_publisher.session.close()
        except:
            pass
        logger.info("👋 Покращений тестовий обробник завершив роботу")

if __name__ == "__main__":
    asyncio.run(main()) 