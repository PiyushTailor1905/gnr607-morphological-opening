"""CSV/XLSX tables, per-experiment README files, comparison summary."""
import platform
import cv2
import numpy as np
import pandas as pd
import matplotlib


def versions():
    return (f"Python {platform.python_version()}, OpenCV {cv2.__version__}, NumPy {np.__version__}, "
            f"pandas {pd.__version__}, Matplotlib {matplotlib.__version__}")


def save_tables(df, out_dir, meta_rows):
    df.to_csv(out_dir / "results.csv", index=False)
    with pd.ExcelWriter(out_dir / "results.xlsx", engine="openpyxl") as xw:
        df.to_excel(xw, sheet_name="results", index=False)
        pd.DataFrame(meta_rows, columns=["parameter", "value"]).to_excel(xw, sheet_name="parameters", index=False)
        ws = xw.sheets["results"]
        for col, w in zip("ABCDEFG", (10, 10, 10, 18, 16, 15, 34)):
            ws.column_dimensions[col].width = w


def size_at(df, pct):
    """Smallest SE size whose remaining foreground is <= pct % of the original."""
    return int(df[df.pct_remaining <= pct].se_size.iloc[0])


def metrics(df, n0):
    return dict(n0=int(n0),
                N_se3=int(df.foreground_pixels.iloc[0]), pct_se3=float(df.pct_remaining.iloc[0]),
                size50=size_at(df, 50), size10=size_at(df, 10), size1=size_at(df, 1),
                last_nonnull=int(df.se_size.iloc[-2]), N_last_nonnull=int(df.foreground_pixels.iloc[-2]),
                null_size=int(df.se_size.iloc[-1]), n_iter=len(df))


def experiment_readme(spec, meta, img_shape, T, fg_def, n_fg, pct_fg, df, path):
    m = metrics(df, n_fg)
    lines = [
        f"RESULT README - {spec.name}", "=" * 60,
        f"Category              : {spec.category}",
        f"Input file            : {spec.image_path.name}  (04_Sample_Data/{spec.image_path.parent.name}/)",
        f"Dataset source        : {meta.get('source', 'n/a')}",
        f"Sentinel-2 item       : {meta.get('stac_item', 'n/a')}  acquired {meta.get('acquisition', 'n/a')}",
        f"Location              : {meta.get('site', 'n/a')}  (centre lon {meta.get('centre_lon', 'n/a')}, lat {meta.get('centre_lat', 'n/a')})",
        f"Spatial resolution    : {meta.get('gsd_m', 'n/a')} m / pixel; bands: {meta.get('bands', 'n/a')}",
        f"Image dimensions      : {img_shape[1]} x {img_shape[0]} pixels (width x height)",
        "", "PARAMETERS",
        "Grayscale conversion  : Y = 0.299 R + 0.587 G + 0.114 B (OpenCV COLOR_BGR2GRAY)",
        f"Thresholding          : {'Otsu global threshold' if spec.threshold is None else 'fixed global threshold'}; T = {T}",
        f"Foreground definition : {fg_def}",
        f"Foreground pixels     : {n_fg:,} ({pct_fg:.2f}% of image)",
        "Initial SE            : 3x3 box (all nine elements = 1), origin at centre",
        "SE generation         : SE_(k+1) = SE_k dilated by the 3x3 box (Minkowski sum computed from its definition): 3,5,7,9,...",
        "Operation             : opening  A o B = (A erode B) dilate B, same SE for both steps, applied to the ORIGINAL binary image each iteration",
        "Border handling       : pixels outside the image are background (constant 0) for erosion and dilation",
        "Stopping condition    : stop at the first SE whose opening leaves 0 foreground pixels (that final row is recorded)",
        "Safeguard             : abort with an error if SE side exceeds min(image height, width)+2",
        "", "RESULT SUMMARY",
        f"SE iterations run     : {m['n_iter']} (SE 3x3 ... {m['null_size']}x{m['null_size']})",
        f"Foreground at 3x3     : {m['N_se3']:,} px ({m['pct_se3']:.2f}% of original)",
        f"SE for <=50% / 10% / 1% remaining : {m['size50']} / {m['size10']} / {m['size1']}",
        f"Last non-null SE      : {m['last_nonnull']}x{m['last_nonnull']} ({m['N_last_nonnull']:,} px)",
        f"First null SE         : {m['null_size']}x{m['null_size']} -> 0 foreground pixels",
        "Robustness note      : exact null SE depends on the threshold (+-10) and the border rule; see 05_Results/Supplementary/Sensitivity/ and Comparative_Analysis/survivor_analysis.txt",
        "", "OUTPUT FILES (this folder)",
        "original_image/ grayscale_image/ binary_image/   - input stages (PNG)",
        "structuring_elements/                            - SE images (nearest-neighbour enlarged x20) for SE <= 17x17",
        "opened_images/opened_iterNNN_SEsxs.png           - opening result for every SE (255 = foreground)",
        "results.csv, results.xlsx                        - iteration, SE size, foreground pixels, % remaining, % removed",
        "preprocessing_panel.png, structuring_elements.png, opened_montage.png, curve.png (SE size vs foreground pixels)",
        "", "SOFTWARE", versions(), "Run command: python main.py"]
    path.write_text("\n".join(lines), encoding="utf-8")


def comparison_summary(dfA, nA, nameA, dfB, nB, nameB, path, note=""):
    mA, mB = metrics(dfA, nA), metrics(dfB, nB)
    sizes = sorted(set(dfA.se_size) & set(dfB.se_size))
    probe = [s for s in (3, 5, 9, 17, 33, 65, 129, 257, 513) if s in sizes]

    def at(df, s):
        return df[df.se_size == s].iloc[0]
    L = ["COMPARATIVE SUMMARY (numbers computed directly from the results.csv tables)", note, "",
         f"{'metric':42s}{nameA:>20s}{nameB:>20s}",
         f"{'foreground pixels in binary image':42s}{mA['n0']:>20,}{mB['n0']:>20,}",
         f"{'foreground after 3x3 opening':42s}{mA['N_se3']:>20,}{mB['N_se3']:>20,}",
         f"{'% remaining after 3x3 opening':42s}{mA['pct_se3']:>20.2f}{mB['pct_se3']:>20.2f}",
         f"{'SE size where <=50% remains':42s}{mA['size50']:>20d}{mB['size50']:>20d}",
         f"{'SE size where <=10% remains':42s}{mA['size10']:>20d}{mB['size10']:>20d}",
         f"{'SE size where <=1% remains':42s}{mA['size1']:>20d}{mB['size1']:>20d}",
         f"{'last non-null SE size':42s}{mA['last_nonnull']:>20d}{mB['last_nonnull']:>20d}",
         f"{'first null SE size':42s}{mA['null_size']:>20d}{mB['null_size']:>20d}",
         f"{'number of SE iterations':42s}{mA['n_iter']:>20d}{mB['n_iter']:>20d}", "",
         "Remaining foreground at common SE sizes:",
         f"{'SE':>6s}{nameA + ' N':>20s}{'%':>8s}{nameB + ' N':>20s}{'%':>8s}"]
    for s in probe:
        a, b = at(dfA, s), at(dfB, s)
        L.append(f"{s:>6d}{int(a.foreground_pixels):>20,}{a.pct_remaining:>8.2f}{int(b.foreground_pixels):>20,}{b.pct_remaining:>8.2f}")
    first_null = nameA if mA["null_size"] < mB["null_size"] else nameB
    L += ["", f"Reaches null image first: {first_null}"]
    path.write_text("\n".join(L), encoding="utf-8")
