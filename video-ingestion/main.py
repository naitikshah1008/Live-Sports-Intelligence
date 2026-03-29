import cv2
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
VIDEO_PATH = BASE_DIR.parent / "sample-videos" / "match.mp4"
OUTPUT_DIR = BASE_DIR / "output" / "frames"
FRAME_INTERVAL_SECONDS = 1

def ensure_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def extract_frames(video_path: Path, output_dir: Path, interval_seconds: int) -> None:
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        print(f"Error: could not open video file at {video_path}")
        return
    fps = capture.get(cv2.CAP_PROP_FPS)
    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_seconds = total_frames / fps if fps > 0 else 0
    print("Video opened successfully")
    print(f"FPS: {fps}")
    print(f"Total frames: {total_frames}")
    print(f"Duration: {duration_seconds:.2f} seconds")
    frame_interval = int(fps * interval_seconds)
    frame_count = 0
    saved_count = 0
    ensure_output_dir(output_dir)
    while True:
        success, frame = capture.read()
        if not success:
            break
        if frame_interval > 0 and frame_count % frame_interval == 0:
            timestamp_seconds = frame_count / fps if fps > 0 else 0
            output_filename = output_dir / f"frame_{saved_count:04d}_t{timestamp_seconds:.2f}.jpg"
            cv2.imwrite(str(output_filename), frame)
            print(f"Saved: {output_filename.name}")
            saved_count += 1
        frame_count += 1
    capture.release()
    print("\nFinished extracting frames")
    print(f"Total saved frames: {saved_count}")

def main() -> None:
    extract_frames(
        video_path=VIDEO_PATH,
        output_dir=OUTPUT_DIR,
        interval_seconds=FRAME_INTERVAL_SECONDS
    )

if __name__ == "__main__":
    main()