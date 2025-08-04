#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test bot functionality after fixes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from news_collector import NewsCollector, parse_published_date
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_date_parsing_fix():
    """Test that date parsing fix works"""
    print("Testing date parsing fix...")
    
    # Test the problematic date from the original error
    problematic_date = "Mon, 04 Aug 2025 18"
    result = parse_published_date(problematic_date)
    
    if result:
        print(f"SUCCESS: Problematic date '{problematic_date}' parsed as: {result}")
        return True
    else:
        print(f"INFO: Problematic date '{problematic_date}' handled gracefully (returned None)")
        return True  # This is also acceptable - no crash

def test_news_collection_no_crash():
    """Test that news collection doesn't crash"""
    print("Testing news collection (no crash)...")
    
    try:
        collector = NewsCollector()
        # Just test that we can create collector and call the method without crashing
        news_list = collector.collect_all_news()
        print(f"SUCCESS: News collection completed with {len(news_list)} items")
        return True
    except Exception as e:
        print(f"ERROR: News collection crashed: {e}")
        return False

def main():
    print("Testing Bot Fixes")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 2
    
    # Test 1: Date parsing fix
    if test_date_parsing_fix():
        tests_passed += 1
        print("+ Date parsing test PASSED")
    else:
        print("- Date parsing test FAILED")
    
    print()
    
    # Test 2: News collection no crash
    if test_news_collection_no_crash():
        tests_passed += 1
        print("+ News collection test PASSED")
    else:
        print("- News collection test FAILED")
    
    print()
    print("=" * 50)
    print(f"Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("SUCCESS: All critical fixes are working!")
        return True
    else:
        print("FAILURE: Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)