import cv2
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
VIDEO_PATH = BASE_DIR.parent / "sample-videos" / "match.mp4"
FRAMES_DIR = BASE_DIR / "output" / "frames"
DETECTED_DIR = BASE_DIR / "output" / "detected-scoreboards"
DEBUG_DIR = BASE_DIR / "output" / "debug-boxes"
TEMPLATE_PATH = BASE_DIR / "template" / "scoreboard_template.jpg"

FRAME_INTERVAL_SECONDS = 1
MATCH_THRESHOLD = 0.60

STANDARD_WIDTH = 420
STANDARD_HEIGHT = 220

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
        print(f"{frame_file.name} -> matched, confidence={confidence:.3f}")
        detected_count += 1
    print(f"\nTemplate matching complete")
    print(f"Detected scoreboards: {detected_count}")
    print(f"Missed frames: {missed_count}")

def normalize_scoreboard(image):
    return cv2.resize(image, (STANDARD_WIDTH, STANDARD_HEIGHT), interpolation=cv2.INTER_CUBIC)

def preprocess_for_region_detection(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # enlarge contrast between text and background
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    # inverted binary helps detect dark text on light backgrounds
    _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)
    # connect nearby text components
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))
    morphed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=1)
    return morphed

def is_valid_candidate_box(x, y, w, h, image_width, image_height):
    area = w * h
    if area < 150:
        return False
    if w < 10 or h < 10:
        return False
    if w > image_width * 0.8 or h > image_height * 0.8:
        return False
    aspect_ratio = w / float(h)
    if aspect_ratio < 0.2 or aspect_ratio > 10:
        return False
    return True

def merge_overlapping_boxes(boxes):
    if not boxes:
        return []
    boxes = sorted(boxes, key=lambda b: (b[1], b[0]))
    merged = []
    for box in boxes:
        x, y, w, h = box
        merged_any = False
        for i, (mx, my, mw, mh) in enumerate(merged):
            if not (x > mx + mw or mx > x + w or y > my + mh or my > y + h):
                nx = min(x, mx)
                ny = min(y, my)
                nr = max(x + w, mx + mw)
                nb = max(y + h, my + mh)
                merged[i] = (nx, ny, nr - nx, nb - ny)
                merged_any = True
                break
        if not merged_any:
            merged.append(box)
    return merged

def detect_text_regions(scoreboard_image):
    normalized = normalize_scoreboard(scoreboard_image)
    processed = preprocess_for_region_detection(normalized)
    contours, _ = cv2.findContours(processed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    height, width = processed.shape[:2]
    boxes = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)

        if is_valid_candidate_box(x, y, w, h, width, height):
            boxes.append((x, y, w, h))
    boxes = merge_overlapping_boxes(boxes)
    # sort top to bottom, then left to right
    boxes = sorted(boxes, key=lambda b: (b[1], b[0]))
    return normalized, processed, boxes


def save_debug_regions(scoreboard_path: Path, debug_dir: Path) -> None:
    ensure_dir(debug_dir)
    image = cv2.imread(str(scoreboard_path))
    if image is None:
        print(f"Skipping unreadable scoreboard: {scoreboard_path.name}")
        return
    normalized, processed, boxes = detect_text_regions(image)
    debug_image = normalized.copy()
    for i, (x, y, w, h) in enumerate(boxes):
        cv2.rectangle(debug_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(
            debug_image,
            str(i),
            (x, max(15, y - 5)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1,
            cv2.LINE_AA
        )
    debug_output_path = debug_dir / scoreboard_path.name.replace(".jpg", "_debug.jpg")
    binary_output_path = debug_dir / scoreboard_path.name.replace(".jpg", "_binary.jpg")
    cv2.imwrite(str(debug_output_path), debug_image)
    cv2.imwrite(str(binary_output_path), processed)
    print(f"\n{scoreboard_path.name}")
    print(f"Detected {len(boxes)} candidate regions:")
    for i, (x, y, w, h) in enumerate(boxes):
        print(f"  box_{i}: x={x}, y={y}, w={w}, h={h}")


def process_sample_debug_images(detected_dir: Path, debug_dir: Path, max_files: int = 10) -> None:
    scoreboard_files = sorted(detected_dir.glob("*.jpg"))
    if not scoreboard_files:
        print(f"No detected scoreboard images found in {detected_dir}")
        return
    print(f"\nGenerating debug region detections for first {min(max_files, len(scoreboard_files))} scoreboards...\n")
    for scoreboard_file in scoreboard_files[:max_files]:
        save_debug_regions(scoreboard_file, debug_dir)

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
    process_sample_debug_images(
        detected_dir=DETECTED_DIR,
        debug_dir=DEBUG_DIR,
        max_files=10
    )

if __name__ == "__main__":
    main()