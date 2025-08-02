#!/usr/bin/env python3
"""
Простий тест функціональності перекладу
"""

import re
import logging

# Налаштування логування
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def translate_text(text):
    """Простий переклад ключових слів з англійської на українську"""
    try:
        if not text or len(text.strip()) < 10:
            return text
        
        # Простий словник перекладів для ключових слів
        translations = {
            'ukraine': 'Україна',
            'ukrainian': 'український',
            'russia': 'Росія',
            'russian': 'російський',
            'war': 'війна',
            'conflict': 'конфлікт',
            'invasion': 'вторгнення',
            'military': 'військовий',
            'defense': 'оборона',
            'weapons': 'зброя',
            'sanctions': 'санкції',
            'zelensky': 'Зеленський',
            'putin': 'Путін',
            'kyiv': 'Київ',
            'kiev': 'Київ',
            'donetsk': 'Донецьк',
            'luhansk': 'Луганськ',
            'crimea': 'Крим',
            'breaking': 'терміново',
            'news': 'новини',
            'latest': 'останні',
            'update': 'оновлення',
            'report': 'звіт',
            'says': 'каже',
            'said': 'сказав',
            'will': 'буде',
            'has': 'має',
            'have': 'мають',
            'is': 'є',
            'are': 'є',
            'was': 'був',
            'were': 'були'
        }
        
        translated_text = text
        for eng_word, ukr_word in translations.items():
            # Замінюємо слова з урахуванням регістру
            translated_text = re.sub(r'\b' + re.escape(eng_word) + r'\b', ukr_word, translated_text, flags=re.IGNORECASE)
        
        return translated_text
    except Exception as e:
        logger.warning(f"Помилка перекладу: {e}")
        return text

def is_english_text(text):
    """Перевіряє чи текст англійською мовою"""
    if not text:
        return False
    
    # Прості індикатори англійської мови
    english_indicators = ['the', 'and', 'for', 'with', 'this', 'that', 'will', 'have', 'been', 'from', 'they', 'said']
    text_lower = text.lower()
    english_count = sum(1 for word in english_indicators if word in text_lower)
    
    # Якщо знайдено більше 2 англійських слів, вважаємо текст англійським
    return english_count >= 2

def test_translation():
    """Тестує функціональність перекладу"""
    
    logger.info("🔍 Тестуємо функцію перекладу...")
    
    test_texts = [
        "Ukraine war latest news",
        "Russia attacks Ukrainian cities",
        "Zelensky says Ukraine will win",
        "Breaking news from Kyiv",
        "Ukrainian military reports success"
    ]
    
    for text in test_texts:
        translated = translate_text(text)
        logger.info(f"Оригінал: {text}")
        logger.info(f"Переклад: {translated}")
        logger.info("---")
    
    # Тестуємо визначення англійської мови
    logger.info("🔍 Тестуємо визначення англійської мови...")
    
    test_language_texts = [
        ("Ukraine war latest news", True),
        ("Україна веде війну з Росією", False),
        ("Breaking news from Kyiv", True),
        ("Новини з Києва", False),
        ("Russia attacks Ukrainian cities", True)
    ]
    
    for text, expected in test_language_texts:
        is_english = is_english_text(text)
        status = "✅" if is_english == expected else "❌"
        logger.info(f"{status} '{text}' -> англійська: {is_english} (очікувано: {expected})")
    
    logger.info("✅ Тест завершено")

if __name__ == "__main__":
    test_translation() 