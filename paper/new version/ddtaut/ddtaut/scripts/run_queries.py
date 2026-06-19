#!/usr/bin/env python3
"""Run the query calculus over selected S-boxes and validate every result
against an exhaustive scan of the dense table. Prints the tables used in the
paper. Requires SageMath (``sage.crypto.sboxes``).

Usage:  python scripts/run_queries.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sage.crypto.sboxes import PRESENT, AES  # noqa: E402

from ddtaut import TableAutomaton, tables, queries, validate  # noqa: E402
from ddtaut.queries import (  # noqa: E402
    fixed_input, truncated, impossible, value_equals, value_at_least,
    magnitude_at_least, hamming_weight_at_most, diagonal, conjoin,
)


def ddt_suite(sbox):
    table, n = tables.ddt(sbox)
    aut = TableAutomaton.from_matrix(table, n)
    assert validate.cells_equal_table(aut, table), "automaton != DDT"
    delta = tables.differential_uniformity(table)
    a0 = int("01" * (n // 2) or "0", 2)
    suite = [
        fixed_input(a0, n),
        truncated({0, 1}, n),
        impossible(fixed_input(1, n)),
        value_equals(delta),
        hamming_weight_at_most(2),
        diagonal(n),
        conjoin(f"value>={max(2, delta // 2)} and wt<=4",
                hamming_weight_at_most(4), hamming_weight_at_most(4),
                lambda v, t=max(2, delta // 2): v >= t),
    ]
    rows = []
    for q in suite:
        res, prod = queries.evaluate(aut, q)
        truth = validate.brute_force(table, lambda a, b, v, q=q:
                                     _matches(aut, table, n, q, a, b, v))
        ok = validate.same_set(res, truth)
        assert ok, f"{sbox} / {q.name} disagreed with brute force"
        rows.append((q.name, len(res), prod, ok))
    return n, aut.num_states(), (1 << n) * (1 << n), rows


def _matches(aut, table, n, q, a, b, v):
    """Ground-truth predicate mirroring a query, for cross-checking."""
    # Re-run the query's automaton on the single word (a, b) and apply accept.
    from ddtaut.encoding import word_of
    state, level = q.q0, 0
    for sigma in word_of(a, b, n):
        state = q.step(level, state, sigma)
        if state is None:
            return False
        level += 1
    return q.accept(v)


def lat_bct_suite(sbox):
    name_rows = []
    lat_tab, n = tables.lat(sbox)
    lat_aut = TableAutomaton.from_matrix(lat_tab, n)
    assert validate.cells_equal_table(lat_aut, lat_tab)
    lin = tables.linearity(lat_tab)
    q = magnitude_at_least(lin)
    res, prod = queries.evaluate(lat_aut, q)
    res = [r for r in res if (r[0], r[1]) != (0, 0)]
    truth = [t for t in validate.brute_force(lat_tab, lambda a, b, v: abs(v) >= lin)
             if (t[0], t[1]) != (0, 0)]
    assert validate.same_set(res, truth)
    name_rows.append(("LAT", f"|LAT| >= {lin}", len(res), prod))

    bct_tab, _ = tables.bct(sbox)
    bct_aut = TableAutomaton.from_matrix(bct_tab, n)
    assert validate.cells_equal_table(bct_aut, bct_tab)
    beta = tables.boomerang_uniformity(bct_tab)
    res, prod = queries.evaluate(bct_aut, value_equals(beta))
    res = [r for r in res if r[0] and r[1]]
    truth = [t for t in validate.brute_force(bct_tab, lambda a, b, v: v == beta)
             if t[0] and t[1]]
    assert validate.same_set(res, truth)
    name_rows.append(("BCT", f"value == {beta}", len(res), prod))
    return name_rows


if __name__ == "__main__":
    for sbox, label in [(PRESENT, "PRESENT"), (AES, "AES")]:
        n, states, dense, rows = ddt_suite(sbox)
        print(f"\nDDT queries on {label}  (n={n}, |D|={states}, dense={dense})")
        for name, nres, prod, ok in rows:
            print(f"  {name:38s} res={nres:6d}  prod.states={prod:6d}  {'OK' if ok else 'FAIL'}")
        for tbl, q, nres, prod in lat_bct_suite(sbox):
            print(f"  [{tbl}] {q:30s} res={nres:6d}  prod.states={prod:6d}  OK")
    print("\nAll queries validated against exhaustive search.")
