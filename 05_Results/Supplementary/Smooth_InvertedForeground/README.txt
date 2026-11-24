RESULT README - Smooth_InvertedForeground
============================================================
Category              : Smooth (water body + forest)
Input file            : smooth_landscape_image.png  (04_Sample_Data/smooth_landscape_image/)
Dataset source        : https://earth-search.aws.element84.com/v1 (Sentinel-2 L2A COGs, ESA/Copernicus)
Sentinel-2 item       : S2C_44RKT_20260420_0_L2A  acquired 2026-04-20T05:30:50.088000Z
Location              : Ramganga reservoir / Corbett forest, Uttarakhand, India  (centre lon 78.76, lat 29.53)
Spatial resolution    : 10 m / pixel; bands: B04 (red), B03 (green), B02 (blue), stretch DN/3000*255
Image dimensions      : 1024 x 1024 pixels (width x height)

PARAMETERS
Grayscale conversion  : Y = 0.299 R + 0.587 G + 0.114 B (OpenCV COLOR_BGR2GRAY)
Thresholding          : Otsu global threshold; T = 61
Foreground definition : gray <= T=61 (dark pixels are foreground = 1)
Foreground pixels     : 787,110 (75.06% of image)
Initial SE            : 3x3 box (all nine elements = 1), origin at centre
SE generation         : SE_(k+1) = SE_k dilated by the 3x3 box (Minkowski sum computed from its definition): 3,5,7,9,...
Operation             : opening  A o B = (A erode B) dilate B, same SE for both steps, applied to the ORIGINAL binary image each iteration
Border handling       : pixels outside the image are background (constant 0) for erosion and dilation
Stopping condition    : stop at the first SE whose opening leaves 0 foreground pixels (that final row is recorded)
Safeguard             : abort with an error if SE side exceeds min(image height, width)+2

RESULT SUMMARY
SE iterations run     : 144 (SE 3x3 ... 289x289)
Foreground at 3x3     : 738,432 px (93.82% of original)
SE for <=50% / 10% / 1% remaining : 17 / 289 / 289
Last non-null SE      : 287x287 (91,355 px)
First null SE         : 289x289 -> 0 foreground pixels
Robustness note      : exact null SE depends on the threshold (+-10) and the border rule; see 05_Results/Supplementary/Sensitivity/ and Comparative_Analysis/survivor_analysis.txt

OUTPUT FILES (this folder)
original_image/ grayscale_image/ binary_image/   - input stages (PNG)
structuring_elements/                            - SE images (nearest-neighbour enlarged x20) for SE <= 17x17
opened_images/opened_iterNNN_SEsxs.png           - opening result for every SE (255 = foreground)
results.csv, results.xlsx                        - iteration, SE size, foreground pixels, % remaining, % removed
preprocessing_panel.png, structuring_elements.png, opened_montage.png, curve.png (SE size vs foreground pixels)

SOFTWARE
Python 3.14.5, OpenCV 5.0.0, NumPy 2.4.6, pandas 3.0.5, Matplotlib 3.11.0
Run command: python main.py