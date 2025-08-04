#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test new news sources
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from news_collector import NewsCollector
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_new_sources():
    """Test the new news sources"""
    print("Testing new news sources...")
    print("=" * 60)
    
    try:
        collector = NewsCollector()
        news_list = collector.collect_all_news()
        
        print(f"Total news collected: {len(news_list)}")
        
        # Show sources that provided news
        sources_with_news = {}
        for news in news_list:
            source = news.get('source', 'Unknown')
            if source not in sources_with_news:
                sources_with_news[source] = 0
            sources_with_news[source] += 1
        
        print("\nActive sources:")
        for source, count in sources_with_news.items():
            print(f"  + {source}: {count} news items")
        
        # Show sample news
        print(f"\nSample news (first 3):")
        for i, news in enumerate(news_list[:3]):
            print(f"{i+1}. {news.get('title', 'No title')[:80]}...")
            print(f"   Source: {news.get('source', 'Unknown')}")
            print(f"   Published: {news.get('published', 'Unknown')}")
            print(f"   Has video: {'Yes' if news.get('video_url') else 'No'}")
            print()
        
        print("=" * 60)
        print(f"SUCCESS: {len(sources_with_news)} sources are working")
        return len(sources_with_news) > 5  # At least 5 sources should work
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing New News Sources")
    print()
    
    success = test_new_sources()
    
    if success:
        print("Test completed successfully!")
        sys.exit(0)
    else:
        print("Test failed!")
        sys.exit(1)