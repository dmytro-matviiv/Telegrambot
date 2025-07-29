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
    # Новини про війну
    'pravda_war': {
        'name': 'Українська правда (Війна)',
        'rss': 'https://www.pravda.com.ua/rss/',
        'website': 'https://www.pravda.com.ua/rus/news/'
    },
    # Шоу-бізнес та зірки
    'tabloid': {
        'name': 'ТаблоID (зірки, шоу-бізнес)',
        'rss': 'https://tabloid.pravda.com.ua/rss/',
        'website': 'https://tabloid.pravda.com.ua/'
    },
    # Регіональні новини
    'kharkiv': {
        'name': 'Харківські новини',
        'rss': 'https://www.objectiv.tv/rss/',
        'website': 'https://www.objectiv.tv/'
    },
    'odesa': {
        'name': 'Одеські новини',
        'rss': 'https://odessa.online/feed/',
        'website': 'https://odessa.online/'
    },
    'dnipro': {
        'name': 'Дніпровські новини',
        'rss': 'https://dnipro.tv/feed/',
        'website': 'https://dnipro.tv/'
    },
    'zaporizhzhia': {
        'name': 'Запорізькі новини',
        'rss': 'https://akzent.zp.ua/feed/',
        'website': 'https://akzent.zp.ua/'
    },
    'vinnytsia': {
        'name': 'Вінницькі новини',
        'rss': 'https://vezha.ua/feed/',
        'website': 'https://vezha.ua/'
    },
    'chernihiv': {
        'name': 'Чернігівські новини',
        'rss': 'https://cheline.com.ua/feed',
        'website': 'https://cheline.com.ua/'
    },
    'kherson': {
        'name': 'Херсонські новини',
        'rss': 'https://most.ks.ua/feed/',
        'website': 'https://most.ks.ua/'
    },
    'ivano_frankivsk': {
        'name': 'Івано-Франківські новини',
        'rss': 'https://galka.if.ua/feed/',
        'website': 'https://galka.if.ua/'
    },
    'zhytomyr': {
        'name': 'Житомирські новини',
        'rss': 'https://zhitomir-online.com/rss.xml',
        'website': 'https://zhitomir-online.com/'
    },
    'rivne': {
        'name': 'Рівненські новини',
        'rss': 'https://rivnepost.rv.ua/rss',
        'website': 'https://rivnepost.rv.ua/'
    },
    'cherkasy': {
        'name': 'Черкаські новини',
        'rss': 'https://procherk.info/rss',
        'website': 'https://procherk.info/'
    },
    'pravda': {
        'name': 'Українська правда',
        'rss': 'https://www.pravda.com.ua/rss/',
        'website': 'https://www.pravda.com.ua/'
    },
}

# Налаштування збору новин
CHECK_INTERVAL = 1000  # секунди (5 хвилин)
MAX_POSTS_PER_CHECK = 1
MAX_TEXT_LENGTH = 4000

# Налаштування зображень
DEFAULT_IMAGE_URL = 'default_ua_news.jpg'
IMAGE_DOWNLOAD_TIMEOUT = 30

# Файл для зберігання опублікованих новин
PUBLISHED_NEWS_FILE = 'published_news.json'

# Токен для API повітряних тривог (alerts.in.ua)
ALERTS_API_TOKEN = "ed1f73bbaaecda208a960c2a84e20de7ae241d6fab2203" 