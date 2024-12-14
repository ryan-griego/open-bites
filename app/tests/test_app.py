import pytest
from app.data_handler import parse_time_string, parse_hours
from datetime import time

def test_parse_time_string():
    assert parse_time_string("1:30 pm") == time(13, 30), "1:30 pm should convert to 13:30"
    assert parse_time_string("9:00 am") == time(9, 0), "9:00 am should convert to 09:00"
    # Checks for an invalid hour in the restauraunt times
    with pytest.raises(ValueError):
        parse_time_string("25 am")

    # Times around noon and midnight to make sure they parse correctly
    assert parse_time_string("12 pm") == time(12, 0), "12 pm is noon"
    assert parse_time_string("12 am") == time(0, 0), "12 am is midnight"

    # Time without minutes specified:
    assert parse_time_string("9 pm") == time(21, 0), "9 pm with no minutes should default to :00"

def test_parse_hours():
    # A simple example from the original test
    hours_str = "Mon-Sun 11:00 am - 10 pm"
    schedule = parse_hours(hours_str)
    assert len(schedule["mon"]) == 1, "Mon should have one time range"
    start, end = schedule["mon"][0]
    # Check start and end times
    assert start == time(11,0), "Start should be 11:00"
    assert end == time(22,0), "End should be 22:00 (10 pm)"

def test_parse_hours_multiple_segments():
    # Isn't in the CSV but represents a possibility in the way the times are entered into the csv
    # Mon-Thu, Sun 11 am - 9 pm  / Fri-Sat 5 pm - 1 am
      # Means:
      #   Mon-Thu: 11:00-21:00
      #   Sun: 11:00-21:00
      #   Fri-Sat: 17:00-01:00 - includes next day
    hours_str = "Mon-Thu, Sun 11 am - 9 pm / Fri-Sat 5 pm - 1 am"
    schedule = parse_hours(hours_str)

    # Checking 2 weekdays Monday and Tuesday
    mon_range = schedule["mon"][0]
    tue_range = schedule["tue"][0]
    assert mon_range == (time(11,0), time(21,0)), "Mon should be 11am-9pm"
    assert tue_range == (time(11,0), time(21,0)), "Tue should be 11am-9pm"

    # Checking that Sunday is separately listed
    sun_range = schedule["sun"][0]
    assert sun_range == (time(11,0), time(21,0)), "Sun should be 11am-9pm"

    # Check Friday with overnight hours


    fri_ranges = schedule["fri"]
    # Check Friday's interval first:
    assert any(r[0] == time(17,0) for r in fri_ranges), "Fri should start at 5 pm"

    sat_ranges = schedule["sat"]
    # Check if Sat has an early morning interval
    assert any(r[1] == time(1,0) for r in sat_ranges), "Sat should have an interval ending at 1 am"

def test_parse_hours_single_day_overnight():
    # Test a single day with overnight hours:
    # Fri 10 pm - 1 am
    # This means it starts at 22:00 on Friday and ends at 01:00 on Saturday.
    hours_str = "Fri 10 pm - 1 am"
    schedule = parse_hours(hours_str)

    fri_ranges = schedule["fri"]
    # Expect Friday interval to end at midnight
    assert any(r[0] == time(22,0) for r in fri_ranges), "Friday should start at 10 pm"
    # Saturday should have a range including the early hour of 1 am
    sat_ranges = schedule["sat"]
    assert any(r[1] == time(1,0) for r in sat_ranges), "Saturday should have interval ending at 1 am"

def test_parse_hours_missing_day():
    # Suppose a restaurant is only open Mon, Wed, Fri and no other days listed
      # This means Tue, Thu, Sat, Sun are closed.
    hours_str = "Mon 11 am - 2 pm / Wed 11 am - 2 pm / Fri 11 am - 2 pm"
    schedule = parse_hours(hours_str)

    # Check Monday:
    assert len(schedule["mon"]) == 1, "Mon should have one interval"
    # Check a day that is not specifie - Tuesday
    # Tuesday should be empty or have no intervals
    assert len(schedule["tue"]) == 0, "Tue should be closed"

def test_parse_hours_non_sequential_days():
    # Non-sequential days: "Mon, Wed, Fri 11 am - 2 pm"
    # This tests that comma-separated non-range days are handled correctly.
    hours_str = "Mon, Wed, Fri 11 am - 2 pm"
    schedule = parse_hours(hours_str)

    # Check Monday
    assert schedule["mon"] == [(time(11,0), time(14,0))], "Mon should have 11am-2pm"
    # Check Wednesday
    assert schedule["wed"] == [(time(11,0), time(14,0))], "Wed should have 11am-2pm"
    # Check Friday
    assert schedule["fri"] == [(time(11,0), time(14,0))], "Fri should have 11am-2pm"

    # Check a day not listed:
    assert schedule["tue"] == [], "Tue should be closed and not have any hours"
