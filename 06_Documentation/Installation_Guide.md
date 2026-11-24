# Installation Guide

Tested with Python 3.14 on Windows 11 (OpenCV 5.0, NumPy 2.4, pandas 3.0, Matplotlib 3.11). Any recent Python 3.10+ should work.

1. Install Python from python.org (tick "Add python.exe to PATH").
2. Open PowerShell in the unzipped folder and install the libraries:
   ```
   cd 02_Source_Code
   python -m pip install -r requirements.txt
   ```
   Minimum for running `main.py`: `numpy opencv-python pandas openpyxl matplotlib`.
   `scipy` is needed for `validate.py`; `rasterio` only for `fetch_data.py`; 
3. No data download is needed: the sample images are already in `04_Sample_Data/`.
   To re-download them: `python fetch_data.py` (internet required, no account needed).
