import os
from dotenv import load_dotenv

load_dotenv()

# Telegram налаштування
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

# Джерела новин (RSS та веб-сайти)
NEWS_SOURCES = {
    # Світові новини (замінюємо на українські)
    'bbc_world': {
        'name': 'Наві України',
        'rss': 'https://navi.ua/rss',
        'website': 'https://navi.ua',
        'category': 'world',
        'language': 'uk'
    },
    'reuters_world': {
        'name': 'Еспресо',
        'rss': 'https://espreso.tv/rss',
        'website': 'https://espreso.tv',
        'category': 'world',
        'language': 'uk'
    },
    'cnn_world': {
        'name': '24 Канал',
        'rss': 'https://24tv.ua/rss',
        'website': 'https://24tv.ua',
        'category': 'world',
        'language': 'uk'
    },
    
    # Українські новини (4 джерела)
    'tsn': {
        'name': 'ТСН',
        'rss': 'https://tsn.ua/rss',
        'website': 'https://tsn.ua',
        'category': 'ukraine',
        'language': 'uk'
    },
    
    'unian': {
        'name': 'УНІАН',
        'rss': 'https://www.unian.ua/rss',
        'website': 'https://www.unian.ua',
        'category': 'ukraine',
        'language': 'uk'
    },
    'pravda': {
        'name': 'Українська правда',
        'rss': 'https://www.pravda.com.ua/rss/',
        'website': 'https://www.pravda.com.ua',
        'category': 'ukraine',
        'language': 'uk'
    },
    
    # Винаходи та технології (замінюємо на українські)
    'techcrunch': {
        'name': 'AIN.UA',
        'rss': 'https://ain.ua/feed/',
        'website': 'https://ain.ua',
        'category': 'inventions',
        'language': 'uk'
    },
    'wired_tech': {
        'name': 'Доун',
        'rss': 'https://dou.ua/feed/',
        'website': 'https://dou.ua',
        'category': 'inventions',
        'language': 'uk'
    },
    'the_verge': {
        'name': 'ITC.ua',
        'rss': 'https://itc.ua/feed/',
        'website': 'https://itc.ua',
        'category': 'inventions',
        'language': 'uk'
    },
    
    # Зіркове життя (замінюємо на українське)
    'people': {
        'name': 'Клік',
        'rss': 'https://clutch.ua/feed/',
        'website': 'https://clutch.ua',
        'category': 'celebrity',
        'language': 'uk'
    },
    
    # Війна з Україною (замінюємо на українські)
    'defense_news': {
        'name': 'Мілітарний',
        'rss': 'https://mil.in.ua/feed/',
        'website': 'https://mil.in.ua',
        'category': 'war',
        'language': 'uk'
    },
    'war_zone': {
        'name': 'АрміяInform',
        'rss': 'https://armyinform.com.ua/feed/',
        'website': 'https://armyinform.com.ua',
        'category': 'war',
        'language': 'uk'
    }
}

# Налаштування збору новин
CHECK_INTERVAL = 3500  # секунди (58 хвилин)
# Кількість новин для публікації за один раз
MAX_POSTS_PER_CHECK = 1
MAX_TEXT_LENGTH = 4000

# Налаштування зображень
DEFAULT_IMAGE_URL = 'file://default_ua_news.jpg'
IMAGE_DOWNLOAD_TIMEOUT = 30

# Файл для зберігання опублікованих новин
PUBLISHED_NEWS_FILE = 'published_news.json'

# Токен для API повітряних тривог (alerts.in.ua)
ALERTS_API_TOKEN = os.getenv('ALERTS_API_TOKEN')

# Налаштування групування відбоїв тривоги
MASS_END_THRESHOLD = 2  # Мінімальна кількість областей для масового відбою
MASS_END_TIME_WINDOW = 1  # Часовий вікно в хвилинах для групування відбоїв

# Налаштування групування тривог
MASS_ALERT_THRESHOLD = 3    # Мінімальна кількість областей для масової тривоги
MASS_ALERT_TIME_WINDOW = 2  # Часовий вікно в хвилинах для групування тривог