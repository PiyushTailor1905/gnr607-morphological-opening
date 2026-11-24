"""Figures: preprocessing panel, SE montage, opened-image montage, curves, comparison."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from morphology import opening, se_sequence, box_se

DPI = 200
C1, C2 = "#C0392B", "#1F77B4"


def preprocessing_figure(bgr, gray, binary, T, title, path, fg_text):
    fig, ax = plt.subplots(1, 4, figsize=(18, 4.8))
    ax[0].imshow(bgr[..., ::-1]); ax[0].set_title("Original (RGB, Sentinel-2)")
    ax[1].imshow(gray, cmap="gray", vmin=0, vmax=255); ax[1].set_title("Grayscale")
    ax[2].hist(gray.ravel(), bins=256, range=(0, 255), color="gray")
    ax[2].axvline(T, color="r"); ax[2].set_title(f"Histogram, threshold T = {T}"); ax[2].set_xlabel("gray level")
    ax[3].imshow(binary, cmap="gray", vmin=0, vmax=1); ax[3].set_title(f"Binary ({fg_text})")
    for a in (ax[0], ax[1], ax[3]):
        a.axis("off")
    fig.suptitle(title); fig.tight_layout(); fig.savefig(path, dpi=DPI); plt.close(fig)


def se_figure(path, count=5):
    fig, ax = plt.subplots(1, count, figsize=(3 * count, 3.4))
    for (k, se), a in zip(se_sequence(box_se(3)), ax):
        a.imshow(se, cmap="gray", vmin=0, vmax=1, interpolation="nearest")
        a.set_title(f"SE{k}: {se.shape[0]}x{se.shape[1]}" + ("\n(3x3 box)" if k == 0 else f"\n= SE{k-1} dilated by 3x3"), fontsize=9)
        a.set_xticks(np.arange(-.5, se.shape[1], 1), minor=True)
        a.set_yticks(np.arange(-.5, se.shape[0], 1), minor=True)
        a.grid(which="minor", color="tab:blue", lw=.6)
        a.tick_params(which="both", length=0, labelbottom=False, labelleft=False)
    fig.tight_layout(); fig.savefig(path, dpi=DPI); plt.close(fig)


def opened_montage(binary, df, sizes, title, path):
    """Original binary image + openings at the requested SE sizes (+ the first null SE)."""
    avail = set(df.se_size)
    sizes = [s for s in sizes if s in avail]
    null_size = int(df.se_size.iloc[-1])
    if null_size not in sizes:
        sizes.append(null_size)
    cols = 4
    rows = int(np.ceil((len(sizes) + 1) / cols))
    fig, ax = plt.subplots(rows, cols, figsize=(4.2 * cols, 4.3 * rows))
    ax = np.atleast_2d(ax)
    for a in ax.ravel():
        a.axis("off")
    ax.ravel()[0].imshow(binary, cmap="gray", vmin=0, vmax=1)
    ax.ravel()[0].set_title(f"Binary input  N={int(binary.sum()):,}", fontsize=10)
    se_by_size = {}
    for (_, se), _i in zip(se_sequence(box_se(3)), range(len(df))):
        se_by_size[se.shape[0]] = se
    for a, s in zip(ax.ravel()[1:], sizes):
        o = opening(binary, se_by_size[s])
        a.imshow(o, cmap="gray", vmin=0, vmax=1)
        a.set_title(f"Opened, SE {s}x{s}  N={int(o.sum()):,}" + ("  (null)" if o.sum() == 0 else ""), fontsize=10)
    fig.suptitle(title); fig.tight_layout(); fig.savefig(path, dpi=DPI); plt.close(fig)


def curve_figure(df, title, path, color=C1):
    n_final = int(df.se_size.iloc[-1])
    fig, ax = plt.subplots(1, 2, figsize=(14, 5.2))
    ax[0].plot(df.se_size, df.foreground_pixels, "-o", color=color, ms=3.2, lw=1.2)
    ax[0].set_xlabel("Structuring element size (side length, pixels)")
    ax[0].set_ylabel("Foreground pixels remaining after opening")
    ax[0].set_title("Linear scale"); ax[0].grid(alpha=.3); ax[0].ticklabel_format(axis="y", style="plain")
    ax[0].annotate(f"N = 0 at {n_final}x{n_final}", (n_final, 0), xytext=(-110, 40), textcoords="offset points",
                   arrowprops=dict(arrowstyle="->"), fontsize=10)
    nz = df[df.foreground_pixels > 0]
    ax[1].semilogy(nz.se_size, nz.foreground_pixels, "-o", color=color, ms=3.2, lw=1.2)
    ax[1].set_xlabel("Structuring element size (side length, pixels)")
    ax[1].set_ylabel("Foreground pixels remaining (log scale)")
    ax[1].set_title("Log scale (non-zero points only; N = 0 not representable)"); ax[1].grid(alpha=.3, which="both")
    fig.suptitle(title, fontsize=13); fig.tight_layout(); fig.savefig(path, dpi=DPI); plt.close(fig)


def comparison_figure(dfs, title, path):
    cols = [C1, C2]
    fig, ax = plt.subplots(1, 3, figsize=(20, 5.4))
    for (name, df), c in zip(dfs.items(), cols):
        ax[0].plot(df.se_size, df.foreground_pixels, "-o", ms=2.8, lw=1.2, color=c, label=name)
        ax[1].plot(df.se_size, df.pct_remaining, "-o", ms=2.8, lw=1.2, color=c, label=name)
        nz = df[df.foreground_pixels > 0]
        ax[2].semilogy(nz.se_size, nz.pct_remaining, "-o", ms=2.8, lw=1.2, color=c, label=name)
    labels = ["Foreground pixels remaining", "Foreground remaining (% of original)", "Foreground remaining (% of original, log)"]
    titles = ["Absolute counts", "Normalised", "Normalised, log scale"]
    for a, yl, t in zip(ax, labels, titles):
        a.set_xlabel("Structuring element size (side length, pixels)"); a.set_ylabel(yl)
        a.set_title(t); a.grid(alpha=.3, which="both"); a.legend()
    ax[0].ticklabel_format(axis="y", style="plain")
    fig.suptitle(title, fontsize=13); fig.tight_layout(); fig.savefig(path, dpi=DPI); plt.close(fig)
