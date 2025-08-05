import os
from dotenv import load_dotenv

load_dotenv()

# Telegram налаштування
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

# Джерела новин (RSS та веб-сайти)
NEWS_SOURCES = {
    # Офіційні українські джерела
    'tsn': {
        'name': 'ТСН',
        'rss': 'https://tsn.ua/rss',
        'website': 'https://tsn.ua/'
    },
    'pravda_war': {
        'name': 'Українська правда (Війна)',
        'rss': 'https://www.pravda.com.ua/rss/',
        'website': 'https://www.pravda.com.ua/rus/news/'
    },
    'ukrinform': {
        'name': 'Укрінформ',
        'rss': 'https://www.ukrinform.ua/rss',
        'website': 'https://www.ukrinform.ua/'
    },
    'espreso': {
        'name': 'Еспресо',
        'rss': 'https://espreso.tv/rss',
        'website': 'https://espreso.tv/'
    },
    'unian': {
        'name': 'УНІАН',
        'rss': 'https://www.unian.ua/static/rss/all.xml',
        'website': 'https://www.unian.ua'
    },
    'pravda': {
        'name': 'Українська правда',
        'rss': 'https://www.pravda.com.ua/rss/',
        'website': 'https://www.pravda.com.ua'
    },
    'liga': {
        'name': 'Ліга.net',
        'rss': 'https://www.liga.net/news/all/rss.xml',
        'website': 'https://www.liga.net'
    },
    'radiosvoboda': {
        'name': 'Радіо Свобода',
        'rss': 'https://www.radiosvoboda.org/api/zrqiteuuir',
        'website': 'https://www.radiosvoboda.org'
    },
    'suspilne': {
        'name': 'Суспільне Новини',
        'rss': 'https://suspilne.media/rss/news.xml',
        'website': 'https://suspilne.media'
    },
    'interfax': {
        'name': 'Інтерфакс-Україна',
        'rss': 'https://ua.interfax.com.ua/news/general.rss',
        'website': 'https://ua.interfax.com.ua'
    },
    'novynarnia': {
        'name': 'Новинарня',
        'rss': 'https://novynarnia.com/feed/',
        'website': 'https://novynarnia.com'
    },
    'espreso': {
        'name': 'Еспресо',
        'rss': 'https://espreso.tv/rss',
        'website': 'https://espreso.tv'
    },
    'channel24': {
        'name': '24 Канал',
        'rss': 'https://24tv.ua/rss/all.xml',
        'website': 'https://24tv.ua'
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