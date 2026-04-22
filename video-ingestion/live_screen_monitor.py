import json
import os
import subprocess
import time
from collections import deque
from pathlib import Path
from digit_classifier import load_digit_classifier, read_digit_with_classifier
import cv2
import mss
import numpy as np
import requests
from kafka import KafkaProducer
from ultralytics import YOLO

from main import (
    YOLO_MODEL_PATH,
    YOLO_CONFIDENCE_THRESHOLD,
    detect_scoreboard_with_yolo,
    detect_text_regions,
    classify_boxes,
    crop_box,
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_TOPIC_SCORE_EVENTS,
)

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

LIVE_CLIPS_DIR = PROJECT_ROOT / "highlight-service" / "output" / "clips"
LIVE_RECORDINGS_DIR = BASE_DIR / "output" / "live-recordings"

BACKEND_HIGHLIGHTS_API = "http://localhost:8080/api/highlights"

CAPTURE_FPS = 15
EVENT_BACKSHIFT_SECONDS = 6
PRE_EVENT_SECONDS = 9
POST_EVENT_SECONDS = 8
MIN_CONFIRM_FRAMES = 3

# Screen region used by Python detection and by the FFmpeg screen recording command
SCREEN_REGION = {
    "left": 0,
    "top": 80,
    "width": 1440,
    "height": 1900,
}

USE_FULL_SCREEN = True

# Record full session to a rolling source file and cut highlights from it
SESSION_RECORDING_PATH = LIVE_RECORDINGS_DIR / "live_session.ts"

def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def create_kafka_producer():
    try:
        return KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda value: json.dumps(value).encode("utf-8")
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
    max_attempts = 5
    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.post(BACKEND_HIGHLIGHTS_API, json=payload, timeout=10)
            response.raise_for_status()
            print(f'Saved highlight to backend: {clip["clip_file"]}')
            return True
        except requests.RequestException as error:
            print(f'Attempt {attempt}/{max_attempts} failed to save highlight: {error}')
            time.sleep(2)
    print(f'Giving up on saving highlight to backend: {clip["clip_file"]}')
    return False

