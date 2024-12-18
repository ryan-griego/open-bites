import sqlite3
import csv
import os

# Define paths
db_path = "app/restaurants.db"
csv_path = "data/restaurants.csv"

# Check if CSV exists
if not os.path.exists(csv_path):
    print(f"CSV file not found at path: '{csv_path}'")
    exit(1)

# Connect to SQLite database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Read CSV and insert data
with open(csv_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        name = row.get("Restaurant Name", "").strip().strip('"')
        hours = row.get("Hours", "").strip()

        if name and hours:
            try:
                cursor.execute("""
                    INSERT INTO restaurants (name, hours)
                    VALUES (?, ?)
                """, (name, hours))
            except sqlite3.IntegrityError:
                print(f"Duplicate entry skipped for restaurant: {name}")
        else:
            print(f"Skipping incomplete row: {row}")

# Commit changes and close connection
conn.commit()
conn.close()
print("Data successfully migrated to SQLite!")
