# # data_handler.py

# import csv
# from datetime import datetime, time
# import re
# import logging

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# DAYS_MAP = {
#     "mon": 0,
#     "tue": 1,
#     "wed": 2,
#     "thu": 3,
#     "fri": 4,
#     "sat": 5,
#     "sun": 6
# }

# # Mapping of possible day name variations to standardized abbreviations
# day_aliases = {
#     'mon': 'mon',
#     'monday': 'mon',
#     'tue': 'tue',
#     'tues': 'tue',
#     'tuesday': 'tue',
#     'wed': 'wed',
#     'weds': 'wed',
#     'wednesday': 'wed',
#     'thu': 'thu',
#     'thurs': 'thu',
#     'thursday': 'thu',
#     'fri': 'fri',
#     'friday': 'fri',
#     'sat': 'sat',
#     'saturday': 'sat',
#     'sun': 'sun',
#     'sunday': 'sun',
# }

# def parse_time_string(time_str):
#     """
#     Parses a time string like '1:30 pm' into a datetime.time object.
#     """
#     time_str = time_str.strip().lower()
#     match = re.match(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)', time_str)
#     if not match:
#         logger.error(f"Invalid time format: '{time_str}'")
#         raise ValueError(f"Invalid time format: '{time_str}'")

#     hour = int(match.group(1))
#     minute = int(match.group(2)) if match.group(2) else 0
#     period = match.group(3)

#     if hour < 1 or hour > 12:
#         logger.error(f"Hour must be between 1 and 12 in time string: '{time_str}'")
#         raise ValueError(f"Hour must be between 1 and 12 in time string: '{time_str}'")

#     if period == 'pm' and hour != 12:
#         hour += 12
#     elif period == 'am' and hour == 12:
#         hour = 0

#     return time(hour, minute)

# def parse_days(days_str):
#     """
#     Parses a string of days into a list of standardized three-letter abbreviations.
#     Handles individual days and ranges, accounting for different abbreviations.
#     """
#     final_days = []

#     # Split by commas first
#     parts = [d.strip() for d in days_str.split(',')]
#     for part in parts:
#         if '-' in part:
#             # Address the range like "Mon-Fri"
#             start_day_raw, end_day_raw = [p.strip().lower() for p in part.split('-')]
#             # Normalize day names
#             start_day = day_aliases.get(start_day_raw)
#             end_day = day_aliases.get(end_day_raw)
#             if not start_day or not end_day:
#                 logger.error(f"Invalid day name in range: '{part}'")
#                 raise ValueError(f"Invalid day name in range: '{part}'")
#             # Expand the day range
#             expanded_days = expand_day_range(start_day, end_day)
#             final_days.extend(expanded_days)
#         else:
#             # Single day
#             day_raw = part.lower()
#             day = day_aliases.get(day_raw)
#             if not day:
#                 logger.error(f"Invalid day name: '{part}'")
#                 raise ValueError(f"Invalid day name: '{part}'")
#             final_days.append(day)

#     return final_days

# def expand_day_range(start, end):
#     """
#     Expands a range of days into a list of standardized day abbreviations.
#     """
#     inv_map = {v: k for k, v in DAYS_MAP.items()}
#     start_idx = DAYS_MAP.get(start[:3])
#     end_idx = DAYS_MAP.get(end[:3])

#     if start_idx is None or end_idx is None:
#         logger.error(f"Invalid day names in range: '{start}-{end}'")
#         raise ValueError(f"Invalid day names in range: '{start}-{end}'")

#     if start_idx <= end_idx:
#         days = [inv_map[i] for i in range(start_idx, end_idx + 1)]
#     else:
#         # Wrap around the week
#         days = [inv_map[i] for i in range(start_idx, 7)] + [inv_map[i] for i in range(0, end_idx + 1)]
#     return days

# def parse_hours(hours_str):
#     """
#     Parses a restaurant's operating hours string into a schedule dictionary.
#     """
#     segments = [seg.strip() for seg in hours_str.split('/') if seg.strip()]
#     schedule = {d: [] for d in DAYS_MAP.keys()}  # mon,tue,wed...

#     for segment in segments:
#         words = segment.split()
#         time_index = None

#         # Find where time starts
#         for i, part in enumerate(words):
#             p = part.lower()
#             if "am" in p or "pm" in p:
#                 # Check if the time includes the previous word
#                 if i > 0 and (any(char.isdigit() for char in words[i-1]) or ':' in words[i-1]):
#                     time_index = i - 1
#                 else:
#                     time_index = i
#                 break

