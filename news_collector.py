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
                    'last_published_time': data.get('last_published_time', '')
                }
        except FileNotFoundError:
            return {
                'published_news': set(),
                'last_source': '',
                'last_published_time': ''
            }

    def save_published_news(self):
        data = {
            'published_news': list(self.published_news),
            'last_source': self.last_source,
            'last_published_time': self.last_published_time,
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
                # Додаємо заглушку-новину для мертвого джерела
                stub_news = {
                    'id': f"{source_key}_stub_{int(time.time())}",
                    'title': f"⚠️ Новини з джерела '{source_info['name']}' тимчасово недоступні",
                    'description': f"Офіційне джерело {source_info['name']} ({source_info.get('website', '')}) наразі не надає новини. Спробуємо пізніше.",
                    'full_text': "",
                    'link': source_info.get('website', ''),
                    'image_url': DEFAULT_IMAGE_URL,
                    'video_url': "",
                    'source': source_info['name'],
                    'source_key': source_key,
                    'published': datetime.now(timezone.utc).isoformat(),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                return [stub_news]
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
                # Конвертуємо в timezone-aware для порівняння
                published_dt = published_dt.replace(tzinfo=timezone.utc)
                if datetime.now(timezone.utc) - published_dt > timedelta(hours=5):
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

                # Обрізаємо description і full_text до 400 символів
                max_len = 400
                def trim(text):
                    if not text:
                        return ""
                    if len(text) > max_len:
                        return text[:max_len].rstrip() + "…"
                    return text

                news_item = {
                    'id': news_id,
                    'title': title,
                    'description': trim(summary),
                    'full_text': trim(full_text),
                    'link': entry.get('link', ''),
                    'image_url': image_url,
                    'video_url': video_url,
                    'source': source_info['name'],
                    'source_key': source_key,
                    'published': entry.get('published', ''),
                    'timestamp': datetime.now(timezone.utc).isoformat()
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
                
                # Шукаємо відео теги
                video = soup.find('video')
                if video and video.get('src'):
                    logger.info(f"🎥 Знайдено відео тег в описі: {video['src'][:50]}...")
                    return video['src']
                
                # Перевіряємо iframe з відео (YouTube, Vimeo, тощо)
                iframes = soup.find_all('iframe')
                for iframe in iframes:
                    src = iframe.get('src')
                    if src:
                        # Розширюємо список підтримуваних платформ
                        video_platforms = [
                            'youtube.com', 'youtu.be', 'vimeo.com', 'facebook.com',
                            'dailymotion.com', 'rutube.ru', 'vk.com', 'ok.ru',
                            'tsn.ua', 'espreso.tv', '24tv.ua', 'hromadske.ua',
                            'suspilne.media', 'pravda.com.ua', 'ukrinform.ua',
                            'nv.ua', 'zn.ua', 'fakty.com.ua', 'obozrevatel.com',
                            'korrespondent.net', 'liga.net', 'ukraina.ru', 'gordonua.com'
                        ]
                        if any(platform in src.lower() for platform in video_platforms):
                            logger.info(f"🎥 Знайдено iframe відео в описі: {src[:50]}...")
                            return src

            # Перевіряємо повну статтю на відео
            if article_url:
                response = self.session.get(article_url, timeout=10, proxies={})
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Розширений список селекторів для відео
                    video_selectors = [
                        'video',
                        'iframe[src*="youtube"]',
                        'iframe[src*="vimeo"]',
                        'iframe[src*="dailymotion"]',
                        'iframe[src*="facebook"]',
                        'iframe[src*="rutube"]',
                        'iframe[src*="vk"]',
                        'iframe[src*="ok"]',
                        'iframe[src*="tsn"]',
                        'iframe[src*="espreso"]',
                        'iframe[src*="24tv"]',
                        'iframe[src*="hromadske"]',
                        'iframe[src*="suspilne"]',
                        'iframe[src*="pravda"]',
                        'iframe[src*="ukrinform"]',
                        'iframe[src*="nv"]',
                        'iframe[src*="zn"]',
                        'iframe[src*="fakty"]',
                        'iframe[src*="obozrevatel"]',
                        'iframe[src*="korrespondent"]',
                        'iframe[src*="liga"]',
                        'iframe[src*="ukraina"]',
                        'iframe[src*="gordon"]',
                        '.video-container iframe',
                        '.video iframe',
                        'article iframe',
                        '.content iframe',
                        '.article iframe',
                        '.post iframe',
                        '.entry iframe',
                        '[class*="video"] iframe',
                        '[class*="player"] iframe'
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
                    
                    # Додатково шукаємо відео в тексті статті
                    article_text = soup.get_text()
                    video_patterns = [
                        r'https?://[^\s<>"]*\.(mp4|avi|mov|mkv|webm)',
                        r'https?://[^\s<>"]*youtube\.com[^\s<>"]*',
                        r'https?://[^\s<>"]*youtu\.be[^\s<>"]*',
                        r'https?://[^\s<>"]*vimeo\.com[^\s<>"]*',
                        r'https?://[^\s<>"]*dailymotion\.com[^\s<>"]*',
                        r'https?://[^\s<>"]*facebook\.com[^\s<>"]*',
                        r'https?://[^\s<>"]*rutube\.ru[^\s<>"]*',
                        r'https?://[^\s<>"]*vk\.com[^\s<>"]*',
                        r'https?://[^\s<>"]*ok\.ru[^\s<>"]*',
                        r'https?://[^\s<>"]*tsn\.ua[^\s<>"]*',
                        r'https?://[^\s<>"]*espreso\.tv[^\s<>"]*',
                        r'https?://[^\s<>"]*24tv\.ua[^\s<>"]*',
                        r'https?://[^\s<>"]*hromadske\.ua[^\s<>"]*',
                        r'https?://[^\s<>"]*suspilne\.media[^\s<>"]*',
                        r'https?://[^\s<>"]*pravda\.com\.ua[^\s<>"]*',
                        r'https?://[^\s<>"]*ukrinform\.ua[^\s<>"]*',
                        r'https?://[^\s<>"]*nv\.ua[^\s<>"]*',
                        r'https?://[^\s<>"]*zn\.ua[^\s<>"]*',
                        r'https?://[^\s<>"]*fakty\.com\.ua[^\s<>"]*',
                        r'https?://[^\s<>"]*obozrevatel\.com[^\s<>"]*',
                        r'https?://[^\s<>"]*korrespondent\.net[^\s<>"]*',
                        r'https?://[^\s<>"]*ukraina\.ru[^\s<>"]*',
                        r'https?://[^\s<>"]*gordonua\.com[^\s<>"]*',
                        r'https?://[^\s<>"]*rbc\.ua[^\s<>"]*'
                    ]
                    
                    for pattern in video_patterns:
                        matches = re.findall(pattern, article_text)
                        if matches:
                            video_url = matches[0] if isinstance(matches[0], str) else matches[0][0]
                            logger.info(f"🎥 Знайдено відео посилання в тексті: {video_url[:50]}...")
                            return video_url
                            
        except Exception as e:
            logger.error(f"❌ Помилка при витягуванні відео: {e}")
        return ""

    def is_direct_video(self, video_url: str) -> bool:
        """Перевіряє чи відео можна дивитися прямо в Telegram"""
        if not video_url:
            return False
        
        # Прямі відео файли можна дивитися в Telegram
        if video_url.endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):
            return True
        
        # YouTube, Vimeo, Facebook - це посилання, не прямі відео
        if any(platform in video_url.lower() for platform in ['youtube.com', 'youtu.be', 'vimeo.com', 'facebook.com']):
            return False
        
        # Інші відео вважаємо потенційно прямими
        return True

    def collect_all_news(self) -> List[Dict]:
        all_news = []
        dead_sources = []  # Список "мертвих" джерел
        sources_with_news = []  # Джерела, які мають новини
        sources_without_news = []  # Джерела без новин
        
        # Перший прохід: збираємо по одній новині з кожного джерела
        source_items = list(NEWS_SOURCES.items())
        random.shuffle(source_items)  # Перемішуємо порядок джерел
        
        for source_key, source_info in source_items:
            try:
                news = self.get_news_from_rss(source_key, source_info)
                if news:
                    sources_with_news.append((source_key, source_info, news))
                    logger.info(f"✅ {source_info['name']}: знайдено {len(news)} новин")
                else:
                    sources_without_news.append((source_key, source_info))
                    dead_sources.append({
                        'key': source_key,
                        'name': source_info.get('name', source_key),
                        'rss': source_info.get('rss', ''),
                        'website': source_info.get('website', '')
                    })
                time.sleep(2)
            except Exception as e:
                logger.error(f"❗ Помилка при зборі новин з {source_key}: {e}")
                sources_without_news.append((source_key, source_info))
        
        # Розподіляємо новини з пріоритизацією прямих відео
        direct_video_news = []  # Прямі відео (найvищий пріоритет)
        link_video_news = []    # Відео-посилання (середній пріоритет)
        no_video_news = []      # Без відео (найнижчий пріоритет)
        
        for source_key, source_info, news_list in sources_with_news:
            for news_item in news_list:
                video_url = news_item.get('video_url', '')
                if video_url:
                    if self.is_direct_video(video_url):
                        direct_video_news.append(news_item)
                        logger.info(f"🎬 ПРІОРИТЕТ: Пряме відео від {source_info['name']}: {news_item.get('title', '')[:50]}...")
                    else:
                        link_video_news.append(news_item)
                        logger.info(f"🎥 Відео-посилання від {source_info['name']}: {news_item.get('title', '')[:50]}...")
                else:
                    no_video_news.append(news_item)
        
        # Перемішуємо новини в кожній категорії для різноманітності джерел
        random.shuffle(direct_video_news)
        random.shuffle(link_video_news)
        random.shuffle(no_video_news)
        
        # Об'єднуємо: спочатку прямі відео, потім відео-посилання, потім без відео
        all_news = direct_video_news + link_video_news + no_video_news

        # --- Додаємо хаотичне чергування джерел ---
        # Групуємо новини за source_key
        from collections import defaultdict, deque
        source_groups = defaultdict(deque)
        for news in all_news:
            source_groups[news.get('source_key', '')].append(news)
        # Створюємо хаотичну чергу, по одній новині з кожного джерела, поки є новини
        shuffled_news = []
        source_keys = list(source_groups.keys())
        random.shuffle(source_keys)
        while any(source_groups.values()):
            for key in source_keys:
                if source_groups[key]:
                    shuffled_news.append(source_groups[key].popleft())
        all_news = shuffled_news
        # --- Кінець хаотичного чергування ---

        # --- Видаляємо дублікати за посиланням (link) ---
        unique_links = set()
        unique_news = []
        for news in all_news:
            link = news.get('link', '')
            if link and link not in unique_links:
                unique_links.add(link)
                unique_news.append(news)
        all_news = unique_news
        # --- Кінець видалення дублікатів ---

        # Логуємо статистику
        logger.info(f"📊 Статистика збору новин:")
        logger.info(f"   🎬 Прямі відео (пріоритет 1): {len(direct_video_news)}")
        logger.info(f"   🎥 Відео-посилання (пріоритет 2): {len(link_video_news)}")
        logger.info(f"   📰 Новини без відео (пріоритет 3): {len(no_video_news)}")
        logger.info(f"   ✅ Активні джерела: {len(sources_with_news)}")
        logger.info(f"   ❌ Неактивні джерела: {len(sources_without_news)}")
        
        if dead_sources:
            logger.warning("\n===== МЕРТВІ ДЖЕРЕЛА (немає новин) =====")
            for src in dead_sources:
                logger.warning(f"{src['name']} | RSS: {src['rss']} | Сайт: {src['website']}")
            logger.warning("===== КІНЕЦЬ СПИСКУ МЕРТВИХ ДЖЕРЕЛ =====\n")
        
        # Фільтруємо новини, щоб уникнути повторів з одного джерела підряд
        filtered_news = []
        if all_news:
            # Додаємо першу новину
            filtered_news.append(all_news[0])
            
            # Для решти новин перевіряємо джерело
            for news_item in all_news[1:]:
                current_source = news_item.get('source_key', '')
                
                # Якщо це не те саме джерело, що й останнє опубліковане, додаємо
                if current_source != self.last_source:
                    filtered_news.append(news_item)
                    break  # Беремо тільки одну новину за раз
            
            # Якщо не знайшли новину з іншого джерела, беремо першу доступну
            if len(filtered_news) == 1 and len(all_news) > 1:
                filtered_news.append(all_news[1])
        
        # Сортуємо за пріоритетом відео та часом (залишаємо для fallback)
        def get_sort_key(news_item):
            video_url = news_item.get('video_url', '')
            
            # Пріоритет: 0 = пряме відео, 1 = відео-посилання, 2 = без відео
            if video_url:
                if self.is_direct_video(video_url):
                    video_priority = 0  # Найвищий пріоритет
                else:
                    video_priority = 1  # Середній пріоритет
            else:
                video_priority = 2  # Найнижчий пріоритет
            
            # Парсимо дату публікації
            published_str = news_item.get('published', '')
            if published_str:
                published_dt = parse_published_date(published_str)
                if published_dt:
                    # Конвертуємо в timestamp без timezone
                    if published_dt.tzinfo:
                        published_dt = published_dt.replace(tzinfo=None)
                    timestamp = time.mktime(published_dt.timetuple())
                    return (video_priority, -timestamp)
            
            # Якщо дати немає, ставимо в кінець
            return (video_priority, 0)
        
        # filtered_news.sort(key=get_sort_key)  # <-- більше не сортуємо тут, бо вже хаотично
        all_news = filtered_news
        
        return all_news

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
