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
from fault_injection import inject_residue_fault
from plotting import annotate_bars, apply_thesis_plot_style, style_axes, wrap_labels
from rns import RNSSystem, encode_rrns
from rrns_checker import check_rrns_codeword


def _system_label(system: RNSSystem, label_index: int) -> str:
    return f"System {chr(ord('A') + label_index)}: {system.describe()}"


def _fault_pattern_label(pattern: str) -> str:
    labels = {
        "single_informative": "Single informative-channel fault",
        "single_redundant": "Single redundant-channel fault",
        "double_informative": "Two informative-channel faults",
        "informative_plus_redundant": "Informative + redundant fault",
        "double_random": "Two-channel mixed fault",
        "overall": "Overall",
    }
    return labels[pattern]


def _channel_bit_width(modulus: int) -> int:
    return max(1, int(np.ceil(np.log2(modulus))))


def _apply_faults(
    clean_codeword: tuple[int, ...],
    moduli: tuple[int, ...],
    target_indices: list[int],
    modes: list[str],
    rng: np.random.Generator,
) -> tuple[tuple[int, ...], list[dict[str, int | str | None]]]:
    corrupted = tuple(clean_codeword)
    records: list[dict[str, int | str | None]] = []
    for target_index, mode in zip(target_indices, modes):
        corrupted, record = inject_residue_fault(
            corrupted,
            moduli,
            target_index=target_index,
            mode=mode,
            rng=rng,
        )
        records.append(
            {
                "target_index": record.target_index,
                "modulus": record.modulus,
                "original_value": record.original_value,
                "corrupted_value": record.corrupted_value,
                "mode": record.mode,
                "delta": record.delta,
                "bit_index": record.bit_index,
            }
        )
    return corrupted, records


def _pick_targets(system: RNSSystem, fault_pattern: str, rng: np.random.Generator) -> list[int]:
    informative_indices = list(range(len(system.moduli)))
    redundant_index = len(system.moduli)
    all_indices = informative_indices + [redundant_index]

    if fault_pattern == "single_informative":
        return [int(rng.choice(informative_indices))]
    if fault_pattern == "single_redundant":
        return [redundant_index]
    if fault_pattern == "double_informative":
        selected = rng.choice(informative_indices, size=2, replace=False)
        return [int(value) for value in selected]
    if fault_pattern == "informative_plus_redundant":
        return [int(rng.choice(informative_indices)), redundant_index]
    if fault_pattern == "double_random":
        selected = rng.choice(all_indices, size=2, replace=False)
        return [int(value) for value in selected]
    raise ValueError(f"Unsupported fault pattern: {fault_pattern}")


