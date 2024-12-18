# Open Bites

**Live Demo:** [https://open-bites.ryangriego.com](https://open-bites.ryangriego.com)

**Discover which restaurants are open at a given date and time.**
This application provides a FastAPI-based backend that parses a CSV of restaurant hours and a frontend interface with a date/time picker for easy queries. The project demonstrates parsing complex schedules, integrating a frontend served by FastAPI, containerization with Docker, and a responsive UI.

![Screenshot of Open Bites](https://res.cloudinary.com/dm7y3yvjp/image/upload/v1734325621/Screenshot_2024-12-15_at_9.06.40_PM_mqfua6.png)

This application provides a FastAPI-based backend that utilizes SQLite for data storage, parses a CSV of restaurant hours, and offers a frontend interface with a date/time picker for easy queries. The project demonstrates parsing complex schedules, integrating a frontend served by FastAPI, containerization with Docker, and a responsive UI.

---

## Features

- **User-Friendly UI:** Select a date and time using a modern date/time picker.
- **SQLite Integration:** Efficiently store and query restaurant data using SQLite.
- **On-the-Fly Filtering:** The endpoint returns only those restaurants open at the requested time.
- **Scalable & Extensible:** Easily add new restaurants to the CSV, change parsing logic, or integrate further features.
- **Easy Testing:** Includes a test suite with `pytest` to ensure parsing and endpoint logic remains robust.

---

## Getting Started

### Prerequisites

- **Python 3.10+** recommended
- **pip** for installing dependencies
- **SQLite** (installed by default with Python's standard library)
- **Docker** (optional) if you want to run in a containerized environment

### Cloning the Repository

```bash
git clone https://github.com/ryan-griego/open-bites.git
cd open-bites
```

### Installing Dependencies and Running Locally

Create and Activate a Virtual Environment (Recommended)
It’s best to use a virtual environment to avoid conflicts with other Python projects.

```bash
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

Install Python Dependencies
Use pip to install all required Python packages listed in requirements.txt:

```bash
pip install -r requirements.txt
```

This will install FastAPI, Uvicorn, and other necessary libraries.

### Run the Application

Start the FastAPI application using Uvicorn:

```bash
uvicorn app.main:app --reload
```

By default, the application runs at http://127.0.0.1:8000.

### Access the Frontend
Open http://127.0.0.1:8000/ in your browser. You’ll see the landing page with a date/time picker. Select a date and time and the application will display which restaurants are open at that moment.


## <a name="tests">Snippets</a>


<details>
<summary><code>app/main.py</code></summary>

```python
from fastapi import FastAPI, HTTPException
from datetime import datetime
from app.data_handler import load_data
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load restaurant data once at startup
restaurants_data = load_data()

@app.get("/open_restaurants/")
def get_open_restaurants(datetime_str: str):
    """
    Endpoint to get a list of open restaurants at a given datetime.
    Expects datetime_str in ISO 8601 format, e.g., "2024-12-13T13:30:00"
    """
    # Parse the input datetime_str into a datetime object
    try:
        query_dt = datetime.fromisoformat(datetime_str)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid datetime format. Please use ISO 8601 (e.g. 2024-12-13T13:30:00)"
        )

    # Determine which day of week this corresponds to
    day_of_week = query_dt.weekday()  # Monday=0, Sunday=6
    inv_map = {0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"}
    query_day = inv_map[day_of_week]
    query_time = query_dt.time()

    open_restaurants = []
    for r_name, schedule in restaurants_data.items():
        if query_day in schedule:
            time_ranges = schedule[query_day]
            for (start, end) in time_ranges:
                if start <= end:
                    if start <= query_time <= end:
                        open_restaurants.append(r_name)
                        break  # No need to check further ranges for this restaurant
                else:
                    # Overnight hours (e.g., 10 pm - 1 am)
                    if query_time >= start or query_time <= end:
                        open_restaurants.append(r_name)
                        break  # No need to check further ranges for this restaurant

    if not open_restaurants:
        return {"message": "No restaurants are open at that time. Please try again."}
    return {"open_restaurants": open_restaurants}

# Serve the frontend static files
app.mount("/", StaticFiles(directory="frontend", html=True), name="static")

```
</details>

<details>
<summary><code>app/data_handler.py</code></summary>

```python
import csv
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

def load_data(csv_path="data/restaurants.csv"):
    """
    Loads restaurant data from a CSV file.
    """
    restaurants = {}
    try:
        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row["Restaurant Name"].strip('"').strip()
                hours = row["Hours"].strip()
                # Parse the hours
                try:
                    schedule = parse_hours(hours)
                    restaurants[name] = schedule
                except ValueError as ve:
                    logger.error(f"Error parsing hours for restaurant '{name}': {ve}")
    except FileNotFoundError:
        logger.error(f"CSV file not found at path: '{csv_path}'")
    except Exception as e:
        logger.error(f"Unexpected error loading data: {e}")
    return restaurants
```

</details>


<details>
<summary><code>app/tests/test_app.py</code></summary>

```python
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

```

</details>

<details>
<summary><code>data/restaurants.csv</code></summary>

## Restaurant Hours Dataset

Below is the dataset used for this project, showing the operating hours of restaurants:

| Restaurant Name                  | Hours                                        |
|----------------------------------|---------------------------------------------|
| The Cowfish Sushi Burger Bar     | Mon-Sun 11:00 am - 10 pm                    |
| Morgan St Food Hall              | Mon-Sun 11 am - 9:30 pm                     |
| Beasley's Chicken + Honey        | Mon-Fri, Sat 11 am - 12 pm / Sun 11 am - 10 pm |
| Garland                          | Tues-Fri, Sun 11:30 am - 10 pm / Sat 5:30 pm - 11 pm |
| Crawford and Son                 | Mon-Sun 11:30 am - 10 pm                    |
| Death and Taxes                  | Mon-Sun 5 pm - 10 pm                        |
| Caffe Luna                       | Mon-Sun 11 am - 12 am                       |
| Bida Manda                       | Mon-Thu, Sun 11:30 am - 10 pm / Fri-Sat 11:30 am - 11 pm |
| The Cheesecake Factory           | Mon-Thu 11 am - 11 pm / Fri-Sat 11 am - 12:30 am / Sun 10 am - 11 pm |
| Tupelo Honey                     | Mon-Thu, Sun 9 am - 10 pm / Fri-Sat 9 am - 11 pm |
| Player's Retreat                 | Mon-Thu, Sun 11:30 am - 9:30 pm / Fri-Sat 11:30 am - 10 pm |
| Glenwood Grill                   | Mon-Sat 11 am - 11 pm / Sun 11 am - 10 pm   |
| Neomonde                         | Mon-Thu 11:30 am - 10 pm / Fri-Sun 11:30 am - 11 pm |
| Page Road Grill                  | Mon-Sun 11 am - 11 pm                       |
| Mez Mexican                      | Mon-Fri 10:30 am - 9:30 pm / Sat-Sun 10 am - 9:30 pm |
| Saltbox                          | Mon-Sun 11:30 am - 10:30 pm                 |
| El Rodeo                         | Mon-Sun 11 am - 10:30 pm                    |
| Provence                         | Mon-Thu, Sun 11:30 am - 9 pm / Fri-Sat 11:30 am - 10 pm |
| Bonchon                          | Mon-Wed 5 pm - 12:30 am / Thu-Fri 5 pm - 1:30 am / Sat 3 pm - 1:30 am / Sun 3 pm - 11:30 pm |
| Tazza Kitchen                    | Mon-Sun 11 am - 10 pm                       |
| Mandolin                         | Mon-Thu 11 am - 10 pm / Fri-Sat 10 am - 10:30 pm / Sun 11 am - 11 pm |
| Mami Nora's                      | Mon-Sat 11 am - 10 pm / Sun 12 pm - 10 pm   |
| Gravy                            | Mon-Sun 11 am - 10 pm                       |
| Taverna Agora                    | Mon-Thu, Sun 11 am - 10 pm / Fri-Sat 11 am - 12 am |
| Char Grill                       | Mon-Fri 11:30 am - 10 pm / Sat-Sun 7 am - 3 pm |
| Seoul 116                        | Mon-Sun 11 am - 4 am                        |
| Whiskey Kitchen                  | Mon-Thu, Sun 11:30 am - 10 pm / Fri-Sat 11:30 am - 11 pm |
| Sitti                            | Mon-Sun 11:30 am - 9:30 pm                  |
| Stanbury                         | Mon-Sun 11 am - 12 am                       |
| Yard House                       | Mon-Sun 11:30 am - 10 pm                    |
| David's Dumpling                 | Mon-Sat 11:30 am - 10 pm / Sun 5:30 pm - 10 pm |
| Gringo a Gogo                    | Mon-Sun 11 am - 11 pm                       |
| Centro                           | Mon, Wed-Sun 11 am - 10 pm                  |
| Brewery Bhavana                  | Mon-Sun 11 am - 10:30 pm                    |
| Dashi                            | Mon-Fri 10 am - 9:30 pm / Sat-Sun 9:30 am - 9:30 pm |
| 42nd Street Oyster Bar           | Mon-Sat 11 am - 12 am / Sun 12 pm - 2 am    |
| Top of the Hill                  | Mon-Fri 11 am - 9 pm / Sat 5 pm - 9 pm      |
| Jose and Sons                    | Mon-Fri 11:30 am - 10 pm / Sat 5:30 pm - 10 pm |
| Oakleaf                          | Mon-Thu, Sun 11 am - 10 pm / Fri-Sat 11 am - 11 pm |
| Second Empire                    | Mon-Fri 11 am - 10 pm / Sat-Sun 5 pm - 10 pm |

</details>

### FAQ

**Q: How can I add a new restaurant to the dataset?**
A: To add a new restaurant, update the `data/restaurants.csv` file with the restaurant's name and operating hours following the existing format.

**Q: What format should the datetime string be in for the API?**
A: The `datetime_str` parameter should be in ISO 8601 format, e.g., `2024-12-16T19:30:00`.

**Q: How do I run the tests?**
A: After setting up the virtual environment and installing dependencies, run:
```bash
pytest
