import asyncio
import aiohttp
import feedparser
import requests
from bs4 import BeautifulSoup
import json
import time
import random
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import List, Dict
import logging
from config import NEWS_SOURCES, PUBLISHED_NEWS_FILE, DEFAULT_IMAGE_URL
import re
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_published_date(date_str):
    """Парсити дату публікації з різних форматів RSS"""
    if not date_str:
        return None
    
    try:
        # Спробуємо RFC 2822 формат (найпоширеніший в RSS)
        dt = parsedate_to_datetime(date_str)
        # Якщо дата timezone-naive, припускаємо UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        pass
    
    # Список можливих форматів дат
    date_formats = [
        "%Y-%m-%dT%H:%M:%S",           # ISO format
        "%Y-%m-%dT%H:%M:%SZ",          # ISO format with Z
        "%Y-%m-%d %H:%M:%S",           # Simple format
        "%a, %d %b %Y %H:%M:%S %z",    # RFC 2822 with timezone
        "%a, %d %b %Y %H:%M:%S",       # RFC 2822 without timezone
        "%a, %d %b %Y %H",             # RFC 2822 incomplete (hour only)
        "%d %b %Y %H:%M:%S",           # Short RFC format
        "%Y-%m-%d",                    # Date only
    ]
    
    for fmt in date_formats:
        try:
            # Обрізаємо рядок до потрібної довжини для формату
            if fmt == "%Y-%m-%dT%H:%M:%S":
                date_str_clean = date_str[:19]
            elif fmt == "%Y-%m-%d %H:%M:%S":
                date_str_clean = date_str[:19]
            elif fmt == "%Y-%m-%d":
                date_str_clean = date_str[:10]
            else:
                date_str_clean = date_str
            
            dt = datetime.strptime(date_str_clean, fmt)
            # Якщо дата timezone-naive, припускаємо UTC
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, TypeError):
            continue
    
    logger.warning(f"Не вдалося розпарсити дату: {date_str}")
    return None

