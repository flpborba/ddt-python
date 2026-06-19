"""Self-tests: the automaton must reproduce each table, and every query must
agree with brute force. Runnable with pytest or directly (`python tests/...`)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ddtaut import TableAutomaton, tables, queries, validate
from ddtaut.queries import fixed_input, hamming_weight_at_most, diagonal

# A small S-box with no Sage dependency: the PRESENT 4-bit S-box.
PRESENT_LUT = [0xC, 5, 6, 0xB, 9, 0, 0xA, 0xD, 3, 0xE, 0xF, 8, 4, 7, 1, 2]


def test_ddt_roundtrip():
    table, n = tables.ddt(PRESENT_LUT)
    aut = TableAutomaton.from_matrix(table, n)
    assert validate.cells_equal_table(aut, table)
    assert aut.num_states() == 39


def test_queries_match_bruteforce():
    table, n = tables.ddt(PRESENT_LUT)
    aut = TableAutomaton.from_matrix(table, n)
    for q in [fixed_input(0b0101, n), hamming_weight_at_most(2), diagonal(n)]:
        res, _ = queries.evaluate(aut, q)
        # independent ground truth for each query
        if q.name.startswith("fixed"):
            truth = validate.brute_force(table, lambda a, b, v: a == 0b0101 and v != 0)
        elif q.name.startswith("wt"):
            pc = lambda x: bin(x).count("1")
            truth = validate.brute_force(table, lambda a, b, v: pc(a) + pc(b) <= 2 and v != 0)
        else:
            truth = validate.brute_force(table, lambda a, b, v: a == b and v != 0)
        assert validate.same_set(res, truth), q.name


if __name__ == "__main__":
    test_ddt_roundtrip()
    test_queries_match_bruteforce()
    print("self-tests passed")
