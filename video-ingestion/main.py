import cv2
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
VIDEO_PATH = BASE_DIR.parent / "sample-videos" / "match.mp4"
FRAMES_DIR = BASE_DIR / "output" / "frames"
CROPPED_DIR = BASE_DIR / "output" / "scoreboard-crops"

FRAME_INTERVAL_SECONDS = 1

# Adjust these coordinates based on your video
SCOREBOARD_REGION = (96, 54, 307, 162)  # (x1, y1, x2, y2)

def ensure_dir(path: Path) -> None:
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
    ensure_dir(output_dir)
    while True:
        success, frame = capture.read()
        if not success:
            break
        if frame_interval > 0 and frame_count % frame_interval == 0:
            timestamp_seconds = frame_count / fps if fps > 0 else 0
            output_filename = output_dir / f"frame_{saved_count:04d}_t{timestamp_seconds:.2f}.jpg"
            cv2.imwrite(str(output_filename), frame)
            print(f"Saved frame: {output_filename.name}")
            saved_count += 1
        frame_count += 1
    capture.release()
    print(f"\nFinished extracting frames. Total saved: {saved_count}")

def crop_scoreboard_from_frames(frames_dir: Path, cropped_dir: Path, region: tuple[int, int, int, int]) -> None:
    ensure_dir(cropped_dir)
    x1, y1, x2, y2 = region
    frame_files = sorted(frames_dir.glob("*.jpg"))
    if not frame_files:
        print(f"No frames found in {frames_dir}")
        return
    print(f"\nCropping scoreboard region from {len(frame_files)} frames...")
    for frame_file in frame_files:
        frame = cv2.imread(str(frame_file))
        if frame is None:
            print(f"Skipping unreadable frame: {frame_file.name}")
            continue
        cropped = frame[y1:y2, x1:x2]
        output_file = cropped_dir / frame_file.name.replace("frame_", "scoreboard_")
        cv2.imwrite(str(output_file), cropped)
        print(f"Cropped: {output_file.name}")
    print(f"\nFinished cropping scoreboard regions into: {cropped_dir}")

def main() -> None:
    extract_frames(
        video_path=VIDEO_PATH,
        output_dir=FRAMES_DIR,
        interval_seconds=FRAME_INTERVAL_SECONDS
    )

    crop_scoreboard_from_frames(
        frames_dir=FRAMES_DIR,
        cropped_dir=CROPPED_DIR,
        region=SCOREBOARD_REGION
    )

if __name__ == "__main__":
    main()