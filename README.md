# Live Sports Intelligence

A real-time sports video intelligence system that detects score-change events from broadcast footage, generates AI-assisted highlight clips, streams events through Kafka, and visualizes results in a live dashboard.

---

## Overview

This project transforms raw sports video into actionable insights by:

- Detecting scoreboard changes using computer vision
- Filtering noisy detections with temporal smoothing
- Generating highlight clips around key events
- Streaming events through Kafka
- Serving data via Spring Boot APIs
- Visualizing everything in a React dashboard with Grafana monitoring

---

## Features

-  Real-time scoreboard detection from video or live screen
-  Noise-resistant event detection using temporal smoothing
-  Accurate highlight generation with timestamp correction
-  FFmpeg-based clip generation for smooth playback
-  Kafka-based event streaming pipeline
-  PostgreSQL-backed storage for events and highlights
-  Live React dashboard with video playback
-  Prometheus + Grafana for system monitoring
-  Delete highlights with confirmation (UI + backend sync)

---

## How It Works

1. **Video / Screen Input**
   - Input can be:
     - Recorded match video
     - Live screen capture (local device)

2. **Scoreboard Detection**
   - YOLO detects scoreboard region
   - Digit classifier extracts score + clock

3. **Event Detection**
   - Temporal smoothing avoids OCR noise
   - Score changes trigger events

4. **Event Streaming**
   - Events are published to Kafka

5. **Highlight Generation**
   - Continuous recording via FFmpeg
   - Clips are cut using refined timestamps

6. **Backend Processing**
   - Spring Boot consumes events
   - Stores data in PostgreSQL

7. **Visualization**
   - React dashboard shows:
     - latest score
     - timeline
     - highlight clips

---

## Architecture

```text
[ Video / Screen Capture ]
            ↓
[ Python Video Pipeline ]
 (YOLO + OCR + Smoothing)
            ↓
        Kafka
            ↓
[ Spring Boot Backend ]
            ↓
     PostgreSQL DB
            ↓
     React Dashboard
            ↓
        Grafana
```
---

## Tech Stack

### Backend
- Java
- Spring Boot
- Spring Kafka
- Spring Data JPA
- PostgreSQL

### Video / AI Pipeline
- Python
- OpenCV
- YOLO (Ultralytics)
- PyTorch (Digit Classifier)
- FFmpeg
- NumPy

### Streaming / Infra
- Apache Kafka
- Zookeeper
- Docker Compose

### Frontend / Monitoring
- React
- Axios
- Prometheus
- Grafana

---

## Project Structure

```bash
live-sports-intelligence/
├── backend-api/           # Spring Boot APIs
├── video-ingestion/       # Python detection + live monitor
├── highlight-service/     # Generated clips
├── frontend/              # React dashboard
├── infra/                 # Kafka, Zookeeper, Prometheus
├── sample-videos/         # Test videos
├── assets/                # Diagrams / media
└── README.md
```

---

## Setup & Run

### 1. Start Infrastructure

```bash
cd infra
docker compose up -d
```

### 2. Run Backend

```bash
cd backend-api
mvn spring-boot:run
```

### 3. Run Frontend
```bash
cd frontend
npm install
npm run dev
```

### 3. Run Video Pipeline
Offline mode (video file):
```bash
cd video-ingestion
python main.py
```
Live mode (screen capture):
```bash
python live_screen_monitor.py
```

---

## Dashboard

Access:
```bash
http://localhost:5173
```
Shows:
- Latest clock & score
- Latest event
- Match timeline (deduplicated)
- Highlight clips with playback
- Delete option for highlights

---

## UI Preview

### Main Dashboard
![Main Dashboard](assets/screenshot.png)
---

## Monitoring

Access Grafana:
```bash
http://localhost:3000
```
Tracks:
- events processed
- highlights generated
- system performance

---

## Known Limitations

- Works best with clear scoreboard layouts
- OCR may fail on low-quality streams
- Screen capture may not work with DRM-protected players
- Audio not included in highlights (future improvement)

---

## Future Improvements

- Multi-sport support (basketball, cricket, etc.)
- Fully automated scoreboard detection (no layout assumptions)
- Audio-based event refinement
- Cloud deployment (AWS/GCP)
- Real-time WebSocket updates
- Auto-delete video files from storage
- ML-based goal detection (beyond scoreboard)

---

## Author

Naitik Shah

---

## Summary

This project demonstrates a full-stack, real-time system combining:
- computer vision
- event-driven architecture
- distributed systems
- backend APIs
- frontend visualization
