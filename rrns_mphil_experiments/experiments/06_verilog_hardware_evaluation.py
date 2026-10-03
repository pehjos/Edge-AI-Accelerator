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
import pandas as pd
from matplotlib.ticker import PercentFormatter

from config import ExperimentArtifacts, VERILOG_DIR, build_logger
from hardware_metrics import summarize_hardware_system
from plotting import annotate_bars, apply_thesis_plot_style, style_axes
from rns import RNSSystem


def _system_label(system: RNSSystem, label_index: int) -> str:
    return f"System {chr(ord('A') + label_index)}: {system.describe()}"


def main() -> None:
    experiment_name = "06_verilog_hardware_evaluation"
    artifacts = ExperimentArtifacts(experiment_name)
    logger = build_logger(experiment_name)
    apply_thesis_plot_style()

    systems = [
        ("system_a", RNSSystem(moduli=(17, 19, 23), redundant_modulus=29)),
        ("system_b", RNSSystem(moduli=(29, 31, 37), redundant_modulus=41)),
    ]

    raw_rows: list[dict[str, int | float | bool | str]] = []
    summary_rows: list[dict[str, int | float | bool | str]] = []

    for index, (system_key, system) in enumerate(systems):
        system_label = _system_label(system, index)
        log_path = VERILOG_DIR / "logs" / f"tb_self_checking_rrns_mac_{system_key}.log"
        waveform_path = VERILOG_DIR / "waveforms" / f"tb_self_checking_rrns_mac_{system_key}.vcd"
        rtl_top_path = VERILOG_DIR / "rtl" / f"self_checking_rrns_mac_{system_key}.sv"
        checker_path = VERILOG_DIR / "rtl" / f"rrns_checker_{system_key}.sv"
        testbench_path = VERILOG_DIR / "tb" / f"tb_self_checking_rrns_mac_{system_key}.sv"

        summary = summarize_hardware_system(
            system_label=system_label,
            system=system,
            log_path=log_path,
            waveform_path=waveform_path,
        )

        raw_rows.append(
            {
                "system_key": system_key,
                "system_label": system_label,
                "rrns_system": system.describe(),
                "informative_moduli": ",".join(str(modulus) for modulus in system.moduli),
                "redundant_modulus": int(system.redundant_modulus or 0),
                "informative_dynamic_range": system.informative_dynamic_range,
                "balanced_signed_limit": system.balanced_limit,
                "informative_bits": summary.informative_bits,
                "redundant_bits": summary.redundant_bits,
                "total_bits": summary.total_bits,
                "informative_channels": summary.informative_channels,
                "redundant_channels": summary.redundant_channels,
                "total_channels": summary.total_channels,
                "residue_bit_overhead_ratio": summary.residue_bit_overhead_ratio,
                "channel_overhead_ratio": summary.channel_overhead_ratio,
                "coding_efficiency": summary.coding_efficiency,
                "checker_input_width": summary.checker_input_width,
                "testbench_cases": summary.testbench.testbench_cases,
                "pass_checks": summary.testbench.pass_checks,
                "fail_checks": summary.testbench.fail_checks,
                "total_checks": summary.testbench.total_checks,
                "simulation_pass_rate": summary.testbench.pass_rate,
                "simulation_verdict": summary.testbench.simulation_verdict,
                "waveform_dump_reported": summary.testbench.waveform_dump_reported,
                "waveform_exists": summary.waveform_exists,
                "finish_reported": summary.testbench.finish_reported,
                "rtl_top_path": str(rtl_top_path),
                "checker_path": str(checker_path),
                "testbench_path": str(testbench_path),
                "log_path": str(log_path),
                "waveform_path": str(waveform_path),
            }
        )

        summary_rows.append(
            {
                "system_label": system_label,
                "rrns_system": system.describe(),
                "informative_moduli": "(" + ", ".join(str(modulus) for modulus in system.moduli) + ")",
                "redundant_modulus": f"({system.redundant_modulus})",
                "informative_dynamic_range": system.informative_dynamic_range,
                "balanced_signed_limit": system.balanced_limit,
                "informative_channels": summary.informative_channels,
                "total_channels": summary.total_channels,
                "channel_overhead_ratio": summary.channel_overhead_ratio,
                "informative_bits": summary.informative_bits,
                "redundant_bits": summary.redundant_bits,
                "total_bits": summary.total_bits,
                "residue_bit_overhead_ratio": summary.residue_bit_overhead_ratio,
                "coding_efficiency": summary.coding_efficiency,
                "testbench_cases": summary.testbench.testbench_cases,
                "pass_checks": summary.testbench.pass_checks,
                "fail_checks": summary.testbench.fail_checks,
                "simulation_pass_rate": summary.testbench.pass_rate,
                "simulation_verdict": summary.testbench.simulation_verdict,
                "waveform_available": bool(summary.testbench.waveform_dump_reported and summary.waveform_exists),
            }
        )

    raw_df = pd.DataFrame(raw_rows)
    summary_df = pd.DataFrame(summary_rows)

    raw_path = artifacts.raw_output_path("06_verilog_hardware_evaluation_raw.csv")
    table_path = artifacts.table_path("06_verilog_hardware_evaluation_summary.csv")
    figure_path = artifacts.figure_path("06_verilog_hardware_evaluation_summary.png")
    metadata_path = artifacts.save_json(
        "06_verilog_hardware_evaluation_metadata.json",
        {
            "systems": [system.describe() for _, system in systems],
            "source_logs": [str(VERILOG_DIR / "logs" / f"tb_self_checking_rrns_mac_{system_key}.log") for system_key, _ in systems],
            "source_waveforms": [str(VERILOG_DIR / "waveforms" / f"tb_self_checking_rrns_mac_{system_key}.vcd") for system_key, _ in systems],
        },
    )

    raw_df.to_csv(raw_path, index=False)
    thesis_table_df = summary_df.rename(
        columns={
            "system_label": "RRNS System",
            "rrns_system": "RRNS Configuration",
            "informative_moduli": "Informative Moduli",
            "redundant_modulus": "Redundant Modulus",
            "informative_dynamic_range": "Informative Dynamic Range",
            "balanced_signed_limit": "Balanced Signed Limit",
            "informative_channels": "Informative Channels",
            "total_channels": "Total Channels",
            "channel_overhead_ratio": "Channel Overhead Ratio",
            "informative_bits": "Informative Bits",
            "redundant_bits": "Redundant Bits",
            "total_bits": "Total Residue Bits",
            "residue_bit_overhead_ratio": "Residue Bit Overhead Ratio",
            "coding_efficiency": "Coding Efficiency",
            "testbench_cases": "Testbench Cases",
            "pass_checks": "PASS Checks",
            "fail_checks": "FAIL Checks",
            "simulation_pass_rate": "Simulation Pass Rate",
            "simulation_verdict": "Simulation Verdict",
            "waveform_available": "Waveform Available",
        }
    )[
        [
            "RRNS System",
            "RRNS Configuration",
            "Informative Moduli",
            "Redundant Modulus",
            "Informative Dynamic Range",
            "Balanced Signed Limit",
            "Informative Channels",
            "Total Channels",
            "Channel Overhead Ratio",
            "Informative Bits",
            "Redundant Bits",
            "Total Residue Bits",
            "Residue Bit Overhead Ratio",
            "Coding Efficiency",
            "Testbench Cases",
            "PASS Checks",
            "FAIL Checks",
            "Simulation Pass Rate",
            "Simulation Verdict",
            "Waveform Available",
        ]
    ]
    thesis_table_df.to_csv(table_path, index=False)

    fig, axes = plt.subplots(1, 2, figsize=(12.8, 4.9))

    plot_df = summary_df.copy()
    bar_positions = range(plot_df.shape[0])

    width = 0.36
    axes[0].bar(
        [position - width / 2 for position in bar_positions],
        plot_df["informative_bits"],
        width=width,
        label="Informative bits",
        color="#4c78a8",
    )
    axes[0].bar(
        [position + width / 2 for position in bar_positions],
        plot_df["total_bits"],
        width=width,
        label="Total residue bits",
        color="#f58518",
    )
    axes[0].set_xticks(list(bar_positions))
    axes[0].set_xticklabels(plot_df["system_label"], rotation=0)
    axes[0].set_ylabel("Bit count")
    axes[0].set_xlabel("Validated RRNS hardware system")
    axes[0].set_title("Residue-Representation Cost of the RTL Systems")
    style_axes(axes[0])
    axes[0].legend(loc="upper left", title="Metric")
    annotate_bars(axes[0], [patch.get_height() for patch in axes[0].patches], fmt="{:.0f}")

    axes[1].bar(
        [position - width / 2 for position in bar_positions],
        plot_df["simulation_pass_rate"],
        width=width,
        label="Simulation pass rate",
        color="#54a24b",
    )
    axes[1].bar(
        [position + width / 2 for position in bar_positions],
        plot_df["residue_bit_overhead_ratio"],
        width=width,
        label="Residue-bit overhead ratio",
        color="#e45756",
    )
    axes[1].set_xticks(list(bar_positions))
    axes[1].set_xticklabels(plot_df["system_label"], rotation=0)
    axes[1].set_ylim(0.0, 1.08)
    axes[1].set_ylabel("Rate")
    axes[1].set_xlabel("Validated RRNS hardware system")
    axes[1].set_title("Simulation Outcome and Redundancy Overhead")
    axes[1].yaxis.set_major_formatter(PercentFormatter(xmax=1.0, decimals=0))
    style_axes(axes[1])
    axes[1].legend(loc="upper right", title="Metric")
    for patch in axes[1].patches:
        axes[1].text(
            patch.get_x() + patch.get_width() / 2,
            patch.get_height() + 0.03,
            f"{patch.get_height():.2%}",
            ha="center",
            va="bottom",
            fontsize=9,
            color="#222222",
        )

    fig.suptitle("Verilog Hardware Evaluation of the Self-Checking RRNS MAC/Checker", fontsize=14, fontweight="bold", y=1.03)
    fig.tight_layout()
    fig.savefig(figure_path, dpi=200, bbox_inches="tight")
    plt.close(fig)

    logger.info("Saved raw outputs to %s", raw_path)
    logger.info("Saved summary table to %s", table_path)
    logger.info("Saved figure to %s", figure_path)
    logger.info("Saved metadata to %s", metadata_path)


if __name__ == "__main__":
    main()
