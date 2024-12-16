# main.py

from fastapi import FastAPI, HTTPException
from datetime import datetime
from app.data_handler import load_data
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# Serve frontend static files
app.mount("/", StaticFiles(directory="frontend", html=True), name="static")