def parse_scoreboard_image(scoreboard_image, digit_model, digit_transform, idx_to_class):
    normalized, _, boxes = detect_text_regions(scoreboard_image)
    field_map = classify_boxes(boxes)
    if field_map is None:
        return None
    top_score, _ = read_digit_with_classifier(
        crop_box(normalized, field_map["top_score"]),
        digit_model,
        digit_transform,
        idx_to_class
    )
    bottom_score, _ = read_digit_with_classifier(
        crop_box(normalized, field_map["bottom_score"]),
        digit_model,
        digit_transform,
        idx_to_class
    )
    c1, _ = read_digit_with_classifier(
        crop_box(normalized, field_map["clock_1"]),
        digit_model,
        digit_transform,
        idx_to_class
    )
    c2, _ = read_digit_with_classifier(
        crop_box(normalized, field_map["clock_2"]),
        digit_model,
        digit_transform,
        idx_to_class
    )
    c3, _ = read_digit_with_classifier(
        crop_box(normalized, field_map["clock_3"]),
        digit_model,
        digit_transform,
        idx_to_class
    )
    c4, _ = read_digit_with_classifier(
        crop_box(normalized, field_map["clock_4"]),
        digit_model,
        digit_transform,
        idx_to_class
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
        self.candidate_started_at = None
        self.candidate_clock = None
        self.event_counter = 0
        self.seen_event_keys = set()

    def update(self, parsed_row, session_elapsed_seconds):
        score_tuple = (parsed_row["top_score"], parsed_row["bottom_score"])
        if self.current_stable_score is None:
            self.current_stable_score = score_tuple
            return None
        if score_tuple == self.current_stable_score:
            self.candidate_score = None
            self.candidate_count = 0
            self.candidate_started_at = None
            self.candidate_clock = None
            return None
        if self.candidate_score == score_tuple:
            self.candidate_count += 1
        else:
            self.candidate_score = score_tuple
            self.candidate_count = 1
            self.candidate_started_at = session_elapsed_seconds
            self.candidate_clock = parsed_row["clock"]
        if self.candidate_count < self.min_confirm_frames:
            return None
        old_score = self.current_stable_score
        new_score = self.candidate_score
        event_timestamp = self.candidate_started_at if self.candidate_started_at is not None else session_elapsed_seconds
        event_clock = self.candidate_clock if self.candidate_clock is not None else parsed_row["clock"]
        self.current_stable_score = new_score
        self.candidate_score = None
        self.candidate_count = 0
        self.candidate_started_at = None
        self.candidate_clock = None
        event_key = f'{event_clock}|{old_score[0]}-{old_score[1]}|{new_score[0]}-{new_score[1]}'
        if event_key in self.seen_event_keys:
            return None
        self.seen_event_keys.add(event_key)
        self.event_counter += 1
        return {
            "timestamp": event_timestamp,
            "clock": event_clock,
            "old_score": f"{old_score[0]}-{old_score[1]}",
            "new_score": f"{new_score[0]}-{new_score[1]}",
            "file": f"live_event_{self.event_counter:03d}.jpg",
            "event_key": event_key,
        }
    
def grab_frame(sct):
    if USE_FULL_SCREEN:
        monitor = sct.monitors[1]
    else:
        monitor = SCREEN_REGION
    shot = sct.grab(monitor)
    frame = np.array(shot)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
    return frame

def get_session_elapsed_seconds(session_start_time: float) -> float:
    return time.time() - session_start_time

def build_ffmpeg_record_command(output_path: Path):
    """
    macOS screen recording via avfoundation.
    You may need to adjust the avfoundation input string on your machine.
    """
    command = [
        "ffmpeg",
        "-y",
        "-f", "avfoundation",
        "-framerate", str(CAPTURE_FPS),
        "-i", "3:none",   # change if needed on your machine
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",
        "-g", str(CAPTURE_FPS * 2),           # keyframe every ~2 seconds
        "-keyint_min", str(CAPTURE_FPS * 2),
        "-sc_threshold", "0",
        "-f", "mpegts",
        str(output_path),
    ]
    if not USE_FULL_SCREEN:
        crop_filter = (
            f"crop={SCREEN_REGION['width']}:{SCREEN_REGION['height']}:"
            f"{SCREEN_REGION['left']}:{SCREEN_REGION['top']}"
        )
        command.insert(-2, "-vf")
        command.insert(-2, crop_filter)
    return command

def start_background_screen_recording(output_path: Path):
    ensure_dir(output_path.parent)
    if output_path.exists():
        output_path.unlink()
    command = build_ffmpeg_record_command(output_path)
    print("Starting background screen recording...")
    print("FFmpeg command:", " ".join(command))
    process = subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return process

def stop_background_screen_recording(process: subprocess.Popen):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

def cut_highlight_from_recording(recording_path: Path, event, clips_dir: Path):
    if not recording_path.exists():
        print("Recording file does not exist yet. Cannot cut clip.")
        return None
    ensure_dir(clips_dir)
    raw_event_timestamp = float(event["timestamp"])
    shifted_event_timestamp = max(0, raw_event_timestamp - EVENT_BACKSHIFT_SECONDS)
    start_time = max(0, shifted_event_timestamp - PRE_EVENT_SECONDS)
    duration = PRE_EVENT_SECONDS + POST_EVENT_SECONDS
    clip_name = f'live_highlight_{event["clock"].replace(":", "-")}_{event["new_score"].replace("-", "_")}.mp4'
    output_path = clips_dir / clip_name
    command = [
        "ffmpeg",
        "-y",
        "-i", str(recording_path),
        "-ss", str(start_time),               # move -ss AFTER -i for accurate cutting
        "-t", str(duration),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(output_path),
    ]
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as error:
        print("Failed to cut highlight from session recording.")
        print(error.stderr.decode(errors="ignore"))
        return None
    return {
        "clip_file": clip_name,
        "clip_path": str(output_path),
        "event_timestamp": raw_event_timestamp,
        "clock": event["clock"],
        "old_score": event["old_score"],
        "new_score": event["new_score"],
        "start_time": start_time,
        "duration": duration,
        "shifted_event_timestamp": shifted_event_timestamp,
    }

def main():
    ensure_dir(LIVE_CLIPS_DIR)
    ensure_dir(LIVE_RECORDINGS_DIR)
    if not YOLO_MODEL_PATH.exists():
        print(f"YOLO model not found: {YOLO_MODEL_PATH}")
        return
    try:
        digit_model, digit_transform, idx_to_class = load_digit_classifier()
    except Exception as error:
        print(f"Failed to load digit classifier: {error}")
        return
    model = YOLO(str(YOLO_MODEL_PATH))
    tracker = LiveScoreTracker(min_confirm_frames=MIN_CONFIRM_FRAMES)
    pending_events = []
    print("Starting live local soccer monitor...")
    print(f"Capture FPS: {CAPTURE_FPS}")
    print(f"Using full screen: {USE_FULL_SCREEN}")
    if not USE_FULL_SCREEN:
        print(f"Screen region: {SCREEN_REGION}")
    session_start_time = time.time()
    ffmpeg_record_process = start_background_screen_recording(SESSION_RECORDING_PATH)
    with mss.mss() as sct:
        try:
            while True:
                loop_start = time.time()
                frame = grab_frame(sct)
                session_elapsed_seconds = get_session_elapsed_seconds(session_start_time)
                detection_box, confidence = detect_scoreboard_with_yolo(
                    frame=frame,
                    model=model,
                    confidence_threshold=YOLO_CONFIDENCE_THRESHOLD
                )
                if detection_box is not None:
                    x1, y1, x2, y2 = detection_box
                    scoreboard_crop = frame[y1:y2, x1:x2]
                    parsed = parse_scoreboard_image( scoreboard_crop,  digit_model, digit_transform, idx_to_class)
                    if parsed is not None:
                        print(
                            f'LIVE -> clock={parsed["clock"]}, '
                            f'score={parsed["top_score"]}-{parsed["bottom_score"]}, '
                            f'conf={confidence:.3f}'
                        )
                        event = tracker.update(parsed, session_elapsed_seconds)
                        if event is not None:
                            print(
                                f'EVENT DETECTED -> clock={event["clock"]} | '
                                f'{event["old_score"]} -> {event["new_score"]} | '
                                f'timestamp={event["timestamp"]:.2f}s'
                            )
                            publish_score_event(event)
                            pending_events.append({
                                "event": event,
                                "ready_at": time.time() + POST_EVENT_SECONDS + 1
                            })
                ready_to_finalize = [
                    item for item in pending_events
                    if time.time() >= item["ready_at"]
                ]
                for item in ready_to_finalize:
                    clip_record = cut_highlight_from_recording(
                        recording_path=SESSION_RECORDING_PATH,
                        event=item["event"],
                        clips_dir=LIVE_CLIPS_DIR
                    )
                    if clip_record is not None:
                        print(
                            f'Generated live clip from recording: {clip_record["clip_file"]} | '
                            f'raw_t={clip_record["event_timestamp"]:.2f}s | '
                            f'shifted_t={clip_record["shifted_event_timestamp"]:.2f}s | '
                            f'start={clip_record["start_time"]:.2f}s | '
                            f'duration={clip_record["duration"]:.2f}s'
                        )
                        send_highlight_to_backend(clip_record)
                    pending_events.remove(item)
                elapsed = time.time() - loop_start
                sleep_time = max(0, (1.0 / CAPTURE_FPS) - elapsed)
                time.sleep(sleep_time)
        except KeyboardInterrupt:
            print("\nStopped live monitor.")
        finally:
            stop_background_screen_recording(ffmpeg_record_process)

if __name__ == "__main__":
    main()