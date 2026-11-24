RESULT README - Urban
============================================================
Category              : Urban / highly textured
Input file            : urban_image.png  (04_Sample_Data/urban_image/)
Dataset source        : https://earth-search.aws.element84.com/v1 (Sentinel-2 L2A COGs, ESA/Copernicus)
Sentinel-2 item       : S2C_43RGM_20251224_0_L2A  acquired 2025-12-24T05:41:11.158000Z
Location              : New Delhi, India (urban core)  (centre lon 77.209, lat 28.6139)
Spatial resolution    : 10 m / pixel; bands: B04 (red), B03 (green), B02 (blue), stretch DN/3000*255
Image dimensions      : 1024 x 1024 pixels (width x height)

PARAMETERS
Grayscale conversion  : Y = 0.299 R + 0.587 G + 0.114 B (OpenCV COLOR_BGR2GRAY)
Thresholding          : Otsu global threshold; T = 70
Foreground definition : gray > T=70 (bright pixels are foreground = 1)
Foreground pixels     : 286,813 (27.35% of image)
Initial SE            : 3x3 box (all nine elements = 1), origin at centre
SE generation         : SE_(k+1) = SE_k dilated by the 3x3 box (Minkowski sum computed from its definition): 3,5,7,9,...
Operation             : opening  A o B = (A erode B) dilate B, same SE for both steps, applied to the ORIGINAL binary image each iteration
Border handling       : pixels outside the image are background (constant 0) for erosion and dilation
Stopping condition    : stop at the first SE whose opening leaves 0 foreground pixels (that final row is recorded)
Safeguard             : abort with an error if SE side exceeds min(image height, width)+2

RESULT SUMMARY
SE iterations run     : 10 (SE 3x3 ... 21x21)
Foreground at 3x3     : 161,943 px (56.46% of original)
SE for <=50% / 10% / 1% remaining : 5 / 9 / 15
Last non-null SE      : 19x19 (817 px)
First null SE         : 21x21 -> 0 foreground pixels
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