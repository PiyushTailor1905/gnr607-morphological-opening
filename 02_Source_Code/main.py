"""GNR 607 - morphological opening with progressively dilated 3x3 structuring elements.

Usage (from 02_Source_Code):
    python main.py                       # run everything with the packaged sample data
    python main.py --urban a.png --smooth b.png --out my_results
    python main.py --no-supplementary --selected-only
"""
import argparse
import sys
import time
from pathlib import Path
import cv2
from config import Config
from image_loader import load_image, load_metadata
from preprocessing import to_gray, binarize
from morphology import count_foreground, is_binary01
from experiment import run_experiment
import visualization as viz
import reporting as rep


def process(spec, cfg, out_root):
    out = out_root / spec.subdir / spec.name
    dirs = {k: out / k for k in ("original_image", "grayscale_image", "binary_image", "structuring_elements", "opened_images")}
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    print(f"\n=== {spec.name}  ({spec.image_path.name}) ===")
    bgr = load_image(spec.image_path)
    meta = load_metadata(spec.image_path)
    gray = to_gray(bgr)
    binary, T = binarize(gray, spec.threshold, spec.invert)
    assert is_binary01(binary)
    fg_def = f"gray {'<=' if spec.invert else '>'} T={T} (" + ("dark" if spec.invert else "bright") + " pixels are foreground = 1)"
    n_fg = count_foreground(binary)
    pct = 100.0 * n_fg / binary.size
    print(f"  image {bgr.shape[1]}x{bgr.shape[0]}, threshold T={T}, foreground {n_fg:,} px ({pct:.2f}%)")
    cv2.imwrite(str(dirs["original_image"] / f"{spec.name}_original.png"), bgr)
    cv2.imwrite(str(dirs["grayscale_image"] / f"{spec.name}_gray.png"), gray)
    cv2.imwrite(str(dirs["binary_image"] / f"{spec.name}_binary_T{T}.png"), binary * 255)
    t0 = time.time()
    df = run_experiment(binary, dirs["opened_images"], dirs["structuring_elements"], cfg.save_all_opened, cfg.selected_sizes)
    print(f"  finished in {time.time() - t0:.1f}s: null image at SE {df.se_size.iloc[-1]}x{df.se_size.iloc[-1]} after {len(df)} iterations")
    assert df.foreground_pixels.iloc[-1] == 0
    params = [("input", spec.image_path.name), ("threshold_T", T), ("foreground", fg_def), ("foreground_pixels", n_fg),
              ("foreground_percent", round(pct, 4)), ("border", "outside = background (0)"), ("versions", rep.versions())]
    rep.save_tables(df, out, params)
    viz.preprocessing_figure(bgr, gray, binary, T, f"{spec.name}: preprocessing", out / "preprocessing_panel.png",
                             "foreground = " + ("dark" if spec.invert else "bright"))
    viz.se_figure(out / "structuring_elements.png")
    viz.opened_montage(binary, df, cfg.selected_sizes, f"{spec.name}: opening of the original binary image", out / "opened_montage.png")
    viz.curve_figure(df, f"{spec.name} ({spec.category}): foreground pixels remaining vs structuring element size", out / "curve.png")
    rep.experiment_readme(spec, meta, bgr.shape, T, fg_def, n_fg, pct, df, out / "README.txt")
    return df, n_fg


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--urban")
    ap.add_argument("--smooth")
    ap.add_argument("--out")
    ap.add_argument("--no-supplementary", action="store_true")
    ap.add_argument("--selected-only", action="store_true", help="save only selected opened images")
    a = ap.parse_args(argv)
    cfg = Config(run_supplementary=not a.no_supplementary, save_all_opened=not a.selected_only)
    if a.out:
        cfg.results_dir = Path(a.out).resolve()
    specs = cfg.specs()
    for sp in specs:
        base = sp.name.split("_Inverted")[0]
        if a.urban and base == "Urban":
            sp.image_path = Path(a.urban)
        if a.smooth and base == "Smooth":
            sp.image_path = Path(a.smooth)
    out = cfg.results_dir
    out.mkdir(parents=True, exist_ok=True)
    res = {}
    try:
        for sp in specs:
            res[sp.name] = process(sp, cfg, out)
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print("ERROR:", e)
        return 1
    comp = out / "Comparative_Analysis"
    comp.mkdir(exist_ok=True)
    (u, nu), (s, ns) = res["Urban"], res["Smooth_Landscape"]
    viz.comparison_figure({"Urban (Delhi)": u, "Smooth (reservoir + forest)": s},
                          "Urban vs smooth landscape: foreground surviving morphological opening", comp / "comparison_graph.png")
    rep.comparison_summary(u, nu, "Urban", s, ns, "Smooth", comp / "comparison_summary.txt")
    if "Urban_InvertedForeground" in res:
        sup = out / "Supplementary" / "Comparison"
        sup.mkdir(parents=True, exist_ok=True)
        (ui, nui), (si, nsi) = res["Urban_InvertedForeground"], res["Smooth_InvertedForeground"]
        viz.comparison_figure({"Urban, dark = fg": ui, "Smooth, dark = fg": si},
                              "Supplementary: foreground = dark pixels (inverted)", sup / "comparison_graph_inverted.png")
        rep.comparison_summary(ui, nui, "Urban-inv", si, nsi, "Smooth-inv", sup / "comparison_summary_inverted.txt",
                               "Supplementary experiment: foreground = DARK pixels (gray <= T)")
    print("\nAll experiments reached the null image. Results in:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
