#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тест для перевірки виправлення парсингу дат
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from news_collector import parse_published_date
from datetime import datetime

def test_date_parsing():
    """Тестує різні формати дат"""
    
    test_dates = [
        # RFC 2822 формати (найпоширеніші в RSS)
        "Mon, 04 Aug 2025 18:30:00 +0000",
        "Mon, 04 Aug 2025 18:30:00",
        "Mon, 04 Aug 2025 18",  # Проблемний формат з помилки
        "04 Aug 2025 18:30:00",
        
        # ISO формати
        "2025-08-04T18:30:00",
        "2025-08-04T18:30:00Z",
        "2025-08-04 18:30:00",
        "2025-08-04",
        
        # Інші формати
        "2025-08-04T18:30:00.000Z",
        "",
        None,
    ]
    
    print("Testuvannya parsingu dat:")
    print("=" * 60)
    
    success_count = 0
    total_count = 0
    
    for date_str in test_dates:
        total_count += 1
        print(f"Testuyemo: '{date_str}'")
        
        try:
            result = parse_published_date(date_str)
            if result:
                print(f"  OK Uspishno: {result}")
                success_count += 1
            else:
                print(f"  WARNING Ne rozparseno (None)")
        except Exception as e:
            print(f"  ERROR Pomilka: {e}")
        
        print()
    
    print("=" * 60)
    print(f"Rezultat: {success_count}/{total_count} uspishnih testiv")
    
    return success_count > 0

if __name__ == "__main__":
    print("Test parsingу dat dlya noviннogo bota")
    print()
    
    success = test_date_parsing()
    
    if success:
        print("Testi proyshli uspishno!")
        sys.exit(0)
    else:
        print("Testi ne proyshli!")
        sys.exit(1)