"""Independent validation of the experiment. Usage: python validate.py [results_dir] [report_path]

Writes a PASS/FAIL report. Cross-checks use SciPy and a brute-force NumPy implementation of the
morphological definitions (not the OpenCV code used by the main program).
"""
import filecmp
import subprocess
import sys
import tempfile
from pathlib import Path
import cv2
import numpy as np
import pandas as pd
from scipy import ndimage as ndi
from config import ROOT
from morphology import box_se, se_sequence, dilate_se, opening, is_binary01

RES = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "05_Results"
REPORT = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "07_Validation" / "validation_report.txt"
lines, failures = [], 0


def check(name, ok, detail=""):
    global failures
    failures += (not ok)
    lines.append(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" -- {detail}" if detail else ""))


def brute_open(A, se):
    """Opening straight from the definitions: erosion = every SE offset lands on foreground;
    dilation = any SE offset lands on foreground. Outside the image counts as background."""
    r = se.shape[0] // 2
    H, W = A.shape
    P = np.pad(A, r)
    E = np.ones_like(A, bool)
    for dy, dx in zip(*np.nonzero(se)):
        E &= P[dy:dy + H, dx:dx + W].astype(bool)
    PE = np.pad(E, r)
    D = np.zeros_like(A, bool)
    for dy, dx in zip(*np.nonzero(se)):          # SE is symmetric, so reflection is irrelevant
        D |= PE[dy:dy + H, dx:dx + W]
    return D.astype(np.uint8)


