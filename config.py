import os
from dotenv import load_dotenv

load_dotenv()

# Telegram налаштування
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

# Джерела новин (RSS та веб-сайти)
NEWS_SOURCES = {
    # Офіційні джерела
    'tsn': {
        'name': 'ТСН',
        'rss': 'https://tsn.ua/rss',
        'website': 'https://tsn.ua/'
    },
    # Новини про війну в Україні
    'pravda_war': {
        'name': 'Українська правда (Війна)',
        'rss': 'https://www.pravda.com.ua/rss/',
        'website': 'https://www.pravda.com.ua/rus/news/'
    },
    # Всесвітні новини
    'bbc_world': {
        'name': 'BBC World News',
        'rss': 'https://feeds.bbci.co.uk/news/world/rss.xml',
        'website': 'https://www.bbc.com/news/world'
    },
    'reuters_world': {
        'name': 'Reuters World',
        'rss': 'https://feeds.reuters.com/Reuters/worldNews',
        'website': 'https://www.reuters.com/world/'
    },
    'cnn_world': {
        'name': 'CNN World',
        'rss': 'https://rss.cnn.com/rss/edition_world.rss',
        'website': 'https://www.cnn.com/world'
    },
    'ap_world': {
        'name': 'Associated Press World',
        'rss': 'https://feeds.feedburner.com/APWorldNews',
        'website': 'https://apnews.com/hub/world-news'
    },
    # Новини про війну та безпеку
    'defense_news': {
        'name': 'Defense News',
        'rss': 'https://www.defensenews.com/rss/feed',
        'website': 'https://www.defensenews.com/'
    },
    'war_zone': {
        'name': 'The War Zone',
        'rss': 'https://www.thedrive.com/the-war-zone/rss',
        'website': 'https://www.thedrive.com/the-war-zone'
    },
    # Українські новини про війну
    'ukrinform': {
        'name': 'Укрінформ',
        'rss': 'https://www.ukrinform.ua/rss',
        'website': 'https://www.ukrinform.ua/'
    },
    'unian_war': {
        'name': 'УНІАН (Війна)',
        'rss': 'https://www.unian.ua/rss/war.rss',
        'website': 'https://www.unian.ua/war'
    },
    'hromadske': {
        'name': 'Громадське',
        'rss': 'https://hromadske.ua/rss',
        'website': 'https://hromadske.ua/'
    },
    'nv_war': {
        'name': 'НВ (Війна)',
        'rss': 'https://nv.ua/rss/war.rss',
        'website': 'https://nv.ua/ukr/war'
    },
    # Міжнародні новини про Україну
    'guardian_ukraine': {
        'name': 'The Guardian (Україна)',
        'rss': 'https://www.theguardian.com/world/ukraine/rss',
        'website': 'https://www.theguardian.com/world/ukraine'
    },
    'nyt_ukraine': {
        'name': 'New York Times (Україна)',
        'rss': 'https://rss.nytimes.com/services/xml/rss/nyt/World.xml',
        'website': 'https://www.nytimes.com/topic/destination/ukraine'
    },
    'washington_post_world': {
        'name': 'Washington Post World',
        'rss': 'https://feeds.washingtonpost.com/rss/world',
        'website': 'https://www.washingtonpost.com/world/'
    },
    'al_jazeera_world': {
        'name': 'Al Jazeera World',
        'rss': 'https://www.aljazeera.com/xml/rss/all.xml',
        'website': 'https://www.aljazeera.com/news/'
    },
    'dw_world': {
        'name': 'Deutsche Welle World',
        'rss': 'https://rss.dw.com/xml/rss-de-all',
        'website': 'https://www.dw.com/en/top-stories/world/s-1007'
    }
}

# Налаштування збору новин
CHECK_INTERVAL = 3000  # секунди (5 хвилин)
MAX_POSTS_PER_CHECK = 1
MAX_TEXT_LENGTH = 4000

# Налаштування зображень
DEFAULT_IMAGE_URL = 'default_ua_news.jpg'
IMAGE_DOWNLOAD_TIMEOUT = 30

# Файл для зберігання опублікованих новин
PUBLISHED_NEWS_FILE = 'published_news.json'

# Токен для API повітряних тривог (alerts.in.ua)
ALERTS_API_TOKEN = "ed1f73bbaaecda208a960c2a84e20de7ae241d6fab2203" 