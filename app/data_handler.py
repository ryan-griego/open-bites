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
                # Check if the previous word might be part of the time (like "11" or "11:00")
                # If yes, move time_index one step back
                if i > 0 and (any(char.isdigit() for char in words[i-1]) or ':' in words[i-1]):
                    time_index = i - 1
                else:
                    time_index = i
                break

        # If we never found am/pm, we might have malformed data. Let's just continue.
        if time_index is None:
            continue

        days_part = " ".join(words[:time_index])
        time_part = " ".join(words[time_index:])

        # Parse days
        days_list = parse_days(days_part)

        # Split time range
        # e.g. "11 am - 12 pm" -> start_str = "11 am", end_str = "12 pm"
        start_str, end_str = [t.strip() for t in time_part.split('-')]

        start_time = parse_time_string(start_str)
        end_time = parse_time_string(end_str)

        # Assign to each day
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
