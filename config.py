import os
from dotenv import load_dotenv

load_dotenv()

# Telegram налаштування
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

# Джерела новин (RSS та веб-сайти)
NEWS_SOURCES = {
    # Офіційні українські джерела з відео
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
        'rss': 'https://www.unian.ua/rss',
        'website': 'https://www.unian.ua'
    },
    'pravda': {
        'name': 'Українська правда',
        'rss': 'https://www.pravda.com.ua/rss/',
        'website': 'https://www.pravda.com.ua'
    },
    'radiosvoboda': {
        'name': 'Радіо Свобода',
        'rss': 'https://www.radiosvoboda.org/api/zrqiteuuir',
        'website': 'https://www.radiosvoboda.org'
    },
    'interfax': {
        'name': 'Інтерфакс-Україна',
        'rss': 'https://ua.interfax.com.ua/news/general.rss',
        'website': 'https://ua.interfax.com.ua'
    },
    'channel24': {
        'name': '24 Канал',
        'rss': 'https://24tv.ua/rss/all.xml',
        'website': 'https://24tv.ua'
    },
    
    # Надійні джерела з кращою підтримкою відео
    'nv': {
        'name': 'НВ',
        'rss': 'https://nv.ua/rss.xml',
        'website': 'https://nv.ua'
    },
    'zn': {
        'name': 'Зеркало недели',
        'rss': 'https://zn.ua/rss',
        'website': 'https://zn.ua'
    },
    'fakty': {
        'name': 'Факти ICTV',
        'rss': 'https://fakty.com.ua/rss',
        'website': 'https://fakty.com.ua'
    },
    'obozrevatel': {
        'name': 'Обозреватель',
        'rss': 'https://obozrevatel.com/rss',
        'website': 'https://obozrevatel.com'
    },
    'korrespondent': {
        'name': 'Корреспондент',
        'rss': 'https://korrespondent.net/rss',
        'website': 'https://korrespondent.net'
    },
    'ukraine': {
        'name': 'Україна.ру',
        'rss': 'https://ukraina.ru/rss',
        'website': 'https://ukraina.ru'
    },
    'gordon': {
        'name': 'ГОРДОН',
        'rss': 'https://gordonua.com/rss',
        'website': 'https://gordonua.com'
    },
    'rbc': {
        'name': 'РБК-Україна',
        'rss': 'https://www.rbc.ua/rss',
        'website': 'https://www.rbc.ua'
    }
}

# Налаштування збору новин
CHECK_INTERVAL = 300  # секунди (5 хвилин)
MAX_POSTS_PER_CHECK = 3
MAX_TEXT_LENGTH = 4000

# Налаштування зображень
DEFAULT_IMAGE_URL = 'default_ua_news.jpg'
IMAGE_DOWNLOAD_TIMEOUT = 30

# Файл для зберігання опублікованих новин
PUBLISHED_NEWS_FILE = 'published_news.json'

# Токен для API повітряних тривог (alerts.in.ua)
ALERTS_API_TOKEN = "ed1f73bbaaecda208a960c2a84e20de7ae241d6fab2203"