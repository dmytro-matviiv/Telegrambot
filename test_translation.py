#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from news_collector import NewsCollector

def test_translation():
    """Тестує покращений переклад"""
    collector = NewsCollector()
    
    # Тестові тексти
    test_texts = [
        "Aid group каже worker killed by Israeli військовий in attack on Gaza HQ",
        "The Palestine Red Crescent має accused Israel of a deliberate strike, but Israel сказав it має no information about it.",
        "Ukraine military says Russian forces are advancing in eastern regions",
        "Breaking news: Zelensky meets with Biden in Washington",
        "Latest update on the war in Ukraine shows significant developments"
    ]
    
    print("=== ТЕСТ ПЕРЕКЛАДУ ===")
    for i, text in enumerate(test_texts, 1):
        print(f"\n{i}. Оригінал:")
        print(text)
        print("\nПереклад:")
        translated = collector.translate_text(text)
        print(translated)
        print("-" * 50)

if __name__ == "__main__":
    test_translation() 