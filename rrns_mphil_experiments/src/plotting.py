from __future__ import annotations

import textwrap

import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter


def apply_thesis_plot_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "#4a4a4a",
            "axes.labelcolor": "#222222",
            "axes.titleweight": "bold",
            "axes.titlesize": 13,
            "axes.labelsize": 11,
            "xtick.color": "#333333",
            "ytick.color": "#333333",
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "grid.color": "#b0b0b0",
            "grid.alpha": 0.28,
            "grid.linestyle": "-",
            "legend.frameon": True,
            "legend.framealpha": 0.95,
            "legend.edgecolor": "#d0d0d0",
            "legend.facecolor": "white",
            "font.family": "serif",
            "font.serif": ["Times New Roman", "DejaVu Serif", "Times"],
        }
    )


def style_axes(axis, percent: bool = False) -> None:
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.grid(axis="y", alpha=0.28)
    if percent:
        axis.yaxis.set_major_formatter(PercentFormatter(xmax=1.0, decimals=0))


def annotate_bars(axis, values, fmt: str = "{:.3f}", zero_threshold: float | None = None) -> None:
    y_min, y_max = axis.get_ylim()
    offset = (y_max - y_min) * 0.02
    for patch, value in zip(axis.patches, values):
        if zero_threshold is not None and abs(value) <= zero_threshold:
            continue
        axis.text(
            patch.get_x() + patch.get_width() / 2,
            patch.get_height() + offset,
            fmt.format(value),
            ha="center",
            va="bottom",
            fontsize=9,
            color="#222222",
        )


def wrap_labels(labels: list[str], width: int = 18) -> list[str]:
    return ["\n".join(textwrap.wrap(label, width=width)) for label in labels]
