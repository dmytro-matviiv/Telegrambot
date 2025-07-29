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

logger = logging.getLogger(__name__)

class TelegramPublisher:
    def __init__(self):
        self.bot = Bot(token=BOT_TOKEN)
        self.session = aiohttp.ClientSession()

    async def download_image(self, image_url: str) -> Optional[bytes]:
        """Завантажує зображення з URL"""
        try:
            if not image_url or image_url == DEFAULT_IMAGE_URL:
                return None
                
            async with self.session.get(image_url, timeout=IMAGE_DOWNLOAD_TIMEOUT) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    logger.warning(f"Не вдалося завантажити зображення: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Помилка при завантаженні зображення: {e}")
            return None

    def format_news_text(self, news_item: Dict) -> str:
        """Форматує текст новини для публікації"""
        title = news_item.get('title', '')
        description = news_item.get('description', '')
        full_text = news_item.get('full_text', '')
        source = news_item.get('source', '')
        link = news_item.get('link', '')
        website = news_item.get('website', link)

        # Очищаємо HTML теги з опису
        if description:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(description, 'html.parser')
            description = soup.get_text()

        # Варіанти емодзі для заголовків
        headline_emojis = ["📰", "✨", "🔥", "📢", "🚀", "🌟", "💡", "🗞️", "📣", "🔔", "🦉", "🦄", "🎯", "🧩", "🦅", "🦾", "🦋", "🦚", "🦜", "🦩", "🦥"]
        end_emojis = ["😉", "🤩", "😎", "👍", "🎉", "🥳", "💙💛", "🇺🇦", "✨", "🌈", "🦄", "🦉", "🦅", "🦾", "🦋", "🦚", "🦜", "🦩", "🦥"]
        headline_emoji = random.choice(headline_emojis)
        end_emoji = random.choice(end_emojis)

        text_parts = []

        # Заголовок (жирний, з емодзі)
        if title:
            text_parts.append(f"{headline_emoji} <b>{title}</b>")

        # Опис або початок повного тексту
        if description:
            text_parts.append(f"\n{description}")
        elif full_text:
            preview = full_text[:300].strip()
            if len(full_text) > 300:
                preview += "..."
            text_parts.append(f"\n{preview}")

        # Джерело як посилання
        if source and link:
            text_parts.append(f"\n📋 Джерело: <a href=\"{link}\">{source}</a>")
        elif source:
            text_parts.append(f"\n📋 Джерело: {source}")

        # Посилання (окремо, якщо потрібно)
        # if link:
        #     text_parts.append(f"\n🔗 Читати повністю: {link}")

        # Хештеги
        hashtags = ["#Україна", "#Новини", "#Офіційно", "#Важливо", "#ГарячіНовини", "#UAnews", "#Ukraine", "#BreakingNews"]
        random.shuffle(hashtags)
        text_parts.append(f"\n\n{' '.join(hashtags[:3])} {end_emoji}")

        text = "\n".join(text_parts)

        # Обмежуємо довжину
        if len(text) > MAX_TEXT_LENGTH:
            text = text[:MAX_TEXT_LENGTH-3] + "..."

        return text

    async def publish_news(self, news_item: Dict) -> bool:
        """Публікує новину в Telegram канал"""
        try:
            text = self.format_news_text(news_item)
            image_url = news_item.get('image_url', '')
            image_data = await self.download_image(image_url)

            # Якщо не вдалося завантажити фото, пробуємо стандартне
            if not image_data:
                image_data = await self.download_image(DEFAULT_IMAGE_URL)

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
        """Публікує кілька новин з затримкою"""
        published_count = 0
        
        for news_item in news_list:
            try:
                success = await self.publish_news(news_item)
                if success:
                    published_count += 1
                
                # Затримка між публікаціями (щоб не спамити)
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Помилка при публікації новини: {e}")
                continue
        
        return published_count

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