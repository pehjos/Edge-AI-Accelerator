from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class FixedPointFormat:
    total_bits: int
    frac_bits: int
    signed: bool = True
    rounding: str = "nearest"
    saturate: bool = True

    def __post_init__(self) -> None:
        if self.total_bits <= 0:
            raise ValueError("total_bits must be positive.")
        if self.frac_bits < 0:
            raise ValueError("frac_bits must be non-negative.")
        if self.frac_bits >= self.total_bits:
            raise ValueError("frac_bits must be smaller than total_bits.")
        if self.rounding not in {"nearest", "floor", "ceil", "trunc"}:
            raise ValueError("Unsupported rounding mode.")

    @property
    def scale(self) -> int:
        return 1 << self.frac_bits

    @property
    def integer_min(self) -> int:
        if self.signed:
            return -(1 << (self.total_bits - 1))
        return 0

    @property
    def integer_max(self) -> int:
        if self.signed:
            return (1 << (self.total_bits - 1)) - 1
        return (1 << self.total_bits) - 1

    @property
    def real_min(self) -> float:
        return self.integer_min / self.scale

    @property
    def real_max(self) -> float:
        return self.integer_max / self.scale

    def describe(self) -> str:
        sign_label = "Q" if self.signed else "UQ"
        return f"{sign_label}{self.total_bits - self.frac_bits}.{self.frac_bits}"


@dataclass(frozen=True)
class QuantizationResult:
    original: np.ndarray
    scaled: np.ndarray
    rounded: np.ndarray
    quantized_int: np.ndarray
    dequantized: np.ndarray
    clip_mask: np.ndarray

    @property
    def clipped_count(self) -> int:
        return int(np.count_nonzero(self.clip_mask))


def _apply_rounding(values: np.ndarray, mode: str) -> np.ndarray:
    if mode == "nearest":
        return np.rint(values)
    if mode == "floor":
        return np.floor(values)
    if mode == "ceil":
        return np.ceil(values)
    if mode == "trunc":
        return np.trunc(values)
    raise ValueError(f"Unsupported rounding mode: {mode}")


def quantize(values: np.ndarray | list[float] | float, fmt: FixedPointFormat) -> QuantizationResult:
    original = np.asarray(values, dtype=np.float64)
    scaled = original * fmt.scale
    rounded = _apply_rounding(scaled, fmt.rounding)
    if fmt.saturate:
        clipped = np.clip(rounded, fmt.integer_min, fmt.integer_max)
    else:
        clipped = rounded
    quantized_int = clipped.astype(np.int64)
    dequantized = quantized_int.astype(np.float64) / fmt.scale
    clip_mask = (rounded < fmt.integer_min) | (rounded > fmt.integer_max)

    return QuantizationResult(
        original=original,
        scaled=scaled,
        rounded=rounded,
        quantized_int=quantized_int,
        dequantized=dequantized,
        clip_mask=clip_mask,
    )


def dequantize_integer(values: np.ndarray | list[int] | int, fmt: FixedPointFormat) -> np.ndarray:
    return np.asarray(values, dtype=np.float64) / fmt.scale
