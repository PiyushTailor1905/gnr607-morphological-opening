# Methodology

## 1. Binary image generation
1. Read the RGB crop (8-bit).
2. Gray = 0.299 R + 0.587 G + 0.114 B.
3. Global Otsu threshold T (maximises between-class variance) – chosen automatically, never tuned by hand. T = 70 (urban), 61 (smooth).
4. Foreground = pixels with gray > T (bright), value 1; background 0. The same rule is used for both scenes so the results are comparable. A supplementary run uses the opposite polarity (gray ≤ T).

## 2. Structuring elements
SE0 = 3×3 box of ones. SE(k+1) = SE(k) ⊕ SE0, where ⊕ is dilation of the SE (an image) by the 3×3 box, i.e. the Minkowski sum (union of the translates of SE(k) by every element of SE0). Sizes: 3, 5, 7, 9, …, 2k+3. `morphology.dilate_se` computes it from the definition and `validate.py` cross-checks it with `cv2.dilate` for 160 elements.

## 3. Opening
A ○ B = (A ⊖ B) ⊕ B with the same B for both steps (OpenCV `erode` then `dilate`). Border: pixels outside the image are background (OpenCV's default border value for erosion is +∞; we pass 0 explicitly). Each opening uses the original binary image A, never the previous output.

## 4. Counting and stopping
N = `np.count_nonzero` of the opened {0,1} image. The loop records a row for each SE and stops after the first row with N = 0 (that row is kept). Safeguard: if the SE side exceeds min(H, W)+2 while N > 0 the program raises an error instead of claiming a null image.

## 5. Why N is non-increasing
SE(k) ⊂ SE(k+1) and SE(k+1) is itself a union of translates of SE(k) (a square of side 2k+5 is a union of squares of side 2k+3), so every set that is open with respect to SE(k+1) is open with respect to SE(k): A ○ SE(k+1) ⊆ A ○ SE(k). Verified numerically for all four experiments.

## 6. Outputs
Per iteration: SE size, foreground count, % remaining, % removed, opened image file. Plots: SE side length (x) vs foreground pixels (y), linear and log views, plus a normalised comparison.

## 7. Software
Python, OpenCV, NumPy, pandas/openpyxl, Matplotlib (versions are written into each result README).

## 8. Data selection and radiometry
* Crops are 1024×1024 px windows centred on fixed coordinates (New Delhi 28.6139 N 77.2090 E; Ramganga reservoir 29.53 N 78.76 E) from Sentinel-2 L2A, cloud cover < 2 % at tile level. `fetch_data.py` walks the candidate scenes (lowest cloud first) and keeps the first whose window has no no-data pixels and < 0.2 % very bright pixels. For Delhi this rejected the seven scenes (Feb–Jun 2026) that had ≥ 0.2 % very bright pixels (bright roofs/clouds) and selected a December 2025 scene; the two scenes therefore differ in season (Dec vs Apr) and illumination.
* Band values are used as stored (they behave like reflectance×10⁴; the STAC item advertises an offset of −0.1 that is not consistent with the observed value range, so no offset was applied) and displayed with one fixed linear stretch, DN/3000×255 (clipped). Otsu is computed on this 8-bit gray image. Any other linear stretch changes the threshold value but not the partition, except for the clipped/quantised pixels.
* **Interpretation caveat:** with Otsu and foreground = bright, the *smooth* scene's foreground is the brighter minority (fields, sunlit/bare slopes, sand), not the water or forest themselves; the water is background. The supplementary dark-foreground run (water + dark forest = foreground) covers the "water body/forest" reading.

## 9. Sensitivity (measured, `sensitivity.py`, `05_Results/Supplementary/Sensitivity/`)
Threshold T±10 and the border rule (outside = background versus OpenCV's neutral border) change the exact null SE: urban 19–23, smooth 35–55. In all four matched variants (T-10, Otsu, T+10, neutral border; same variant applied to both images) the urban curve lies below the smooth curve at every common SE size and reaches null first (`survivor_analysis.txt`). Border: with a neutral border the urban null moves from 21×21 to 23×23, smooth stays 49×49.