#         if time_index is None:
#             logger.warning(f"No time found in segment: '{segment}'")
#             continue

#         days_part = " ".join(words[:time_index])
#         time_part = " ".join(words[time_index:])

#         try:
#             days_list = parse_days(days_part)
#         except ValueError as ve:
#             logger.error(f"Error parsing days in segment '{segment}': {ve}")
#             continue

#         try:
#             start_str, end_str = [t.strip() for t in time_part.split('-')]
#         except ValueError:
#             logger.error(f"Invalid time range in segment: '{segment}'")
#             continue

#         try:
#             start_time = parse_time_string(start_str)
#             end_time = parse_time_string(end_str)
#         except ValueError as ve:
#             logger.error(f"Error parsing time in segment '{segment}': {ve}")
#             continue

#         # Check if end_time is actually on the next day (end_time < start_time)
#         if end_time < start_time:
#             # The hours roll over past midnight.
#             # Interval 1: from start_time until end of day
#             # Interval 2: from midnight to end_time on the NEXT day
#             midnight = time(0, 0)
#             end_of_day = time(23, 59)

#             for d in days_list:
#                 # Interval from start_time to end_of_day for the same day
#                 schedule[d].append((start_time, end_of_day))

#                 # Now find the next day (wrap around if needed)
#                 current_day_idx = DAYS_MAP[d]
#                 next_day_idx = (current_day_idx + 1) % 7
#                 inv_map = {v: k for k, v in DAYS_MAP.items()}
#                 next_day = inv_map[next_day_idx]

#                 # Interval from midnight to end_time for the next day
#                 schedule[next_day].append((midnight, end_time))
#         else:
#             # Normal case: within the same day
#             for d in days_list:
#                 schedule[d].append((start_time, end_time))

#     return schedule

# def load_data(csv_path="data/restaurants.csv"):
#     """
#     Loads restaurant data from a CSV file.
#     """
#     restaurants = {}
#     try:
#         with open(csv_path, 'r', newline='', encoding='utf-8') as f:
#             reader = csv.DictReader(f)
#             for row in reader:
#                 name = row["Restaurant Name"].strip('"').strip()
#                 hours = row["Hours"].strip()
#                 # Parse the hours
#                 try:
#                     schedule = parse_hours(hours)
#                     restaurants[name] = schedule
#                 except ValueError as ve:
#                     logger.error(f"Error parsing hours for restaurant '{name}': {ve}")
#     except FileNotFoundError:
#         logger.error(f"CSV file not found at path: '{csv_path}'")
#     except Exception as e:
#         logger.error(f"Unexpected error loading data: {e}")
#     return restaurants


# data_handler.py

import sqlite3
from datetime import datetime, time
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DAYS_MAP = {
    "mon": 0,
    "tue": 1,
    "wed": 2,
    "thu": 3,
    "fri": 4,
    "sat": 5,
    "sun": 6
}

# Mapping of possible day name variations to standardized abbreviations
day_aliases = {
    'mon': 'mon',
    'monday': 'mon',
    'tue': 'tue',
    'tues': 'tue',
    'tuesday': 'tue',
    'wed': 'wed',
    'weds': 'wed',
    'wednesday': 'wed',
    'thu': 'thu',
    'thurs': 'thu',
    'thursday': 'thu',
    'fri': 'fri',
    'friday': 'fri',
    'sat': 'sat',
    'saturday': 'sat',
    'sun': 'sun',
    'sunday': 'sun',
}

def parse_time_string(time_str):
    """
    Parses a time string like '1:30 pm' into a datetime.time object.
    """
    time_str = time_str.strip().lower()
    match = re.match(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)', time_str)
    if not match:
        logger.error(f"Invalid time format: '{time_str}'")
        raise ValueError(f"Invalid time format: '{time_str}'")

    hour = int(match.group(1))
    minute = int(match.group(2)) if match.group(2) else 0
    period = match.group(3)

    if hour < 1 or hour > 12:
        logger.error(f"Hour must be between 1 and 12 in time string: '{time_str}'")
        raise ValueError(f"Hour must be between 1 and 12 in time string: '{time_str}'")

    if period == 'pm' and hour != 12:
        hour += 12
    elif period == 'am' and hour == 12:
        hour = 0

    return time(hour, minute)

