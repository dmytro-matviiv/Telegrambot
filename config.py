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
        'rss': 'https://rss.unian.net/site/news_ukr.rss',
        'website': 'https://www.unian.ua/'
    },
    'korrespondent': {
        'name': 'Кореспондент.net',
        'rss': 'https://ua.korrespondent.net/rss/',
        'website': 'https://ua.korrespondent.net/'
    },
    'segodnya': {
        'name': 'Сьогодні.ua',
        'rss': 'https://ukr.segodnya.ua/rss.xml',
        'website': 'https://ukr.segodnya.ua/'
    },
    'zn_ua': {
        'name': 'Дзеркало тижня',
        'rss': 'https://zn.ua/rss/full.rss',
        'website': 'https://zn.ua/'
    },
    # Міжнародні джерела
    'bbc_world': {
        'name': 'BBC World News',
        'rss': 'https://feeds.bbci.co.uk/news/world/rss.xml',
        'website': 'https://www.bbc.com/news/world'
    },
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
    'al_jazeera_world': {
        'name': 'Al Jazeera World',
        'rss': 'https://www.aljazeera.com/xml/rss/all.xml',
        'website': 'https://www.aljazeera.com/news/'
    },
    'dw_ukraine': {
        'name': 'Deutsche Welle Україна',
        'rss': 'https://rss.dw.com/xml/rss-uk-all',
        'website': 'https://www.dw.com/uk/'
    },
    'radiosvoboda': {
        'name': 'Радіо Свобода',
        'rss': 'https://www.radiosvoboda.org/api/zrqiteuuir',
        'website': 'https://www.radiosvoboda.org/'
    },
    'voa_ukraine': {
        'name': 'Голос Америки Україна',
        'rss': 'https://ukrainian.voanews.com/api/zrqiteuuir',
        'website': 'https://ukrainian.voanews.com/'
    },
    'censor_net': {
        'name': 'Цензор.НЕТ',
        'rss': 'https://censor.net/includes/news_rss.php',
        'website': 'https://censor.net/'
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