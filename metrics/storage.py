import statistics
from collections import defaultdict

from sage.crypto import sboxes

import differential.automaton


def get_sboxes():
    return [sboxes.sboxes[name] for name in sboxes.sboxes]


def dense_bits(sbox):
    max_value = sbox.differential_uniformity() // 2
    nrows = 2 ** sbox.input_size()
    ncols = 2 ** sbox.output_size()

    return nrows * ncols * max_value.bit_length()


if __name__ == "__main__":
    groups = defaultdict(list)

    for sbox in get_sboxes():
        i = sbox.input_size()

        if i > 7:
            continue

        ddt = sbox.difference_distribution_table()
        automaton = differential.automaton.make_automaton(ddt)
        cells = ddt.nrows() * ddt.ncols()
        states = len(automaton.states())
        groups[i].append(cells / states)

    for size in sorted(groups):
        sorted_values = sorted(groups[size])
        count = len(sorted_values)
        minimum = sorted_values[0]
        maximum = sorted_values[-1]
        median = statistics.median(sorted_values)
        print(f"size={size} count={count} min={minimum} median={median} max={maximum}")
