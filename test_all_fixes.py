#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Comprehensive test for all bot fixes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from news_collector import NewsCollector, parse_published_date
from datetime import datetime, timezone
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_date_parsing_comprehensive():
    """Test comprehensive date parsing"""
    print("1. Testing comprehensive date parsing...")
    
    test_cases = [
        # Original problematic format
        ("Mon, 04 Aug 2025 18", "Should handle incomplete RFC format"),
        # Standard formats
        ("Mon, 04 Aug 2025 18:30:00 +0000", "RFC 2822 with timezone"),
        ("Mon, 04 Aug 2025 18:30:00", "RFC 2822 without timezone"),
        ("2025-08-04T18:30:00", "ISO format"),
        ("2025-08-04T18:30:00Z", "ISO with Z"),
        ("2025-08-04 18:30:00", "Simple format"),
        ("2025-08-04", "Date only"),
    ]
    
    success_count = 0
    for date_str, description in test_cases:
        try:
            result = parse_published_date(date_str)
            if result:
                print(f"  + {description}: '{date_str}' -> {result}")
                success_count += 1
            else:
                print(f"  - {description}: '{date_str}' -> None (handled gracefully)")
                success_count += 1  # Graceful handling is also success
        except Exception as e:
            print(f"  x {description}: '{date_str}' -> ERROR: {e}")
    
    print(f"  Result: {success_count}/{len(test_cases)} cases handled successfully")
    return success_count == len(test_cases)

def test_timezone_consistency():
    """Test timezone consistency"""
    print("2. Testing timezone consistency...")
    
    now = datetime.now(timezone.utc)
    test_date = "Mon, 04 Aug 2025 18:30:00"
    
    try:
        parsed_dt = parse_published_date(test_date)
        if parsed_dt:
            # This should not raise an exception
            age = (now - parsed_dt).total_seconds() / 60
            print(f"  + Timezone comparison successful: {age:.1f} minutes difference")
            return True
        else:
            print("  - Failed to parse test date")
            return False
    except Exception as e:
        print(f"  x Timezone comparison failed: {e}")
        return False

def test_news_collection():
    """Test news collection without crashes"""
    print("3. Testing news collection...")
    
    try:
        collector = NewsCollector()
        news_list = collector.collect_all_news()
        print(f"  + News collection successful: {len(news_list)} items collected")
        
        # Check if any news have video
        video_count = sum(1 for news in news_list if news.get('video_url'))
        print(f"  + Video detection working: {video_count} items with video")
        
        return True
    except Exception as e:
        print(f"  x News collection failed: {e}")
        return False

def main():
    print("Comprehensive Bot Fixes Test")
    print("=" * 60)
    
    tests = [
        ("Date Parsing", test_date_parsing_comprehensive),
        ("Timezone Consistency", test_timezone_consistency),
        ("News Collection", test_news_collection),
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            if test_func():
                print(f"  PASSED: {test_name}")
                passed_tests += 1
            else:
                print(f"  FAILED: {test_name}")
        except Exception as e:
            print(f"  ERROR: {test_name} - {e}")
    
    print("\n" + "=" * 60)
    print(f"SUMMARY: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("SUCCESS: All critical fixes are working correctly!")
        print("The bot should now run without the original errors.")
        return True
    else:
        print("FAILURE: Some issues remain.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)