"""Binary morphology: structuring elements, erosion, dilation, opening, counting.

Convention: images are uint8 arrays with values {0,1}; 1 = foreground.
Border handling: pixels outside the image are treated as BACKGROUND (constant 0) in both erosion
and dilation.  (OpenCV's default border for erosion is +infinity, which we deliberately override.)
"""
import cv2
import numpy as np


def box_se(size=3):
    """size x size box structuring element (all ones)."""
    return np.ones((size, size), np.uint8)


def dilate_se(se, other):
    """Minkowski sum  se (+) other  computed from the definition (union of translates).

    Independent of OpenCV so it can be used to cross-check cv2.  The result array grows by
    (other.shape - 1) in each dimension, so 3x3 (+) 3x3 -> 5x5.  Both inputs are assumed to have
    odd dimensions with the origin at the centre.
    """
    h, w = se.shape
    oh, ow = other.shape
    out = np.zeros((h + oh - 1, w + ow - 1), np.uint8)
    for dy, dx in zip(*np.nonzero(other)):          # every foreground offset of 'other'
        out[dy:dy + h, dx:dx + w] |= se             # translate se by (dy,dx) and OR it in
    return out


def se_sequence(base=None):
    """Yield (index, SE) forever: SE0 = 3x3 box, SE_{k+1} = SE_k dilated by the 3x3 box."""
    base = box_se(3) if base is None else base
    se = base.copy()
    k = 0
    while True:
        yield k, se
        se = dilate_se(se, base)
        k += 1


def erode(img, se, border="background"):
    """border='background': outside = 0 (default). border='neutral': outside does not constrain the
    erosion (OpenCV's default, equivalent to outside = foreground for the minimum)."""
    return cv2.erode(img, se, borderType=cv2.BORDER_CONSTANT, borderValue=0 if border == "background" else 1)


def dilate(img, se):
    return cv2.dilate(img, se, borderType=cv2.BORDER_CONSTANT, borderValue=0)


def opening(img, se, border="background"):
    """A o B = (A erode B) dilate B   (same SE for both steps)."""
    return dilate(erode(img, se, border), se)


def count_foreground(img):
    """Number of foreground pixels of a {0,1} (or {0,255}) binary image."""
    return int(np.count_nonzero(img))


def is_binary01(img):
    return img.dtype == np.uint8 and set(np.unique(img).tolist()) <= {0, 1}
