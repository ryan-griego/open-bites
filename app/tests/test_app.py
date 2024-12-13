import pytest
from app.data_handler import parse_time_string, parse_hours
from datetime import datetime, time


# def test_parse_time_string():
#     assert parse_time_string("11 am") == time(11, 0)

#     assert parse_time_string("12 pm").hour == 12
#     assert parse_time_string("12 am").hour == 0


def test_parse_time_string():
    assert parse_time_string("1:30 pm") == time(13, 30)
    assert parse_time_string("9:00 am") == time(9, 0)
    with pytest.raises(ValueError):
        parse_time_string("25 am")


def test_parse_hours():
    hours_str = "Mon-Sun 11:00 am - 10 pm"
    schedule = parse_hours(hours_str)
    # Check if mon in schedule and time range correct
    assert len(schedule["mon"]) == 1
    start, end = schedule["mon"][0]
    # assert start == datetime.time(11,0)
    # assert end == datetime.time(22,0)
    # Similarly check other days...
