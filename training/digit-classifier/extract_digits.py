from pathlib import Path
import sys
import cv2

# adjust this if needed
PROJECT_ROOT = Path(__file__).resolve().parents[2]
VIDEO_INGESTION_DIR = PROJECT_ROOT / "video-ingestion"
sys.path.append(str(VIDEO_INGESTION_DIR))
from main import detect_text_regions, classify_boxes, crop_box  # noqa: E402
DETECTED_SCOREBOARDS_DIR = VIDEO_INGESTION_DIR / "output" / "detected-scoreboards"
RAW_CROPS_DIR = PROJECT_ROOT / "training" / "digit-classifier" / "raw-crops"

def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def save_digit_crops(scoreboard_path: Path) -> None:
    image = cv2.imread(str(scoreboard_path))
    if image is None:
        print(f"Skipping unreadable image: {scoreboard_path.name}")
        return
    normalized, _, boxes = detect_text_regions(image)
    field_map = classify_boxes(boxes)
    if field_map is None:
        print(f"Could not classify boxes for: {scoreboard_path.name}")
        return
    digit_fields = [
        "top_score",
        "bottom_score",
        "clock_1",
        "clock_2",
        "clock_3",
        "clock_4",
    ]
    for field_name in digit_fields:
        digit_crop = crop_box(normalized, field_map[field_name])
        output_name = f"{scoreboard_path.stem}_{field_name}.png"
        output_path = RAW_CROPS_DIR / output_name
        cv2.imwrite(str(output_path), digit_crop)

def main() -> None:
    ensure_dir(RAW_CROPS_DIR)
    scoreboard_files = sorted(DETECTED_SCOREBOARDS_DIR.glob("*.jpg"))
    if not scoreboard_files:
        print(f"No scoreboard files found in {DETECTED_SCOREBOARDS_DIR}")
        return
    print(f"Found {len(scoreboard_files)} detected scoreboard images")
    # Start with first 200 images. Increase later if needed.
    for scoreboard_file in scoreboard_files[:200]:
        save_digit_crops(scoreboard_file)
    print(f"Saved digit crops to {RAW_CROPS_DIR}")

if __name__ == "__main__":
    main()