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
            
            # Перевіряємо розмір відео перед завантаженням
            async with self.session.head(video_url, timeout=10) as response:
                if response.status != 200:
                    logger.warning(f"Не вдалося отримати заголовки відео: {response.status}")
                    return None
                
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) > 50 * 1024 * 1024:  # 50MB ліміт Telegram
                    logger.warning(f"Відео занадто велике: {content_length} bytes")
                    return None
                
                # Перевіряємо content-type
                content_type = response.headers.get('content-type', '').lower()
                if not any(video_type in content_type for video_type in ['video/', 'application/octet-stream']):
                    logger.warning(f"URL не є відео файлом: {content_type}")
                    return None
                
            # Завантажуємо відео
            async with self.session.get(video_url, timeout=60) as response:
                if response.status == 200:
                    video_data = await response.read()
                    if len(video_data) > 50 * 1024 * 1024:  # Додаткова перевірка розміру
                        logger.warning(f"Відео занадто велике після завантаження: {len(video_data)} bytes")
                        return None
                    logger.info(f"✅ Відео успішно завантажено: {len(video_data)} bytes")
                    return video_data
                else:
                    logger.warning(f"Не вдалося завантажити відео: {response.status}")
                    return None
        except asyncio.TimeoutError:
            logger.error(f"Таймаут при завантаженні відео: {video_url}")
            return None
        except Exception as e:
            logger.error(f"Помилка при завантаженні відео: {e}")
            return None

    def extract_direct_video_url(self, video_url: str) -> Optional[str]:
        """Витягує прямий URL відео з iframe або embed посилань"""
        try:
            if not video_url:
                return None
            
            # Розширений список платформ, які не підтримують пряме завантаження
            embed_platforms = [
                'youtube.com', 'youtu.be', 'vimeo.com', 'facebook.com',
                'dailymotion.com', 'rutube.ru', 'vk.com', 'ok.ru'
            ]
            
            # Для embed платформ повертаємо оригінальний URL
            if any(platform in video_url.lower() for platform in embed_platforms):
                return video_url
            
            # Для українських новинних сайтів з відео
            ukrainian_video_platforms = [
                'tsn.ua', 'espreso.tv', '24tv.ua', 'hromadske.ua',
                'suspilne.media', 'pravda.com.ua', 'ukrinform.ua'
            ]
            
            if any(platform in video_url.lower() for platform in ukrainian_video_platforms):
                return video_url
            
            # Для прямих відео файлів
            if video_url.endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):
                return video_url
            
            # Для iframe посилань, спробуємо витягнути src
            if 'iframe' in video_url.lower():
                try:
                    import re
                    src_match = re.search(r'src=["\']([^"\']+)["\']', video_url)
                    if src_match:
                        extracted_url = src_match.group(1)
                        # Перевіряємо чи це не embed платформа
                        if not any(platform in extracted_url.lower() for platform in embed_platforms):
                            return extracted_url
                except Exception as e:
                    logger.warning(f"Помилка при витягуванні src з iframe: {e}")
            
            # Спробуємо знайти прямий відео файл в URL
            try:
                import re
                # Шукаємо прямий відео файл в URL
                video_file_pattern = r'https?://[^\s<>"]*\.(mp4|avi|mov|mkv|webm)(\?[^\s<>"]*)?'
                match = re.search(video_file_pattern, video_url)
                if match:
                    return match.group(0)
            except Exception as e:
                logger.warning(f"Помилка при пошуку відео файлу: {e}")
            
            return video_url
            
        except Exception as e:
            logger.error(f"Помилка при витягуванні прямого URL відео: {e}")
            return video_url

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
            video_published = False
            
            if video_url:
                # Спробуємо опублікувати відео напряму
                direct_video_url = self.extract_direct_video_url(video_url)
                
                # Для прямих відео файлів спробуємо завантажити та надіслати
                if direct_video_url and (direct_video_url.endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')) or 
                                       'cdn' in direct_video_url.lower() or 'video' in direct_video_url.lower() or
                                       'media' in direct_video_url.lower() or 'stream' in direct_video_url.lower()):
                    try:
                        video_data = await self.download_video(direct_video_url)
                        if video_data:
                            await self.bot.send_video(
                                chat_id=CHANNEL_ID,
                                video=video_data,
                                caption=text,
                                parse_mode='HTML',
                                supports_streaming=True
                            )
                            logger.info(f"🎥 Опубліковано новину з відео: {news_item.get('title', '')[:50]}...")
                            video_published = True
                    except Exception as e:
                        logger.warning(f"Не вдалося надіслати відео файл: {e}")
                        # Спробуємо надіслати як документ якщо відео не підтримується
                        try:
                            await self.bot.send_document(
                                chat_id=CHANNEL_ID,
                                document=video_data,
                                caption=text,
                                parse_mode='HTML'
                            )
                            logger.info(f"📎 Опубліковано новину з відео як документ: {news_item.get('title', '')[:50]}...")
                            video_published = True
                        except Exception as e2:
                            logger.warning(f"Не вдалося надіслати відео як документ: {e2}")
                
                # Якщо не вдалося надіслати відео файл, додаємо посилання до тексту
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
                        'ukrinform.ua': ('📰', 'Укрінформ'), 'nv.ua': ('📰', 'НВ'),
                        'zn.ua': ('📰', 'Зеркало недели'), 'fakty.com.ua': ('📺', 'Факти ICTV'),
                        'obozrevatel.com': ('📰', 'Обозреватель'), 'korrespondent.net': ('📰', 'Корреспондент'),
                        'ukraina.ru': ('📰', 'Україна.ру'), 'gordonua.com': ('📺', 'ГОРДОН'),
                        'rbc.ua': ('📰', 'РБК-Україна')
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
            video_published = False
            
            if video_url:
                # Спробуємо опублікувати відео напряму
                direct_video_url = self.extract_direct_video_url(video_url)
                
                # Для прямих відео файлів спробуємо завантажити та надіслати
                if direct_video_url and (direct_video_url.endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')) or 
                                       'cdn' in direct_video_url.lower() or 'video' in direct_video_url.lower() or
                                       'media' in direct_video_url.lower() or 'stream' in direct_video_url.lower()):
                    try:
                        video_data = await self.download_video(direct_video_url)
                        if video_data:
                            await self.bot.send_video(
                                chat_id=CHANNEL_ID,
                                video=video_data,
                                caption=text,
                                parse_mode='HTML',
                                supports_streaming=True
                            )
                            logger.info(f"🎥 Опубліковано новину з відео: {news_item.get('title', '')[:50]}...")
                            video_published = True
                    except Exception as e:
                        logger.warning(f"Не вдалося надіслати відео файл: {e}")
                        # Спробуємо надіслати як документ якщо відео не підтримується
                        try:
                            await self.bot.send_document(
                                chat_id=CHANNEL_ID,
                                document=video_data,
                                caption=text,
                                parse_mode='HTML'
                            )
                            logger.info(f"📎 Опубліковано новину з відео як документ: {news_item.get('title', '')[:50]}...")
                            video_published = True
                        except Exception as e2:
                            logger.warning(f"Не вдалося надіслати відео як документ: {e2}")
                
                # Додаємо посилання на відео до тексту для всіх типів відео
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
                        'ukrinform.ua': ('📰', 'Укрінформ'), 'nv.ua': ('📰', 'НВ'),
                        'zn.ua': ('📰', 'Зеркало недели'), 'fakty.com.ua': ('📺', 'Факти ICTV'),
                        'obozrevatel.com': ('📰', 'Обозреватель'), 'korrespondent.net': ('📰', 'Корреспондент'),
                        'ukraina.ru': ('📰', 'Україна.ру'), 'gordonua.com': ('📺', 'ГОРДОН'),
                        'rbc.ua': ('📰', 'РБК-Україна')
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
            
            try:
                # Якщо відео не було опубліковано окремо, публікуємо з зображенням
                if not video_published:
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

    async def send_news(self, news_item):
        video_url = news_item.get("video_url")
        if video_url:
            try:
                video_path = await self.download_video(video_url)
                if video_path:
                    await self.bot.send_video(
                        chat_id=CHANNEL_ID,
                        video=open(video_path, "rb"),
                        caption=self.format_news_text(news_item),
                        parse_mode="HTML"
                    )
                    logger.info(f"✅ Відео надіслано: {video_url}")
                    os.remove(video_path)
                    return True
                else:
                    logger.warning(f"⚠️ Не вдалося завантажити відео: {video_url}")
            except Exception as e:
                logger.error(f"❌ Помилка при надсиланні відео: {e}")
        # Якщо немає відео або не вдалося — fallback
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
        return False

    async def download_video(self, url):
        filename = "temp_video.mp4"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        with open(filename, "wb") as f:
                            while True:
                                chunk = await resp.content.read(1024*1024)
                                if not chunk:
                                    break
                                f.write(chunk)
                        return filename
                    else:
                        logging.error(f"❌ Не вдалося завантажити відео: {url} (status {resp.status})")
                        return None
        except Exception as e:
            logging.error(f"❌ Помилка при завантаженні відео: {e}")
            return None