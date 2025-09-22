#!/usr/bin/env python3
"""
Тест RSS джерел для перевірки їх роботи
"""

import feedparser
import requests
import time
from datetime import datetime

# Копіюємо джерела з config.py
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
        'name': 'Доун',
        'rss': 'https://dou.ua/feed/',
        'website': 'https://dou.ua',
        'category': 'inventions',
        'language': 'uk'
    },
    'wired_tech': {
        'name': 'ITC.ua',
        'rss': 'https://itc.ua/feed/',
        'website': 'https://itc.ua',
        'category': 'inventions',
        'language': 'uk'
    },
    'the_verge': {
        'name': 'Dev.ua',
        'rss': 'https://dev.ua/feed/',
        'website': 'https://dev.ua',
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

def test_rss_source(source_key, source_info):
    """Тестує одне RSS джерело"""
    print(f"\n🔍 Тестуємо: {source_info['name']} ({source_key})")
    print(f"📡 RSS: {source_info['rss']}")
    print(f"🌐 Сайт: {source_info['website']}")
    print(f"📂 Категорія: {source_info['category']}")
    
    try:
        # Тестуємо HTTP запит
        response = requests.get(source_info['rss'], timeout=10)
        print(f"📊 HTTP статус: {response.status_code}")
        
        if response.status_code == 200:
            # Тестуємо парсинг RSS
            feed = feedparser.parse(response.content)
            
            if feed.bozo:
                print(f"⚠️ RSS має помилки: {feed.bozo_exception}")
            
            print(f"📰 Кількість записів: {len(feed.entries)}")
            
            if feed.entries:
                # Показуємо перші 3 заголовки
                print("📋 Перші заголовки:")
                for i, entry in enumerate(feed.entries[:3]):
                    title = entry.get('title', 'Без заголовка')[:60]
                    print(f"   {i+1}. {title}...")
                
                # Перевіряємо наявність зображень
                images_found = 0
                for entry in feed.entries[:5]:
                    if hasattr(entry, 'media_content') and entry.media_content:
                        images_found += 1
                    elif entry.get('summary') and '<img' in entry.get('summary', ''):
                        images_found += 1
                
                print(f"🖼️ Записів з зображеннями: {images_found}/{min(5, len(feed.entries))}")
                
                return True
            else:
                print("❌ RSS не містить записів")
                return False
        else:
            print(f"❌ HTTP помилка: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Таймаут запиту")
        return False
    except requests.exceptions.ConnectionError:
        print("🔌 Помилка з'єднання")
        return False
    except Exception as e:
        print(f"❌ Помилка: {e}")
        return False

def test_all_sources():
    """Тестує всі RSS джерела"""
    print("🚀 ТЕСТ RSS ДЖЕРЕЛ")
    print("=" * 60)
    print(f"📅 Час тесту: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Всього джерел: {len(NEWS_SOURCES)}")
    
    working_sources = []
    broken_sources = []
    
    for source_key, source_info in NEWS_SOURCES.items():
        if test_rss_source(source_key, source_info):
            working_sources.append((source_key, source_info['name']))
        else:
            broken_sources.append((source_key, source_info['name']))
        
        # Невелика пауза між запитами
        time.sleep(1)
    
    # Підсумки
    print("\n" + "=" * 60)
    print("📊 ПІДСУМКИ ТЕСТУ")
    print("=" * 60)
    
    print(f"✅ Працюючі джерела ({len(working_sources)}):")
    for source_key, name in working_sources:
        print(f"   • {name} ({source_key})")
    
    print(f"\n❌ Непрацюючі джерела ({len(broken_sources)}):")
    for source_key, name in broken_sources:
        print(f"   • {name} ({source_key})")
    
    print(f"\n📈 Статистика: {len(working_sources)}/{len(NEWS_SOURCES)} джерел працюють")
    
    if broken_sources:
        print(f"\n🔧 Рекомендації:")
        print("   • Перевірте URL непрацюючих джерел")
        print("   • Можливо, сайт змінив структуру RSS")
        print("   • Спробуйте знайти альтернативні RSS посилання")

if __name__ == "__main__":
    test_all_sources()
