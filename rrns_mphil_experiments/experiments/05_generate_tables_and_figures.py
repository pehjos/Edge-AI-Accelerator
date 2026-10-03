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
from matplotlib.ticker import PercentFormatter
import pandas as pd

from config import ExperimentArtifacts, TABLES_DIR, build_logger
from plotting import annotate_bars, apply_thesis_plot_style, style_axes, wrap_labels


def _integrity_label(experiment: str, metric: str) -> str:
    experiment_labels = {
        "clean_rns_equivalence": "Clean equivalence",
        "fault_injection": "Fault injection",
        "false_positive_test": "False-positive validation",
        "hardware_validation": "Hardware validation",
    }
    return f"{experiment_labels.get(experiment, experiment)}: {metric}"


def main() -> None:
    experiment_name = "05_generate_tables_and_figures"
    artifacts = ExperimentArtifacts(experiment_name)
    logger = build_logger(experiment_name)
    apply_thesis_plot_style()

    table_files = sorted(
        path
        for path in TABLES_DIR.glob("*.csv")
        if path.name not in {"05_chapter4_master_tables.csv", "05_chapter4_metric_snapshot.csv"}
    )

    combined_tables: list[pd.DataFrame] = []
    for path in table_files:
        table = pd.read_csv(path)
        table.insert(0, "source_table", path.stem)
        combined_tables.append(table)
        logger.info("Loaded table %s", path)

    if combined_tables:
        master_df = pd.concat(combined_tables, ignore_index=True, sort=False)
    else:
        master_df = pd.DataFrame(columns=["source_table"])
        logger.warning("No source tables found. Creating an empty master table.")

    snapshot_rows: list[dict[str, float | str]] = []

    quantization_path = TABLES_DIR / "01_quantization_summary.csv"
    if quantization_path.exists():
        quant_df = pd.read_csv(quantization_path)
        for _, row in quant_df.iterrows():
            snapshot_rows.append(
                {
                    "experiment": "quantization",
                    "label": str(row["Fixed-Point Format"]),
                    "metric": "RMSE",
                    "value": float(row["RMSE"]),
                }
            )

    clean_equivalence_path = TABLES_DIR / "02_clean_rns_equivalence_summary.csv"
    if clean_equivalence_path.exists():
        clean_df = pd.read_csv(clean_equivalence_path)
        snapshot_rows.append(
            {
                "experiment": "clean_rns_equivalence",
                "label": "Worst case across test cases",
                "metric": "Minimum exact-match rate",
                "value": float(clean_df["Exact Match Rate"].min()),
            }
        )
        snapshot_rows.append(
            {
                "experiment": "clean_rns_equivalence",
                "label": "Worst case across test cases",
                "metric": "Minimum checker-acceptance rate",
                "value": float(clean_df["Checker Acceptance Rate"].min()),
            }
        )

    fault_detection_path = TABLES_DIR / "03_rrns_fault_injection_summary.csv"
    if fault_detection_path.exists():
        fault_df = pd.read_csv(fault_detection_path)
        single_info = fault_df[fault_df["Fault Pattern"] == "Single informative-channel fault"]
        double_info = fault_df[fault_df["Fault Pattern"] == "Two informative-channel faults"]
        if not single_info.empty:
            snapshot_rows.append(
                {
                    "experiment": "fault_injection",
                    "label": "Single informative-channel faults",
                    "metric": "Minimum detection rate",
                    "value": float(single_info["Detection Rate"].min()),
                }
            )
        if not double_info.empty:
            snapshot_rows.append(
                {
                    "experiment": "fault_injection",
                    "label": "Two informative-channel faults",
                    "metric": "Maximum harmful-undetected rate",
                    "value": float(double_info["Harmful Undetected Rate"].max()),
                }
            )

    false_positive_path = TABLES_DIR / "04_false_positive_test_summary.csv"
    if false_positive_path.exists():
        fp_df = pd.read_csv(false_positive_path)
        overall_fp = fp_df[fp_df["Validation Regime"] == "Overall"]
        source = overall_fp if not overall_fp.empty else fp_df
        snapshot_rows.append(
            {
                "experiment": "false_positive_test",
                "label": "Worst case across validation regimes",
                "metric": "Maximum false-positive rate",
                "value": float(source["False Positive Rate"].max()),
            }
        )

    hardware_validation_path = TABLES_DIR / "06_verilog_hardware_evaluation_summary.csv"
    if hardware_validation_path.exists():
        hardware_df = pd.read_csv(hardware_validation_path)
        snapshot_rows.append(
            {
                "experiment": "hardware_validation",
                "label": "Across validated RTL systems",
                "metric": "Minimum simulation pass rate",
                "value": float(hardware_df["Simulation Pass Rate"].min()),
            }
        )
        snapshot_rows.append(
            {
                "experiment": "hardware_validation",
                "label": "Across validated RTL systems",
                "metric": "Maximum residue-bit overhead ratio",
                "value": float(hardware_df["Residue Bit Overhead Ratio"].max()),
            }
        )

    snapshot_df = pd.DataFrame(snapshot_rows, columns=["experiment", "label", "metric", "value"])
    snapshot_df = snapshot_df.rename(
        columns={
            "experiment": "Experiment",
            "label": "Evaluation Scope",
            "metric": "Metric",
            "value": "Value",
        }
    )

    master_path = artifacts.table_path("05_chapter4_master_tables.csv")
    snapshot_path = artifacts.table_path("05_chapter4_metric_snapshot.csv")
    figure_path = artifacts.figure_path("05_chapter4_summary_metrics.png")

    master_df.to_csv(master_path, index=False)
    snapshot_df.to_csv(snapshot_path, index=False)

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.8))
    if snapshot_df.empty:
        for axis in axes:
            axis.text(0.5, 0.5, "Run experiments 01-04 to populate summary metrics.", ha="center", va="center")
            axis.set_axis_off()
    else:
        quant_df = snapshot_df[snapshot_df["Experiment"] == "quantization"].copy()
        integrity_df = snapshot_df[snapshot_df["Experiment"] != "quantization"].copy()

        quant_bars = axes[0].bar(quant_df["Evaluation Scope"], quant_df["Value"], color=["#4c78a8", "#f58518", "#54a24b"], width=0.62)
        axes[0].set_ylabel("RMSE")
        axes[0].set_title("Quantization Error by Fixed-Point Format")
        axes[0].set_xlabel("Fixed-point format")
        style_axes(axes[0])
        annotate_bars(axes[0], quant_df["Value"].tolist(), fmt="{:.4f}")

        integrity_labels = [
            _integrity_label(str(row["Experiment"]), str(row["Metric"]))
            for _, row in integrity_df.iterrows()
        ]
        integrity_palette = ["#72b7b2", "#e45756", "#4c78a8", "#f58518", "#54a24b", "#b279a2"]
        integrity_colors = [integrity_palette[index % len(integrity_palette)] for index in range(len(integrity_df))]
        axes[1].barh(range(len(integrity_df)), integrity_df["Value"], color=integrity_colors)
        axes[1].set_yticks(range(len(integrity_df)))
        axes[1].set_yticklabels(wrap_labels(integrity_labels, width=24))
        axes[1].set_xlim(0.0, 1.05)
        axes[1].set_xlabel("Rate")
        axes[1].set_title("Integrity and Checker Metrics")
        axes[1].xaxis.set_major_formatter(PercentFormatter(xmax=1.0, decimals=0))
        style_axes(axes[1])
        for y_position, value in enumerate(integrity_df["Value"].tolist()):
            axes[1].text(value + 0.015, y_position, f"{value:.2%}", va="center", fontsize=9)

    fig.suptitle("Chapter Four Summary Metrics", fontsize=14, fontweight="bold", y=1.03)
    fig.tight_layout()
    fig.savefig(figure_path, dpi=200, bbox_inches="tight")
    plt.close(fig)

    logger.info("Saved combined master table to %s", master_path)
    logger.info("Saved metric snapshot to %s", snapshot_path)
    logger.info("Saved summary figure to %s", figure_path)


if __name__ == "__main__":
    main()
