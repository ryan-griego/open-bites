from fastapi import FastAPI, HTTPException
from datetime import datetime
from app.data_handler import load_data

app = FastAPI()
restaurants_data = load_data()  # parse CSV once at startup

@app.get("/open_restaurants/")
def get_open_restaurants(datetime_str: str):
    # Parse the input datetime_str into a datetime object:
    # Expecting an ISO 8601 string, e.g. "2024-12-13T13:30:00"
    try:
        query_dt = datetime.fromisoformat(datetime_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format. Please use ISO 8601 (e.g. 2024-12-13T13:30:00)")

    # Determine which day of week this corresponds to
    day_of_week = query_dt.weekday()  # Monday=0, Sunday=6
    # Invert the DAYS_MAP to get day strings if needed, or we can map directly
    inv_map = {0:"mon", 1:"tue", 2:"wed", 3:"thu", 4:"fri", 5:"sat", 6:"sun"}
    query_day = inv_map[day_of_week]
    query_time = query_dt.time()

    open_restaurants = []
    for r_name, schedule in restaurants_data.items():
        # schedule[query_day] might have several ranges
        if query_day in schedule:
            time_ranges = schedule[query_day]
            for (start, end) in time_ranges:
                if start <= query_time <= end:
                    open_restaurants.append(r_name)
                    break

    if not open_restaurants:
        return {"message": "No restaurants are open at that time. Please try again."}
    return {"open_restaurants": open_restaurants}
