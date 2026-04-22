FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY video-ingestion/requirements.txt /app/video-ingestion/requirements.txt
COPY highlight-service/requirements.txt /app/highlight-service/requirements.txt

RUN pip install --no-cache-dir -r /app/video-ingestion/requirements.txt -r /app/highlight-service/requirements.txt

COPY . /app