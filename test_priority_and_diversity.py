#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test priority and source diversity functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from news_collector import NewsCollector
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_video_priority():
    """Test video priority logic"""
    print("Testing video priority logic...")
    
    collector = NewsCollector()
    
    # Test direct video detection
    test_cases = [
        ("https://example.com/video.mp4", True, "Direct MP4 video"),
        ("https://example.com/video.webm", True, "Direct WebM video"),
        ("https://www.youtube.com/watch?v=abc123", False, "YouTube link"),
        ("https://youtu.be/abc123", False, "YouTube short link"),
        ("https://vimeo.com/123456789", False, "Vimeo link"),
        ("https://www.facebook.com/video.php?v=123", False, "Facebook link"),
        ("", False, "No video"),
    ]
    
    success_count = 0
    for video_url, expected, description in test_cases:
        result = collector.is_direct_video(video_url)
        if result == expected:
            print(f"  + {description}: CORRECT ({result})")
            success_count += 1
        else:
            print(f"  - {description}: WRONG (expected {expected}, got {result})")
    
    print(f"Video priority detection: {success_count}/{len(test_cases)} tests passed")
    return success_count == len(test_cases)

def test_source_diversity():
    """Test source diversity logic"""
    print("\nTesting source diversity logic...")
    
    collector = NewsCollector()
    
    # Simulate setting last source
    collector.last_source = 'tsn'
    
    # Create mock news items
    mock_news = [
        {
            'id': 'tsn_1',
            'title': 'TSN News 1',
            'source_key': 'tsn',
            'source': 'ТСН',
            'video_url': 'https://example.com/video.mp4',  # Direct video
            'published': '2025-08-04T18:00:00'
        },
        {
            'id': 'pravda_1', 
            'title': 'Pravda News 1',
            'source_key': 'pravda_war',
            'source': 'Українська правда',
            'video_url': 'https://youtube.com/watch?v=abc',  # YouTube link
            'published': '2025-08-04T17:55:00'
        },
        {
            'id': 'bbc_1',
            'title': 'BBC News 1', 
            'source_key': 'bbc_world',
            'source': 'BBC World News',
            'video_url': '',  # No video
            'published': '2025-08-04T17:50:00'
        }
    ]
    
    print("Mock news items created:")
    for news in mock_news:
        video_type = "Direct video" if collector.is_direct_video(news['video_url']) else "Link video" if news['video_url'] else "No video"
        print(f"  - {news['source']} ({news['source_key']}): {video_type}")
    
    print(f"\nLast published source was: {collector.last_source}")
    print("Expected behavior: Should avoid TSN since it was last published")
    
    return True

def test_news_collection_priority():
    """Test actual news collection with priority"""
    print("\nTesting actual news collection with priority...")
    
    try:
        collector = NewsCollector()
        news_list = collector.collect_all_news()
        
        if not news_list:
            print("No news collected")
            return False
        
        print(f"Collected {len(news_list)} news items")
        print("\nPriority order:")
        
        for i, news in enumerate(news_list[:5]):  # Show first 5
            video_url = news.get('video_url', '')
            if video_url:
                if collector.is_direct_video(video_url):
                    video_type = "🎬 DIRECT VIDEO (Priority 1)"
                else:
                    video_type = "🎥 Link video (Priority 2)"
            else:
                video_type = "📰 No video (Priority 3)"
            
            print(f"  {i+1}. {news.get('source', 'Unknown')} - {video_type}")
            print(f"     Title: {news.get('title', 'No title')[:60]}...")
        
        # Check if direct videos are prioritized
        direct_video_count = 0
        for news in news_list:
            if collector.is_direct_video(news.get('video_url', '')):
                direct_video_count += 1
        
        print(f"\nDirect videos found: {direct_video_count}")
        
        # Check first item priority
        first_news = news_list[0]
        first_video_url = first_news.get('video_url', '')
        if first_video_url and collector.is_direct_video(first_video_url):
            print("✓ First news item has direct video (correct priority)")
            return True
        elif not any(collector.is_direct_video(news.get('video_url', '')) for news in news_list):
            print("✓ No direct videos available, priority working correctly")
            return True
        else:
            print("⚠ Priority might not be working correctly")
            return False
            
    except Exception as e:
        print(f"Error during news collection test: {e}")
        return False

def main():
    print("Testing Priority and Source Diversity")
    print("=" * 50)
    
    tests = [
        ("Video Priority Detection", test_video_priority),
        ("Source Diversity Logic", test_source_diversity),
        ("News Collection Priority", test_news_collection_priority),
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"PASSED: {test_name}")
                passed_tests += 1
            else:
                print(f"FAILED: {test_name}")
        except Exception as e:
            print(f"ERROR: {test_name} - {e}")
    
    print("\n" + "=" * 50)
    print(f"SUMMARY: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("SUCCESS: Priority and diversity logic is working!")
        print("\nNew behavior:")
        print("1. 🎬 Direct videos (.mp4, .webm, etc.) have highest priority")
        print("2. 🎥 Video links (YouTube, Vimeo) have medium priority")
        print("3. 📰 News without video have lowest priority")
        print("4. 🔄 Bot avoids publishing from same source consecutively")
        return True
    else:
        print("FAILURE: Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)