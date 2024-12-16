# Use an official Python base image from Docker Hub
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install dependencies:
# 1. Copy requirements.txt
# 2. Install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code and data
COPY app/ app/
COPY data/ data/
COPY frontend/ frontend/

# Optional: If you use a startup script or just run uvicorn directly
# Expose the port you want to run on
EXPOSE 8000

# Run the FastAPI app with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
