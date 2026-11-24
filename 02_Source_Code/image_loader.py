"""Image input with friendly error handling."""
import json
from pathlib import Path
import cv2


def load_image(path):
    """Load an image as an 8-bit BGR array. Raises a clear error if it cannot be read."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Input image not found: {path}\n"
                                "Run 'python fetch_data.py' or place your own image at that path.")
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"OpenCV could not decode image: {path}")
    return img


def load_metadata(image_path):
    """Return the dataset metadata JSON that sits next to the image (or {} if absent)."""
    p = Path(image_path)
    m = p.with_name(p.stem + "_metadata.json")
    return json.loads(m.read_text()) if m.is_file() else {}
