from __future__ import annotations

from typing import Sequence

import numpy as np


def _safe_divide(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def compute_error_metrics(reference: np.ndarray, estimate: np.ndarray) -> dict[str, float]:
    reference = np.asarray(reference, dtype=np.float64)
    estimate = np.asarray(estimate, dtype=np.float64)
    error = estimate - reference

    return {
        "mae": float(np.mean(np.abs(error))),
        "mse": float(np.mean(np.square(error))),
        "rmse": float(np.sqrt(np.mean(np.square(error)))),
        "max_abs_error": float(np.max(np.abs(error))),
        "mean_bias": float(np.mean(error)),
    }


def confusion_counts(ground_truth_faults: Sequence[bool], detected_faults: Sequence[bool]) -> dict[str, int]:
    truth = np.asarray(ground_truth_faults, dtype=bool)
    detected = np.asarray(detected_faults, dtype=bool)

    return {
        "tp": int(np.sum(truth & detected)),
        "tn": int(np.sum(~truth & ~detected)),
        "fp": int(np.sum(~truth & detected)),
        "fn": int(np.sum(truth & ~detected)),
    }


def detection_metrics(ground_truth_faults: Sequence[bool], detected_faults: Sequence[bool]) -> dict[str, float]:
    counts = confusion_counts(ground_truth_faults, detected_faults)
    tp = counts["tp"]
    tn = counts["tn"]
    fp = counts["fp"]
    fn = counts["fn"]

    return {
        **counts,
        "accuracy": _safe_divide(tp + tn, tp + tn + fp + fn),
        "precision": _safe_divide(tp, tp + fp),
        "recall": _safe_divide(tp, tp + fn),
        "specificity": _safe_divide(tn, tn + fp),
        "false_positive_rate": _safe_divide(fp, fp + tn),
        "miss_rate": _safe_divide(fn, fn + tp),
        "detection_rate": _safe_divide(tp, tp + fn),
    }
