from pathlib import Path
import sys
import cv2
import torch
import torch.nn as nn
from torchvision import transforms
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = PROJECT_ROOT / "training" / "digit-classifier" / "models" / "digit_classifier.pt"
RAW_CROPS_DIR = PROJECT_ROOT / "training" / "digit-classifier" / "raw-crops"

IMAGE_SIZE = 32

class DigitCNN(nn.Module):

    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64 * 4 * 4, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 10),
        )
    
    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x

def main():
    checkpoint = torch.load(MODEL_PATH, map_location="cpu")
    class_to_idx = checkpoint["class_to_idx"]
    idx_to_class = {v: k for k, v in class_to_idx.items()}
    model = DigitCNN()
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    transform = transforms.Compose([
        transforms.Grayscale(num_output_channels=1),
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize((0.5,), (0.5,))
    ])
    sample_files = sorted(RAW_CROPS_DIR.glob("*.png"))[:20]
    for sample_file in sample_files:
        image = Image.open(sample_file)
        tensor = transform(image).unsqueeze(0)
        with torch.no_grad():
            output = model(tensor)
            pred_idx = output.argmax(dim=1).item()
            pred_class = idx_to_class[pred_idx]
        print(f"{sample_file.name} -> predicted: {pred_class}")

if __name__ == "__main__":
    main()