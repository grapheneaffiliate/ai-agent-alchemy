#!/usr/bin/env python3
"""Test time functionality."""

from src.plugins.time_utils import TimePlugin


def test_time_plugin():
    """Test time plugin operations."""
    print("=== Testing Time Plugin (Eastern Time - Washington DC) ===\n")

    time_plugin = TimePlugin(timezone="America/New_York")

    # Test current time
    print("1. Testing get_current_time()...")
    time_result = time_plugin.get_current_time()
    print(f"✅ Current time: {time_result['time_12h']}")
    print(f"   Date: {time_result['date']}")
    print(f"   Day: {time_result['day_of_week']}")
    print(f"   Timezone: {time_result['timezone']}\n")

    # Test current date
    print("2. Testing get_current_date()...")
    date_result = time_plugin.get_current_date()
    print(f"✅ Current date: {date_result['date']}")
    print(f"   Month: {date_result['month_name']}")
    print(f"   Day: {date_result['day_of_week']}\n")

    # Test day info
    print("3. Testing get_day_info()...")
    day_info = time_plugin.get_day_info()
    print(f"✅ Day info:")
    print(f"   Week number: {day_info['week_number']}")
    print(f"   Day of year: {day_info['day_of_year']}")
    print(f"   Quarter: Q{day_info['quarter']}")
    print(f"   Is weekend: {day_info['is_weekend']}\n")

    # Test format datetime
    print("4. Testing format_datetime()...")
    formatted = time_plugin.format_datetime("%A, %B %d, %Y at %I:%M %p")
    print(f"✅ Formatted: {formatted}\n")

    # Test timestamp
    print("5. Testing get_timestamp()...")
    timestamp = time_plugin.get_timestamp()
    print(f"✅ Unix timestamp: {timestamp}\n")

    print("✅ All time tests passed!")


if __name__ == "__main__":
    test_time_plugin()
