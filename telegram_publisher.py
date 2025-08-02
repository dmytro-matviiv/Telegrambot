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

    async def download_video(self, video_url: str) -> Optional[bytes]:
        """Завантажує відео з URL"""
        try:
            if not video_url:
                return None
                
            async with self.session.get(video_url, timeout=30) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    logger.warning(f"Не вдалося завантажити відео: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Помилка при завантаженні відео: {e}")
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
        source_key = news_item.get('source_key', '').lower()
        is_international = any(keyword in source_key for keyword in ['bbc', 'reuters', 'cnn', 'ap', 'guardian', 'nyt', 'washington', 'al_jazeera', 'dw', 'defense', 'war_zone'])
        
        if is_international:
            hashtags = ["#Ukraine", "#War", "#BreakingNews", "#International", "#WorldNews", "#Conflict", "#Military", "#Defense", "#Russia", "#Zelensky"]
        else:
            hashtags = ["#Україна", "#Новини", "#Офіційно", "#Важливо", "#ГарячіНовини", "#UAnews", "#Ukraine", "#BreakingNews"]
        
        random.shuffle(hashtags)
        text_parts.append(f"\n\n{' '.join(hashtags[:3])} {end_emoji}")

        text = "\n".join(text_parts)

        # Обмежуємо довжину
        if len(text) > MAX_TEXT_LENGTH:
            text = text[:MAX_TEXT_LENGTH-3] + "..."

        return text

    def clean_html(self, text: str) -> str:
        soup = BeautifulSoup(text, 'html.parser')
        for tag in soup.find_all(True):
            if tag.name not in ['b', 'i', 'a', 'u', 's', 'code', 'pre']:
                tag.unwrap()
        return str(soup)

    async def publish_news(self, news_item: Dict) -> bool:
        """Публікує новину в Telegram канал"""
        try:
            text = self.format_news_text(news_item)
            
            # Перевіряємо чи є відео
            video_url = news_item.get('video_url', '')
            video_data = None
            if video_url:
                video_data = await self.download_video(video_url)
            
            # Якщо є відео, публікуємо його
            if video_data:
                await self.bot.send_video(
                    chat_id=CHANNEL_ID,
                    video=video_data,
                    caption=text,
                    parse_mode='HTML'
                )
                logger.info(f"Опубліковано новину з відео: {news_item.get('title', '')[:50]}...")
                return True
            
            # Якщо немає відео, публікуємо з зображенням
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
        published_count = 0
        for news_item in news_list:
            # Очищення тексту від непідтримуваних тегів
            news_item['title'] = self.clean_html(news_item.get('title', ''))
            news_item['description'] = self.clean_html(news_item.get('description', ''))
            news_item['full_text'] = self.clean_html(news_item.get('full_text', ''))
            text = self.format_news_text(news_item)
            text = self.clean_html(text)
            
            # Перевіряємо чи є відео
            video_url = news_item.get('video_url', '')
            video_data = None
            if video_url:
                video_data = await self.download_video(video_url)
            
            try:
                # Якщо є відео, публікуємо його
                if video_data:
                    await self.bot.send_video(
                        chat_id=CHANNEL_ID,
                        video=video_data,
                        caption=text,
                        parse_mode='HTML'
                    )
                    logger.info(f"Опубліковано новину з відео: {news_item.get('title', '')[:50]}...")
                else:
                    # Якщо немає відео, публікуємо з зображенням
                    image_url = news_item.get('image_url', '')
                    image_data = await self.download_image(image_url)
                    if not image_data:
                        image_data = await self.download_image(DEFAULT_IMAGE_URL)
                    
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
                break  # Публікуємо лише одну успішну новину за раз
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