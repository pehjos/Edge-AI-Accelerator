from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
MPLCONFIG_DIR = PROJECT_ROOT / ".mplconfig"
MPLCONFIG_DIR.mkdir(exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPLCONFIG_DIR))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import DEFAULT_SEED, ExperimentArtifacts, build_logger, set_random_seed
from metrics import compute_error_metrics
from plotting import apply_thesis_plot_style, style_axes
from quantization import FixedPointFormat, quantize


def main() -> None:
    experiment_name = "01_quantization_experiment"
    artifacts = ExperimentArtifacts(experiment_name)
    logger = build_logger(experiment_name)
    rng = set_random_seed(DEFAULT_SEED)
    apply_thesis_plot_style()

    base_grid = np.linspace(-1.5, 1.5, 49, dtype=np.float64).reshape(7, 7)
    sample = base_grid + rng.normal(loc=0.0, scale=0.05, size=base_grid.shape)

    formats = [
        FixedPointFormat(total_bits=8, frac_bits=4),
        FixedPointFormat(total_bits=10, frac_bits=5),
        FixedPointFormat(total_bits=12, frac_bits=6),
    ]

    raw_rows: list[dict[str, float | int | str]] = []
    summary_rows: list[dict[str, float | int | str]] = []

    fig, axes = plt.subplots(1, len(formats), figsize=(5.2 * len(formats), 4.4), sharey=True)
    axes = np.atleast_1d(axes)
    palette = ["#4c78a8", "#f58518", "#54a24b"]

    for axis, fmt, color in zip(axes, formats, palette):
        quantized = quantize(sample, fmt)
        metrics = compute_error_metrics(sample, quantized.dequantized)
        format_label = fmt.describe()
        logger.info("Processed format %s with %d clipped values.", format_label, quantized.clipped_count)

        for index, (original, integer_value, dequantized, clipped) in enumerate(
            zip(
                sample.flatten(),
                quantized.quantized_int.flatten(),
                quantized.dequantized.flatten(),
                quantized.clip_mask.flatten(),
            )
        ):
            raw_rows.append(
                {
                    "format": format_label,
                    "sample_index": index,
                    "original": float(original),
                    "quantized_int": int(integer_value),
                    "dequantized": float(dequantized),
                    "error": float(dequantized - original),
                    "clipped": bool(clipped),
                }
            )

        summary_rows.append(
            {
                "Fixed-Point Format": format_label,
                "Total Bits": fmt.total_bits,
                "Fractional Bits": fmt.frac_bits,
                "Scaling Factor": fmt.scale,
                "Clipped Samples": quantized.clipped_count,
                "Mean Absolute Error": metrics["mae"],
                "Mean Squared Error": metrics["mse"],
                "RMSE": metrics["rmse"],
                "Maximum Absolute Error": metrics["max_abs_error"],
                "Mean Bias": metrics["mean_bias"],
            }
        )

        axis.scatter(
            sample.flatten(),
            quantized.dequantized.flatten(),
            alpha=0.82,
            s=28,
            color=color,
            edgecolors="white",
            linewidths=0.4,
        )
        lower = float(sample.min())
        upper = float(sample.max())
        axis.plot([lower, upper], [lower, upper], linestyle="--", linewidth=1.2, color="#666666")
        axis.set_title(f"Quantization response for {format_label}")
        axis.set_xlabel("Original value")
        axis.set_ylabel("Dequantized value")
        axis.text(
            0.04,
            0.95,
            f"RMSE = {metrics['rmse']:.4f}\nMAE = {metrics['mae']:.4f}",
            transform=axis.transAxes,
            ha="left",
            va="top",
            fontsize=9,
            bbox={"facecolor": "white", "edgecolor": "#d0d0d0", "boxstyle": "round,pad=0.25"},
        )
        style_axes(axis)

    raw_df = pd.DataFrame(raw_rows)
    summary_df = pd.DataFrame(summary_rows)

    raw_path = artifacts.raw_output_path("01_quantization_raw.csv")
    table_path = artifacts.table_path("01_quantization_summary.csv")
    figure_path = artifacts.figure_path("01_quantization_scatter.png")
    metadata_path = artifacts.save_json(
        "01_quantization_metadata.json",
        {
            "seed": DEFAULT_SEED,
            "sample_shape": sample.shape,
            "formats": [fmt.describe() for fmt in formats],
        },
    )

    raw_df.to_csv(raw_path, index=False)
    summary_df.to_csv(table_path, index=False)
    fig.suptitle("Quantization Precision and Reconstruction Accuracy", fontsize=14, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(figure_path, dpi=200, bbox_inches="tight")
    plt.close(fig)

    logger.info("Saved raw outputs to %s", raw_path)
    logger.info("Saved summary table to %s", table_path)
    logger.info("Saved figure to %s", figure_path)
    logger.info("Saved metadata to %s", metadata_path)


if __name__ == "__main__":
    main()
