import json
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

VIDEO_PATH = PROJECT_ROOT / "sample-videos" / "match.mp4"
EVENTS_JSON_PATH = PROJECT_ROOT / "video-ingestion" / "output" / "parsed-data" / "score_change_events.json"
CLIPS_DIR = BASE_DIR / "output" / "clips"

PRE_EVENT_SECONDS = 10
POST_EVENT_SECONDS = 5


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_events(events_path: Path):
    if not events_path.exists():
        print(f"Events file not found: {events_path}")
        return []

    with open(events_path, "r", encoding="utf-8") as file:
        return json.load(file)


def build_clip_times(event_timestamp: float, pre_seconds: int, post_seconds: int):
    start_time = max(0, event_timestamp - pre_seconds)
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


def generate_clips_from_events(events, video_path: Path, clips_dir: Path):
    ensure_dir(clips_dir)

    generated = []

    for index, event in enumerate(events, start=1):
        timestamp = event.get("timestamp")
        if timestamp is None:
            continue

        start_time, duration = build_clip_times(
            event_timestamp=float(timestamp),
            pre_seconds=PRE_EVENT_SECONDS,
            post_seconds=POST_EVENT_SECONDS
        )

        clip_name = f"highlight_{index:03d}_t{float(timestamp):.2f}.mp4"
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
                "event_timestamp": float(timestamp),
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
                f"{clip_record['old_score']} -> {clip_record['new_score']}"
            )

    return generated


def save_generated_clips_metadata(clips, output_path: Path) -> None:
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(clips, file, indent=2)


def main() -> None:
    ensure_dir(CLIPS_DIR)

    if not VIDEO_PATH.exists():
        print(f"Video file not found: {VIDEO_PATH}")
        return

    events = load_events(EVENTS_JSON_PATH)
    if not events:
        print("No events found. Nothing to generate.")
        return

    generated_clips = generate_clips_from_events(
        events=events,
        video_path=VIDEO_PATH,
        clips_dir=CLIPS_DIR
    )

    metadata_path = BASE_DIR / "output" / "generated_highlights.json"
    save_generated_clips_metadata(generated_clips, metadata_path)

    print(f"\nSaved highlight metadata: {metadata_path}")
    print(f"Generated {len(generated_clips)} highlight clip(s)")


if __name__ == "__main__":
    main()