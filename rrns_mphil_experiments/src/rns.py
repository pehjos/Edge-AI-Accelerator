from __future__ import annotations

import math
from dataclasses import dataclass
from functools import reduce
from typing import Iterable, Sequence


def product(values: Iterable[int]) -> int:
    return reduce(lambda acc, item: acc * item, values, 1)


def _validate_pairwise_coprime(moduli: Sequence[int]) -> None:
    if not moduli:
        raise ValueError("At least one modulus is required.")
    for modulus in moduli:
        if modulus <= 1:
            raise ValueError("Moduli must be greater than one.")
    for index, left in enumerate(moduli):
        for right in moduli[index + 1 :]:
            if math.gcd(left, right) != 1:
                raise ValueError(f"Moduli {left} and {right} are not pairwise coprime.")


@dataclass(frozen=True)
class RNSSystem:
    moduli: tuple[int, ...]
    redundant_modulus: int | None = None

    def __post_init__(self) -> None:
        _validate_pairwise_coprime(self.moduli)
        if self.redundant_modulus is not None:
            if self.redundant_modulus <= 1:
                raise ValueError("redundant_modulus must be greater than one.")
            for modulus in self.moduli:
                if math.gcd(modulus, self.redundant_modulus) != 1:
                    raise ValueError("redundant_modulus must be coprime with each informative modulus.")

    @property
    def informative_dynamic_range(self) -> int:
        return product(self.moduli)

    @property
    def all_moduli(self) -> tuple[int, ...]:
        if self.redundant_modulus is None:
            return self.moduli
        return self.moduli + (self.redundant_modulus,)

    @property
    def balanced_limit(self) -> int:
        return self.informative_dynamic_range // 2

    def supports_balanced_value(self, value: int) -> bool:
        return -self.balanced_limit <= value <= self.balanced_limit

    def describe(self) -> str:
        if self.redundant_modulus is None:
            return f"RNS{self.moduli}"
        return f"RRNS{self.moduli}+({self.redundant_modulus})"


def encode(value: int, moduli: Sequence[int]) -> tuple[int, ...]:
    return tuple(int(value) % modulus for modulus in moduli)


def crt_reconstruct(residues: Sequence[int], moduli: Sequence[int]) -> int:
    if len(residues) != len(moduli):
        raise ValueError("The number of residues must match the number of moduli.")

    modulus_product = product(moduli)
    reconstruction = 0
    for residue, modulus in zip(residues, moduli):
        partial_product = modulus_product // modulus
        inverse = pow(partial_product, -1, modulus)
        reconstruction += residue * partial_product * inverse

    return reconstruction % modulus_product


def balanced_signed_decode(unsigned_value: int, modulus_product: int) -> int:
    if unsigned_value > (modulus_product / 2):
        return unsigned_value - modulus_product
    return unsigned_value


def decode(residues: Sequence[int], moduli: Sequence[int], balanced: bool = True) -> int:
    unsigned_value = crt_reconstruct(residues, moduli)
    if not balanced:
        return unsigned_value
    return balanced_signed_decode(unsigned_value, product(moduli))


def encode_rrns(value: int, system: RNSSystem) -> tuple[int, ...]:
    return encode(value, system.all_moduli)


def decode_rrns(codeword: Sequence[int], system: RNSSystem, balanced: bool = True) -> int:
    informative = tuple(codeword[: len(system.moduli)])
    return decode(informative, system.moduli, balanced=balanced)


def predicted_redundant_residue(informative_residues: Sequence[int], system: RNSSystem) -> int | None:
    if system.redundant_modulus is None:
        return None
    unsigned_value = crt_reconstruct(informative_residues, system.moduli)
    signed_value = balanced_signed_decode(unsigned_value, system.informative_dynamic_range)
    return signed_value % system.redundant_modulus


def choose_rrns_system(
    required_magnitude: int,
    candidate_moduli_sets: Sequence[tuple[int, ...]] | None = None,
    redundant_candidates: Sequence[int] = (29, 31, 37, 41, 43, 47),
) -> RNSSystem:
    candidate_moduli_sets = candidate_moduli_sets or (
        (17, 19, 23),
        (23, 29, 31),
        (29, 31, 37),
        (37, 41, 43),
    )

    for moduli in candidate_moduli_sets:
        dynamic_range = product(moduli)
        if required_magnitude <= dynamic_range // 2:
            for redundant_modulus in redundant_candidates:
                if redundant_modulus not in moduli and all(math.gcd(redundant_modulus, modulus) == 1 for modulus in moduli):
                    return RNSSystem(moduli=tuple(moduli), redundant_modulus=redundant_modulus)

    raise ValueError(
        f"No candidate RRNS system supports balanced magnitude {required_magnitude}. "
        "Add a larger candidate modulus set."
    )
