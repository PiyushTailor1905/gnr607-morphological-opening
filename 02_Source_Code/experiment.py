"""The core loop: open the ORIGINAL binary image with SE0, SE1, ... until the result is null."""
import cv2
import pandas as pd
from morphology import se_sequence, opening, count_foreground, box_se


def run_experiment(binary, opened_dir=None, se_dir=None, save_all=True, selected_sizes=(), log=print, border="background"):
    """Return a DataFrame with one row per structuring element (last row has 0 foreground pixels).

    binary : uint8 {0,1} image (never modified; every opening starts from it)
    """
    n0 = count_foreground(binary)
    if n0 == 0:
        raise ValueError("Binary image has no foreground pixels; nothing to open.")
    max_size = min(binary.shape) + 2           # an SE larger than the image must yield a null image
    rows = []
    for k, se in se_sequence(box_se(3)):
        size = se.shape[0]
        if size > max_size:
            raise RuntimeError(f"Safeguard hit: SE {size}x{size} exceeds image size but image is not null.")
        opened = opening(binary, se, border)                       # always from the original image
        n = count_foreground(opened)
        fname = f"opened_iter{k:03d}_SE{size}x{size}.png"
        if opened_dir is not None and (save_all or size in selected_sizes or n == 0):
            cv2.imwrite(str(opened_dir / fname), opened * 255)
        if se_dir is not None and size <= 17:
            cv2.imwrite(str(se_dir / f"SE{k:03d}_{size}x{size}.png"), cv2.resize(se * 255, None, fx=20, fy=20, interpolation=cv2.INTER_NEAREST))
        rows.append(dict(iteration=k, se_size=size, se_dims=f"{size}x{size}", foreground_pixels=n,
                         pct_remaining=100.0 * n / n0, pct_removed=100.0 * (n0 - n) / n0, opened_file=fname))
        if k % 20 == 0 or n == 0:
            log(f"    iter {k:3d}  SE {size:4d}x{size:<4d}  foreground = {n:8d}  ({100.0*n/n0:6.2f}% left)")
        if n == 0:
            break
    return pd.DataFrame(rows)
