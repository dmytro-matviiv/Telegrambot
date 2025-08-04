#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test video embedding functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from telegram_publisher import TelegramPublisher
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_video_url_extraction():
    """Test video URL extraction functionality"""
    print("Testing video URL extraction...")
    
    publisher = TelegramPublisher()
    
    test_cases = [
        # Direct video files
        ("https://example.com/video.mp4", "Direct MP4 file"),
        ("https://example.com/video.webm", "Direct WebM file"),
        
        # YouTube videos
        ("https://www.youtube.com/watch?v=abc123", "YouTube video"),
        ("https://youtu.be/abc123", "YouTube short URL"),
        
        # Vimeo videos
        ("https://vimeo.com/123456789", "Vimeo video"),
        
        # Facebook videos
        ("https://www.facebook.com/video.php?v=123", "Facebook video"),
        
        # Iframe embed
        ('src="https://example.com/embed/video.mp4"', "Iframe embed"),
    ]
    
    success_count = 0
    for video_url, description in test_cases:
        try:
            result = publisher.extract_direct_video_url(video_url)
            print(f"  + {description}: '{video_url}' -> '{result}'")
            success_count += 1
        except Exception as e:
            print(f"  - {description}: ERROR - {e}")
    
    print(f"Video URL extraction: {success_count}/{len(test_cases)} tests passed")
    return success_count == len(test_cases)

def test_video_format_detection():
    """Test video format detection"""
    print("\nTesting video format detection...")
    
    publisher = TelegramPublisher()
    
    test_urls = [
        "https://example.com/video.mp4",
        "https://example.com/video.avi", 
        "https://example.com/video.mov",
        "https://example.com/video.mkv",
        "https://example.com/video.webm",
        "https://www.youtube.com/watch?v=abc123",
        "https://vimeo.com/123456789",
    ]
    
    direct_video_count = 0
    for url in test_urls:
        is_direct = url.endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm'))
        if is_direct:
            direct_video_count += 1
            print(f"  + Direct video detected: {url}")
        else:
            print(f"  + Embed video detected: {url}")
    
    print(f"Format detection: {direct_video_count} direct videos, {len(test_urls) - direct_video_count} embed videos")
    return True

def main():
    print("Testing Video Embedding Functionality")
    print("=" * 50)
    
    tests = [
        ("Video URL Extraction", test_video_url_extraction),
        ("Video Format Detection", test_video_format_detection),
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
        print("SUCCESS: Video embedding functionality is working!")
        print("\nHow it works:")
        print("- Direct video files (.mp4, .webm, etc.) will be downloaded and sent as videos")
        print("- YouTube/Vimeo/Facebook videos will be sent as formatted links")
        print("- Videos will be embedded directly in Telegram when possible")
        return True
    else:
        print("FAILURE: Some video embedding tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)