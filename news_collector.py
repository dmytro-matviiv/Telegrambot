import asyncio
import aiohttp
import feedparser
import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict
import logging
from config import NEWS_SOURCES, PUBLISHED_NEWS_FILE, DEFAULT_IMAGE_URL
import re
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsCollector:
    def __init__(self):
        self.published_news = self.load_published_news()
        self.session = requests.Session()
        self.session.trust_env = False  # Вимикаємо використання проксі з env
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def load_published_news(self) -> set:
        try:
            with open(PUBLISHED_NEWS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(data.get('published_news', []))
        except FileNotFoundError:
            return set()

    def save_published_news(self):
        data = {
            'published_news': list(self.published_news),
            'last_updated': datetime.now().isoformat()
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

    def get_news_from_rss(self, source_key: str, source_info: Dict) -> List[Dict]:
        try:
            logger.info(f"📰 Збираємо новини з {source_info['name']}")
            rss_urls = [
                source_info.get('rss', ''),
                f"{source_info['website'].rstrip('/')}/rss",
                f"{source_info['website'].rstrip('/')}/feed",
                f"{source_info['website'].rstrip('/')}/rss.xml"
            ]
            feed = None
            for rss_url in rss_urls:
                try:
                    logger.info(f"🔍 Пробуємо RSS URL: {rss_url}")
                    response = self.session.get(rss_url, timeout=10, proxies={})
                    logger.info(f"↪️ Статус відповіді: {response.status_code}")
                    if response.status_code == 200:
                        feed = feedparser.parse(response.content)
                        if feed.entries:
                            logger.info(f"✅ Знайдено {len(feed.entries)} записів у RSS")
                            break
                except Exception as e:
                    logger.warning(f"⚠️ Помилка при отриманні RSS з {rss_url}: {e}")
                    continue
            if not feed or not feed.entries:
                logger.warning(f"🚫 Не вдалося отримати новини з {source_info['name']}")
                return []
            # Відсортувати за датою публікації (якщо можливо)
            entries = sorted(feed.entries, key=lambda e: e.get('published_parsed', None) or e.get('updated_parsed', None) or 0, reverse=True)
            for entry in entries:
                news_id = f"{source_key}_{entry.get('id', entry.get('link', ''))}"
                if news_id in self.published_news:
                    continue
                # --- Фільтрація мови ---
                lang = entry.get('language') or entry.get('lang') or entry.get('dc_language')
                title = entry.get('title', '')
                summary = entry.get('summary', '')
                
                # Для міжнародних джерел дозволяємо англійську мову
                source_key_lower = source_key.lower()
                is_international_source = any(keyword in source_key_lower for keyword in ['bbc', 'reuters', 'cnn', 'ap', 'guardian', 'nyt', 'washington', 'al_jazeera', 'dw', 'defense', 'war_zone'])
                
                # Дуже простий Heuristic: якщо явно не вказано lang, перевірити наявність українських літер
                def is_ukrainian(text):
                    ukr_letters = set('іїєґІЇЄҐ')
                    return any(c in ukr_letters for c in text)
                
                def is_english(text):
                    # Проста перевірка на англійську мову
                    common_english_words = ['the', 'and', 'for', 'with', 'this', 'that', 'will', 'have', 'been', 'from', 'they', 'said', 'time', 'people', 'year', 'into', 'just', 'over', 'think', 'also', 'around', 'another', 'come', 'work', 'first', 'well', 'way', 'even', 'want', 'because', 'any', 'these', 'give', 'day', 'most', 'us']
                    text_lower = text.lower()
                    english_word_count = sum(1 for word in common_english_words if word in text_lower)
                    return english_word_count >= 3
                
                # Для міжнародних джерел дозволяємо англійську
                if is_international_source:
                    if lang and not (lang.startswith('uk') or lang.startswith('en')):
                        logger.info(f"⏩ Пропускаємо новину: не українською/англійською мовою (lang={lang})")
                        continue
                    if not lang and not (is_ukrainian(title) or is_ukrainian(summary) or is_english(title) or is_english(summary)):
                        logger.info(f"⏩ Пропускаємо новину: не схожа на українську/англійську (title/summary)")
                        continue
                else:
                    # Для українських джерел тільки українська
                    if lang and not lang.startswith('uk'):
                        logger.info(f"⏩ Пропускаємо новину: не українською мовою (lang={lang})")
                        continue
                    if not lang and not (is_ukrainian(title) or is_ukrainian(summary)):
                        logger.info(f"⏩ Пропускаємо новину: не схожа на українську (title/summary)")
                        continue
                # --- Кінець фільтрації мови ---
                
                # Фільтрація за ключовими словами для міжнародних джерел
                if is_international_source:
                    ukraine_keywords = ['ukraine', 'ukrainian', 'kyiv', 'kiev', 'donetsk', 'luhansk', 'crimea', 'russia', 'russian', 'putin', 'zelensky', 'war', 'conflict', 'invasion', 'military', 'defense', 'weapons', 'sanctions']
                    title_lower = title.lower()
                    summary_lower = summary.lower()
                    
                    # Перевіряємо чи є ключові слова в заголовку або описі
                    has_ukraine_keywords = any(keyword in title_lower or keyword in summary_lower for keyword in ukraine_keywords)
                    
                    if not has_ukraine_keywords:
                        logger.info(f"⏩ Пропускаємо міжнародну новину: немає ключових слів про Україну/війну")
                        continue
                
                published = entry.get('published_parsed', None) or entry.get('updated_parsed', None)
                if not published:
                    continue
                published_dt = datetime.fromtimestamp(time.mktime(published))
                if datetime.now() - published_dt > timedelta(hours=5):
                    logger.info(f"⏩ Пропускаємо новину: старіша за 5 годин")
                    return []
                full_text = self.get_full_article_text(entry.get('link', ''))
                image_url = self.extract_image_url(entry, entry.get('link', ''))
                video_url = self.extract_video_url(entry, entry.get('link', ''))
                
                # Логуємо знайдені відео
                if video_url:
                    logger.info(f"🎥 Знайдено відео в новині: {title[:50]}... (URL: {video_url[:50]}...)")
                
                # --- Перевірка якості фото ---
                if image_url:
                    try:
                        img_resp = self.session.get(image_url, timeout=10, stream=True)
                        from PIL import Image
                        from io import BytesIO
                        img = Image.open(BytesIO(img_resp.content))
                        width, height = img.size
                        if width < 400 or height < 200:
                            logger.info(f"⏩ Фото замінено на дефолтне: маленький розмір {width}x{height}")
                            image_url = DEFAULT_IMAGE_URL
                    except Exception as e:
                        logger.info(f"⏩ Фото замінено на дефолтне: не вдалося визначити якість ({e})")
                        image_url = DEFAULT_IMAGE_URL
                else:
                    image_url = DEFAULT_IMAGE_URL
                # --- Кінець перевірки якості фото ---
                
                # --- Переклад англійських новин ---
                is_international_source = any(keyword in source_key.lower() for keyword in ['bbc', 'reuters', 'cnn', 'ap', 'guardian', 'nyt', 'washington', 'al_jazeera', 'dw', 'defense', 'war_zone'])
                
                if is_international_source and self.is_english_text(title):
                    logger.info(f"🔄 Перекладаємо заголовок з англійської на українську")
                    translated_title = self.translate_text(title)
                    if translated_title != title:
                        title = translated_title
                
                if is_international_source and self.is_english_text(summary):
                    logger.info(f"🔄 Перекладаємо опис з англійської на українську")
                    translated_summary = self.translate_text(summary)
                    if translated_summary != summary:
                        summary = translated_summary
                
                # --- Кінець перекладу ---
                
                news_item = {
                    'id': news_id,
                    'title': title,
                    'description': summary,
                    'full_text': full_text,
                    'link': entry.get('link', ''),
                    'image_url': image_url,
                    'video_url': video_url,
                    'source': source_info['name'],
                    'source_key': source_key,
                    'published': entry.get('published', ''),
                    'timestamp': datetime.now().isoformat()
                }
                return [news_item]  # Повертаємо лише одну новину
            return []  # Якщо немає нової новини
        except Exception as e:
            logger.error(f"❗ Помилка при зборі новин з {source_info['name']}: {e}")
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
        try:
            if hasattr(entry, 'media_content') and entry.media_content:
                return entry.media_content[0]['url']

            if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
                return entry.media_thumbnail[0]['url']

            if entry.get('summary'):
                soup = BeautifulSoup(entry['summary'], 'html.parser')
                img = soup.find('img')
                if img and img.get('src'):
                    return img['src']

            if article_url:
                response = self.session.get(article_url, timeout=10, proxies={})
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    img_selectors = [
                        'article img',
                        '.article-image img',
                        '.post-image img',
                        '.entry-image img',
                        '.content img',
                        'main img'
                    ]
                    for selector in img_selectors:
                        img = soup.select_one(selector)
                        if img and img.get('src'):
                            src = img['src']
                            if src.startswith('//'):
                                src = 'https:' + src
                            elif src.startswith('/'):
                                src = 'https://' + article_url.split('/')[2] + src
                            return src
        except Exception as e:
            logger.error(f"❌ Помилка при витягуванні зображення: {e}")
        return ""

    def extract_video_url(self, entry, article_url: str) -> str:
        """Витягує URL відео з новини"""
        try:
            # Перевіряємо медіа контент на відео
            if hasattr(entry, 'media_content') and entry.media_content:
                for media in entry.media_content:
                    if media.get('type', '').startswith('video/'):
                        logger.info(f"🎥 Знайдено відео в медіа контенті: {media['url'][:50]}...")
                        return media['url']

            # Перевіряємо опис на відео теги
            if entry.get('summary'):
                soup = BeautifulSoup(entry['summary'], 'html.parser')
                video = soup.find('video')
                if video and video.get('src'):
                    logger.info(f"🎥 Знайдено відео тег в описі: {video['src'][:50]}...")
                    return video['src']
                
                # Перевіряємо iframe з відео (YouTube, Vimeo, тощо)
                iframe = soup.find('iframe')
                if iframe and iframe.get('src'):
                    src = iframe['src']
                    if 'youtube.com' in src or 'youtu.be' in src or 'vimeo.com' in src:
                        logger.info(f"🎥 Знайдено iframe відео в описі: {src[:50]}...")
                        return src

            # Перевіряємо повну статтю на відео
            if article_url:
                response = self.session.get(article_url, timeout=10, proxies={})
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Шукаємо відео теги
                    video_selectors = [
                        'video',
                        'iframe[src*="youtube"]',
                        'iframe[src*="vimeo"]',
                        'iframe[src*="dailymotion"]',
                        '.video-container iframe',
                        '.video iframe',
                        'article iframe',
                        '.content iframe'
                    ]
                    
                    for selector in video_selectors:
                        video_elem = soup.select_one(selector)
                        if video_elem:
                            src = video_elem.get('src')
                            if src:
                                if src.startswith('//'):
                                    src = 'https:' + src
                                elif src.startswith('/'):
                                    src = 'https://' + article_url.split('/')[2] + src
                                logger.info(f"🎥 Знайдено відео в статті ({selector}): {src[:50]}...")
                                return src
        except Exception as e:
            logger.error(f"❌ Помилка при витягуванні відео: {e}")
        return ""

    def collect_all_news(self) -> List[Dict]:
        all_news = []
        dead_sources = []  # Список "мертвих" джерел
        for source_key, source_info in NEWS_SOURCES.items():
            try:
                news = self.get_news_from_rss(source_key, source_info)
                if not news:
                    dead_sources.append({
                        'key': source_key,
                        'name': source_info.get('name', source_key),
                        'rss': source_info.get('rss', ''),
                        'website': source_info.get('website', '')
                    })
                all_news.extend(news)
                time.sleep(2)
            except Exception as e:
                logger.error(f"❗ Помилка при зборі новин з {source_key}: {e}")
        if dead_sources:
            logger.warning("\n===== МЕРТВІ ДЖЕРЕЛА (немає новин) =====")
            for src in dead_sources:
                logger.warning(f"{src['name']} | RSS: {src['rss']} | Сайт: {src['website']}")
            logger.warning("===== КІНЕЦЬ СПИСКУ МЕРТВИХ ДЖЕРЕЛ =====\n")
        all_news.sort(key=lambda x: x.get('published', ''), reverse=True)
        return all_news

    def mark_as_published(self, news_id: str):
        self.published_news.add(news_id)
        self.save_published_news()

    def cleanup_old_news(self, days: int = 7):
        cutoff_date = datetime.now() - timedelta(days=days)
        old_news = set()

        # Це місце для реалізації очищення (можна додати за потреби)

        self.published_news -= old_news
        self.save_published_news()
