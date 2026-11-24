"""Grayscale conversion and two-level (binary) image generation."""
import cv2
import numpy as np


def to_gray(bgr):
    """ITU-R BT.601 luminance: Y = 0.299 R + 0.587 G + 0.114 B (OpenCV's BGR2GRAY)."""
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)


def binarize(gray, threshold=None, invert=False):
    """Return (binary, T). binary is uint8 with values {0,1}; 1 = foreground.

    threshold=None -> Otsu's automatic global threshold (maximises between-class variance).
    invert=False   -> foreground = pixels with gray >  T (bright)
    invert=True    -> foreground = pixels with gray <= T (dark)
    """
    if threshold is None:
        T, _ = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        T = int(T)
    else:
        T = int(threshold)
    fg = (gray <= T) if invert else (gray > T)
    return fg.astype(np.uint8), T
