#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from news_collector import NewsCollector

def test_google_translate():
    """Тестує Google Translate"""
    collector = NewsCollector()
    
    # Тестові тексти
    test_texts = [
        "Aid group says worker killed by Israeli military in attack on Gaza HQ",
        "The Palestine Red Crescent has accused Israel of a deliberate strike, but Israel said it has no information about it.",
        "Ukraine military says Russian forces are advancing in eastern regions",
        "Breaking news: Zelensky meets with Biden in Washington",
        "Latest update on the war in Ukraine shows significant developments",
        "Russian forces are advancing in eastern regions of Ukraine",
        "The Ukrainian military reports that Russian troops are moving forward",
        "Breaking news from Kyiv shows that the situation is developing rapidly",
        "Latest developments in the conflict zone indicate significant changes",
        "The war in Ukraine continues with new developments every day"
    ]
    
    print("=== ТЕСТ GOOGLE TRANSLATE ===")
    for i, text in enumerate(test_texts, 1):
        print(f"\n{i}. Оригінал:")
        print(text)
        print("\nПереклад:")
        translated = collector.translate_text(text)
        print(translated)
        print("-" * 50)

if __name__ == "__main__":
    test_google_translate() 