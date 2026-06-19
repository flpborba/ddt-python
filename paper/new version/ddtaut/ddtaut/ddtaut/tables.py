"""Build the DDT, LAT, and BCT of an S-box as plain integer matrices.

Each builder accepts either a SageMath ``SBox`` (whose optimised C methods are
used when available) or a raw lookup table given as a list. The DDT's trivial
``(0, 0) = 2^n`` entry is zeroed by default, as is standard in differential
cryptanalysis; the LAT and BCT are returned verbatim.
"""
from __future__ import annotations

from typing import List, Sequence, Union

Matrix = List[List[int]]
SBoxLike = Union["SBox", Sequence[int]]  # noqa: F821  (Sage SBox or a lookup list)


def _as_lookup(sbox: SBoxLike) -> tuple[list, int]:
    """Normalise an S-box to a (lookup list, bit-width) pair."""
    if hasattr(sbox, "input_size"):                  # a Sage SBox
        n = int(sbox.input_size())
        return [int(sbox(x)) for x in range(1 << n)], n
    lut = list(sbox)
    n = (len(lut) - 1).bit_length()
    return lut, n


def _sage_matrix(method, n: int) -> Matrix:
    m = method()
    N = 1 << n
    return [[int(m[i, j]) for j in range(N)] for i in range(N)]


def ddt(sbox: SBoxLike, zero_trivial: bool = True) -> tuple[Matrix, int]:
    """Difference distribution table; returns ``(matrix, n)``."""
    if hasattr(sbox, "difference_distribution_table"):
        lut, n = _as_lookup(sbox)
        table = _sage_matrix(sbox.difference_distribution_table, n)
    else:
        lut, n = _as_lookup(sbox)
        N = 1 << n
        table = [[0] * N for _ in range(N)]
        for a in range(N):
            for x in range(N):
                table[a][lut[x] ^ lut[x ^ a]] += 1
    if zero_trivial:
        table[0][0] = 0
    return table, n


def lat(sbox: SBoxLike) -> tuple[Matrix, int]:
    """Linear approximation table (Walsh / correlation), returned verbatim."""
    lut, n = _as_lookup(sbox)
    if hasattr(sbox, "linear_approximation_table"):
        return _sage_matrix(sbox.linear_approximation_table, n), n
    N = 1 << n
    par = lambda v: bin(v).count("1") & 1
    table = [[sum(1 for x in range(N) if par(a & x) == par(b & lut[x])) - (N >> 1)
              for b in range(N)] for a in range(N)]
    return table, n


def bct(sbox: SBoxLike) -> tuple[Matrix, int]:
    """Boomerang connectivity table (permutations only), returned verbatim."""
    lut, n = _as_lookup(sbox)
    if hasattr(sbox, "boomerang_connectivity_table"):
        return _sage_matrix(sbox.boomerang_connectivity_table, n), n
    N = 1 << n
    inv = [0] * N
    for x in range(N):
        inv[lut[x]] = x
    table = [[sum(1 for x in range(N)
                  if inv[lut[x] ^ b] ^ inv[lut[x ^ a] ^ b] == a)
              for b in range(N)] for a in range(N)]
    return table, n


def differential_uniformity(table: Matrix) -> int:
    return max(table[a][b] for a in range(1, len(table)) for b in range(len(table)))


def linearity(table: Matrix) -> int:
    return max(abs(table[a][b]) for a in range(len(table)) for b in range(len(table))
               if (a, b) != (0, 0))


def boomerang_uniformity(table: Matrix) -> int:
    N = len(table)
    return max(table[a][b] for a in range(1, N) for b in range(1, N))
