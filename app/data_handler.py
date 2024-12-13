# data_handler.py


import csv
from datetime import datetime, time

DAYS_MAP = {
    "mon": 0,
    "tue": 1,
    "wed": 2,
    "thu": 3,
    "fri": 4,
    "sat": 5,
    "sun": 6
}

def parse_time_string(time_str):
    # Remove extra spaces and convert to lower case
    time_str = time_str.strip().lower()

    print(time_str)
    # Split by space:
    parts = time_str.split()
    print(parts)
    extract_time = parts[0]
    extract_am_pm = parts[1] if len(parts) > 1 else None

    # Check if the time includes minutes, if not assume the minutes are 0
    if ":" in extract_time:
        hour_str, minute_str = extract_time.split(":")
    else:
        hour_str = extract_time
        minute_str = "00"

    hour = int(hour_str)
    minute = int(minute_str)

    if extract_am_pm == "pm" and hour != 12:
        hour += 12
    elif extract_am_pm == "am" and hour == 12:
        hour = 0

    return time(hour, minute)

def parse_days(days_str):
    # days_str could be "Mon-Fri, Sat" -> split by ',' first -> ["Mon-Fri", " Sat"]
    # Then strip spaces and handle each range
    final_days = []

    # if there's a comma, split the string so the days are separated
    parts = [d.strip() for d in days_str.split(',')]
    for part in parts:
        if '-' in part:
            # range like "Mon-Fri"
            start_day, end_day = [p.strip().lower() for p in part.split('-')]
            # Map them to numeric or just keep them in a list
            # We'll do a helper to expand day ranges:
            final_days.extend(expand_day_range(start_day, end_day))
        else:
            # single day
            final_days.append(part.lower())
    return final_days

def expand_day_range(start, end):
    # Using DAYS_MAP, we can find the numeric day, then add until we reach end.
    inv_map = {v:k for k,v in DAYS_MAP.items()}
    start_idx = DAYS_MAP[start[:3]]  # just take first three letters for mapping
    end_idx = DAYS_MAP[end[:3]]

    # If start to end wraps, handle that. Usually it won't if well-formed.
    # For simplicity assume start <= end
    return [inv_map[i] for i in range(start_idx, end_idx+1)]


def parse_hours(hours_str):
    segments = [seg.strip() for seg in hours_str.split('/')]
    schedule = {d: [] for d in DAYS_MAP.keys()}  # mon,tue,wed...

    for segment in segments:
        words = segment.split()
        time_index = None

        # Find where time starts
        for i, part in enumerate(words):
            p = part.lower()
            if "am" in p or "pm" in p:
                # Check if the previous word is part of the time
                if i > 0 and (any(char.isdigit() for char in words[i-1]) or ':' in words[i-1]):
                    time_index = i - 1
                else:
                    time_index = i
                break

        if time_index is None:
            continue

        days_part = " ".join(words[:time_index])
        time_part = " ".join(words[time_index:])

        days_list = parse_days(days_part)
        start_str, end_str = [t.strip() for t in time_part.split('-')]

        start_time = parse_time_string(start_str)
        end_time = parse_time_string(end_str)

        # Check if end_time is actually on the next day (end_time < start_time)
        if end_time < start_time:
            # The hours roll over past midnight.
            # Interval 1: from start_time until end of day
            # Interval 2: from midnight to end_time on the NEXT day
            #
            # Example:
            # Fri 23:00 - 01:00 (Sat)
            # Fri: (23:00 - 23:59:59)
            # Sat: (00:00 - 01:00)
            #
            # For simplicity, we assume "end of day" as 23:59.
            # Alternatively, you can store times as (start, end, next_day_flag) or just to midnight directly.

            # Define a helper time: midnight and end of day
            midnight = time(0, 0)
            end_of_day = time(23, 59)

            for d in days_list:
                # Interval from start_time to end_of_day for the same day
                schedule[d].append((start_time, end_of_day))

                # Now find the next day (wrap around if needed)
                current_day_idx = DAYS_MAP[d[:3]]
                next_day_idx = (current_day_idx + 1) % 7
                inv_map = {v: k for k, v in DAYS_MAP.items()}
                next_day = inv_map[next_day_idx]

                # Interval from midnight to end_time for the next day
                schedule[next_day].append((midnight, end_time))

        else:
            # Normal case: within the same day
            for d in days_list:
                schedule[d].append((start_time, end_time))

    return schedule



def load_data(csv_path="data/restaurants.csv"):
    restaurants = {}
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["Restaurant Name"].strip('"')
            hours = row["Hours"]
            # parse the hours
            schedule = parse_hours(hours)
            restaurants[name] = schedule
    return restaurants
