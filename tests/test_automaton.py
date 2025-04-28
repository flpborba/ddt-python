import math
from itertools import product

import pytest
from sage.crypto.sboxes import SEA

import differential.automaton
from differential.automaton import ALPHABET


@pytest.fixture(scope="module")
def ddt():
    table = SEA.difference_distribution_table()
    table.add_to_entry(0, 0, -table[0, 0])

    return table


@pytest.fixture(scope="module")
def automaton(ddt):
    return differential.automaton.make_automaton(ddt)


@pytest.fixture(scope="module")
def words(ddt):
    n = int(math.log(ddt.nrows(), 2))

    return ["".join(w) for w in product(ALPHABET, repeat=n)]


def get_index(encoding):
    binary_encoding = {
        "0": ("0", "0"),
        "1": ("0", "1"),
        "2": ("1", "0"),
        "3": ("1", "1"),
    }

    row_encoding = ""
    col_encoding = ""

    for symbol in encoding:
        row_bit, col_bit = binary_encoding[symbol]
        row_encoding += row_bit
        col_encoding += col_bit

    return (int(row_encoding, 2), int(col_encoding, 2))


def test_outputs_match_ddt(automaton, ddt, words):
    for word in words:
        i, j = get_index(word)
        count = int(ddt[i][j])
        state = f"F{count}"

        assert automaton.evaluate(word) == state
