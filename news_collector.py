import feedparser
import requests
from bs4 import BeautifulSoup
import json
import random
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import List, Dict
import logging
from config import NEWS_SOURCES, PUBLISHED_NEWS_FILE, DEFAULT_IMAGE_URL
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
    
    def is_similar_news(self, news1: dict, news2: dict) -> bool:
        """Перевіряє чи новини схожі (для уникнення дублювання)"""
        try:
            title1 = news1.get('title', '').lower()
            title2 = news2.get('title', '').lower()
            
            # Якщо заголовки ідентичні
            if title1 == title2:
                return True
            
            # Якщо один заголовок містить інший
            if title1 in title2 or title2 in title1:
                return True
            
            # Перевіряємо ключові слова
            keywords1 = set(title1.split())
            keywords2 = set(title2.split())
            
            # Якщо більше 70% ключових слів співпадають
            if len(keywords1) > 0 and len(keywords2) > 0:
                common_words = keywords1.intersection(keywords2)
                similarity = len(common_words) / max(len(keywords1), len(keywords2))
                if similarity > 0.7:
                    return True
            
            # Перевіряємо посилання
            link1 = news1.get('link', '')
            link2 = news2.get('link', '')
            if link1 == link2:
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Помилка при перевірці схожості новин: {e}")
            return False

    def is_food_related_content(self, title: str, summary: str, full_text: str = '') -> bool:
        """Перевіряє чи новина стосується приготування їжі, рецептів або кулінарії"""
        # Об'єднуємо весь текст для перевірки
        text = f"{title} {summary} {full_text}".lower()
        
        # Ключові слова та фрази, пов'язані з їжею та рецептами
        food_keywords = [
            # Українські слова
            'рецепт', 'рецепти', 'приготування', 'кулінарія', 'кухня', 'страва', 'страви',
            'готувати', 'готуємо', 'приготувати', 'приготуємо', 'смажити', 'варити', 'пекти',
            'інгредієнти', 'інгредієнт', 'приправи', 'приправа', 'соус', 'соуси',
            'салат', 'салати', 'суп', 'супи', 'борщ', 'вареники', 'пельмені', 'котлети',
            'торт', 'торти', 'десерт', 'десерти', 'випічка', 'печиво', 'кекс', 'кекси',
            'кава', 'чай', 'напій', 'напої', 'коктейль', 'коктейлі',
            'сніданок', 'обід', 'вечеря', 'перекуска', 'закуска', 'закуски',
            'хліб', 'молоко', 'сир', 'м\'ясо', 'риба', 'овочі', 'фрукти',
            'смак', 'смачний', 'смачна', 'смачне', 'аромат', 'ароматний',
            'калорії', 'калорійність', 'дієта', 'дієтичний', 'здорове харчування',
            'ресторан', 'ресторани', 'кафе', 'бар', 'бари', 'меню',
            'шеф-кухар', 'кухар', 'кухарка', 'кулінар', 'кулінари',
            'майстер-клас', 'майстер-класи', 'кулінарний', 'гастрономічний',
            
            # Англійські слова (на випадок, якщо потраплять англійські новини)
            'recipe', 'recipes', 'cooking', 'cook', 'kitchen', 'food', 'dish', 'dishes',
            'ingredient', 'ingredients', 'spice', 'spices', 'sauce', 'sauces',
            'salad', 'salads', 'soup', 'soups', 'cake', 'cakes', 'dessert', 'desserts',
            'baking', 'baked', 'coffee', 'tea', 'drink', 'drinks', 'cocktail', 'cocktails',
            'breakfast', 'lunch', 'dinner', 'snack', 'snacks', 'appetizer', 'appetizers',
            'bread', 'milk', 'cheese', 'meat', 'fish', 'vegetables', 'fruits',
            'taste', 'tasty', 'delicious', 'flavor', 'flavored', 'aroma', 'aromatic',
            'calories', 'calorie', 'diet', 'dietary', 'healthy eating', 'nutrition',
            'restaurant', 'restaurants', 'cafe', 'bar', 'bars', 'menu',
            'chef', 'cook', 'cooking', 'culinary', 'gastronomic', 'gastronomy',
            'masterclass', 'master class', 'cooking class', 'food preparation'
        ]
        
        # Перевіряємо наявність ключових слів
        for keyword in food_keywords:
            if keyword in text:
                logger.info(f"🚫 Знайдено ключове слово про їжу: '{keyword}' в новині: {title[:50]}...")
                return True
        
        # Додаткові фрази та словосполучення
        food_phrases = [
            'як приготувати', 'як зробити', 'як зварити', 'як спекти', 'як смажити',
            'рецепт приготування', 'спосіб приготування', 'приготування страви',
            'кулінарні поради', 'кулінарні секрети', 'кулінарний майстер-клас',
            'домашня кухня', 'традиційна кухня', 'національна кухня',
            'здорове харчування', 'дієтичне харчування', 'правильне харчування',
            'how to cook', 'how to make', 'cooking tips', 'cooking secrets',
            'home cooking', 'traditional cooking', 'healthy eating'
        ]
        
        for phrase in food_phrases:
            if phrase in text:
                logger.info(f"🚫 Знайдено фразу про їжу: '{phrase}' в новині: {title[:50]}...")
                return True
        
        return False
    
    def is_good_image_size(self, image_url: str) -> bool:
        """Швидка перевірка розміру фото та фільтрація реклами"""
        try:
            # Перевіряємо чи це не аналітичне посилання
            if any(analytics in image_url.lower() for analytics in ['google-analytics', 'facebook.com/tr', 'googletagmanager']):
                return False
            
            # Перевіряємо чи це не іконка або логотип
            if any(icon in image_url.lower() for icon in ['icon', 'logo', 'avatar', 'thumb']):
                return False
            
            # Перевіряємо чи це не реклама
            if any(ad in image_url.lower() for ad in ['ad', 'advertisement', 'banner', 'promo', 'sponsor']):
                return False
            
            # Перевіряємо чи це не реклама автомобілів
            if any(car in image_url.lower() for car in ['mazda', 'toyota', 'bmw', 'mercedes', 'audi', 'volkswagen', 'ford', 'chevrolet']):
                return False
            
            # Перевіряємо розширення файлу
            if image_url.endswith(('.svg', '.gif')):
                return False
            
            # Якщо URL виглядає нормально, приймаємо зображення
            if image_url.startswith('http') and len(image_url) > 20:
                return True
            
            return False
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
            filtered_food_count = 0  # Лічильник відфільтрованих новин про їжу
            
            for entry in feed.entries[:10]:  # Обмежуємо до 10 новин для швидкості
                try:
                    # Отримуємо дані новини
                    title = entry.get('title', '')
                    summary = entry.get('summary', '')
                    language = source_info.get('language', 'uk')  # За замовчуванням українська
                    
                    # Перевіряємо чи це українська мова (всі джерела тепер українські)
                    if not self.is_ukrainian_content(title, summary):
                        logger.warning(f"⚠️ Пропускаємо не українську новину: {title[:50]}...")
                        continue
                    
                    # Перевіряємо чи новина не стосується приготування їжі або рецептів
                    if self.is_food_related_content(title, summary):
                        logger.warning(f"🍽️ Пропускаємо новину про їжу/рецепти: {title[:50]}...")
                        filtered_food_count += 1
                        continue
                    
                    # Швидко шукаємо фото
                    image_url = self.extract_image_url(entry, entry.get('link', ''))
                    if not image_url:
                        # Спеціальна обробка для різних джерел
                        image_url = self.extract_image_for_source(entry, entry.get('link', ''), source_key)
                    
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
                                
                                # Додаткова перевірка повного тексту на кулінарну тематику
                                if self.is_food_related_content(title, summary, full_text):
                                    logger.warning(f"🍽️ Пропускаємо новину про їжу/рецепти (перевірка повного тексту): {title[:50]}...")
                                    filtered_food_count += 1
                                    continue
                        except Exception as e:
                            logger.warning(f"⚠️ Не вдалося отримати повний текст: {e}")
                    
                    # Формуємо детальний опис
                    detailed_description = self.create_detailed_description(summary, full_text, title)
                    
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
            
            # Логуємо статистику фільтрації
            if filtered_food_count > 0:
                logger.info(f"🍽️ {source_info['name']}: відфільтровано {filtered_food_count} новин про їжу/рецепти")
                
            return news_list
            
        except Exception as e:
            logger.error(f"Помилка при зборі новин з {source_info['name']}: {e}")
            return []

    def create_detailed_description(self, summary: str, full_text: str, title: str = "") -> str:
        """Створює детальний опис новини, уникаючи повторів та роблячи текст цікавим"""
        try:
            # Очищаємо вхідні дані
            summary = summary or ""
            full_text = full_text or ""
            title = title or ""
            
            # Очищаємо HTML теги
            if summary:
                soup = BeautifulSoup(summary, 'html.parser')
                summary = soup.get_text(separator=' ', strip=True)
            
            if full_text:
                soup = BeautifulSoup(full_text, 'html.parser')
                full_text = soup.get_text(separator=' ', strip=True)
            
            # Нормалізуємо пробіли
            summary = ' '.join(summary.split())
            full_text = ' '.join(full_text.split())
            title = ' '.join(title.split())
            
            # Видаляємо заголовок з опису та повного тексту, якщо він там є
            if title:
                # Видаляємо заголовок з початку опису
                if summary.lower().startswith(title.lower()):
                    summary = summary[len(title):].strip()
                    # Видаляємо зайві двокрапки та тире
                    if summary.startswith((':', '-', '—', '–')):
                        summary = summary[1:].strip()
                
                # Видаляємо заголовок з початку повного тексту
                if full_text.lower().startswith(title.lower()):
                    full_text = full_text[len(title):].strip()
                    if full_text.startswith((':', '-', '—', '–')):
                        full_text = full_text[1:].strip()
            
            # Додаткова очистка від метаданих на початку тексту
            import re
            
            # Видаляємо дати та час з початку
            summary = re.sub(r'^\d{1,2}\s+(січня|лютого|березня|квітня|травня|червня|липня|серпня|вересня|жовтня|листопада|грудня),?\s+\d{1,2}:\d{2}\s*', '', summary, flags=re.IGNORECASE)
            full_text = re.sub(r'^\d{1,2}\s+(січня|лютого|березня|квітня|травня|червня|липня|серпня|вересня|жовтня|листопада|грудня),?\s+\d{1,2}:\d{2}\s*', '', full_text, flags=re.IGNORECASE)
            
            # Видаляємо "Основні тези" з початку
            summary = re.sub(r'^Основні тези\s*', '', summary, flags=re.IGNORECASE)
            full_text = re.sub(r'^Основні тези\s*', '', full_text, flags=re.IGNORECASE)
            
            # Видаляємо повторення між summary та full_text
            if summary and full_text:
                # Якщо summary є частиною full_text, використовуємо тільки full_text
                if summary.lower() in full_text.lower():
                    summary = ""
                # Якщо full_text починається з summary, обрізаємо summary
                elif full_text.lower().startswith(summary.lower()):
                    summary = ""
            
            # Формуємо фінальний опис
            description = ""
            
            # Пріоритет надаємо повному тексту для більшої інформативності
            if full_text and len(full_text) >= 200:
                description = full_text
            # Якщо повного тексту немає або він короткий, використовуємо summary
            elif summary and len(summary) >= 100:
                description = summary
            # Якщо є і summary і full_text, поєднуємо їх
            elif summary and full_text:
                # Перевіряємо, чи не дублюються вони
                if summary.lower() not in full_text.lower() and full_text.lower() not in summary.lower():
                    description = f"{summary} {full_text}"
                else:
                    description = full_text if len(full_text) > len(summary) else summary
            # Якщо немає нічого, повертаємо порожній рядок
            else:
                return ""
            
            # Обмежуємо довжину до 600 символів для лаконічності
            if len(description) > 600:
                # Шукаємо кінець речення близько до 600 символів
                cut_point = 600
                for i in range(550, 650):
                    if i < len(description):
                        if description[i] in '.!?':
                            cut_point = i + 1
                            break
                
                description = description[:cut_point].strip()
                
                # Додаємо три крапки, якщо текст обрізано
                if not description.endswith(('.', '!', '?')):
                    description += "..."
            
            # Додаткове очищення від зайвих символів
            description = description.replace('  ', ' ').replace('\n', ' ').strip()
            
            # Покращуємо читабельність тексту
            description = self.improve_text_readability(description)
            
            return description
            
        except Exception as e:
            logger.warning(f"Помилка при створенні детального опису: {e}")
            return summary or ""

    def improve_text_readability(self, text: str) -> str:
        """Покращує читабельність тексту, видаляючи повторення та зайві слова"""
        try:
            if not text:
                return text
            
            # Видаляємо метадані (дата, час, автор)
            import re
            
            # Видаляємо дати та час
            text = re.sub(r'\d{1,2}\s+(січня|лютого|березня|квітня|травня|червня|липня|серпня|вересня|жовтня|листопада|грудня),?\s+\d{1,2}:\d{2}', '', text, flags=re.IGNORECASE)
            text = re.sub(r'\d{1,2}\s+вересня,?\s+\d{1,2}:\d{2}', '', text, flags=re.IGNORECASE)
            text = re.sub(r'\d{1,2}:\d{2}', '', text)
            
            # Видаляємо імена авторів та їх біографії
            text = re.sub(r'\n\s*[А-ЯІЇЄҐ][а-яіїєґ]+\s+[А-ЯІЇЄҐ][а-яіїєґ]+(?:\s+[А-ЯІЇЄҐ][а-яіїєґ]+)?\s*$', '', text)
            
            # Видаляємо біографії авторів (довгі тексти про автора)
            bio_patterns = [
                r'[А-ЯІЇЄҐ][а-яіїєґ]+\s+[А-ЯІЇЄҐ][а-яіїєґ]+[^.]*цікавлюся[^.]*\.',
                r'[А-ЯІЇЄҐ][а-яіїєґ]+\s+[А-ЯІЇЄҐ][а-яіїєґ]+[^.]*люблю[^.]*\.',
                r'[А-ЯІЇЄҐ][а-яіїєґ]+\s+[А-ЯІЇЄҐ][а-яіїєґ]+[^.]*розуміюся[^.]*\.',
                r'[А-ЯІЇЄҐ][а-яіїєґ]+\s+[А-ЯІЇЄҐ][а-яіїєґ]+[^.]*стежу[^.]*\.',
                r'[А-ЯІЇЄҐ][а-яіїєґ]+\s+[А-ЯІЇЄҐ][а-яіїєґ]+[^.]*пишу[^.]*\.'
            ]
            
            for pattern in bio_patterns:
                text = re.sub(pattern, '', text, flags=re.IGNORECASE)
            
            # Видаляємо "Основні тези"
            text = re.sub(r'Основні тези\s*', '', text, flags=re.IGNORECASE)
            
            # Видаляємо описи фото
            text = re.sub(r'[А-ЯІЇЄҐ][^.]*\/\s*Фото\s+[^.]*', '', text)
            text = re.sub(r'Фото\s+[^.]*', '', text, flags=re.IGNORECASE)
            
            # Видаляємо зайві фрази та слова (розширений список)
            redundant_phrases = [
                'повний текст новини', 'читати далі', 'детальніше читайте', 'більше інформації',
                'продовження читайте', 'далі читайте', 'читати повністю', 'повний текст',
                'детальніше', 'більше', 'далі', 'продовження', 'що відбувається', 'що сталося',
                'що трапилося', 'подробиці', 'деталі події', 'дивіться також', 'читайте також',
                'також читайте', 'що відомо', 'що відомо на цей момент', 'на цей момент',
                'повідомляють', 'пишуть', 'інформує', 'повідомляє', 'зазначає', 'відзначає',
                'про це повідомили', 'про це інформували', 'про це зазначають', 'про це відзначають'
            ]
            
            for phrase in redundant_phrases:
                text = re.sub(rf'\b{re.escape(phrase)}\b', '', text, flags=re.IGNORECASE)
            
            # Видаляємо питання в кінці тексту
            text = re.sub(r'\s*[?]\s*$', '', text)
            text = re.sub(r'\s*[?]\s*[А-ЯІЇЄҐ].*$', '', text)
            
            # Видаляємо повторення речень
            sentences = text.split('. ')
            unique_sentences = []
            seen_sentences = set()
            
            for sentence in sentences:
                # Нормалізуємо речення для порівняння
                normalized = sentence.lower().strip()
                if normalized and normalized not in seen_sentences and len(normalized) > 10:
                    unique_sentences.append(sentence.strip())
                    seen_sentences.add(normalized)
            
            text = '. '.join(unique_sentences)
            
            # Видаляємо зайві пробіли та символи
            text = ' '.join(text.split())
            text = text.replace('..', '.').replace('...', '...')
            
            # Видаляємо повторення слів у реченнях
            words = text.split()
            cleaned_words = []
            prev_word = ""
            
            for word in words:
                if word.lower() != prev_word.lower():
                    cleaned_words.append(word)
                    prev_word = word
            
            text = ' '.join(cleaned_words)
            
            # Видаляємо порожні речення та зайві пробіли
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'\.\s*\.', '.', text)
            
            return text.strip()
            
        except Exception as e:
            logger.warning(f"Помилка при покращенні читабельності: {e}")
            return text

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
                '.article-body',
                '.post-body',
                '.entry-body',
                '.news-body',
                '.story-body',
                '.article-text',
                '.post-text',
                '.entry-text',
                'main',
                '.main-content',
                '.text-content',
                '.body-content',
                '.article-wrapper',
                '.post-wrapper',
                '.entry-wrapper'
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
                            if any(keyword in class_name.lower() for keyword in ['content', 'article', 'post', 'story', 'text', 'body', 'wrapper', 'main']):
                                content = tag
                                logger.info(f"📖 Знайдено контент за класом: {class_name}")
                                break
                        if content:
                            break
            
            # Додаткова логіка для українських новинних сайтів
            if not content:
                # Шукаємо за ID
                for tag in soup.find_all(['div', 'section'], id=True):
                    tag_id = tag.get('id', '').lower()
                    if any(keyword in tag_id for keyword in ['content', 'article', 'post', 'story', 'text', 'body', 'main']):
                        content = tag
                        logger.info(f"📖 Знайдено контент за ID: {tag_id}")
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
                
                # Обмежуємо довжину до 2000 символів для більшої інформативності
                if len(text) > 2000:
                    text = text[:2000]
                    # Шукаємо кінець речення
                    for i in range(1950, 2000):
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
                            if src and src.startswith('http'):
                                # Фільтруємо аналітичні та Facebook посилання
                                if any(analytics in src.lower() for analytics in ['google-analytics', 'facebook.com/tr', 'googletagmanager', 'facebook.com']):
                                    continue
                                # Перевіряємо розмір зображення (пропускаємо маленькі іконки)
                                if any(size in src.lower() for size in ['thumb', 'icon', 'logo', 'avatar', '16x16', '32x32', '48x48']):
                                    continue
                                # Пропускаємо SVG та GIF
                                if src.endswith(('.svg', '.gif')):
                                    continue
                                # Пріоритет для великих зображень
                                if any(size in src.lower() for size in ['1200x630', '800x600', '1200x800', '1600x900', '1920x1080']):
                                    logger.info(f"📸 Знайдено велике зображення: {src[:50]}...")
                                    return src
                                images.append(src)
                        
                        # 2. Шукаємо в основному контенті
                        main_content = soup.find('article') or soup.find('main') or soup.find('.content') or soup.find('.article-content') or soup.find('.post-content')
                        if main_content:
                            main_images = main_content.find_all('img')
                            for img in main_images:
                                src = img.get('src', '')
                                if src and src.startswith('http'):
                                    # Фільтруємо аналітичні та Facebook посилання
                                    if any(analytics in src.lower() for analytics in ['google-analytics', 'facebook.com/tr', 'googletagmanager', 'facebook.com']):
                                        continue
                                    # Перевіряємо розмір зображення
                                    if any(size in src.lower() for size in ['thumb', 'icon', 'logo', 'avatar', '16x16', '32x32', '48x48']):
                                        continue
                                    if src.endswith(('.svg', '.gif')):
                                        continue
                                    # Пріоритет для великих зображень
                                    if any(size in src.lower() for size in ['1200x630', '800x600', '1200x800', '1600x900', '1920x1080']):
                                        logger.info(f"📸 Знайдено велике зображення в контенті: {src[:50]}...")
                                        return src
                                    images.append(src)
                        
                        # 3. Шукаємо в різних контейнерах для зображень
                        image_containers = [
                            '.hero-image', '.featured-image', '.lead-image', '.main-image',
                            '.article-image', '.post-image', '.story-image', '.news-image',
                            '.image-container', '.media-container', '.photo-container',
                            '[data-image]', '[data-src]', '.lazy-image'
                        ]
                        
                        for container_selector in image_containers:
                            try:
                                container = soup.select_one(container_selector)
                                if container:
                                    img = container.find('img')
                                    if img:
                                        src = img.get('src') or img.get('data-src') or img.get('data-image')
                                        if src and src.startswith('http'):
                                            if any(size in src.lower() for size in ['thumb', 'icon', 'logo', 'avatar', '16x16', '32x32', '48x48']):
                                                continue
                                            if src.endswith(('.svg', '.gif')):
                                                continue
                                            logger.info(f"📸 Знайдено зображення в контейнері {container_selector}: {src[:50]}...")
                                            return src
                            except:
                                continue
                        
                        # 4. Шукаємо за атрибутами data-src та data-image
                        for img in soup.find_all('img'):
                            src = img.get('data-src') or img.get('data-image') or img.get('data-lazy')
                            if src and src.startswith('http'):
                                if any(size in src.lower() for size in ['thumb', 'icon', 'logo', 'avatar', '16x16', '32x32', '48x48']):
                                    continue
                                if src.endswith(('.svg', '.gif')):
                                    continue
                                logger.info(f"📸 Знайдено зображення з data-атрибуту: {src[:50]}...")
                                return src
                        
                        # 5. Повертаємо перше знайдене зображення
                        for img_url in images:
                            if not img_url.endswith(('.svg', '.gif')):
                                logger.info(f"📸 Використовуємо зображення: {img_url[:50]}...")
                                return img_url
                                
                except Exception as e:
                    logger.warning(f"Помилка при отриманні повного тексту: {e}")

            return ""  # Повертаємо порожній рядок якщо фото не знайдено

        except Exception as e:
            logger.error(f"Помилка при витягуванні зображення: {e}")
            return ""  # Повертаємо порожній рядок якщо помилка

    def extract_image_for_source(self, entry, article_url: str, source_key: str) -> str:
        """Спеціальна обробка для різних джерел новин, щоб краще знаходити зображення"""
        try:
            def is_bad_image(url: str) -> bool:
                u = url.lower()
                if any(bad in u for bad in ['google-analytics', 'facebook.com/tr', 'googletagmanager', 'doubleclick.net', 'pixel']) or u.endswith(('.svg', '.gif')) or any(icon in u for icon in ['icon', 'logo', 'avatar', 'thumb']):
                    return True
                # Фільтруємо рекламу
                if any(ad in u for ad in ['ad', 'advertisement', 'banner', 'promo', 'sponsor']):
                    return True
                # Фільтруємо рекламу автомобілів
                if any(car in u for car in ['mazda', 'toyota', 'bmw', 'mercedes', 'audi', 'volkswagen', 'ford', 'chevrolet']):
                    return True
                return False

            # Перевіряємо медіа контент на зображення
            if hasattr(entry, 'media_content') and entry.media_content:
                for media in entry.media_content:
                    url = media.get('url') or media.get('href')
                    if url and media.get('type', '').startswith('image/') and not is_bad_image(url):
                        logger.info(f"📸 Спеціально зображення в медіа контенті для {source_key}: {url[:50]}...")
                        return url

            # Перевіряємо опис на зображення
            if entry.get('summary'):
                soup = BeautifulSoup(entry['summary'], 'html.parser')
                img = soup.find('img')
                if img:
                    url = img.get('src') or img.get('data-src')
                    if url and url.startswith('http') and not is_bad_image(url):
                        logger.info(f"📸 Спеціально зображення в описі для {source_key}: {url[:50]}...")
                        return url

            # Перевіряємо повний текст статті
            if article_url:
                try:
                    response = self.session.get(article_url, timeout=15)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')

                        # Спеціальна логіка для ТСН
                        if source_key == 'tsn':
                            tsn_images = []
                            for img in soup.find_all('img'):
                                src = img.get('src') or img.get('data-src') or ''
                                if not src or not src.startswith('http'):
                                    continue
                                if is_bad_image(src):
                                    continue
                                if 'img.tsn.ua' in src and 'thumb' in src:
                                    if any(size in src for size in ['1200x630', '1200x800', '800x600', '1600x900', '1920x1080', '1280x720']):
                                        logger.info(f"📸 TSN основне зображення: {src[:80]}...")
                                        return src
                                    tsn_images.append(src)
                            for src in tsn_images:
                                logger.info(f"📸 TSN альтернативне зображення: {src[:80]}...")
                                return src

                        # Спеціальна логіка для Наві України
                        elif source_key == 'bbc_world':
                            navi_images = []
                            for img in soup.find_all('img'):
                                src = img.get('src') or img.get('data-src') or ''
                                if not src or not src.startswith('http'):
                                    continue
                                if is_bad_image(src):
                                    continue
                                if 'navi.ua' in src:
                                    if any(size in src for size in ['1200x630', '1200x800', '800x600', '1600x900', '1920x1080', '1280x720']):
                                        logger.info(f"📸 Наві України основне зображення: {src[:80]}...")
                                        return src
                                    navi_images.append(src)
                            for src in navi_images:
                                logger.info(f"📸 Наві України альтернативне зображення: {src[:80]}...")
                                return src

                        # Спеціальна логіка для Еспресо
                        elif source_key == 'reuters_world':
                            espreso_images = []
                            for img in soup.find_all('img'):
                                src = img.get('src') or img.get('data-src') or ''
                                if not src or not src.startswith('http'):
                                    continue
                                if is_bad_image(src):
                                    continue
                                if 'espreso.tv' in src:
                                    if any(size in src for size in ['1200x630', '1200x800', '800x600', '1600x900', '1920x1080', '1280x720']):
                                        logger.info(f"📸 Еспресо основне зображення: {src[:80]}...")
                                        return src
                                    espreso_images.append(src)
                            for src in espreso_images:
                                logger.info(f"📸 Еспресо альтернативне зображення: {src[:80]}...")
                                return src

                        # Загальна логіка
                        images = []
                        for img in soup.find_all('img'):
                            src = img.get('src') or img.get('data-src') or img.get('data-image') or ''
                            if not src or not src.startswith('http'):
                                continue
                            if is_bad_image(src):
                                continue
                            # Пріоритет для великих зображень
                            if any(size in src.lower() for size in ['1200x630', '800x600', '1200x800', '1600x900', '1920x1080']):
                                logger.info(f"📸 Спеціально велике зображення в контенті для {source_key}: {src[:50]}...")
                                return src
                            images.append(src)

                        if images:
                            logger.info(f"📸 Спеціально використовуємо зображення для {source_key}: {images[0][:50]}...")
                            return images[0]
                except Exception as e:
                    logger.warning(f"Помилка при отриманні повного тексту для спеціальної обробки: {e}")

            return ""

        except Exception as e:
            logger.error(f"Помилка при спеціальній обробці зображення: {e}")
            return ""

    def collect_all_news(self) -> List[Dict]:
        """Збирає новини з усіх категорій та перемішує їх"""
        all_news = []
        
        # Визначаємо категорії та їх джерела
        categories = {
            'world': ['bbc_world', 'reuters_world', 'cnn_world'],  # Наві України, Еспресо, 24 Канал
            'ukraine': ['tsn', 'unian', 'pravda'],                # ТСН, УНІАН, Українська правда
            'inventions': ['techcrunch', 'wired_tech', 'the_verge'], # Доун, ITC.ua, Dev.ua
            'celebrity': ['people'],                              # Клік
            'war': ['defense_news', 'war_zone']                   # Мілітарний, АрміяInform
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
        
        # Фільтруємо вже опубліковані новини та дублікати
        new_news = []
        seen_news = []  # Для дедуплікації
        
        for news in all_news:
            news_id = f"{news['source_key']}_{news['id']}"
            if news_id not in self.published_news:
                # Перевіряємо чи це не дублікат
                is_duplicate = False
                for seen in seen_news:
                    if self.is_similar_news(news, seen):
                        logger.info(f"🚫 Пропускаємо дублікат: {news['title'][:50]}... (схоже на {seen['title'][:50]}...)")
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    new_news.append(news)
                    seen_news.append(news)
        
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

