#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from news_collector import NewsCollector
import logging

# Налаштування логування
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_published_news():
    """Перевіряє файл опублікованих новин на дублікати"""
    try:
        # Завантажуємо опубліковані новини
        with open('published_news.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        published_news = data.get('published_news', [])
        
        logger.info(f"📊 Всього записів у файлі: {len(published_news)}")
        
        # Перевіряємо на дублікати
        unique_news = set()
        duplicates = []
        
        for news_id in published_news:
            if news_id in unique_news:
                duplicates.append(news_id)
            else:
                unique_news.add(news_id)
        
        logger.info(f"✅ Унікальних записів: {len(unique_news)}")
        logger.info(f"❌ Дублікатів знайдено: {len(duplicates)}")
        
        if duplicates:
            logger.info("🔍 Знайдені дублікати:")
            for dup in duplicates[:5]:  # Показуємо перші 5
                logger.info(f"   {dup}")
        
        # Показуємо приклади ID
        logger.info("📝 Приклади ID новин:")
        for i, news_id in enumerate(published_news[:5]):
            logger.info(f"   {i+1}. {news_id}")
        
        return len(duplicates) > 0
        
    except Exception as e:
        logger.error(f"❌ Помилка при перевірці: {e}")
        return False

def fix_published_news():
    """Виправляє файл опублікованих новин, видаляючи дублікати"""
    try:
        # Завантажуємо опубліковані новини
        with open('published_news.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        published_news = data.get('published_news', [])
        original_count = len(published_news)
        
        # Видаляємо дублікати
        unique_news = list(set(published_news))
        new_count = len(unique_news)
        
        logger.info(f"📊 Було записів: {original_count}")
        logger.info(f"📊 Стало записів: {new_count}")
        logger.info(f"🗑️ Видалено дублікатів: {original_count - new_count}")
        
        # Зберігаємо виправлений файл
        data['published_news'] = unique_news
        
        with open('published_news.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info("✅ Файл виправлено та збережено")
        return True
        
    except Exception as e:
        logger.error(f"❌ Помилка при виправленні: {e}")
        return False

def test_news_collection():
    """Тестує збір новин та перевіряє на дублікати"""
    try:
        collector = NewsCollector()
        
        logger.info("🔍 Тестуємо збір новин...")
        all_news = collector.collect_all_news()
        
        if all_news:
            logger.info(f"📰 Знайдено {len(all_news)} нових новин")
            
            # Показуємо приклади ID
            logger.info("📝 Приклади ID нових новин:")
            for i, news in enumerate(all_news[:3]):
                news_id = f"{news['source_key']}_{news['id']}"
                logger.info(f"   {i+1}. {news_id}")
                logger.info(f"      Заголовок: {news['title'][:50]}...")
        else:
            logger.info("📭 Нових новин не знайдено")
            
    except Exception as e:
        logger.error(f"❌ Помилка при тестуванні: {e}")

if __name__ == "__main__":
    print("🔍 Перевірка дублікатів новин")
    print("=" * 50)
    
    # Перевіряємо на дублікати
    has_duplicates = check_published_news()
    
    if has_duplicates:
        print("\n🗑️ Виправляємо дублікати...")
        fix_published_news()
    
    print("\n🧪 Тестуємо збір новин...")
    test_news_collection()
