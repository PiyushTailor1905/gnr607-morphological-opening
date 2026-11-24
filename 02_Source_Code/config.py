"""Configuration for the GNR 607 morphological-opening experiment."""
from dataclasses import dataclass, field
import sys
from pathlib import Path

# project root: folder containing 02_Source_Code (or, for the frozen .exe in 03_Executables, its parent)
ROOT = Path(sys.executable).resolve().parent.parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent


@dataclass
class ExperimentSpec:
    name: str                 # folder / label, e.g. "Urban"
    image_path: Path          # input RGB satellite image
    category: str             # human-readable category
    invert: bool = False      # False: foreground = bright pixels (gray > T); True: foreground = dark pixels
    threshold: int | None = None   # None -> Otsu
    subdir: str = ""          # optional sub-folder under the results root (e.g. "Supplementary")


@dataclass
class Config:
    data_dir: Path = ROOT / "04_Sample_Data"
    results_dir: Path = ROOT / "05_Results"
    base_se_size: int = 3                 # 3x3 box = SE0
    save_all_opened: bool = True          # save every opened image (otherwise only a selection)
    selected_sizes: tuple = (3, 5, 9, 17, 33, 65, 129, 257)
    run_supplementary: bool = True        # inverted-foreground sensitivity runs

    def specs(self):
        u = self.data_dir / "urban_image" / "urban_image.png"
        s = self.data_dir / "smooth_landscape_image" / "smooth_landscape_image.png"
        main = [ExperimentSpec("Urban", u, "Urban / highly textured"),
                ExperimentSpec("Smooth_Landscape", s, "Smooth (water body + forest)")]
        sup = [ExperimentSpec("Urban_InvertedForeground", u, "Urban / highly textured", invert=True, subdir="Supplementary"),
               ExperimentSpec("Smooth_InvertedForeground", s, "Smooth (water body + forest)", invert=True, subdir="Supplementary")]
        return main + (sup if self.run_supplementary else [])
