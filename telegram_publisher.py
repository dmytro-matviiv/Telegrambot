import asyncio
import aiohttp
import logging
from typing import Dict, Optional
from telegram import Bot
from telegram.error import TelegramError
from PIL import Image
import io
import requests
from config import BOT_TOKEN, CHANNEL_ID, DEFAULT_IMAGE_URL, MAX_TEXT_LENGTH, IMAGE_DOWNLOAD_TIMEOUT
import random
from bs4 import BeautifulSoup
import os
import subprocess
import tempfile

logger = logging.getLogger(__name__)

class TelegramPublisher:
    def __init__(self):
        self.bot = Bot(token=BOT_TOKEN)
        self.session = aiohttp.ClientSession()

    async def download_image(self, image_url: str) -> Optional[bytes]:
        """Завантажує зображення з URL або локального файлу"""
        try:
            if not image_url:
                return None
                
            # Якщо це локальний файл
            if image_url.startswith('file://'):
                file_path = image_url[7:]  # Видаляємо 'file://'
                try:
                    with open(file_path, 'rb') as f:
                        return f.read()
                except Exception as e:
                    logger.error(f"Помилка при читанні локального файлу {file_path}: {e}")
                    return None
            elif image_url == DEFAULT_IMAGE_URL:
                # Для дефолтного зображення
                try:
                    with open('default_ua_news.jpg', 'rb') as f:
                        return f.read()
                except Exception as e:
                    logger.error(f"Помилка при читанні дефолтного зображення: {e}")
                    return None
                
            # Для URL
            async with self.session.get(image_url, timeout=IMAGE_DOWNLOAD_TIMEOUT) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    logger.warning(f"Не вдалося завантажити зображення: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Помилка при завантаженні зображення: {e}")
            return None

    # Видалено логіку завантаження відео

    def format_news_text(self, news_item: Dict) -> str:
        """Форматує текст новини для Telegram, роблячи його цікавим та інформативним"""
        title = news_item.get('title', '')
        description = news_item.get('description', '')
        link = news_item.get('link', '')
        source = news_item.get('source', '')
        category = news_item.get('category', 'unknown')
        
        # Емодзі для категорій
        category_emojis = {
            'world': '🌍',
            'ukraine': '🇺🇦',
            'inventions': '🔬',
            'celebrity': '⭐',
            'war': '⚔️'
        }
        
        category_emoji = category_emojis.get(category, '📰')
        
        # Встановлюємо ліміт для повної інформації в каналі
        max_length = 2000  # Збільшуємо для повної інформації
        
        # Формуємо заголовок з емодзі
        text = f"{category_emoji} <b>{title}</b>\n\n"
        
        if description:
            # Додаємо цікавий вступ до опису
            intro_phrases = [
                "📋 Деталі:",
                "ℹ️ Інформація:",
                "🔍 Що відомо:",
                "📝 Подробиці:",
                "💡 Важливо:",
                "📰 Новина:",
                "🔎 Розкриваємо:"
            ]
            
            # Вибираємо випадковий вступ
            import random
            intro = random.choice(intro_phrases)
            
            # Обрізаємо опис якщо він занадто довгий
            available_length = max_length - len(text) - len(intro) - 150  # Залишаємо місце для посилання та джерела
            
            if len(description) > available_length:
                # Шукаємо кінець речення близько до ліміту
                cut_point = available_length
                for i in range(available_length - 100, available_length + 50):
                    if i < len(description):
                        if description[i] in '.!?':
                            cut_point = i + 1
                            break
                
                description = description[:cut_point].strip()
                if not description.endswith(('.', '!', '?')):
                    description += "..."
            
            text += f"{intro} {description}\n\n"
        
        # Додаємо посилання та джерело з емодзі (менш нав'язливо)
        text += f"📌 Джерело: {source}"
        if link:
            text += f"\n🔗 <a href='{link}'>Детальніше на сайті</a>"
        
        return text

    def clean_html(self, text: str) -> str:
        """Очищає HTML від непідтримуваних тегів та виправляє помилки"""
        try:
            soup = BeautifulSoup(text, 'html.parser')
            
            # Видаляємо всі теги крім дозволених
            for tag in soup.find_all(True):
                if tag.name not in ['b', 'i', 'a', 'u', 's', 'code', 'pre']:
                    tag.unwrap()
            
            # Виправляємо пошкоджені посилання
            for link in soup.find_all('a'):
                href = link.get('href')
                if not href or href.strip() == '':
                    # Якщо href порожній, видаляємо тег
                    link.unwrap()
                elif not href.startswith(('http://', 'https://')):
                    # Якщо href не є валідним URL, видаляємо тег
                    link.unwrap()
            
            # Видаляємо порожні атрибути
            for tag in soup.find_all(True):
                attrs_to_remove = []
                for attr, value in tag.attrs.items():
                    if value == '' or value is None:
                        attrs_to_remove.append(attr)
                for attr in attrs_to_remove:
                    del tag[attr]
            
            return str(soup)
        except Exception as e:
            logger.warning(f"Помилка при очищенні HTML: {e}")
            # Якщо не вдалося обробити HTML, повертаємо простий текст
            return BeautifulSoup(text, 'html.parser').get_text()

    async def publish_news(self, news_item: Dict) -> bool:
        """Публікує новину в Telegram канал"""
        try:
            text = self.format_news_text(news_item)
            
            # Якщо є відео — спробуємо відео
            video_url = news_item.get('video_url', '')
            if video_url:
                video_data = await self.download_video(video_url)
                if video_data:
                    try:
                        await self.bot.send_video(
                            chat_id=CHANNEL_ID,
                            video=video_data,
                            caption=text,
                            parse_mode='HTML'
                        )
                        logger.info(f"Опубліковано новину з відео: {news_item.get('title', '')[:50]}...")
                        return True
                    except Exception as e:
                        logger.warning(f"Не вдалося опублікувати відео, спробуємо фото/текст: {e}")

            # Публікуємо з зображенням
            image_url = news_item.get('image_url', '')
            image_data = await self.download_image(image_url)

            if image_data:
                # Публікуємо з зображенням
                await self.bot.send_photo(
                    chat_id=CHANNEL_ID,
                    photo=image_data,
                    caption=text,
                    parse_mode='HTML'
                )
                logger.info(f"Опубліковано новину з зображенням: {news_item.get('title', '')[:50]}...")
            else:
                # Публікуємо без зображення
                await self.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=text,
                    parse_mode='HTML',
                    disable_web_page_preview=False
                )
                logger.info(f"Опубліковано новину без зображення: {news_item.get('title', '')[:50]}...")
            
            return True
            
        except TelegramError as e:
            logger.error(f"Помилка Telegram при публікації: {e}")
            return False
        except Exception as e:
            logger.error(f"Помилка при публікації новини: {e}")
            return False

    async def publish_multiple_news(self, news_list: list) -> int:
        published_count = 0
        for news_item in news_list:
            # Очищення тексту від непідтримуваних тегів
            news_item['title'] = self.clean_html(news_item.get('title', ''))
            news_item['description'] = self.clean_html(news_item.get('description', ''))
            news_item['full_text'] = self.clean_html(news_item.get('full_text', ''))
            text = self.format_news_text(news_item)
            text = self.clean_html(text)
            
            try:
                # Публікуємо з зображенням
                image_url = news_item.get('image_url', '')
                image_data = await self.download_image(image_url)
                
                if image_data:
                    await self.bot.send_photo(
                        chat_id=CHANNEL_ID,
                        photo=image_data,
                        caption=text,
                        parse_mode='HTML'
                    )
                    logger.info(f"Опубліковано новину з зображенням: {news_item.get('title', '')[:50]}...")
                else:
                    await self.bot.send_message(
                        chat_id=CHANNEL_ID,
                        text=text,
                        parse_mode='HTML',
                        disable_web_page_preview=False
                    )
                    logger.info(f"Опубліковано новину без зображення: {news_item.get('title', '')[:50]}...")
                
                published_count += 1
                # Публікуємо всі новини з різних джерел
            except Exception as e:
                logger.error(f"Помилка Telegram при публікації: {e}")
                continue  # Якщо помилка — пробуємо наступну новину
        return published_count

    async def send_simple_message(self, text: str) -> bool:
        try:
            await self.bot.send_message(
                chat_id=CHANNEL_ID,
                text=text,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            logger.info(f"Сповіщення надіслано: {text[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Помилка при надсиланні сповіщення: {e}")
            return False

    async def test_connection(self) -> bool:
        """Тестує з'єднання з Telegram"""
        try:
            me = await self.bot.get_me()
            logger.info(f"Бот підключений: @{me.username}")
            
            # Перевіряємо доступ до каналу
            chat = await self.bot.get_chat(CHANNEL_ID)
            logger.info(f"Канал знайдено: {chat.title}")
            
            return True
        except Exception as e:
            logger.error(f"Помилка підключення до Telegram: {e}")
            return False

    async def close(self):
        """Закриває з'єднання"""
        await self.session.close()

