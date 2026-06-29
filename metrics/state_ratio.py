"""Cell/state ratio for DDT, LAT, and BCT automata over the SageMath S-box library, grouped by S-box
input size."""

import statistics
from collections import defaultdict

from sage.crypto import sboxes

import differential.automaton


def get_sboxes():
    """Return all S-boxes from the SageMath library.

    Returns
    -------
    list
        A list of all S-box objects from ``sage.crypto.sboxes``.
    """
    return [sboxes.sboxes[name] for name in sboxes.sboxes]


if __name__ == "__main__":
    ddt_groups = defaultdict(list)
    lat_groups = defaultdict(list)
    bct_groups = defaultdict(list)

    for sbox in get_sboxes():
        i = sbox.input_size()
        o = sbox.output_size()

        cells = 2 ** (i + o)

        ddt = sbox.difference_distribution_table()
        automaton = differential.automaton.make_automaton(ddt)

        states = len(automaton.states())
        ddt_groups[i].append(cells / states)

        lat = sbox.linear_approximation_table()
        automaton = differential.automaton.make_automaton(lat)

        states = len(automaton.states())
        lat_groups[i].append(cells / states)

        if sbox.is_permutation():
            bct = sbox.boomerang_connectivity_table()
            automaton = differential.automaton.make_automaton(bct)

            states = len(automaton.states())
            bct_groups[i].append(cells / states)

    print("=" * 75)
    print("Cell/State Ratio Statistics by S-Box Input Size")
    print("=" * 75)

    for table, groups in [
        ("ddt", ddt_groups),
        ("lat", lat_groups),
        ("bct", bct_groups),
    ]:
        print(f"\n[{table.upper()}]")
        print("-" * 75)

        for size in sorted(groups):
            sorted_values = sorted(groups[size])

            count = len(sorted_values)
            median = statistics.median(sorted_values)
            minimum = sorted_values[0]
            maximum = sorted_values[-1]

            print(
                f"Size {size}:\n\t"
                f"count = {count:3d} | "
                f"median = {median:8.1f} | "
                f"min = {minimum:8.1f} | "
                f"max = {maximum:8.1f}"
            )
