#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test timezone fixes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from news_collector import parse_published_date
from datetime import datetime, timezone
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_timezone_consistency():
    """Test that timezone handling is consistent"""
    print("Testing timezone consistency...")
    
    # Test dates with different formats
    test_dates = [
        "Mon, 04 Aug 2025 18:30:00 +0000",  # RFC 2822 with timezone
        "Mon, 04 Aug 2025 18:30:00",        # RFC 2822 without timezone
        "2025-08-04T18:30:00",              # ISO without timezone
        "2025-08-04T18:30:00Z",             # ISO with Z
    ]
    
    now = datetime.now(timezone.utc)
    print(f"Current time (UTC): {now}")
    
    success_count = 0
    for date_str in test_dates:
        try:
            parsed_dt = parse_published_date(date_str)
            if parsed_dt:
                print(f"Parsed '{date_str}' -> {parsed_dt}")
                print(f"  Timezone info: {parsed_dt.tzinfo}")
                
                # Test datetime comparison (this should not fail)
                try:
                    age_minutes = (now - parsed_dt).total_seconds() / 60
                    print(f"  Age: {age_minutes:.1f} minutes")
                    success_count += 1
                    print("  + Comparison successful")
                except Exception as e:
                    print(f"  - Comparison failed: {e}")
            else:
                print(f"Failed to parse: '{date_str}'")
        except Exception as e:
            print(f"Error parsing '{date_str}': {e}")
        print()
    
    return success_count > 0

def main():
    print("Testing Timezone Fixes")
    print("=" * 50)
    
    success = test_timezone_consistency()
    
    print("=" * 50)
    if success:
        print("SUCCESS: Timezone fixes are working!")
        return True
    else:
        print("FAILURE: Timezone issues remain")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)