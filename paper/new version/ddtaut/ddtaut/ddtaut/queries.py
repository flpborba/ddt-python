"""A query calculus over the quadrant encoding.

A *query* is a length-``n`` deterministic automaton over ``Sigma`` together with
an acceptance test on the table value reached. Each query is built from the
encoding conventions in :mod:`ddtaut.encoding`, so the regular expressions in the
paper and the code agree by construction. The :func:`evaluate` engine walks the
product of a :class:`~ddtaut.automaton.TableAutomaton` and a query without ever
materialising the dense matrix, reporting both the matching cells and the number
of product states visited.

A query is described by:
    ``step(level, qstate, sigma) -> qstate | None``   (None == reject this edge)
    ``q0``                                            initial query state
    ``accept(value) -> bool``                         test on the reached value
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Tuple

from .automaton import TableAutomaton
from .encoding import input_bit, output_bit

Result = Tuple[int, int, int]  # (a, b, value)


@dataclass(frozen=True)
class Query:
    """A length-n query automaton plus an acceptance test on the value."""
    name: str
    q0: object
    step: Callable[[int, object, int], object]
    accept: Callable[[int], bool]


def evaluate(table: TableAutomaton, query: Query) -> Tuple[List[Result], int]:
    """Enumerate ``L(table) cap L(query)``; return ``(results, product_states)``."""
    n = table.n
    results: List[Result] = []
    visited = set()

    def walk(node, qstate, level, word):
        visited.add((node, qstate, level))
        if level == n:
            if table.is_terminal(node) and query.accept(table.value(node)):
                a = b = 0
                for sigma in word:
                    a = (a << 1) | input_bit(sigma)
                    b = (b << 1) | output_bit(sigma)
                results.append((a, b, table.value(node)))
            return
        advance = (not table.is_terminal(node)) and table.level(node) == level
        for sigma in range(4):
            nq = query.step(level, qstate, sigma)
            if nq is None:
                continue
            walk(table.child(node, sigma) if advance else node, nq, level + 1, word + (sigma,))

    walk(table.root, query.q0, 0, ())
    return results, len(visited)


# ---- query constructors ---------------------------------------------------

def fixed_input(a: int, n: int) -> Query:
    """All possible output differences for a fixed input difference ``a``."""
    def step(level, _q, sigma):
        return 0 if input_bit(sigma) == ((a >> (n - 1 - level)) & 1) else None
    return Query(f"fixed input a={a:0{n}b}", 0, step, lambda v: v != 0)


def truncated(active_input: set, n: int) -> Query:
    """Input positions in ``active_input`` must be active; others free."""
    def step(level, _q, sigma):
        if level in active_input and input_bit(sigma) != 1:
            return None
        return 0
    return Query("truncated", 0, step, lambda v: v != 0)


def impossible(base: Query) -> Query:
    """Cells matching ``base``'s pattern that are *zero* (impossible)."""
    return Query("impossible " + base.name, base.q0, base.step, lambda v: v == 0)


def value_at_least(table: TableAutomaton, tau: int) -> Query:
    """Differentials of probability >= tau / 2^n (extremal when tau = Delta)."""
    return Query(f"value >= {tau}", 0, lambda l, q, s: 0, lambda v: v >= tau)


def value_equals(value: int) -> Query:
    return Query(f"value == {value}", 0, lambda l, q, s: 0, lambda v: v == value)


def magnitude_at_least(tau: int) -> Query:
    """High-|value| cells (e.g. high-bias linear approximations on a LAT)."""
    return Query(f"|value| >= {tau}", 0, lambda l, q, s: 0, lambda v: abs(v) >= tau)


def hamming_weight_at_most(w: int) -> Query:
    """Differentials with wt(a) + wt(b) <= w via a popcount counter automaton."""
    def step(_level, acc, sigma):
        acc2 = acc + input_bit(sigma) + output_bit(sigma)
        return acc2 if acc2 <= w else None
    return Query(f"wt(a)+wt(b) <= {w}", 0, step, lambda v: v != 0)


def diagonal(n: int) -> Query:
    """The linear relation a = b, recognised by (0|3)^n."""
    return Query("linear a = b", 0,
                 lambda l, q, s: 0 if s in (0, 3) else None,
                 lambda v: v != 0)


def conjoin(name: str, qa: Query, qb: Query, accept: Callable[[int], bool]) -> Query:
    """Product of two query automata with a combined value test."""
    def step(level, state, sigma):
        sa, sb = state
        na = qa.step(level, sa, sigma)
        if na is None:
            return None
        nb = qb.step(level, sb, sigma)
        if nb is None:
            return None
        return (na, nb)
    return Query(name, (qa.q0, qb.q0), step, accept)