def parse_days(days_str):
    """
    Parses a string of days into a list of standardized three-letter abbreviations.
    Handles individual days and ranges, accounting for different abbreviations.
    """
    final_days = []

    # Split by commas first
    parts = [d.strip() for d in days_str.split(',')]
    for part in parts:
        if '-' in part:
            # Address the range like "Mon-Fri"
            start_day_raw, end_day_raw = [p.strip().lower() for p in part.split('-')]
            # Normalize day names
            start_day = day_aliases.get(start_day_raw)
            end_day = day_aliases.get(end_day_raw)
            if not start_day or not end_day:
                logger.error(f"Invalid day name in range: '{part}'")
                raise ValueError(f"Invalid day name in range: '{part}'")
            # Expand the day range
            expanded_days = expand_day_range(start_day, end_day)
            final_days.extend(expanded_days)
        else:
            # Single day
            day_raw = part.lower()
            day = day_aliases.get(day_raw)
            if not day:
                logger.error(f"Invalid day name: '{part}'")
                raise ValueError(f"Invalid day name: '{part}'")
            final_days.append(day)

    return final_days

def expand_day_range(start, end):
    """
    Expands a range of days into a list of standardized day abbreviations.
    """
    inv_map = {v: k for k, v in DAYS_MAP.items()}
    start_idx = DAYS_MAP.get(start[:3])
    end_idx = DAYS_MAP.get(end[:3])

    if start_idx is None or end_idx is None:
        logger.error(f"Invalid day names in range: '{start}-{end}'")
        raise ValueError(f"Invalid day names in range: '{start}-{end}'")

    if start_idx <= end_idx:
        days = [inv_map[i] for i in range(start_idx, end_idx + 1)]
    else:
        # Wrap around the week
        days = [inv_map[i] for i in range(start_idx, 7)] + [inv_map[i] for i in range(0, end_idx + 1)]
    return days

def parse_hours(hours_str):
    """
    Parses a restaurant's operating hours string into a schedule dictionary.
    """
    segments = [seg.strip() for seg in hours_str.split('/') if seg.strip()]
    schedule = {d: [] for d in DAYS_MAP.keys()}  # mon,tue,wed...

    for segment in segments:
        words = segment.split()
        time_index = None

        # Find where time starts
        for i, part in enumerate(words):
            p = part.lower()
            if "am" in p or "pm" in p:
                # Check if the time includes the previous word
                if i > 0 and (any(char.isdigit() for char in words[i-1]) or ':' in words[i-1]):
                    time_index = i - 1
                else:
                    time_index = i
                break

        if time_index is None:
            logger.warning(f"No time found in segment: '{segment}'")
            continue

        days_part = " ".join(words[:time_index])
        time_part = " ".join(words[time_index:])

        try:
            days_list = parse_days(days_part)
        except ValueError as ve:
            logger.error(f"Error parsing days in segment '{segment}': {ve}")
            continue

        try:
            start_str, end_str = [t.strip() for t in time_part.split('-')]
        except ValueError:
            logger.error(f"Invalid time range in segment: '{segment}'")
            continue

        try:
            start_time = parse_time_string(start_str)
            end_time = parse_time_string(end_str)
        except ValueError as ve:
            logger.error(f"Error parsing time in segment '{segment}': {ve}")
            continue

        # Check if end_time is actually on the next day (end_time < start_time)
        if end_time < start_time:
            # The hours roll over past midnight.
            # Interval 1: from start_time until end of day
            # Interval 2: from midnight to end_time on the NEXT day
            midnight = time(0, 0)
            end_of_day = time(23, 59)

            for d in days_list:
                # Interval from start_time to end_of_day for the same day
                schedule[d].append((start_time, end_of_day))

                # Now find the next day (wrap around if needed)
                current_day_idx = DAYS_MAP[d]
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

def load_data(db_path="app/restaurants.db"):
    """
    Loads restaurant data from the SQLite database.
    """
    restaurants = {}
    try:
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Fetch all restaurant data
        cursor.execute("SELECT name, hours FROM restaurants")
        rows = cursor.fetchall()

        for name, hours_str in rows:
            try:
                schedule = parse_hours(hours_str)
                restaurants[name] = schedule
            except ValueError as ve:
                logger.error(f"Error parsing hours for restaurant '{name}': {ve}")

        conn.close()
    except sqlite3.Error as e:
        logger.error(f"Error loading data from SQLite: {e}")
    return restaurants

if __name__ == "__main__":
    data = load_data()
    logger.info(f"Loaded {len(data)} restaurants from SQLite.")
    # Continue with your backend logic...
