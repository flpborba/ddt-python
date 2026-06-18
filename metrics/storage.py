import math
from collections import Counter


def entries(ddt):
    return [int(ddt[i, j]) for i in range(ddt.nrows()) for j in range(ddt.ncols())]


def entropy(ddt):
    values = entries(ddt)
    n = len(values)
    frequencies = Counter(values)

    return -sum((count / n) * math.log2(count / n) for count in frequencies.values())


def dense(ddt):
    n = ddt.nrows() * ddt.ncols()
    bits = max(1, max(entries(ddt)).bit_length())

    return n * bits


def bitmap(ddt):
    values = entries(ddt)
    nonzero = [value for value in values if value != 0]
    distinct = sorted(set(nonzero))

    n = len(values)
    value_bits = max(1, max(distinct).bit_length())
    index_bits = max(1, (len(distinct) - 1).bit_length())

    return n + len(nonzero) * index_bits + len(distinct) * value_bits


def wavelet_matrix(ddt):
    n = ddt.nrows() * ddt.ncols()
    distinct = sorted(set(entries(ddt)))
    levels = max(1, (len(distinct) - 1).bit_length())
    value_bits = max(1, max(distinct).bit_length())

    return math.ceil(levels * n * entropy(ddt) / math.log2(len(distinct))) + len(distinct) * value_bits


def min_dfa(ddt):
    distinct = sorted(value for value in set(entries(ddt)) if value != 0)
    leaf_id = {value: index for index, value in enumerate(distinct)}
    cache = {}

    def canonical(i, j, size):
        if size == 1:
            value = int(ddt[i, j])

            return leaf_id[value] if value else None

        half = size // 2
        children = (
            canonical(i, j, half),
            canonical(i, j + half, half),
            canonical(i + half, j, half),
            canonical(i + half, j + half, half),
        )

        if all(child is None for child in children):
            return None

        if children not in cache:
            cache[children] = len(leaf_id) + len(cache)

        return cache[children]

    canonical(0, 0, ddt.nrows())

    n_states = len(leaf_id) + len(cache)
    pointer_bits = max(1, n_states.bit_length())

    return n_states * 4 * pointer_bits


ENCODINGS = [
    ("entropy", lambda ddt: math.ceil(entropy(ddt) * ddt.nrows() * ddt.ncols())),
    ("dense", dense),
    ("bitmap", bitmap),
    ("wavelet", wavelet_matrix),
    ("min_dfa", min_dfa),
]


def header():
    cells = [f"{'sbox':18s}", f"{'size':>7}", f"{'H':>6}"]
    cells.extend(f"{label:>9}" for label, _ in ENCODINGS)
    print("  ".join(cells))


def row(name, ddt):
    cells = [f"{name:18s}", f"{ddt.nrows():>3}x{ddt.ncols():<3}", f"{entropy(ddt):6.3f}"]
    cells.extend(f"{encode(ddt) / 8:9.1f}" for _, encode in ENCODINGS)
    print("  ".join(cells))


if __name__ == "__main__":
    from sage.crypto import sboxes
    from sage.crypto.sbox import SBox

    items = sorted(
        ((name, getattr(sboxes, name)) for name in dir(sboxes) if isinstance(getattr(sboxes, name), SBox)),
        key=lambda item: (item[1].input_size(), item[0]),
    )

    header()

    for name, sbox in items:
        ddt = sbox.difference_distribution_table()
        ddt.add_to_entry(0, 0, -ddt[0, 0])

        row(name, ddt)
