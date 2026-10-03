from __future__ import annotations

import csv
import json
import logging
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np

BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"
EXPERIMENTS_DIR = BASE_DIR / "experiments"
RESULTS_DIR = BASE_DIR / "results"
TABLES_DIR = RESULTS_DIR / "tables"
FIGURES_DIR = RESULTS_DIR / "figures"
LOGS_DIR = RESULTS_DIR / "logs"
RAW_OUTPUTS_DIR = RESULTS_DIR / "raw_outputs"
VERILOG_DIR = BASE_DIR / "verilog"

DEFAULT_SEED = 7
DEFAULT_FIXED_POINT_TOTAL_BITS = 8
DEFAULT_FIXED_POINT_FRAC_BITS = 4
DEFAULT_ACTIVATION_SHAPE = (6, 6)
DEFAULT_KERNEL_SHAPE = (3, 3)


def ensure_project_layout() -> None:
    for directory in (
        SRC_DIR,
        EXPERIMENTS_DIR,
        TABLES_DIR,
        FIGURES_DIR,
        LOGS_DIR,
        RAW_OUTPUTS_DIR,
        VERILOG_DIR / "rtl",
        VERILOG_DIR / "tb",
        VERILOG_DIR / "logs",
        VERILOG_DIR / "waveforms",
    ):
        directory.mkdir(parents=True, exist_ok=True)


def set_random_seed(seed: int = DEFAULT_SEED) -> np.random.Generator:
    random.seed(seed)
    np.random.seed(seed)
    return np.random.default_rng(seed)


def utc_timestamp_label() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    return value


@dataclass(frozen=True)
class ExperimentArtifacts:
    experiment_name: str

    def __post_init__(self) -> None:
        ensure_project_layout()

    def raw_output_path(self, filename: str) -> Path:
        return RAW_OUTPUTS_DIR / filename

    def table_path(self, filename: str) -> Path:
        return TABLES_DIR / filename

    def figure_path(self, filename: str) -> Path:
        return FIGURES_DIR / filename

    def log_path(self, filename: str | None = None) -> Path:
        log_name = filename or f"{self.experiment_name}.log"
        return LOGS_DIR / log_name

    def save_json(self, filename: str, payload: Any) -> Path:
        destination = self.raw_output_path(filename)
        destination.write_text(
            json.dumps(payload, indent=2, default=_json_default),
            encoding="utf-8",
        )
        return destination

    def save_csv_rows(
        self,
        filename: str,
        fieldnames: Iterable[str],
        rows: Iterable[dict[str, Any]],
        output_type: str = "raw",
    ) -> Path:
        destination = self.raw_output_path(filename) if output_type == "raw" else self.table_path(filename)
        with destination.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
            writer.writeheader()
            writer.writerows(rows)
        return destination


def build_logger(experiment_name: str, log_filename: str | None = None) -> logging.Logger:
    ensure_project_layout()
    logger = logging.getLogger(experiment_name)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.handlers.clear()

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    log_path = LOGS_DIR / (log_filename or f"{experiment_name}.log")
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger


ensure_project_layout()
