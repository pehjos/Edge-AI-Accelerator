from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from rns import RNSSystem, balanced_signed_decode, crt_reconstruct, predicted_redundant_residue


@dataclass(frozen=True)
class RRNSCheckResult:
    is_valid: bool
    informative_residues: tuple[int, ...]
    observed_redundant: int | None
    predicted_redundant: int | None
    syndrome: int | None
    reconstructed_unsigned: int
    reconstructed_balanced: int


def check_rrns_codeword(codeword: Sequence[int], system: RNSSystem) -> RRNSCheckResult:
    expected_length = len(system.moduli) + (1 if system.redundant_modulus is not None else 0)
    if len(codeword) != expected_length:
        raise ValueError(f"Expected codeword of length {expected_length}, received {len(codeword)}.")

    informative_residues = tuple(int(value) for value in codeword[: len(system.moduli)])
    reconstructed_unsigned = crt_reconstruct(informative_residues, system.moduli)
    reconstructed_balanced = balanced_signed_decode(reconstructed_unsigned, system.informative_dynamic_range)

    if system.redundant_modulus is None:
        return RRNSCheckResult(
            is_valid=True,
            informative_residues=informative_residues,
            observed_redundant=None,
            predicted_redundant=None,
            syndrome=None,
            reconstructed_unsigned=reconstructed_unsigned,
            reconstructed_balanced=reconstructed_balanced,
        )

    observed_redundant = int(codeword[-1])
    predicted = predicted_redundant_residue(informative_residues, system)
    syndrome = (observed_redundant - predicted) % system.redundant_modulus

    return RRNSCheckResult(
        is_valid=(syndrome == 0),
        informative_residues=informative_residues,
        observed_redundant=observed_redundant,
        predicted_redundant=predicted,
        syndrome=syndrome,
        reconstructed_unsigned=reconstructed_unsigned,
        reconstructed_balanced=reconstructed_balanced,
    )
