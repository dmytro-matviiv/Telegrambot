#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test news collection with fixed date parsing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from news_collector import NewsCollector
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_news_collection():
    """Test news collection functionality"""
    
    print("Testing news collection...")
    print("=" * 50)
    
    try:
        # Create news collector
        collector = NewsCollector()
        print("News collector created successfully")
        
        # Test collecting news
        print("Collecting news from sources...")
        news_list = collector.collect_all_news()
        
        print(f"Found {len(news_list)} news items")
        
        # Show first few news items
        for i, news in enumerate(news_list[:3]):
            print(f"\nNews #{i+1}:")
            print(f"  Title: {news.get('title', 'N/A')[:100]}...")
            print(f"  Source: {news.get('source', 'N/A')}")
            print(f"  Published: {news.get('published', 'N/A')}")
            print(f"  Has video: {'Yes' if news.get('video_url') else 'No'}")
        
        print("\n" + "=" * 50)
        print(f"SUCCESS: News collection completed with {len(news_list)} items")
        return True
        
    except Exception as e:
        print(f"ERROR: News collection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing Ukrainian News Bot - News Collection")
    print()
    
    success = test_news_collection()
    
    if success:
        print("Test completed successfully!")
        sys.exit(0)
    else:
        print("Test failed!")
        sys.exit(1)