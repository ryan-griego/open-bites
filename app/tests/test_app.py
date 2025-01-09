# test_app.py

import pytest
from app.data_handler import parse_time_string, parse_hours, load_data
from datetime import time

def test_parse_time_string():
    # Valid time strings
    assert parse_time_string("1:30 pm") == time(13, 30), "1:30 pm should convert to 13:30"
    assert parse_time_string("9:00 am") == time(9, 0), "9:00 am should convert to 09:00"
    assert parse_time_string("12 pm") == time(12, 0), "12 pm is noon"
    assert parse_time_string("12 am") == time(0, 0), "12 am is midnight"
    assert parse_time_string("9 pm") == time(21, 0), "9 pm with no minutes should default to :00"

    # Invalid time strings
    with pytest.raises(ValueError):
        parse_time_string("25 am")
    with pytest.raises(ValueError):
        parse_time_string("13:60 pm")
    with pytest.raises(ValueError):
        parse_time_string("invalid time")

def test_parse_hours_single_day():
    # Single day, no range
    hours_str = "Mon 11 am - 10 pm"
    schedule = parse_hours(hours_str)
    assert len(schedule["mon"]) == 1, "Mon should have one time range"
    start, end = schedule["mon"][0]
    assert start == time(11, 0), "Start should be 11:00"
    assert end == time(22, 0), "End should be 22:00 (10 pm)"

    # Days not listed should have no hours
    assert len(schedule["tue"]) == 0, "Tue should have no hours"

def test_parse_hours_day_aliases():
    # Using different day name abbreviations
    hours_str = "Tues-Fri, Sunday 11 am - 10 pm / Sat 5 pm - 11 pm"
    schedule = parse_hours(hours_str)

    # Check Tuesday
    assert len(schedule["tue"]) == 1, "Tue should have one time range"
    assert schedule["tue"][0] == (time(11, 0), time(22, 0)), "Tue time range incorrect"

    # Check Friday
    assert len(schedule["fri"]) == 1, "Fri should have one time range"
    assert schedule["fri"][0] == (time(11, 0), time(22, 0)), "Fri time range incorrect"

    # Check Sunday
    assert len(schedule["sun"]) == 1, "Sun should have one time range"
    assert schedule["sun"][0] == (time(11, 0), time(22, 0)), "Sun time range incorrect"

    # Check Saturday
    assert len(schedule["sat"]) == 1, "Sat should have one time range"
    assert schedule["sat"][0] == (time(17, 0), time(23, 0)), "Sat time range incorrect"

def test_parse_hours_overlapping_ranges():
    # Overlapping and overnight ranges
    hours_str = "Fri 10 pm - 1 am"
    schedule = parse_hours(hours_str)

    # Friday should have 10 pm - 23:59
    assert len(schedule["fri"]) == 1, "Fri should have one time range"
    assert schedule["fri"][0] == (time(22, 0), time(23, 59)), "Fri time range incorrect"

    # Saturday should have 00:00 - 01:00
    assert len(schedule["sat"]) == 1, "Sat should have one time range"
    assert schedule["sat"][0] == (time(0, 0), time(1, 0)), "Sat time range incorrect"

def test_parse_hours_missing_time():
    # Missing time part
    hours_str = "Mon-Fri"
    schedule = parse_hours(hours_str)
    for day in ["mon", "tue", "wed", "thu", "fri"]:
        assert len(schedule[day]) == 0, f"{day} should have no time ranges"

def test_load_data():
    # Assuming 'data/restaurants.csv' exists and is correctly formatted
    restaurants = load_data("data/restaurants.csv")
    assert isinstance(restaurants, dict), "Restaurants should be a dictionary"
    for name, schedule in restaurants.items():
        assert isinstance(schedule, dict), f"Schedule for '{name}' should be a dictionary"
        for day, times in schedule.items():
            assert isinstance(times, list), f"Times for '{day}' in '{name}' should be a list"
            for start, end in times:
                assert isinstance(start, time), "Start time should be a datetime.time object"
                assert isinstance(end, time), "End time should be a datetime.time object"


# Tests to make sure load_data can load data from the SQLite database

def test_load_data_sqlite():
    # Assuming 'app/restaurants.db' exists and contains valid data
    restaurants = load_data("app/restaurants.db")
    assert isinstance(restaurants, dict), "Restaurants should be a dictionary"
    assert len(restaurants) > 0, "Restaurants dictionary should not be empty"

    for name, schedule in restaurants.items():
        assert isinstance(name, str), f"Restaurant name '{name}' should be a string"
        assert isinstance(schedule, dict), f"Schedule for '{name}' should be a dictionary"

        for day, times in schedule.items():
            assert isinstance(day, str), f"Day '{day}' in '{name}' should be a string"
            assert isinstance(times, list), f"Times for '{day}' in '{name}' should be a list"
            for start, end in times:
                assert isinstance(start, time), "Start time should be a datetime.time object"
                assert isinstance(end, time), "End time should be a datetime.time object"

def test_parse_hours_non_sequential_days():
    # Non-sequential days: "Mon, Wed, Fri 11 am - 2 pm"
    hours_str = "Mon, Wed, Fri 11 am - 2 pm"
    schedule = parse_hours(hours_str)

    # Check Monday
    assert schedule["mon"] == [(time(11, 0), time(14, 0))], "Mon should have 11am-2pm"
    # Check Wednesday
    assert schedule["wed"] == [(time(11, 0), time(14, 0))], "Wed should have 11am-2pm"
    # Check Friday
    assert schedule["fri"] == [(time(11, 0), time(14, 0))], "Fri should have 11am-2pm"

    # Check a day not listed
    assert schedule["tue"] == [], "Tue should be closed and have no hours"

def test_parse_hours_multiple_aliases():
    # Using multiple aliases for days
    hours_str = "Tues-Thurs, Sunday 10 am - 8 pm / Sat 5 pm - 11 pm"
    schedule = parse_hours(hours_str)

    # Check Tuesday
    assert len(schedule["tue"]) == 1, "Tue should have one time range"
    assert schedule["tue"][0] == (time(10, 0), time(20, 0)), "Tue time range incorrect"

    # Check Thursday
    assert len(schedule["thu"]) == 1, "Thu should have one time range"
    assert schedule["thu"][0] == (time(10, 0), time(20, 0)), "Thu time range incorrect"

    # Check Sunday
    assert len(schedule["sun"]) == 1, "Sun should have one time range"
    assert schedule["sun"][0] == (time(10, 0), time(20, 0)), "Sun time range incorrect"

    # Check Saturday
    assert len(schedule["sat"]) == 1, "Sat should have one time range"
    assert schedule["sat"][0] == (time(17, 0), time(23, 0)), "Sat time range incorrect"
