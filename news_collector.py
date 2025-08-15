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
                    
                    # Отримуємо повний текст статті для більш детального опису
                    full_text = ""
                    article_url = entry.get('link', '')
                    if article_url:
                        try:
                            full_text = self.get_full_article_text(article_url)
                            if full_text:
                                logger.info(f"📖 Отримано повний текст статті: {len(full_text)} символів")
                        except Exception as e:
                            logger.warning(f"⚠️ Не вдалося отримати повний текст: {e}")
                    
                    # Формуємо детальний опис
                    detailed_description = self.create_detailed_description(summary, full_text)
                    
                    # Створюємо новину
                    news_item = {
                        'title': title,
                        'description': detailed_description,
                        'full_text': full_text,  # Зберігаємо повний текст для подальшого використання
                        'link': article_url,
                        'image_url': image_url,
                        'source': source_info['name'],
                        'source_key': source_key,
                        'category': source_info.get('category', 'unknown'),
                        'language': language,
                        'published': entry.get('published', ''),
                        'id': entry.get('id', article_url)
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

    def create_detailed_description(self, summary: str, full_text: str) -> str:
        """Створює детальний опис новини, поєднуючи RSS опис та повний текст"""
        try:
            # Починаємо з RSS опису
            description = summary or ""
            
            # Якщо є повний текст, додаємо його частину
            if full_text and len(full_text) > 100:
                # Очищаємо повний текст від зайвих пробілів
                clean_full_text = ' '.join(full_text.split())
                
                # Якщо RSS опис короткий або порожній, використовуємо повний текст
                if len(description) < 150:
                    # Беремо перші 250-300 символів з повного тексту
                    if len(clean_full_text) > 300:
                        # Шукаємо кінець речення близько до 300 символів
                        cut_point = 300
                        for i in range(250, 350):
                            if i < len(clean_full_text):
                                if clean_full_text[i] in '.!?':
                                    cut_point = i + 1
                                    break
                        
                        description = clean_full_text[:cut_point].strip()
                        if not description.endswith(('.', '!', '?')):
                            description += "..."
                    else:
                        description = clean_full_text
                else:
                    # Якщо RSS опис достатньо довгий, додаємо трохи з повного тексту
                    if len(clean_full_text) > 200:
                        # Додаємо додаткову інформацію з повного тексту
                        additional_text = clean_full_text[:200]
                        # Шукаємо кінець речення
                        for i in range(150, 200):
                            if i < len(additional_text):
                                if additional_text[i] in '.!?':
                                    additional_text = additional_text[:i+1]
                                    break
                        
                        if additional_text and not additional_text.endswith(('.', '!', '?')):
                            additional_text += "..."
                        
                        # Поєднуємо опис та додаткову інформацію
                        if description and additional_text:
                            description = f"{description}\n\n{additional_text}"
                        elif additional_text:
                            description = additional_text
            
            # Очищаємо HTML теги
            if description:
                soup = BeautifulSoup(description, 'html.parser')
                description = soup.get_text(separator=' ', strip=True)
                
                # Обмежуємо довжину
                if len(description) > 400:
                    # Шукаємо кінець речення близько до 400 символів
                    cut_point = 400
                    for i in range(350, 450):
                        if i < len(description):
                            if description[i] in '.!?':
                                cut_point = i + 1
                                break
                    
                    description = description[:cut_point].strip()
                    if not description.endswith(('.', '!', '?')):
                        description += "..."
            
            return description
            
        except Exception as e:
            logger.warning(f"Помилка при створенні детального опису: {e}")
            return summary or ""

    def get_full_article_text(self, url: str) -> str:
        try:
            response = self.session.get(url, timeout=15, proxies={})
            if response.status_code != 200:
                return ""

            soup = BeautifulSoup(response.content, 'html.parser')

            # Видаляємо непотрібні елементи
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe', 'form']):
                element.decompose()

            # Список селекторів для основного контенту (в порядку пріоритету)
            content_selectors = [
                'article',
                '.content',
                '.article-content',
                '.post-content',
                '.entry-content',
                '.news-content',
                '.story-content',
                'main',
                '.main-content',
                '.text-content',
                '.body-content'
            ]

            content = None
            for selector in content_selectors:
                content = soup.select_one(selector)
                if content:
                    logger.info(f"📖 Знайдено контент за селектором: {selector}")
                    break

            if not content:
                # Якщо не знайшли за селекторами, шукаємо за класами
                for tag in soup.find_all(['div', 'section']):
                    class_names = tag.get('class', [])
                    if isinstance(class_names, list):
                        for class_name in class_names:
                            if any(keyword in class_name.lower() for keyword in ['content', 'article', 'post', 'story', 'text']):
                                content = tag
                                logger.info(f"📖 Знайдено контент за класом: {class_name}")
                                break
                        if content:
                            break

            if not content:
                # Остання спроба - використовуємо body
                content = soup.find('body')
                logger.info("📖 Використовуємо body як контент")

            if content:
                # Видаляємо додаткові непотрібні елементи з контенту
                for element in content(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe', 'form', 'button', 'input']):
                    element.decompose()
                
                # Видаляємо елементи з рекламою та соціальними мережами
                for element in content.find_all(['div', 'span'], class_=lambda x: x and any(keyword in x.lower() for keyword in ['ad', 'advertisement', 'social', 'share', 'comment', 'related'])):
                    element.decompose()
                
                # Отримуємо текст
                text = content.get_text(separator=' ', strip=True)
                
                # Очищаємо текст
                lines = []
                for line in text.split('\n'):
                    line = line.strip()
                    if line and len(line) > 20:  # Пропускаємо дуже короткі рядки
                        # Видаляємо зайві пробіли
                        line = ' '.join(line.split())
                        lines.append(line)
                
                text = ' '.join(lines)
                
                # Обмежуємо довжину
                if len(text) > 1500:
                    text = text[:1500]
                    # Шукаємо кінець речення
                    for i in range(1450, 1500):
                        if i < len(text):
                            if text[i] in '.!?':
                                text = text[:i+1]
                                break
                
                logger.info(f"📖 Отримано текст довжиною {len(text)} символів")
                return text

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
                    # Отримуємо повну сторінку статті
                    response = self.session.get(article_url, timeout=15)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Видаляємо непотрібні елементи
                        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                            element.decompose()
                        
                        # Шукаємо зображення різними способами
                        images = []
                        
                        # 1. Шукаємо всі img теги
                        img_tags = soup.find_all('img')
                        for img in img_tags:
                            src = img.get('src', '')
                            if src and src.startswith('http') and 'tsn.ua' in src:
                                # Пріоритет для зображень ТСН
                                if 'thumbs' in src and ('1200x630' in src or '800x600' in src):
                                    logger.info(f"📸 Знайдено основне зображення ТСН: {src[:50]}...")
                                    return src
                                images.append(src)
                        
                        # 2. Шукаємо в основному контенті
                        main_content = soup.find('article') or soup.find('main') or soup.find('.content')
                        if main_content:
                            main_images = main_content.find_all('img')
                            for img in main_images:
                                src = img.get('src', '')
                                if src and src.startswith('http') and 'tsn.ua' in src:
                                    if 'thumbs' in src and ('1200x630' in src or '800x600' in src):
                                        logger.info(f"📸 Знайдено зображення в контенті: {src[:50]}...")
                                        return src
                                    images.append(src)
                        
                        # 3. Повертаємо перше знайдене зображення ТСН
                        for img_url in images:
                            if 'tsn.ua' in img_url and not img_url.endswith('.svg'):
                                logger.info(f"📸 Використовуємо зображення ТСН: {img_url[:50]}...")
                                return img_url
                                
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
            'ukraine': ['tsn', 'unian', 'pravda'],
            'inventions': ['techcrunch', 'wired_tech', 'the_verge'],
            'celebrity': ['people'],
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
