import math
from itertools import product

import pytest
from sage.crypto.sboxes import Ascon

import differential.automaton
from differential.automaton import ALPHABET


@pytest.fixture(scope="module")
def ddt():
    table = Ascon.difference_distribution_table()
    table.add_to_entry(0, 0, -table[0, 0])

    return table


@pytest.fixture(scope="module")
def automaton(ddt):
    return differential.automaton.make(ddt)


@pytest.fixture(scope="module")
def ascon_simplified(automaton):
    return automaton.simplification()


@pytest.fixture(scope="module")
def words(ddt):
    n = int(math.log(ddt.nrows(), 2))

    return list(product(ALPHABET, repeat=n))


def test_ascon_outputs_match_ascon_ddt(automaton, ddt, words):
    for word in words:
        i, j = differential.automaton.get_index("".join(word))
        count = int(ddt[i][j])

        accepted, _, output = automaton.process(list(word))

        if count == 0:
            assert not accepted
        else:
            assert accepted
            assert output == [count]


def test_simplification_preserves_behavior(automaton, ascon_simplified, words):
    for word in words:
        a1, _, o1 = automaton.process(list(word))
        a2, _, o2 = ascon_simplified.process(list(word))

        assert a1 == a2
        assert o1 == o2


def test_simplification_reduces_states(automaton, ascon_simplified):
    assert len(ascon_simplified.states()) < len(automaton.states())


def test_is_deterministic(automaton):
    assert automaton.is_deterministic()
