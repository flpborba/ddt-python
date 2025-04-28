import math

from sage.combinat.finite_state_machine import Transducer

ALPHABET = ["0", "1", "2", "3"]


def make(ddt):
    cache = {}
    transitions = []
    final_states = set()

    def build(i, j, size):
        if size == 1:
            value = int(ddt[i, j])

            if value == 0:
                return None, 0

            state = f"F{value}"
            final_states.add(state)

            return state, value

        half = size // 2
        children = [
            build(i, j, half),
            build(i, j + half, half),
            build(i + half, j, half),
            build(i + half, j + half, half),
        ]

        key = tuple(child for child, _ in children)

        if all(child is None for child in key):
            return None, 0

        if key in cache:
            return cache[key], None

        state = f"S{len(cache)}"
        cache[key] = state

        for symbol, (target, value) in zip(ALPHABET, children):
            if target is None:
                continue

            output = [value] if value else []
            transitions.append((state, target, symbol, output))

        return state, None

    initial, _ = build(0, 0, ddt.nrows())

    return Transducer(
        transitions,
        initial_states=[initial],
        final_states=list(final_states),
    )


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


def get_quadrant(ddt, encoding):
    encoding = encoding[1:]
    nbits = int(math.log(ddt.nrows(), 2))
    pad = nbits - len(encoding)

    i, j = get_index(encoding + "0" * pad)
    size = 1 << pad

    return ddt.submatrix(i, j, size, size)


if __name__ == "__main__":
    from sage.crypto.sboxes import SEA

    ddt = SEA.difference_distribution_table()
    ddt.add_to_entry(0, 0, -ddt[0, 0])

    T = make(ddt).simplification()

    print(len(T.states()), len(T.transitions()))

    for t in T.transitions():
        print(t)
