import os
from dotenv import load_dotenv

load_dotenv()

# Telegram налаштування
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

# Джерела новин (RSS та веб-сайти)
NEWS_SOURCES = {
    # Світові новини (3 джерела)
    'bbc_world': {
        'name': 'BBC World',
        'rss': 'https://feeds.bbci.co.uk/news/world/rss.xml',
        'website': 'https://www.bbc.com/news/world',
        'category': 'world',
        'language': 'en'
    },
    'reuters_world': {
        'name': 'Reuters World',
        'rss': 'https://feeds.reuters.com/Reuters/worldNews',
        'website': 'https://www.reuters.com/world',
        'category': 'world',
        'language': 'en'
    },
    'cnn_world': {
        'name': 'CNN World',
        'rss': 'http://rss.cnn.com/rss/edition_world.rss',
        'website': 'https://www.cnn.com/world',
        'category': 'world',
        'language': 'en'
    },
    
    # Українські новини (3 джерела)
    'channel24': {
        'name': '24 Канал',
        'rss': 'https://24tv.ua/rss/all.xml',
        'website': 'https://24tv.ua',
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
    
    # Винаходи та технології (3 джерела)
    'techcrunch': {
        'name': 'TechCrunch',
        'rss': 'https://techcrunch.com/feed/',
        'website': 'https://techcrunch.com',
        'category': 'inventions',
        'language': 'en'
    },
    'wired_tech': {
        'name': 'Wired Technology',
        'rss': 'https://www.wired.com/feed/rss',
        'website': 'https://www.wired.com',
        'category': 'inventions',
        'language': 'en'
    },
    'the_verge': {
        'name': 'The Verge',
        'rss': 'https://www.theverge.com/rss/index.xml',
        'website': 'https://www.theverge.com',
        'category': 'inventions',
        'language': 'en'
    },
    
    # Зіркове життя (2 джерела)
    'people': {
        'name': 'People',
        'rss': 'https://people.com/feed/',
        'website': 'https://people.com',
        'category': 'celebrity',
        'language': 'en'
    },
    'eonline': {
        'name': 'E! Online',
        'rss': 'https://www.eonline.com/feed',
        'website': 'https://www.eonline.com',
        'category': 'celebrity',
        'language': 'en'
    },
    
    # Війна з Україною (2 джерела)
    'defense_news': {
        'name': 'Defense News',
        'rss': 'https://www.defensenews.com/rss/',
        'website': 'https://www.defensenews.com',
        'category': 'war',
        'language': 'en'
    },
    'war_zone': {
        'name': 'The War Zone',
        'rss': 'https://www.thedrive.com/the-war-zone/rss',
        'website': 'https://www.thedrive.com/the-war-zone',
        'category': 'war',
        'language': 'en'
    }
}

# Налаштування збору новин
CHECK_INTERVAL = 2500  # секунди (5 хвилин)
MAX_POSTS_PER_CHECK = 3
MAX_TEXT_LENGTH = 3000

# Налаштування зображень
DEFAULT_IMAGE_URL = 'file://default_ua_news.jpg'
IMAGE_DOWNLOAD_TIMEOUT = 30

# Файл для зберігання опублікованих новин
PUBLISHED_NEWS_FILE = 'published_news.json'

# Токен для API повітряних тривог (alerts.in.ua)
ALERTS_API_TOKEN = "ed1f73bbaaecda208a960c2a84e20de7ae241d6fab2203"