import time
from collections import deque
from pathlib import Path

import cv2
import mss
import numpy as np
import requests
from kafka import KafkaProducer
from ultralytics import YOLO
import subprocess
import tempfile

from main import (
    YOLO_MODEL_PATH,
    YOLO_CONFIDENCE_THRESHOLD,
    load_digit_templates,
    detect_scoreboard_with_yolo,
    detect_text_regions,
    classify_boxes,
    crop_box,
    read_digit_with_templates,
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_TOPIC_SCORE_EVENTS,
)

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

# Save live-generated clips into the same folder your backend already serves
LIVE_CLIPS_DIR = PROJECT_ROOT / "highlight-service" / "output" / "clips"

BACKEND_HIGHLIGHTS_API = "http://localhost:8080/api/highlights"

# Capture settings
CAPTURE_FPS = 20
BUFFER_SECONDS = 45
PRE_EVENT_SECONDS = 12
POST_EVENT_SECONDS = 6
MIN_CONFIRM_FRAMES = 3

# IMPORTANT:
# Set this to the region where the match video is playing on your screen.
# Example values only. Adjust for your screen/player window.
SCREEN_REGION = {
    "left": 0,
    "top": 80,
    "width": 1440,
    "height": 900,
}

# If you want to test quickly, set USE_FULL_SCREEN = True
USE_FULL_SCREEN = True


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def create_kafka_producer():
    try:
        return KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda value: __import__("json").dumps(value).encode("utf-8")
        )
    except Exception as error:
        print(f"Failed to create Kafka producer: {error}")
        return None


def publish_score_event(event):
    producer = create_kafka_producer()
    if producer is None:
        print("Kafka producer unavailable. Skipping event publish.")
        return

    payload = {
        "event_type": "score_change",
        "timestamp": event["timestamp"],
        "clock": event["clock"],
        "old_score": event["old_score"],
        "new_score": event["new_score"],
        "file": event["file"]
    }

    try:
        producer.send(KAFKA_TOPIC_SCORE_EVENTS, value=payload)
        producer.flush()
        print(f"Published event to Kafka: {payload}")
    except Exception as error:
        print(f"Failed to publish Kafka event: {error}")
    finally:
        producer.close()


def send_highlight_to_backend(clip):
    payload = {
        "clipFile": clip["clip_file"],
        "clipPath": clip["clip_path"],
        "eventTimestamp": clip["event_timestamp"],
        "clock": clip["clock"],
        "oldScore": clip["old_score"],
        "newScore": clip["new_score"],
        "startTime": clip["start_time"],
        "duration": clip["duration"]
    }

    try:
        response = requests.post(BACKEND_HIGHLIGHTS_API, json=payload, timeout=10)
        response.raise_for_status()
        print(f'Saved highlight to backend: {clip["clip_file"]}')
    except requests.RequestException as error:
        print(f'Failed to save highlight to backend: {error}')


def parse_scoreboard_image(scoreboard_image, templates):
    normalized, processed, boxes = detect_text_regions(scoreboard_image)
    field_map = classify_boxes(boxes)

    if field_map is None:
        return None

    top_score, _ = read_digit_with_templates(
        crop_box(normalized, field_map["top_score"]),
        templates
    )
    bottom_score, _ = read_digit_with_templates(
        crop_box(normalized, field_map["bottom_score"]),
        templates
    )
    c1, _ = read_digit_with_templates(
        crop_box(normalized, field_map["clock_1"]),
        templates
    )
    c2, _ = read_digit_with_templates(
        crop_box(normalized, field_map["clock_2"]),
        templates
    )
    c3, _ = read_digit_with_templates(
        crop_box(normalized, field_map["clock_3"]),
        templates
    )
    c4, _ = read_digit_with_templates(
        crop_box(normalized, field_map["clock_4"]),
        templates
    )

    if not all([top_score, bottom_score, c1, c2, c3, c4]):
        return None

    clock = f"{c1}{c2}:{c3}{c4}"

    if not top_score.isdigit() or not bottom_score.isdigit():
        return None

    return {
        "clock": clock,
        "top_score": top_score,
        "bottom_score": bottom_score,
    }


class LiveScoreTracker:
    def __init__(self, min_confirm_frames=3):
        self.min_confirm_frames = min_confirm_frames
        self.current_stable_score = None
        self.candidate_score = None
        self.candidate_count = 0
        self.event_counter = 0
        self.seen_event_keys = set()

    def update(self, parsed_row, capture_time):
        score_tuple = (parsed_row["top_score"], parsed_row["bottom_score"])

        if self.current_stable_score is None:
            self.current_stable_score = score_tuple
            return None

        if score_tuple == self.current_stable_score:
            self.candidate_score = None
            self.candidate_count = 0
            return None

        if self.candidate_score == score_tuple:
            self.candidate_count += 1
        else:
            self.candidate_score = score_tuple
            self.candidate_count = 1

        if self.candidate_count < self.min_confirm_frames:
            return None

        old_score = self.current_stable_score
        new_score = self.candidate_score

        self.current_stable_score = new_score
        self.candidate_score = None
        self.candidate_count = 0

        event_key = f'{parsed_row["clock"]}|{old_score[0]}-{old_score[1]}|{new_score[0]}-{new_score[1]}'
        if event_key in self.seen_event_keys:
            return None

        self.seen_event_keys.add(event_key)
        self.event_counter += 1

        return {
            "timestamp": capture_time,
            "clock": parsed_row["clock"],
            "old_score": f"{old_score[0]}-{old_score[1]}",
            "new_score": f"{new_score[0]}-{new_score[1]}",
            "file": f"live_event_{self.event_counter:03d}.jpg",
            "event_key": event_key,
        }