def window_sum(M, s):
    """Sum of M over every s x s window centred on each pixel (outside = 0), via a summed-area table."""
    r = s // 2
    P = np.pad(M.astype(np.int64), r)
    I = np.pad(P.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    H, W = M.shape
    return I[s:s + H, s:s + W] - I[0:H, s:s + W] - I[s:s + H, 0:W] + I[0:H, 0:W]


def sat_open(A, s):
    """Opening by an s x s square computed with a method that shares no code with cv2/scipy:
    erosion = windows whose sum equals s*s; dilation = pixels whose window contains an eroded pixel."""
    E = window_sum(A, s) == s * s
    return (window_sum(E, s) > 0).astype(np.uint8)


def otsu_numpy(gray):
    h = np.bincount(gray.ravel(), minlength=256).astype(np.float64)
    p = h / h.sum(); w0 = np.cumsum(p); mu = np.cumsum(p * np.arange(256)); mt = mu[-1]
    with np.errstate(divide="ignore", invalid="ignore"):
        sb = (mt * w0 - mu) ** 2 / (w0 * (1 - w0))
    return int(np.nanargmax(sb))


# ---- Check 1: structuring elements -------------------------------------------------------
seq = []
for (k, se), _ in zip(se_sequence(box_se(3)), range(160)):
    seq.append(se)
check("C1a SE0 is exactly the 3x3 all-ones box", np.array_equal(seq[0], np.ones((3, 3), np.uint8)))
ok = all(se.shape == (2 * k + 3, 2 * k + 3) and se.all() for k, se in enumerate(seq))
check("C1b SE_k are full square boxes of side 3,5,7,...,321", ok)
ok = True
for k in range(1, len(seq)):
    prev = np.pad(seq[k - 1], 1)                       # independent: cv2 dilation of zero-padded previous SE
    ok &= np.array_equal(cv2.dilate(prev, box_se(3)), seq[k])
    ok &= np.array_equal(dilate_se(seq[k - 1], box_se(3)), seq[k])
check("C1c SE_(k+1) == SE_k dilated by 3x3 (Minkowski sum and cv2.dilate agree)", ok)

for name in ("Urban", "Smooth_Landscape", "Supplementary/Urban_InvertedForeground", "Supplementary/Smooth_InvertedForeground"):
    d = RES / name
    lines.append(f"\n--- {name} ---")
    df = pd.read_csv(d / "results.csv")
    binf = next((d / "binary_image").glob("*.png"))
    A = (cv2.imread(str(binf), cv2.IMREAD_GRAYSCALE) > 0).astype(np.uint8)
    check("binary input contains only {0,255} values", set(np.unique(cv2.imread(str(binf), 0)).tolist()) <= {0, 255})
    # ---- Check 3: pixel counting
    rec = [int(np.count_nonzero(cv2.imread(str(d / "opened_images" / f), 0))) for f in df.opened_file]
    check("C3 CSV counts equal counts recounted from the saved opened PNGs (all iterations)", rec == df.foreground_pixels.tolist())
    check("C3 counts are non-negative integers", (df.foreground_pixels >= 0).all() and df.foreground_pixels.dtype.kind == "i")
    # ---- Check 4: monotonic
    N = df.foreground_pixels.to_numpy()
    check("C4 N(k+1) <= N(k) for all k", bool(np.all(np.diff(N) <= 0)))
    # ---- Check 5: termination
    check("C5 last row is the first zero; all earlier rows > 0", N[-1] == 0 and (N[:-1] > 0).all(), f"null at SE {df.se_size.iloc[-1]}x{df.se_size.iloc[-1]} after {len(df)} iterations")
    check("C1d SE sizes in CSV are 3,5,7,... consecutive odd", df.se_size.tolist() == list(range(3, 3 + 2 * len(df), 2)))
    # ---- Check 2/6: opening correctness via independent implementations
    sizes_scipy = [s for s in (3, 5, 9, 17) if s in set(df.se_size)]
    ok = True
    for s in sizes_scipy:
        ref = ndi.binary_opening(A.astype(bool), structure=np.ones((s, s), bool), border_value=0).astype(np.uint8)
        got = (cv2.imread(str(d / "opened_images" / df[df.se_size == s].opened_file.iloc[0]), 0) > 0).astype(np.uint8)
        ok &= np.array_equal(ref, got)
    check(f"C6 saved opened images equal scipy.ndimage.binary_opening (full image, SE {sizes_scipy})", ok)
    ok = all(np.array_equal(sat_open(A, int(sz)), (cv2.imread(str(d / "opened_images" / f), 0) > 0).astype(np.uint8))
             for sz, f in zip(df.se_size, df.opened_file))
    check(f"C6 summed-area-table opening (independent algorithm) equals saved output for ALL {len(df)} SEs on the full image", ok)
    orig = cv2.imread(str(next((d / "original_image").glob("*.png"))))
    gray = cv2.cvtColor(orig, cv2.COLOR_BGR2GRAY)
    Tfile = int(binf.stem.split("_T")[-1])
    ref = ((gray <= Tfile) if "Inverted" in name else (gray > Tfile)).astype(np.uint8)
    check("C0 saved binary image == (gray > T) or (gray <= T) recomputed from the saved original", np.array_equal(ref, A))
    check(f"C0 threshold T={Tfile} equals an independent NumPy Otsu implementation", otsu_numpy(gray) == Tfile, f"numpy Otsu = {otsu_numpy(gray)}")
    gref = np.round(0.299 * orig[..., 2] + 0.587 * orig[..., 1] + 0.114 * orig[..., 0])
    check("C0 gray image is BT.601 luminance (max abs diff <= 1 level)", float(np.abs(gref - gray).max()) <= 1)
    crop = A[300:556, 300:556]
    ok = True
    for k, se in enumerate(seq[:min(len(df), 25)]):
        ok &= np.array_equal(brute_open(crop, se), opening(crop, se))
    check("C6 brute-force NumPy definition == cv2-based opening on a 256x256 crop for the first 25 SEs (3x3..51x51) or until null", ok)
    # ---- original image used each time, outputs binary, anti-extensive, nested
    ok_orig = ok_bin = ok_sub = True
    prev = None
    for k in range(len(df)):
        o = (cv2.imread(str(d / "opened_images" / df.opened_file.iloc[k]), 0))
        ok_bin &= set(np.unique(o).tolist()) <= {0, 255}
        ob = (o > 0).astype(np.uint8)
        ok_sub &= bool(np.all(ob <= A)) and (prev is None or bool(np.all(ob <= prev)))
        prev = ob
        if k in (0, 1, 3, len(df) - 1):
            ok_orig &= np.array_equal(ob, opening(A, seq[k]))
    check("C2 opened images are {0,255}", ok_bin)
    check("C2 opening(A, SE_k) recomputed from the saved binary image matches saved outputs (original used each time)", ok_orig)
    check("C2 opened_k subset of A and subset of opened_(k-1) (anti-extensive, nested)", ok_sub)
    check("C2 idempotence: open(open(A,SE)) == open(A,SE)", np.array_equal(opening(opening(A, seq[3]), seq[3]), opening(A, seq[3])))

# ---- Random-image tests (objects touching the border, sparse noise, squares) -------------------
rng = np.random.default_rng(0)
ok = True
for trial in range(12):
    R = (rng.random((90, 70)) < rng.choice([0.5, 0.8, 0.95])).astype(np.uint8)
    R[:, :20] = 1 if trial % 2 else R[:, :20]                      # a block touching the border
    R[10:40, 30:60] = 1
    for se in seq[:25]:
        a, b, c = opening(R, se), brute_open(R, se), sat_open(R, se.shape[0])
        ok &= np.array_equal(a, b) and np.array_equal(a, c)
        if not a.any():
            break
check("C6 random images (incl. border-touching objects): cv2 == brute-force == summed-area-table for all SEs until null", ok)
Rn = (rng.random((60, 60)) < 0.9).astype(np.uint8)
neutral = opening(Rn, seq[2], "neutral")
check("C2 neutral-border opening >= zero-border opening (sanity of the border option)", bool(np.all(neutral >= opening(Rn, seq[2]))))

# ---- Check 7: reproducibility ------------------------------------------------------------
with tempfile.TemporaryDirectory() as t:
    r = subprocess.run([sys.executable, str(Path(__file__).parent / "main.py"), "--out", t, "--no-supplementary", "--selected-only"], capture_output=True, text=True)
    same = r.returncode == 0 and all(filecmp.cmp(RES / n / "results.csv", Path(t) / n / "results.csv", shallow=False) for n in ("Urban", "Smooth_Landscape"))
    check("C7 re-running main.py reproduces results.csv byte-for-byte", same)

lines.append(f"\nTOTAL FAILURES: {failures}")
REPORT.parent.mkdir(exist_ok=True)
REPORT.write_text("GNR 607 VALIDATION REPORT\n" + "=" * 60 + "\n" + "\n".join(lines), encoding="utf-8")
print("\n".join(lines))
sys.exit(1 if failures else 0)
