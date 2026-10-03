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
from convolution import quantized_convolution
from plotting import annotate_bars, apply_thesis_plot_style, style_axes
from quantization import FixedPointFormat
from rns import choose_rrns_system, encode_rrns
from rrns_checker import check_rrns_codeword


def _case_short_label(case_index: int) -> str:
    return f"TC{case_index + 1}"


def main() -> None:
    experiment_name = "02_clean_rns_equivalence"
    artifacts = ExperimentArtifacts(experiment_name)
    logger = build_logger(experiment_name)
    set_random_seed(DEFAULT_SEED)
    apply_thesis_plot_style()

    workloads = [
        {
            "case_id": "tc1_small_low_precision",
            "case_label": "Test Case 1: Small workload (Q4.4)",
            "activation_shape": (6, 6),
            "kernel_shape": (3, 3),
            "activation_range": (-0.9, 0.9),
            "kernel_range": (-0.7, 0.7),
            "format": FixedPointFormat(total_bits=8, frac_bits=4),
        },
        {
            "case_id": "tc2_medium_precision",
            "case_label": "Test Case 2: Medium workload (Q5.5)",
            "activation_shape": (8, 8),
            "kernel_shape": (3, 3),
            "activation_range": (-1.15, 1.15),
            "kernel_range": (-0.95, 0.95),
            "format": FixedPointFormat(total_bits=10, frac_bits=5),
        },
        {
            "case_id": "tc3_large_kernel_high_precision",
            "case_label": "Test Case 3: Large-kernel workload (Q6.6)",
            "activation_shape": (9, 9),
            "kernel_shape": (5, 5),
            "activation_range": (-1.3, 1.3),
            "kernel_range": (-0.85, 0.85),
            "format": FixedPointFormat(total_bits=12, frac_bits=6),
        },
        {
            "case_id": "tc4_near_limit_stress",
            "case_label": "Test Case 4: Near-range stress workload (Q7.5)",
            "activation_shape": (10, 10),
            "kernel_shape": (3, 3),
            "activation_range": (-1.45, 1.45),
            "kernel_range": (-1.1, 1.1),
            "format": FixedPointFormat(total_bits=12, frac_bits=5),
        },
    ]

    rows: list[dict[str, float | int | bool | str]] = []
    summary_rows: list[dict[str, float | int | bool | str]] = []

    for case_index, workload in enumerate(workloads):
        case_rng = np.random.default_rng(DEFAULT_SEED + case_index)
        short_label = _case_short_label(case_index)
        activation_map = case_rng.uniform(
            workload["activation_range"][0],
            workload["activation_range"][1],
            size=workload["activation_shape"],
        )
        kernel = case_rng.uniform(
            workload["kernel_range"][0],
            workload["kernel_range"][1],
            size=workload["kernel_shape"],
        )
        fmt = workload["format"]
        conv_result = quantized_convolution(activation_map, kernel, fmt)

        max_abs_value = int(np.max(np.abs(conv_result.integer_output)))
        rrns_system = choose_rrns_system(max_abs_value)
        balanced_limit = rrns_system.balanced_limit
        logger.info(
            "Case %s uses %s with max |accumulator|=%d and balanced limit=%d.",
            workload["case_id"],
            rrns_system.describe(),
            max_abs_value,
            balanced_limit,
        )

        case_matches = 0
        case_valid_checks = 0
        total_outputs = int(conv_result.integer_output.size)

        for row in range(conv_result.integer_output.shape[0]):
            for col in range(conv_result.integer_output.shape[1]):
                integer_value = int(conv_result.integer_output[row, col])
                codeword = encode_rrns(integer_value, rrns_system)
                check = check_rrns_codeword(codeword, rrns_system)
                integer_match = bool(check.reconstructed_balanced == integer_value)
                checker_valid = bool(check.is_valid)
                case_matches += int(integer_match)
                case_valid_checks += int(checker_valid)
                rows.append(
                    {
                        "case_id": workload["case_id"],
                        "case_short_label": short_label,
                        "case_label": workload["case_label"],
                        "fixed_point_format": fmt.describe(),
                        "rrns_system": rrns_system.describe(),
                        "row": row,
                        "col": col,
                        "float_reference": float(conv_result.float_reference[row, col]),
                        "dequantized_output": float(conv_result.dequantized_output[row, col]),
                        "integer_output": integer_value,
                        "reconstructed_unsigned": check.reconstructed_unsigned,
                        "reconstructed_balanced": check.reconstructed_balanced,
                        "informative_residue_0": codeword[0],
                        "informative_residue_1": codeword[1],
                        "informative_residue_2": codeword[2],
                        "redundant_residue": codeword[3],
                        "checker_valid": checker_valid,
                        "integer_match": integer_match,
                    }
                )

        summary_rows.append(
            {
                "case_id": workload["case_id"],
                "case_short_label": short_label,
                "case_label": workload["case_label"],
                "fixed_point_format": fmt.describe(),
                "rrns_system": rrns_system.describe(),
                "informative_dynamic_range": rrns_system.informative_dynamic_range,
                "balanced_limit": balanced_limit,
                "max_abs_integer_output": max_abs_value,
                "range_margin": int(balanced_limit - max_abs_value),
                "num_outputs": total_outputs,
                "exact_match_rate": case_matches / total_outputs,
                "check_valid_rate": case_valid_checks / total_outputs,
                "all_integer_matches": bool(case_matches == total_outputs),
                "all_checks_valid": bool(case_valid_checks == total_outputs),
                "input_clipped_count": conv_result.input_quantization.clipped_count,
                "kernel_clipped_count": conv_result.kernel_quantization.clipped_count,
            }
        )

    results_df = pd.DataFrame(rows)
    summary_df = pd.DataFrame(summary_rows)

    raw_path = artifacts.raw_output_path("02_clean_rns_equivalence_raw.csv")
    table_path = artifacts.table_path("02_clean_rns_equivalence_summary.csv")
    figure_path = artifacts.figure_path("02_clean_rns_equivalence_stress_summary.png")
    metadata_path = artifacts.save_json(
        "02_clean_rns_equivalence_metadata.json",
        {
            "seed": DEFAULT_SEED,
            "num_cases": len(workloads),
            "cases": [
                {
                    "case_id": workload["case_id"],
                    "activation_shape": workload["activation_shape"],
                    "kernel_shape": workload["kernel_shape"],
                    "activation_range": workload["activation_range"],
                    "kernel_range": workload["kernel_range"],
                    "fixed_point_format": workload["format"].describe(),
                }
                for workload in workloads
            ],
        },
    )

    results_df.to_csv(raw_path, index=False)
    thesis_table_df = summary_df.rename(
        columns={
            "case_short_label": "Case Code",
            "case_label": "Test Case",
            "fixed_point_format": "Fixed-Point Format",
            "rrns_system": "RRNS System",
            "informative_dynamic_range": "Informative Dynamic Range",
            "balanced_limit": "Balanced Signed Limit",
            "max_abs_integer_output": "Observed Max |Output|",
            "range_margin": "Range Margin",
            "num_outputs": "Number of Outputs",
            "exact_match_rate": "Exact Match Rate",
            "check_valid_rate": "Checker Acceptance Rate",
            "all_integer_matches": "All Integer Matches",
            "all_checks_valid": "All Checks Valid",
            "input_clipped_count": "Input Clip Count",
            "kernel_clipped_count": "Kernel Clip Count",
        }
    )
    thesis_table_df.insert(3, "Feature-Map Size", [f"{item['activation_shape'][0]}x{item['activation_shape'][1]}" for item in workloads])
    thesis_table_df.insert(4, "Kernel Size", [f"{item['kernel_shape'][0]}x{item['kernel_shape'][1]}" for item in workloads])
    thesis_table_df = thesis_table_df[
        [
            "Case Code",
            "Test Case",
            "Feature-Map Size",
            "Kernel Size",
            "Fixed-Point Format",
            "RRNS System",
            "Informative Dynamic Range",
            "Balanced Signed Limit",
            "Observed Max |Output|",
            "Range Margin",
            "Number of Outputs",
            "Exact Match Rate",
            "Checker Acceptance Rate",
            "All Integer Matches",
            "All Checks Valid",
            "Input Clip Count",
            "Kernel Clip Count",
        ]
    ]
    thesis_table_df.to_csv(table_path, index=False)

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.8))
    case_labels = summary_df["case_short_label"].tolist()

    bars = axes[0].bar(case_labels, summary_df["max_abs_integer_output"], color="#4c78a8", width=0.62, label="Observed max |output|")
    axes[0].plot(case_labels, summary_df["balanced_limit"], color="#e45756", marker="o", linewidth=2.4, label="Balanced limit")
    axes[0].set_title("Observed Output Range Versus RRNS Balanced Limit")
    axes[0].set_ylabel("Integer magnitude")
    axes[0].set_xlabel("Test case")
    style_axes(axes[0])
    axes[0].legend(loc="upper left")
    annotate_bars(axes[0], summary_df["max_abs_integer_output"].tolist(), fmt="{:.0f}")
    for x_position, margin in zip(case_labels, summary_df["range_margin"].tolist()):
        axes[0].annotate(
            f"margin {margin}",
            xy=(x_position, float(summary_df.loc[summary_df["case_short_label"] == x_position, "balanced_limit"].iloc[0])),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center",
            fontsize=8,
            color="#b03a2e",
        )

    axes[1].plot(case_labels, summary_df["exact_match_rate"], color="#54a24b", marker="o", linewidth=2.4, label="Exact reconstruction")
    axes[1].plot(case_labels, summary_df["check_valid_rate"], color="#f58518", marker="s", linewidth=2.0, linestyle="--", label="Checker validity")
    axes[1].set_ylim(0.94, 1.01)
    axes[1].set_title("Clean-Case Exact Equivalence Across Test Cases")
    axes[1].set_ylabel("Rate")
    axes[1].set_xlabel("Test case")
    style_axes(axes[1], percent=True)
    axes[1].legend(loc="lower left")
    for case_label, exact_rate, check_rate in zip(
        case_labels,
        summary_df["exact_match_rate"].tolist(),
        summary_df["check_valid_rate"].tolist(),
    ):
        axes[1].annotate(f"{exact_rate:.3f}", (case_label, exact_rate), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8)
        axes[1].annotate(f"{check_rate:.3f}", (case_label, check_rate), textcoords="offset points", xytext=(0, -16), ha="center", fontsize=8)

    fig.suptitle("Clean RRNS Reconstruction Across Representative Convolution Workloads", fontsize=14, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(figure_path, dpi=200, bbox_inches="tight")
    plt.close(fig)

    logger.info("Saved raw outputs to %s", raw_path)
    logger.info("Saved summary table to %s", table_path)
    logger.info("Saved figure to %s", figure_path)
    logger.info("Saved metadata to %s", metadata_path)


if __name__ == "__main__":
    main()