def write_clip_from_buffer(frame_buffer, event, clips_dir, fps):
    start_time = event["timestamp"] - PRE_EVENT_SECONDS
    end_time = event["timestamp"] + POST_EVENT_SECONDS

    selected_frames = [
        (ts, frame) for ts, frame in frame_buffer
        if start_time <= ts <= end_time
    ]

    if len(selected_frames) < 2:
        print("Not enough buffered frames to create clip.")
        return None

    height, width = selected_frames[0][1].shape[:2]
    clip_name = f'live_highlight_{event["clock"].replace(":", "-")}_{event["new_score"].replace("-", "_")}.mp4'
    output_path = clips_dir / clip_name

    temp_raw_path = clips_dir / f'temp_{clip_name}'

    writer = cv2.VideoWriter(
        str(temp_raw_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height)
    )

    for _, frame in selected_frames:
        writer.write(frame)

    writer.release()

    ffmpeg_command = [
        "ffmpeg",
        "-y",
        "-i", str(temp_raw_path),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(output_path)
    ]

    try:
        subprocess.run(ffmpeg_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        temp_raw_path.unlink(missing_ok=True)
    except subprocess.CalledProcessError as error:
        print("FFmpeg transcoding failed for live clip.")
        print(error.stderr.decode(errors="ignore"))
        return None

    clip_record = {
        "clip_file": clip_name,
        "clip_path": str(output_path),
        "event_timestamp": event["timestamp"],
        "clock": event["clock"],
        "old_score": event["old_score"],
        "new_score": event["new_score"],
        "start_time": max(0, start_time),
        "duration": PRE_EVENT_SECONDS + POST_EVENT_SECONDS,
    }

    return clip_record


def grab_frame(sct):
    if USE_FULL_SCREEN:
        monitor = sct.monitors[1]
    else:
        monitor = SCREEN_REGION

    shot = sct.grab(monitor)
    frame = np.array(shot)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
    return frame


def main():
    ensure_dir(LIVE_CLIPS_DIR)
    if not YOLO_MODEL_PATH.exists():
        print(f"YOLO model not found: {YOLO_MODEL_PATH}")
        return
    templates = load_digit_templates()
    if not templates:
        print("Digit templates not found. Make sure video-ingestion/templates/digits exists.")
        return

    model = YOLO(str(YOLO_MODEL_PATH))
    tracker = LiveScoreTracker(min_confirm_frames=MIN_CONFIRM_FRAMES)

    max_buffer_frames = BUFFER_SECONDS * CAPTURE_FPS
    frame_buffer = deque(maxlen=max_buffer_frames)
    pending_events = []

    print("Starting live local soccer monitor...")
    print(f"Capture FPS: {CAPTURE_FPS}")
    print(f"Buffer seconds: {BUFFER_SECONDS}")
    print(f"Using full screen: {USE_FULL_SCREEN}")
    if not USE_FULL_SCREEN:
        print(f"Screen region: {SCREEN_REGION}")

    with mss.mss() as sct:
        try:
            while True:
                loop_start = time.time()

                frame = grab_frame(sct)
                capture_time = time.time()

                frame_buffer.append((capture_time, frame.copy()))

                detection_box, confidence = detect_scoreboard_with_yolo(
                    frame=frame,
                    model=model,
                    confidence_threshold=YOLO_CONFIDENCE_THRESHOLD
                )

                if detection_box is not None:
                    x1, y1, x2, y2 = detection_box
                    scoreboard_crop = frame[y1:y2, x1:x2]

                    parsed = parse_scoreboard_image(scoreboard_crop, templates)
                    if parsed is not None:
                        print(
                            f'LIVE -> clock={parsed["clock"]}, '
                            f'score={parsed["top_score"]}-{parsed["bottom_score"]}, '
                            f'conf={confidence:.3f}'
                        )

                        event = tracker.update(parsed, capture_time)
                        if event is not None:
                            print(
                                f'EVENT DETECTED -> {event["clock"]} | '
                                f'{event["old_score"]} -> {event["new_score"]}'
                            )
                            publish_score_event(event)

                            pending_events.append({
                                "event": event,
                                "ready_at": capture_time + POST_EVENT_SECONDS
                            })

                ready_to_finalize = [
                    item for item in pending_events
                    if time.time() >= item["ready_at"]
                ]

                for item in ready_to_finalize:
                    clip_record = write_clip_from_buffer(
                        frame_buffer=frame_buffer,
                        event=item["event"],
                        clips_dir=LIVE_CLIPS_DIR,
                        fps=CAPTURE_FPS
                    )

                    if clip_record is not None:
                        print(f'Generated live clip: {clip_record["clip_file"]}')
                        send_highlight_to_backend(clip_record)

                    pending_events.remove(item)

                elapsed = time.time() - loop_start
                sleep_time = max(0, (1.0 / CAPTURE_FPS) - elapsed)
                time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("\nStopped live monitor.")


if __name__ == "__main__":
    main()