def main() -> None:
    experiment_name = "03_rrns_fault_injection"
    artifacts = ExperimentArtifacts(experiment_name)
    logger = build_logger(experiment_name)
    rng = set_random_seed(DEFAULT_SEED)
    apply_thesis_plot_style()

    systems = [
        RNSSystem(moduli=(17, 19, 23), redundant_modulus=29),
        RNSSystem(moduli=(29, 31, 37), redundant_modulus=41),
    ]
    system_labels = {system.describe(): _system_label(system, index) for index, system in enumerate(systems)}
    fault_patterns = [
        "single_informative",
        "single_redundant",
        "double_informative",
        "informative_plus_redundant",
        "double_random",
    ]
    trials_per_pattern = 240
    modes = ["delta", "bit_flip", "random"]

    raw_rows: list[dict[str, float | int | bool | str]] = []
    for system_index, rrns_system in enumerate(systems):
        system_rng = np.random.default_rng(DEFAULT_SEED + 50 + system_index)
        value_limit = int(rrns_system.balanced_limit * 0.75)
        system_values = system_rng.integers(-value_limit, value_limit + 1, size=trials_per_pattern * len(fault_patterns), dtype=np.int64)

        for pattern_index, fault_pattern in enumerate(fault_patterns):
            for local_trial in range(trials_per_pattern):
                global_trial = pattern_index * trials_per_pattern + local_trial
                value = int(system_values[global_trial])
                clean_codeword = encode_rrns(value, rrns_system)
                target_indices = _pick_targets(rrns_system, fault_pattern, system_rng)
                fault_modes = [modes[(global_trial + offset) % len(modes)] for offset in range(len(target_indices))]
                corrupted_codeword, fault_records = _apply_faults(
                    clean_codeword,
                    rrns_system.all_moduli,
                    target_indices=target_indices,
                    modes=fault_modes,
                    rng=system_rng,
                )
                check = check_rrns_codeword(corrupted_codeword, rrns_system)
                reconstructed_balanced = int(check.reconstructed_balanced)
                detected = bool(not check.is_valid)
                output_changed = bool(reconstructed_balanced != value)
                harmful_undetected = bool(output_changed and not detected)

                raw_rows.append(
                    {
                        "system": rrns_system.describe(),
                        "system_label": system_labels[rrns_system.describe()],
                        "trial_id": global_trial,
                        "fault_pattern": fault_pattern,
                        "fault_pattern_label": _fault_pattern_label(fault_pattern),
                        "num_faulted_channels": len(target_indices),
                        "value": value,
                        "target_indices": "|".join(str(index) for index in target_indices),
                        "target_segment_signature": "|".join(
                            "redundant" if index == len(rrns_system.moduli) else "informative" for index in target_indices
                        ),
                        "fault_modes": "|".join(fault_modes),
                        "detected": detected,
                        "output_changed": output_changed,
                        "harmful_undetected": harmful_undetected,
                        "syndrome": int(check.syndrome if check.syndrome is not None else 0),
                        "clean_value": value,
                        "reconstructed_balanced": reconstructed_balanced,
                        "absolute_output_error": abs(reconstructed_balanced - value),
                        "fault_record_count": len(fault_records),
                    }
                )

    raw_df = pd.DataFrame(raw_rows)

    summary_rows: list[dict[str, float | int | str]] = []
    for (system_label, fault_pattern), group in raw_df.groupby(["system", "fault_pattern"], sort=False):
        system = next(system for system in systems if system.describe() == system_label)
        informative_bits = sum(_channel_bit_width(modulus) for modulus in system.moduli)
        redundant_bits = _channel_bit_width(system.redundant_modulus or 1)
        total_bits = informative_bits + redundant_bits
        summary_rows.append(
            {
                "system": system_label,
                "system_label": system_labels[system_label],
                "fault_pattern": fault_pattern,
                "fault_pattern_label": _fault_pattern_label(fault_pattern),
                "num_trials": int(group.shape[0]),
                "detected_count": int(group["detected"].sum()),
                "detection_rate": float(group["detected"].mean()),
                "output_changed_count": int(group["output_changed"].sum()),
                "output_changed_rate": float(group["output_changed"].mean()),
                "harmful_undetected_count": int(group["harmful_undetected"].sum()),
                "harmful_undetected_rate": float(group["harmful_undetected"].mean()),
                "mean_abs_output_error": float(group["absolute_output_error"].mean()),
                "max_abs_output_error": float(group["absolute_output_error"].max()),
                "informative_bits": informative_bits,
                "redundant_bits": redundant_bits,
                "total_bits": total_bits,
                "redundancy_overhead_ratio": float(redundant_bits / informative_bits),
            }
        )
    for system_label, group in raw_df.groupby("system", sort=False):
        system = next(system for system in systems if system.describe() == system_label)
        informative_bits = sum(_channel_bit_width(modulus) for modulus in system.moduli)
        redundant_bits = _channel_bit_width(system.redundant_modulus or 1)
        total_bits = informative_bits + redundant_bits
        summary_rows.append(
            {
                "system": system_label,
                "system_label": system_labels[system_label],
                "fault_pattern": "overall",
                "fault_pattern_label": _fault_pattern_label("overall"),
                "num_trials": int(group.shape[0]),
                "detected_count": int(group["detected"].sum()),
                "detection_rate": float(group["detected"].mean()),
                "output_changed_count": int(group["output_changed"].sum()),
                "output_changed_rate": float(group["output_changed"].mean()),
                "harmful_undetected_count": int(group["harmful_undetected"].sum()),
                "harmful_undetected_rate": float(group["harmful_undetected"].mean()),
                "mean_abs_output_error": float(group["absolute_output_error"].mean()),
                "max_abs_output_error": float(group["absolute_output_error"].max()),
                "informative_bits": informative_bits,
                "redundant_bits": redundant_bits,
                "total_bits": total_bits,
                "redundancy_overhead_ratio": float(redundant_bits / informative_bits),
            }
        )
    summary_df = pd.DataFrame(summary_rows)

    raw_path = artifacts.raw_output_path("03_rrns_fault_injection_raw.csv")
    table_path = artifacts.table_path("03_rrns_fault_injection_summary.csv")
    figure_path = artifacts.figure_path("03_rrns_fault_injection_detection_profiles.png")
    metadata_path = artifacts.save_json(
        "03_rrns_fault_injection_metadata.json",
        {
            "seed": DEFAULT_SEED,
            "trials_per_pattern": trials_per_pattern,
            "fault_patterns": fault_patterns,
            "systems": [system.describe() for system in systems],
        },
    )

    raw_df.to_csv(raw_path, index=False)
    thesis_table_df = summary_df.rename(
        columns={
            "system_label": "RRNS System",
            "fault_pattern_label": "Fault Pattern",
            "num_trials": "Trials",
            "detected_count": "Detected Faults",
            "detection_rate": "Detection Rate",
            "output_changed_count": "Output-Changed Faults",
            "output_changed_rate": "Output-Change Rate",
            "harmful_undetected_count": "Harmful Undetected Faults",
            "harmful_undetected_rate": "Harmful Undetected Rate",
            "mean_abs_output_error": "Mean Absolute Output Error",
            "max_abs_output_error": "Maximum Absolute Output Error",
            "informative_bits": "Informative Bits",
            "redundant_bits": "Redundant Bits",
            "total_bits": "Total Bits",
            "redundancy_overhead_ratio": "Redundancy Overhead Ratio",
        }
    )[
        [
            "RRNS System",
            "Fault Pattern",
            "Trials",
            "Detected Faults",
            "Detection Rate",
            "Output-Changed Faults",
            "Output-Change Rate",
            "Harmful Undetected Faults",
            "Harmful Undetected Rate",
            "Mean Absolute Output Error",
            "Maximum Absolute Output Error",
            "Informative Bits",
            "Redundant Bits",
            "Total Bits",
            "Redundancy Overhead Ratio",
        ]
    ]
    thesis_table_df.to_csv(table_path, index=False)

    plot_df = summary_df[summary_df["fault_pattern"] != "overall"].copy()
    pivot_detection = plot_df.pivot(index="fault_pattern", columns="system", values="detection_rate")
    pivot_undetected = plot_df.pivot(index="fault_pattern", columns="system", values="harmful_undetected_rate")
    pivot_detection = pivot_detection.reindex(fault_patterns)
    pivot_undetected = pivot_undetected.reindex(fault_patterns)
    pivot_detection.index = [_fault_pattern_label(pattern) for pattern in pivot_detection.index]
    pivot_undetected.index = [_fault_pattern_label(pattern) for pattern in pivot_undetected.index]
    pivot_detection.columns = [system_labels[column] for column in pivot_detection.columns]
    pivot_undetected.columns = [system_labels[column] for column in pivot_undetected.columns]

    fig, axes = plt.subplots(1, 2, figsize=(13.2, 4.9))
    pivot_detection.plot(kind="bar", ax=axes[0], color=["#4c78a8", "#f58518"])
    axes[0].set_ylim(0.0, 1.06)
    axes[0].set_ylabel("Detection rate")
    axes[0].set_title("Detection Rate by RRNS System and Fault Pattern")
    axes[0].set_xlabel("Injected fault pattern")
    axes[0].set_xticklabels(wrap_labels(list(pivot_detection.index), width=16), rotation=0)
    style_axes(axes[0], percent=True)
    axes[0].legend(title="System", loc="lower left")
    for patch in axes[0].patches:
        value = patch.get_height()
        if value >= 0.9999:
            continue
        axes[0].text(
            patch.get_x() + patch.get_width() / 2,
            value + 0.012,
            f"{value:.2%}",
            ha="center",
            va="bottom",
            fontsize=9,
            color="#222222",
        )

    pivot_undetected.plot(kind="bar", ax=axes[1], color=["#e45756", "#72b7b2"])
    axes[1].set_ylim(0.0, max(0.05, float(pivot_undetected.max().max()) * 1.18))
    axes[1].set_ylabel("Harmful undetected rate")
    axes[1].set_title("Harmful Undetected Fault Exposure Under Harder Fault Patterns")
    axes[1].set_xlabel("Injected fault pattern")
    axes[1].set_xticklabels(wrap_labels(list(pivot_undetected.index), width=16), rotation=0)
    style_axes(axes[1], percent=True)
    axes[1].legend(title="System", loc="upper left")
    annotate_bars(axes[1], [patch.get_height() for patch in axes[1].patches], fmt="{:.2%}", zero_threshold=1e-12)

    fig.suptitle("RRNS Checker Behaviour Under Single- and Multi-Channel Fault Patterns", fontsize=14, fontweight="bold", y=1.03)
    fig.tight_layout()
    fig.savefig(figure_path, dpi=200, bbox_inches="tight")
    plt.close(fig)

    logger.info("Saved raw outputs to %s", raw_path)
    logger.info("Saved summary table to %s", table_path)
    logger.info("Saved figure to %s", figure_path)
    logger.info("Saved metadata to %s", metadata_path)


if __name__ == "__main__":
    main()
