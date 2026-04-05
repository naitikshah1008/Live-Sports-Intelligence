import json
import subprocess
from pathlib import Path

import cv2
import librosa
import numpy as np
import requests

BACKEND_HIGHLIGHTS_API = "http://localhost:8080/api/highlights"

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

VIDEO_PATH = PROJECT_ROOT / "sample-videos" / "match.mp4"
EVENTS_JSON_PATH = PROJECT_ROOT / "video-ingestion" / "output" / "parsed-data" / "score_change_events.json"

CLIPS_DIR = BASE_DIR / "output" / "clips"
REFINED_EVENTS_PATH = BASE_DIR / "output" / "refined_score_events.json"
GENERATED_HIGHLIGHTS_PATH = BASE_DIR / "output" / "generated_highlights.json"

PRE_EVENT_SECONDS = 8
POST_EVENT_SECONDS = 6

SEARCH_BACK_SECONDS = 20
SEARCH_FORWARD_SECONDS = 0
FRAME_SAMPLE_SECONDS = 1


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_events(events_path: Path):
    if not events_path.exists():
        print(f"Events file not found: {events_path}")
        return []

    with open(events_path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(data, output_path: Path) -> None:
    ensure_dir(output_path.parent)
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def get_video_duration(video_path: Path) -> float:
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        return 0.0

    fps = capture.get(cv2.CAP_PROP_FPS)
    total_frames = capture.get(cv2.CAP_PROP_FRAME_COUNT)
    capture.release()

    if fps <= 0:
        return 0.0

    return float(total_frames / fps)


def extract_audio_energy_series(video_path: Path, sr: int = 16000):
    audio, sample_rate = librosa.load(str(video_path), sr=sr, mono=True)
    hop_length = sample_rate
    rms = librosa.feature.rms(y=audio, frame_length=2048, hop_length=hop_length)[0]

    energy_by_second = {}
    for index, value in enumerate(rms):
        energy_by_second[index] = float(value)

    return energy_by_second


def extract_frame_change_series(video_path: Path, step_seconds: int = 1):
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        return {}

    fps = capture.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        capture.release()
        return {}

    frame_interval = int(fps * step_seconds)
    if frame_interval <= 0:
        frame_interval = 1

    changes = {}
    frame_index = 0
    second_index = 0
    previous_gray = None

    while True:
        success, frame = capture.read()
        if not success:
            break

        if frame_index % frame_interval == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, (320, 180))

            if previous_gray is None:
                changes[second_index] = 0.0
            else:
                diff = cv2.absdiff(previous_gray, gray)
                changes[second_index] = float(np.mean(diff))

            previous_gray = gray
            second_index += step_seconds

        frame_index += 1

    capture.release()
    return changes


def normalize_series(values_dict):
    if not values_dict:
        return {}

    values = list(values_dict.values())
    max_value = max(values)
    min_value = min(values)

    if max_value == min_value:
        return {key: 0.0 for key in values_dict}

    return {
        key: (value - min_value) / (max_value - min_value)
        for key, value in values_dict.items()
    }


def score_candidate_seconds(event_timestamp, audio_scores, frame_scores, video_duration):
    start_second = max(0, int(event_timestamp) - SEARCH_BACK_SECONDS)
    end_second = min(int(video_duration), int(event_timestamp) + SEARCH_FORWARD_SECONDS)

    candidates = []

    for second in range(start_second, end_second + 1):
        audio_score = audio_scores.get(second, 0.0)
        frame_score = frame_scores.get(second, 0.0)

        proximity_score = 1.0 - (abs(event_timestamp - second) / max(1, SEARCH_BACK_SECONDS))
        if second > event_timestamp:
            proximity_score = 0.0

        combined_score = (
            0.50 * audio_score +
            0.35 * frame_score +
            0.15 * proximity_score
        )

        candidates.append({
            "second": second,
            "audio_score": round(audio_score, 4),
            "frame_score": round(frame_score, 4),
            "proximity_score": round(proximity_score, 4),
            "combined_score": round(combined_score, 4),
        })

    candidates.sort(key=lambda item: item["combined_score"], reverse=True)
    return candidates


def refine_event_timestamps(events, video_path: Path):
    video_duration = get_video_duration(video_path)
    audio_energy = extract_audio_energy_series(video_path)
    frame_changes = extract_frame_change_series(video_path, step_seconds=FRAME_SAMPLE_SECONDS)

    normalized_audio = normalize_series(audio_energy)
    normalized_frame = normalize_series(frame_changes)

    refined_events = []

    for event in events:
        raw_timestamp = float(event["timestamp"])
        candidates = score_candidate_seconds(
            event_timestamp=raw_timestamp,
            audio_scores=normalized_audio,
            frame_scores=normalized_frame,
            video_duration=video_duration
        )

        if not candidates:
            refined_timestamp = raw_timestamp
            best_candidate = None
        else:
            refined_timestamp = float(candidates[0]["second"])
            best_candidate = candidates[0]

        refined_event = {
            **event,
            "raw_timestamp": raw_timestamp,
            "refined_timestamp": refined_timestamp,
            "best_candidate": best_candidate,
            "top_candidates": candidates[:5]
        }
        refined_events.append(refined_event)

    return refined_events


