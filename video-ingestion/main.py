import cv2
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
VIDEO_PATH = BASE_DIR.parent / "sample-videos" / "match.mp4"
FRAMES_DIR = BASE_DIR / "output" / "frames"
DETECTED_DIR = BASE_DIR / "output" / "detected-scoreboards"
TEMPLATE_PATH = BASE_DIR / "template" / "scoreboard_template.jpg"

FRAME_INTERVAL_SECONDS = 1
MATCH_THRESHOLD = 0.60

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
            saved_count += 1
        frame_count += 1
    capture.release()
    print(f"\nFinished extracting frames. Total saved: {saved_count}")


def locate_scoreboard(frame, template, threshold: float):
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    result = cv2.matchTemplate(frame_gray, template_gray, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    if max_val < threshold:
        return None, max_val
    template_height, template_width = template_gray.shape
    top_left = max_loc
    bottom_right = (top_left[0] + template_width, top_left[1] + template_height)

    return (top_left, bottom_right), max_val

def auto_crop_scoreboards(frames_dir: Path, detected_dir: Path, template_path: Path, threshold: float) -> None:
    ensure_dir(detected_dir)
    template = cv2.imread(str(template_path))
    if template is None:
        print(f"Error: could not read template image at {template_path}")
        return
    frame_files = sorted(frames_dir.glob("*.jpg"))
    if not frame_files:
        print(f"No frames found in {frames_dir}")
        return
    detected_count = 0
    missed_count = 0
    print(f"\nRunning template matching on {len(frame_files)} frames...\n")
    for frame_file in frame_files:
        frame = cv2.imread(str(frame_file))
        if frame is None:
            print(f"Skipping unreadable frame: {frame_file.name}")
            continue
        match_box, confidence = locate_scoreboard(frame, template, threshold)
        if match_box is None:
            print(f"{frame_file.name} -> no match, confidence={confidence:.3f}")
            missed_count += 1
            continue
        (x1, y1), (x2, y2) = match_box
        scoreboard_crop = frame[y1:y2, x1:x2]
        output_file = detected_dir / frame_file.name.replace("frame_", "scoreboard_")
        cv2.imwrite(str(output_file), scoreboard_crop)
        print(f"{frame_file.name} -> matched, confidence={confidence:.3f}, box=({x1},{y1})-({x2},{y2})")
        detected_count += 1
    print(f"\nTemplate matching complete")
    print(f"Detected scoreboards: {detected_count}")
    print(f"Missed frames: {missed_count}")


def main() -> None:
    extract_frames(
        video_path=VIDEO_PATH,
        output_dir=FRAMES_DIR,
        interval_seconds=FRAME_INTERVAL_SECONDS
    )
    auto_crop_scoreboards(
        frames_dir=FRAMES_DIR,
        detected_dir=DETECTED_DIR,
        template_path=TEMPLATE_PATH,
        threshold=MATCH_THRESHOLD
    )

if __name__ == "__main__":
    main()