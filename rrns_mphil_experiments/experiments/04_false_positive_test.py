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
from plotting import annotate_bars, apply_thesis_plot_style, style_axes, wrap_labels
from rns import RNSSystem, encode_rrns
from rrns_checker import check_rrns_codeword


def _system_label(system: RNSSystem, label_index: int) -> str:
    return f"System {chr(ord('A') + label_index)}: {system.describe()}"


def _regime_label(regime: str) -> str:
    labels = {
        "random_interior": "Random interior values",
        "edge_band": "Signed-range edge values",
        "full_balanced_range": "Full balanced signed range",
        "overall": "Overall",
    }
    return labels[regime]


def main() -> None:
    experiment_name = "04_false_positive_test"
    artifacts = ExperimentArtifacts(experiment_name)
    logger = build_logger(experiment_name)
    set_random_seed(DEFAULT_SEED)
    apply_thesis_plot_style()

    systems = [
        RNSSystem(moduli=(17, 19, 23), redundant_modulus=29),
        RNSSystem(moduli=(29, 31, 37), redundant_modulus=41),
    ]
    system_labels = {system.describe(): _system_label(system, index) for index, system in enumerate(systems)}

    raw_rows: list[dict[str, float | int | bool | str]] = []
    summary_rows: list[dict[str, float | int | bool | str]] = []

    for system_index, rrns_system in enumerate(systems):
        system_rng = np.random.default_rng(DEFAULT_SEED + 100 + system_index)
        balanced_limit = rrns_system.balanced_limit
        regimes = {
            "random_interior": system_rng.integers(-int(balanced_limit * 0.8), int(balanced_limit * 0.8) + 1, size=500, dtype=np.int64),
            "edge_band": np.array(
                [
                    -balanced_limit,
                    -balanced_limit + 1,
                    -balanced_limit + 2,
                    -balanced_limit // 2,
                    -1,
                    0,
                    1,
                    balanced_limit // 2,
                    balanced_limit - 2,
                    balanced_limit - 1,
                    balanced_limit,
                ],
                dtype=np.int64,
            ),
            "full_balanced_range": np.arange(-balanced_limit, balanced_limit + 1, dtype=np.int64),
        }

        for regime, values in regimes.items():
            for trial_id, value in enumerate(values):
                codeword = encode_rrns(int(value), rrns_system)
                check = check_rrns_codeword(codeword, rrns_system)
                false_positive = bool(not check.is_valid)
                raw_rows.append(
                    {
                        "system": rrns_system.describe(),
                        "system_label": system_labels[rrns_system.describe()],
                        "regime": regime,
                        "regime_label": _regime_label(regime),
                        "trial_id": trial_id,
                        "value": int(value),
                        "checker_valid": bool(check.is_valid),
                        "false_positive": false_positive,
                        "syndrome": int(check.syndrome if check.syndrome is not None else 0),
                    }
                )

            summary_rows.append(
                {
                    "system": rrns_system.describe(),
                    "system_label": system_labels[rrns_system.describe()],
                    "regime": regime,
                    "regime_label": _regime_label(regime),
                    "num_trials": int(values.size),
                    "accepted_clean_codewords": int(values.size - np.count_nonzero([False])),
                    "false_positive_count": 0,  # updated below after the dataframe is built
                    "false_positive_rate": 0.0,
                    "min_value": int(values.min()),
                    "max_value": int(values.max()),
                }
            )

    raw_df = pd.DataFrame(raw_rows)
    summary_df = pd.DataFrame(summary_rows)
    for row_index in range(summary_df.shape[0]):
        mask = (
            (raw_df["system"] == summary_df.loc[row_index, "system"])
            & (raw_df["regime"] == summary_df.loc[row_index, "regime"])
        )
        group = raw_df.loc[mask]
        summary_df.loc[row_index, "accepted_clean_codewords"] = int(group["checker_valid"].sum())
        summary_df.loc[row_index, "false_positive_count"] = int(group["false_positive"].sum())
        summary_df.loc[row_index, "false_positive_rate"] = float(group["false_positive"].mean())

    overall_rows = []
    for system_label, group in raw_df.groupby("system", sort=False):
        overall_rows.append(
            {
                "system": system_label,
                "system_label": system_labels[system_label],
                "regime": "overall",
                "regime_label": _regime_label("overall"),
                "num_trials": int(group.shape[0]),
                "accepted_clean_codewords": int(group["checker_valid"].sum()),
                "false_positive_count": int(group["false_positive"].sum()),
                "false_positive_rate": float(group["false_positive"].mean()),
                "min_value": int(group["value"].min()),
                "max_value": int(group["value"].max()),
            }
        )
    summary_df = pd.concat([summary_df, pd.DataFrame(overall_rows)], ignore_index=True)

    raw_path = artifacts.raw_output_path("04_false_positive_test_raw.csv")
    table_path = artifacts.table_path("04_false_positive_test_summary.csv")
    figure_path = artifacts.figure_path("04_false_positive_test_profiles.png")
    metadata_path = artifacts.save_json(
        "04_false_positive_test_metadata.json",
        {
            "seed": DEFAULT_SEED,
            "systems": [system.describe() for system in systems],
            "regimes": ["random_interior", "edge_band", "full_balanced_range"],
        },
    )

    raw_df.to_csv(raw_path, index=False)
    thesis_table_df = summary_df.rename(
        columns={
            "system_label": "RRNS System",
            "regime_label": "Validation Regime",
            "num_trials": "Clean Codewords Tested",
            "accepted_clean_codewords": "Accepted Clean Codewords",
            "false_positive_count": "False Positives",
            "false_positive_rate": "False Positive Rate",
            "min_value": "Minimum Value",
            "max_value": "Maximum Value",
        }
    )[
        [
            "RRNS System",
            "Validation Regime",
            "Clean Codewords Tested",
            "Accepted Clean Codewords",
            "False Positives",
            "False Positive Rate",
            "Minimum Value",
            "Maximum Value",
        ]
    ]
    thesis_table_df.to_csv(table_path, index=False)

    plot_df = summary_df[summary_df["regime"] != "overall"].copy()
    pivot_false_positive = plot_df.pivot(index="regime", columns="system", values="false_positive_rate")
    pivot_trials = plot_df.pivot(index="regime", columns="system", values="num_trials")
    regime_order = ["random_interior", "edge_band", "full_balanced_range"]
    pivot_false_positive = pivot_false_positive.reindex(regime_order)
    pivot_trials = pivot_trials.reindex(regime_order)
    pivot_false_positive.index = [_regime_label(regime) for regime in pivot_false_positive.index]
    pivot_trials.index = [_regime_label(regime) for regime in pivot_trials.index]
    pivot_false_positive.columns = [system_labels[column] for column in pivot_false_positive.columns]
    pivot_trials.columns = [system_labels[column] for column in pivot_trials.columns]

    fig, axes = plt.subplots(1, 2, figsize=(12.4, 4.9))
    pivot_false_positive.plot(kind="bar", ax=axes[0], color=["#e45756", "#72b7b2"])
    axes[0].set_ylim(0.0, max(0.01, float(pivot_false_positive.max().max()) * 1.1 if not pivot_false_positive.empty else 0.01))
    axes[0].set_ylabel("False positive rate")
    axes[0].set_title("False Positive Screening Across Clean-Codeword Regimes")
    axes[0].set_xlabel("Validation regime")
    axes[0].set_xticklabels(wrap_labels(list(pivot_false_positive.index), width=16), rotation=0)
    style_axes(axes[0], percent=True)
    axes[0].legend(title="System", loc="upper right")
    annotate_bars(axes[0], [patch.get_height() for patch in axes[0].patches], fmt="{:.2%}", zero_threshold=1e-12)
    if float(pivot_false_positive.max().max()) == 0.0:
        axes[0].text(
            0.5,
            0.88,
            "No false positives observed in any regime.",
            transform=axes[0].transAxes,
            ha="center",
            va="center",
            fontsize=9,
            bbox={"facecolor": "white", "edgecolor": "#d0d0d0", "boxstyle": "round,pad=0.25"},
        )

    pivot_trials.plot(kind="bar", ax=axes[1], color=["#54a24b", "#4c78a8"])
    axes[1].set_ylabel("Clean codewords tested")
    axes[1].set_title("Coverage of Clean-Codeword Validation")
    axes[1].set_xlabel("Validation regime")
    axes[1].set_xticklabels(wrap_labels(list(pivot_trials.index), width=16), rotation=0)
    axes[1].set_yscale("log")
    style_axes(axes[1])
    axes[1].legend(title="System", loc="upper left")
    annotate_bars(axes[1], [patch.get_height() for patch in axes[1].patches], fmt="{:.0f}")

    fig.suptitle("False-Positive Validation of the RRNS Checker on Clean Codewords", fontsize=14, fontweight="bold", y=1.03)
    fig.tight_layout()
    fig.savefig(figure_path, dpi=200, bbox_inches="tight")
    plt.close(fig)

    logger.info("Saved raw outputs to %s", raw_path)
    logger.info("Saved summary table to %s", table_path)
    logger.info("Saved figure to %s", figure_path)
    logger.info("Saved metadata to %s", metadata_path)


if __name__ == "__main__":
    main()
