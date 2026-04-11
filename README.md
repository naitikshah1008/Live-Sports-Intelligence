# Live Sports Intelligence

A low-latency sports video intelligence system that detects score-change events from broadcast footage, generates refined AI-assisted highlight clips, streams events through Kafka, serves results through Spring Boot APIs, and visualizes highlights and system metrics in a React dashboard and Grafana.

## Features

- Detects score changes from broadcast scoreboard footage
- Uses temporal smoothing to reduce OCR noise
- Refines event timestamps using audio and frame-change signals
- Generates highlight clips with FFmpeg
- Publishes events through Kafka
- Stores events and highlights in PostgreSQL
- Exposes data through Spring Boot REST APIs
- Displays highlights in a React dashboard
- Monitors system health with Prometheus and Grafana

## Architecture Overview

[Add architecture diagram image here]

## Tech Stack

### Backend
- Spring Boot
- Java
- Spring Kafka
- Spring Data JPA
- PostgreSQL

### Video / AI Pipeline
- Python
- OpenCV
- FFmpeg
- Librosa
- NumPy

### Streaming / Infra
- Apache Kafka
- Redis
- Docker Compose

### Frontend / Monitoring
- React
- Axios
- Prometheus
- Grafana

## Project Structure

```bash
live-sports-intelligence/
├── backend-api/
├── video-ingestion/
├── highlight-service/
├── frontend/
├── infra/
├── sample-videos/
├── assets/
└── README.md