def build_clip_times(refined_timestamp: float, pre_seconds: int, post_seconds: int):
    start_time = max(0, refined_timestamp - pre_seconds)
    duration = pre_seconds + post_seconds
    return start_time, duration


def generate_highlight_clip(
    video_path: Path,
    output_path: Path,
    start_time: float,
    duration: float
) -> bool:
    command = [
        "ffmpeg",
        "-y",
        "-ss", str(start_time),
        "-i", str(video_path),
        "-t", str(duration),
        "-c:v", "libx264",
        "-c:a", "aac",
        str(output_path)
    ]

    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError as error:
        print(f"FFmpeg failed for clip {output_path.name}")
        print(error.stderr.decode(errors="ignore"))
        return False


def generate_clips_from_refined_events(events, video_path: Path, clips_dir: Path):
    ensure_dir(clips_dir)

    generated = []

    for index, event in enumerate(events, start=1):
        refined_timestamp = float(event.get("refined_timestamp", event["timestamp"]))

        start_time, duration = build_clip_times(
            refined_timestamp=refined_timestamp,
            pre_seconds=PRE_EVENT_SECONDS,
            post_seconds=POST_EVENT_SECONDS
        )

        clip_name = f"highlight_{index:03d}_t{refined_timestamp:.2f}.mp4"
        output_path = clips_dir / clip_name

        success = generate_highlight_clip(
            video_path=video_path,
            output_path=output_path,
            start_time=start_time,
            duration=duration
        )

        if success:
            clip_record = {
                "clip_file": clip_name,
                "clip_path": str(output_path),
                "event_timestamp": float(event["timestamp"]),
                "refined_event_timestamp": refined_timestamp,
                "clock": event.get("clock", ""),
                "old_score": event.get("old_score", ""),
                "new_score": event.get("new_score", ""),
                "start_time": start_time,
                "duration": duration
            }
            generated.append(clip_record)

            print(
                f"Generated clip: {clip_name} | "
                f"clock={clip_record['clock']} | "
                f"{clip_record['old_score']} -> {clip_record['new_score']} | "
                f"raw_t={clip_record['event_timestamp']:.2f}s | "
                f"refined_t={clip_record['refined_event_timestamp']:.2f}s"
            )

    return generated


def send_highlights_to_backend(clips):
    sent_files = set()

    for clip in clips:
        if clip["clip_file"] in sent_files:
            continue

        sent_files.add(clip["clip_file"])

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
            print(f'Failed to save highlight {clip["clip_file"]} to backend: {error}')


def main() -> None:
    ensure_dir(CLIPS_DIR)

    if not VIDEO_PATH.exists():
        print(f"Video file not found: {VIDEO_PATH}")
        return

    events = load_events(EVENTS_JSON_PATH)
    if not events:
        print("No events found. Nothing to generate.")
        return

    refined_events = refine_event_timestamps(events, VIDEO_PATH)
    save_json(refined_events, REFINED_EVENTS_PATH)

    print("\nRefined score-change events:\n")
    for event in refined_events:
        best = event.get("best_candidate")
        if best:
            print(
                f'clock={event["clock"]} | '
                f'{event["old_score"]} -> {event["new_score"]} | '
                f'raw_t={event["raw_timestamp"]:.2f}s | '
                f'refined_t={event["refined_timestamp"]:.2f}s | '
                f'combined_score={best["combined_score"]}'
            )
        else:
            print(
                f'clock={event["clock"]} | '
                f'{event["old_score"]} -> {event["new_score"]} | '
                f'raw_t={event["raw_timestamp"]:.2f}s | '
                f'refined_t={event["refined_timestamp"]:.2f}s'
            )

    generated_clips = generate_clips_from_refined_events(
        events=refined_events,
        video_path=VIDEO_PATH,
        clips_dir=CLIPS_DIR
    )

    save_json(generated_clips, GENERATED_HIGHLIGHTS_PATH)
    send_highlights_to_backend(generated_clips)

    print(f"\nSaved refined events: {REFINED_EVENTS_PATH}")
    print(f"Saved highlight metadata: {GENERATED_HIGHLIGHTS_PATH}")
    print(f"Generated {len(generated_clips)} refined highlight clip(s)")


if __name__ == "__main__":
    main()