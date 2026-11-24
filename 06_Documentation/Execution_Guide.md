# Execution Guide

All commands are run from `02_Source_Code`.

| Goal | Command |
|---|---|
| Run both required experiments + supplementary inverted runs | `python main.py` |
| Required experiments only | `python main.py --no-supplementary` |
| Your own images | `python main.py --urban my_city.png --smooth my_lake.png --out my_results` |
| Save only selected opened images (smaller output) | `python main.py --selected-only` |
| Independent validation (writes `07_Validation/validation_report.txt`) | `python validate.py` |
| Re-download Sentinel-2 crops | `python fetch_data.py` |

## What `main.py` does and prints
For every experiment it prints the image size, threshold and foreground count, then one progress line every 20 iterations and the final null-image line. Exit code 0 means every experiment reached N = 0; a missing/unreadable image prints `ERROR: …` and returns 1.

## Where the outputs are
`05_Results/<Experiment>/` contains `original_image/`, `grayscale_image/`, `binary_image/`, `structuring_elements/`, `opened_images/`, `results.csv`, `results.xlsx`, `curve.png` (the required graph), `opened_montage.png`, `preprocessing_panel.png`, `structuring_elements.png`, `README.txt`.
`05_Results/Comparative_Analysis/` has `comparison_graph.png` and `comparison_summary.txt`. `05_Results/Supplementary/` holds the inverted-foreground runs.
