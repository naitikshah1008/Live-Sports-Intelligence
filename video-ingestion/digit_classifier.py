from pathlib import Path

import cv2
import torch
import torch.nn as nn
from PIL import Image
from torchvision import transforms

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR.parent / "training" / "digit-classifier" / "models" / "digit_classifier.pt"


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


def load_digit_classifier(model_path: Path = MODEL_PATH):
    if not model_path.exists():
        raise FileNotFoundError(f"Digit classifier model not found at {model_path}")

    checkpoint = torch.load(model_path, map_location="cpu")
    model = DigitCNN()
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    class_to_idx = checkpoint["class_to_idx"]
    idx_to_class = {v: k for k, v in class_to_idx.items()}
    image_size = checkpoint.get("image_size", 32)

    transform = transforms.Compose([
        transforms.Grayscale(num_output_channels=1),
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize((0.5,), (0.5,))
    ])

    return model, transform, idx_to_class


def read_digit_with_classifier(image, model, transform, idx_to_class):
    pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    tensor = transform(pil_image).unsqueeze(0)

    with torch.no_grad():
        output = model(tensor)
        pred_idx = output.argmax(dim=1).item()
        confidence = torch.softmax(output, dim=1)[0][pred_idx].item()

    digit = idx_to_class[pred_idx]
    return digit, confidence