class NewsCollector:
    def __init__(self):
        published_data = self.load_published_news()
        self.published_news = published_data['published_news']
        self.last_source = published_data['last_source']
        self.last_published_time = published_data['last_published_time']
        self.last_category_index = published_data.get('last_category_index', 0)  # Індекс останньої категорії
        self.session = requests.Session()
        self.session.trust_env = False  # Вимикаємо використання проксі з env
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def load_published_news(self) -> dict:
        try:
            with open(PUBLISHED_NEWS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    'published_news': set(data.get('published_news', [])),
                    'last_source': data.get('last_source', ''),
                    'last_published_time': data.get('last_published_time', ''),
                    'last_category_index': data.get('last_category_index', 0)
                }
        except FileNotFoundError:
            return {
                'published_news': set(),
                'last_source': '',
                'last_published_time': '',
                'last_category_index': 0
            }

    def save_published_news(self):
        data = {
            'published_news': list(self.published_news),
            'last_source': self.last_source,
            'last_published_time': self.last_published_time,
            'last_category_index': self.last_category_index,
            'last_updated': datetime.now(timezone.utc).isoformat()
        }
        with open(PUBLISHED_NEWS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def translate_text(self, text, source_lang='en', target_lang='uk'):
        """Переклад тексту з англійської на українську через Google Translate"""
        try:
            if not text or len(text.strip()) < 10:
                return text
            
            # Перевіряємо чи текст дійсно англійською мовою
            if not self.is_english_text(text):
                return text
            
            from deep_translator import GoogleTranslator
            
            # Розбиваємо довгий текст на частини (Google Translate має ліміт)
            max_length = 4000
            if len(text) > max_length:
                # Розбиваємо на речення
                sentences = text.split('. ')
                translated_parts = []
                
                current_part = ""
                for sentence in sentences:
                    if len(current_part + sentence) < max_length:
                        current_part += sentence + ". "
                    else:
                        if current_part:
                            translated_part = GoogleTranslator(source='en', target='uk').translate(current_part.strip())
                            translated_parts.append(translated_part)
                        current_part = sentence + ". "
                
                # Перекладаємо останню частину
                if current_part:
                    translated_part = GoogleTranslator(source='en', target='uk').translate(current_part.strip())
                    translated_parts.append(translated_part)
                
                return " ".join(translated_parts)
            else:
                # Перекладаємо весь текст одразу
                translated = GoogleTranslator(source='en', target='uk').translate(text)
                logger.info(f"🔄 Перекладено через Google Translate: {text[:50]}... → {translated[:50]}...")
                return translated
                
        except Exception as e:
            logger.warning(f"Помилка Google Translate: {e}")
            # Якщо Google Translate не працює, повертаємо оригінальний текст
            return text

    def is_english_text(self, text):
        """Перевіряє чи текст англійською мовою"""
        if not text:
            return False
        
        # Розширені індикатори англійської мови
        english_indicators = [
            'the', 'and', 'for', 'with', 'this', 'that', 'will', 'have', 'been', 'from', 'they', 'said',
            'news', 'latest', 'breaking', 'report', 'says', 'said', 'ukraine', 'russia', 'war', 'military', 'defense', 'zelensky', 'putin',
            'a', 'an', 'of', 'in', 'on', 'by', 'to', 'is', 'are', 'was', 'were', 'has', 'had', 'would', 'could', 'should',
            'says', 'said', 'reports', 'reported', 'announced', 'announces', 'confirmed', 'confirms',
            'forces', 'troops', 'military', 'defense', 'attack', 'strike', 'bombing', 'shelling',
            'developments', 'situation', 'conflict', 'crisis', 'emergency', 'alert', 'warning'
        ]
        text_lower = text.lower()
        english_count = sum(1 for word in english_indicators if word in text_lower)
        
        # Якщо знайдено більше 2 англійських слів, вважаємо текст англійським
        return english_count >= 2

    def is_ukrainian_content(self, title: str, summary: str) -> bool:
        """Швидка перевірка на українську мову"""
        ukr_letters = set('іїєґІЇЄҐ')
        text = title + ' ' + summary
        return any(c in ukr_letters for c in text)
    
    def is_good_image_size(self, image_url: str) -> bool:
        """Швидка перевірка розміру фото"""
        try:
            response = self.session.get(image_url, timeout=5, stream=True)
            if response.status_code != 200:
                return False
            
            from PIL import Image
            from io import BytesIO
            img = Image.open(BytesIO(response.content))
            width, height = img.size
            return width >= 400 and height >= 200
        except:
            return False
    
    def get_rss_feed(self, rss_url: str):
        """Отримує RSS feed"""
        try:
            response = self.session.get(rss_url, timeout=10)
            if response.status_code == 200:
                return feedparser.parse(response.content)
        except Exception as e:
            logger.warning(f"⚠️ Помилка при отриманні RSS з {rss_url}: {e}")
        return None

    def get_news_from_rss(self, source_key: str, source_info: dict) -> List[Dict]:
        """Збирає новини з RSS джерела"""
        try:
            logger.info(f"📰 Збираємо новини з {source_info['name']} ({source_info.get('category', 'unknown')})")
            
            # Отримуємо RSS
            feed = self.get_rss_feed(source_info['rss'])
            if not feed or not feed.entries:
                logger.warning(f"🚫 Не вдалося отримати новини з {source_info['name']}")
                return []
            
            logger.info(f"✅ Знайдено {len(feed.entries)} записів у RSS")
            
            news_list = []
            processed_count = 0
            
            for entry in feed.entries[:10]:  # Обмежуємо до 10 новин для швидкості
                try:
                    # Отримуємо дані новини
                    title = entry.get('title', '')
                    summary = entry.get('summary', '')
                    language = source_info.get('language', 'en')
                    
                    # Перевіряємо мову та перекладаємо якщо потрібно
                    if language == 'en':
                        # Перекладаємо англійські новини
                        if title:
                            title = self.translate_text(title)
                        if summary:
                            summary = self.translate_text(summary)
                        logger.info(f"🔄 Перекладено новину: {title[:50]}...")
                    elif language == 'uk':
                        # Перевіряємо чи це українська мова
                        if not self.is_ukrainian_content(title, summary):
                            continue
                    
                    # Швидко шукаємо фото
                    image_url = self.extract_image_url(entry, entry.get('link', ''))
                    if not image_url:
                        continue  # Пропускаємо без фото
                    
                    # Перевіряємо розмір фото
                    if not self.is_good_image_size(image_url):
                        continue
                    
                    # Створюємо новину
                    news_item = {
                        'title': title,
                        'description': summary,
                        'link': entry.get('link', ''),
                        'image_url': image_url,
                        'source': source_info['name'],
                        'source_key': source_key,
                        'category': source_info.get('category', 'unknown'),
                        'language': language,
                        'published': entry.get('published', ''),
                        'id': entry.get('id', entry.get('link', ''))
                    }
                    
                    news_list.append(news_item)
                    processed_count += 1
                    
                    # Зупиняємося після перших 3 хороших новин
                    if processed_count >= 3:
                        break
                        
                except Exception as e:
                    logger.warning(f"Помилка при обробці новини: {e}")
                    continue
            
            if news_list:
                logger.info(f"✅ {source_info['name']}: знайдено {len(news_list)} новин з фото")
            else:
                logger.info(f"⏩ {source_info['name']}: немає новин з фото")
                
            return news_list
            
        except Exception as e:
            logger.error(f"Помилка при зборі новин з {source_info['name']}: {e}")
            return []

    def get_full_article_text(self, url: str) -> str:
        try:
            response = self.session.get(url, timeout=15, proxies={})
            if response.status_code != 200:
                return ""

            soup = BeautifulSoup(response.content, 'html.parser')

            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()

            content_selectors = [
                'article',
                '.content',
                '.article-content',
                '.post-content',
                '.entry-content',
                'main',
                '.main-content'
            ]

            content = None
            for selector in content_selectors:
                content = soup.select_one(selector)
                if content:
                    break

            if not content:
                content = soup.find('body')

            if content:
                text = content.get_text(separator=' ', strip=True)
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                text = ' '.join(lines)
                return text[:2000]

            return ""
        except Exception as e:
            logger.error(f"❌ Помилка при отриманні повного тексту: {e}")
            return ""

    def extract_image_url(self, entry, article_url: str) -> str:
        """Витягує URL зображення з новини"""
        try:
            # Перевіряємо медіа контент на зображення
            if hasattr(entry, 'media_content') and entry.media_content:
                for media in entry.media_content:
                    if media.get('type', '').startswith('image/'):
                        logger.info(f"📸 Знайдено зображення в медіа контенті: {media['url'][:50]}...")
                        return media['url']

            # Перевіряємо опис на зображення
            if entry.get('summary'):
                soup = BeautifulSoup(entry['summary'], 'html.parser')
                
                # Шукаємо зображення теги
                img = soup.find('img')
                if img and img.get('src'):
                    logger.info(f"📸 Знайдено зображення в описі: {img['src'][:50]}...")
                    return img['src']

            # Перевіряємо повний текст статті
            if article_url:
                try:
                    full_text = self.get_full_article_text(article_url)
                    if full_text:
                        soup = BeautifulSoup(full_text, 'html.parser')
                        
                        # Шукаємо зображення в повному тексті
                        img = soup.find('img')
                        if img and img.get('src'):
                            logger.info(f"📸 Знайдено зображення в повному тексті: {img['src'][:50]}...")
                            return img['src']
                except Exception as e:
                    logger.warning(f"Помилка при отриманні повного тексту: {e}")

            return ""  # Повертаємо порожній рядок якщо фото не знайдено

        except Exception as e:
            logger.error(f"Помилка при витягуванні зображення: {e}")
            return ""  # Повертаємо порожній рядок якщо помилка

    def collect_all_news(self) -> List[Dict]:
        """Збирає новини з усіх категорій та перемішує їх"""
        all_news = []
        
        # Визначаємо категорії та їх джерела
        categories = {
            'world': ['bbc_world', 'reuters_world', 'cnn_world'],
            'ukraine': ['channel24', 'unian', 'pravda'],
            'inventions': ['techcrunch', 'wired_tech', 'the_verge'],
            'celebrity': ['people', 'eonline'],
            'war': ['defense_news', 'war_zone']
        }
        
        logger.info("🔄 Збираємо новини з усіх категорій...")
        
        # Збираємо новини з усіх категорій
        for category_name, category_sources in categories.items():
            logger.info(f"📰 Перевіряємо категорію: {category_name}")
            
            # Перемішуємо джерела в категорії для різноманітності
            random.shuffle(category_sources)
            
            # Збираємо новини з джерел поточної категорії
            for source_key in category_sources:
                try:
                    source_info = NEWS_SOURCES.get(source_key)
                    if not source_info:
                        continue
                        
                    news = self.get_news_from_rss(source_key, source_info)
                    if news:
                        all_news.extend(news)
                        logger.info(f"✅ {source_info['name']}: знайдено {len(news)} новин")
                    else:
                        logger.info(f"⏩ {source_info['name']}: немає новин")
                        
                except Exception as e:
                    logger.error(f"Помилка при зборі з {source_key}: {e}")
                    continue
        
        # Перемішуємо всі знайдені новини
        if all_news:
            random.shuffle(all_news)
            logger.info(f"🎲 Перемішано {len(all_news)} новин у випадковому порядку")
        
        # Фільтруємо вже опубліковані новини
        new_news = []
        for news in all_news:
            news_id = f"{news['source_key']}_{news['id']}"
            if news_id not in self.published_news:
                new_news.append(news)
        
        if new_news:
            logger.info(f"📰 Знайдено {len(new_news)} нових новин з різних джерел")
            
            # Показуємо статистику по джерелах
            sources_count = {}
            for news in new_news:
                source = news['source']
                sources_count[source] = sources_count.get(source, 0) + 1
            
            logger.info("📊 Статистика по джерелах:")
            for source, count in sources_count.items():
                logger.info(f"   {source}: {count} новин")
        else:
            logger.info("📭 Нові новини не знайдено")
            
        return new_news

    def mark_as_published(self, news_id: str, source_key: str = ''):
        self.published_news.add(news_id)
        if source_key:
            self.last_source = source_key
            self.last_published_time = datetime.now(timezone.utc).isoformat()
        self.save_published_news()

    def cleanup_old_news(self, days: int = 7):
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        old_news = set()

        # Це місце для реалізації очищення (можна додати за потреби)

        self.published_news -= old_news
        self.save_published_news()
