"""Brute-force oracles used to validate the automaton and every query."""
from __future__ import annotations

from typing import Callable, List, Sequence, Tuple

from .automaton import TableAutomaton


def cells_equal_table(aut: TableAutomaton, table: Sequence[Sequence[int]]) -> bool:
    """Exhaustive check that the automaton reproduces every cell of ``table``."""
    N = 1 << aut.n
    return all(aut.evaluate(a, b) == table[a][b] for a in range(N) for b in range(N))


def brute_force(table: Sequence[Sequence[int]],
                pred: Callable[[int, int, int], bool]) -> List[Tuple[int, int, int]]:
    """All cells (a, b, value) of the dense table satisfying ``pred``."""
    N = len(table)
    return [(a, b, table[a][b]) for a in range(N) for b in range(N)
            if pred(a, b, table[a][b])]


def same_set(xs, ys) -> bool:
    return sorted(xs) == sorted(ys)
