"""Measured sensitivity analysis + survivor analysis (supplementary).  Usage: python sensitivity.py [results_dir]

1. Threshold sensitivity: Otsu T-10, T, T+10 (foreground = bright) for both images.
2. Border sensitivity: outside = background (used) vs neutral border (OpenCV default).
3. Survivor analysis: connected components left just before the null image, and (for the
   dark-foreground run) how many survivors lie in the water-like gray range.
"""
import sys
from pathlib import Path
import cv2
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from config import Config, ROOT
from image_loader import load_image
from preprocessing import to_gray, binarize
from experiment import run_experiment
from morphology import se_sequence, box_se, opening

out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "05_Results"
sd = out / "Supplementary" / "Sensitivity"
sd.mkdir(parents=True, exist_ok=True)
cfg = Config()
imgs = {"Urban": cfg.data_dir / "urban_image" / "urban_image.png", "Smooth": cfg.data_dir / "smooth_landscape_image" / "smooth_landscape_image.png"}
quiet = lambda *a, **k: None
rows, curves = [], {}
for name, p in imgs.items():
    gray = to_gray(load_image(p))
    _, T0 = binarize(gray)
    for label, T, border in ((f"T-10", T0 - 10, "background"), ("Otsu (baseline)", T0, "background"), ("T+10", T0 + 10, "background"),
                             ("Otsu, neutral border", T0, "neutral")):
        A, T = binarize(gray, T)
        df = run_experiment(A, log=quiet, border=border)
        curves[(name, label)] = df
        rows.append(dict(image=name, variant=label, threshold=T, foreground_px=int(A.sum()), foreground_pct=round(100 * A.mean(), 2),
                         pct_after_3x3=round(df.pct_remaining.iloc[0], 2), se_for_50pct=int(df[df.pct_remaining <= 50].se_size.iloc[0]),
                         se_for_10pct=int(df[df.pct_remaining <= 10].se_size.iloc[0]), null_se=int(df.se_size.iloc[-1]), iterations=len(df)))
tab = pd.DataFrame(rows)
tab.to_csv(sd / "sensitivity_table.csv", index=False)
fig, ax = plt.subplots(1, 2, figsize=(14, 5))
for a, name in zip(ax, imgs):
    for (n, label), df in curves.items():
        if n == name:
            a.plot(df.se_size, df.pct_remaining, "-o", ms=2.5, label=label)
    a.set_title(f"{name}: sensitivity of the curve"); a.set_xlabel("Structuring element size (side length, pixels)")
    a.set_ylabel("Foreground remaining (% of original)"); a.grid(alpha=.3); a.legend()
fig.tight_layout(); fig.savefig(sd / "sensitivity_graph.png", dpi=200); plt.close(fig)

# ---- is the urban curve below the smooth curve in every matched variant (common SE sizes)?
dom = []
for label in ("T-10", "Otsu (baseline)", "T+10", "Otsu, neutral border"):
    u, sm = curves[("Urban", label)], curves[("Smooth", label)]
    m = u.merge(sm, on="se_size", suffixes=("_u", "_s"))
    dom.append((label, bool((m.pct_remaining_u <= m.pct_remaining_s).all()), int(u.se_size.iloc[-1]), int(sm.se_size.iloc[-1])))
dom_lines = ["URBAN BELOW SMOOTH AT EVERY COMMON SE SIZE? (same variant for both images)"] + [f"  {l}: {'yes' if ok else 'NO'} (null SE urban {a}, smooth {b})" for l, ok, a, b in dom] + [""]
print(chr(10).join(dom_lines))
# ---- survivor analysis
seq = {}
for (k, se), _ in zip(se_sequence(box_se(3)), range(150)):
    seq[se.shape[0]] = se
L = dom_lines + ["SURVIVOR ANALYSIS (computed by sensitivity.py)", ""]
for name, p in imgs.items():
    gray = to_gray(load_image(p))
    A, T = binarize(gray)
    df = run_experiment(A, log=quiet)
    for size in (int(df.se_size.iloc[-2]),):
        o = opening(A, seq[size])
        n, _, st, _ = cv2.connectedComponentsWithStats(o, connectivity=8)
        L.append(f"{name}: last non-null SE {size}x{size}: {int(o.sum())} px in {n-1} connected component(s):")
        for s in st[1:]:
            L.append(f"   bounding box x={s[0]}, y={s[1]}, w={s[2]}, h={s[3]}, area={s[4]} px")
    # plateau
    vc = df.foreground_pixels.value_counts()
    rep = vc[vc > 1]
    if len(rep):
        v = int(rep.index[0]); sizes = df[df.foreground_pixels == v].se_size.tolist()
        L.append(f"   identical count {v} px for SE sizes {sizes[0]}..{sizes[-1]} (plateau)")
    L.append("")
gray = to_gray(load_image(imgs["Smooth"]))
A, T = binarize(gray, None, True)
df = run_experiment(A, log=quiet)
for size in (43, 103, 203, 243):
    o = opening(A, seq[size])
    L.append(f"Smooth, dark-pixel foreground, SE {size}x{size}: {int(o.sum())} px ({100*o.sum()/A.sum():.2f}% of foreground); "
             f"{100*float((gray[o > 0] <= 30).mean()):.1f}% of the surviving pixels have gray <= 30 (water mode of the histogram); mean gray {gray[o>0].mean():.1f}")
(out / "Comparative_Analysis" / "survivor_analysis.txt").write_text("\n".join(L), encoding="utf-8")
print(tab.to_string(index=False)); print("\n".join(L))
