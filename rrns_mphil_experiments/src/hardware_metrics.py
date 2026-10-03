from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

from rns import RNSSystem


@dataclass(frozen=True)
class TestbenchSummary:
    testbench_cases: int
    pass_checks: int
    fail_checks: int
    waveform_dump_reported: bool
    finish_reported: bool

    @property
    def total_checks(self) -> int:
        return self.pass_checks + self.fail_checks

    @property
    def pass_rate(self) -> float:
        if self.total_checks == 0:
            return 0.0
        return self.pass_checks / self.total_checks

    @property
    def simulation_verdict(self) -> str:
        if self.fail_checks == 0 and self.total_checks > 0:
            return "PASS"
        if self.total_checks == 0:
            return "NO RESULTS"
        return "FAIL"


@dataclass(frozen=True)
class HardwareSystemSummary:
    system_label: str
    system: RNSSystem
    informative_bits: int
    redundant_bits: int
    total_bits: int
    informative_channels: int
    redundant_channels: int
    total_channels: int
    residue_bit_overhead_ratio: float
    channel_overhead_ratio: float
    coding_efficiency: float
    checker_input_width: int
    testbench: TestbenchSummary
    waveform_exists: bool


def residue_bit_width(modulus: int) -> int:
    return math.ceil(math.log2(modulus))


def parse_testbench_log(log_path: Path) -> TestbenchSummary:
    if not log_path.exists():
        return TestbenchSummary(
            testbench_cases=0,
            pass_checks=0,
            fail_checks=0,
            waveform_dump_reported=False,
            finish_reported=False,
        )

    text = log_path.read_text(encoding="utf-8")
    case_count = len(re.findall(r"^---- Case \d+:", text, flags=re.MULTILINE))

    pass_match = re.search(r"PASS COUNT = (\d+)", text)
    fail_match = re.search(r"FAIL COUNT = (\d+)", text)

    pass_checks = int(pass_match.group(1)) if pass_match else len(re.findall(r"^PASS:", text, flags=re.MULTILINE))
    fail_checks = int(fail_match.group(1)) if fail_match else len(re.findall(r"^FAIL:", text, flags=re.MULTILINE))

    return TestbenchSummary(
        testbench_cases=case_count,
        pass_checks=pass_checks,
        fail_checks=fail_checks,
        waveform_dump_reported="VCD info: dumpfile" in text,
        finish_reported="$finish called" in text,
    )


def summarize_hardware_system(
    system_label: str,
    system: RNSSystem,
    log_path: Path,
    waveform_path: Path,
) -> HardwareSystemSummary:
    informative_bits = sum(residue_bit_width(modulus) for modulus in system.moduli)
    redundant_bits = residue_bit_width(system.redundant_modulus) if system.redundant_modulus is not None else 0
    total_bits = informative_bits + redundant_bits
    informative_channels = len(system.moduli)
    redundant_channels = 1 if system.redundant_modulus is not None else 0
    total_channels = informative_channels + redundant_channels
    testbench = parse_testbench_log(log_path)

    return HardwareSystemSummary(
        system_label=system_label,
        system=system,
        informative_bits=informative_bits,
        redundant_bits=redundant_bits,
        total_bits=total_bits,
        informative_channels=informative_channels,
        redundant_channels=redundant_channels,
        total_channels=total_channels,
        residue_bit_overhead_ratio=redundant_bits / informative_bits if informative_bits else 0.0,
        channel_overhead_ratio=redundant_channels / informative_channels if informative_channels else 0.0,
        coding_efficiency=math.log2(system.informative_dynamic_range) / total_bits if total_bits else 0.0,
        checker_input_width=total_bits,
        testbench=testbench,
        waveform_exists=waveform_path.exists(),
    )
