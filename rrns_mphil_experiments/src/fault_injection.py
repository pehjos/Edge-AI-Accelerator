from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class FaultInjectionRecord:
    target_index: int
    modulus: int
    original_value: int
    corrupted_value: int
    mode: str
    delta: int | None = None
    bit_index: int | None = None


def bit_width_for_modulus(modulus: int) -> int:
    return max(1, math.ceil(math.log2(modulus)))


def flip_integer_bit(value: int, bit_index: int) -> int:
    return int(value) ^ (1 << int(bit_index))


def inject_array_fault(
    array: np.ndarray,
    index: tuple[int, ...],
    mode: str = "bit_flip",
    bit_index: int | None = None,
    delta: int | None = None,
) -> np.ndarray:
    corrupted = np.array(array, copy=True)
    original = int(corrupted[index])

    if mode == "bit_flip":
        bit_index = 0 if bit_index is None else bit_index
        corrupted[index] = flip_integer_bit(original, bit_index)
    elif mode == "delta":
        corrupted[index] = original + (1 if delta is None else delta)
    else:
        raise ValueError(f"Unsupported fault mode: {mode}")

    return corrupted


def inject_residue_fault(
    codeword: Sequence[int],
    moduli: Sequence[int],
    target_index: int,
    mode: str = "delta",
    rng: np.random.Generator | None = None,
    delta: int | None = None,
    bit_index: int | None = None,
) -> tuple[tuple[int, ...], FaultInjectionRecord]:
    if len(codeword) != len(moduli):
        raise ValueError("codeword and moduli lengths must match.")

    rng = rng or np.random.default_rng()
    corrupted = list(int(value) for value in codeword)
    modulus = int(moduli[target_index])
    original = corrupted[target_index]

    if mode == "delta":
        delta = int(delta if delta is not None else rng.integers(1, modulus))
        corrupted_value = (original + delta) % modulus
    elif mode == "random":
        corrupted_value = original
        while corrupted_value == original:
            corrupted_value = int(rng.integers(0, modulus))
    elif mode == "bit_flip":
        width = bit_width_for_modulus(modulus)
        bit_index = int(bit_index if bit_index is not None else rng.integers(0, width))
        mask = (1 << width) - 1
        corrupted_value = (flip_integer_bit(original, bit_index) & mask) % modulus
        if corrupted_value == original:
            corrupted_value = (original + 1) % modulus
    else:
        raise ValueError(f"Unsupported residue fault mode: {mode}")

    corrupted[target_index] = corrupted_value
    record = FaultInjectionRecord(
        target_index=target_index,
        modulus=modulus,
        original_value=original,
        corrupted_value=corrupted_value,
        mode=mode,
        delta=delta,
        bit_index=bit_index,
    )
    return tuple(corrupted), record
