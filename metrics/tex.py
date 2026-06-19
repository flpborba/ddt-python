import math
import statistics

from metrics.storage import entries, entropy, dense, bitmap, wavelet_matrix, min_dfa


def dfa(ddt):
    distinct = sorted(value for value in set(entries(ddt)) if value != 0)
    leaf_id = {value: index for index, value in enumerate(distinct)}
    counter = [len(leaf_id)]

    def build(i, j, size):
        if size == 1:
            value = int(ddt[i, j])

            return leaf_id[value] if value else None

        half = size // 2
        children = (
            build(i, j, half),
            build(i, j + half, half),
            build(i + half, j, half),
            build(i + half, j + half, half),
        )

        if all(child is None for child in children):
            return None

        node = counter[0]
        counter[0] += 1

        return node

    build(0, 0, ddt.nrows())

    n_states = counter[0]
    pointer_bits = max(1, n_states.bit_length())

    return n_states * 4 * pointer_bits


SIZE_ENCODINGS = [
    ("entropy", lambda ddt: math.ceil(entropy(ddt) * ddt.nrows() * ddt.ncols())),
    ("dense", dense),
    ("bitmap", bitmap),
    ("wavelet", wavelet_matrix),
    ("dfa", dfa),
    ("min_dfa", min_dfa),
]

OTHERS = ["entropy", "dense", "bitmap", "wavelet", "dfa"]


def escape(name):
    return name.replace("_", r"\_")


def collect():
    from sage.crypto import sboxes
    from sage.crypto.sbox import SBox

    items = sorted(
        ((name, getattr(sboxes, name)) for name in dir(sboxes) if isinstance(getattr(sboxes, name), SBox)),
        key=lambda item: (item[1].input_size(), item[0]),
    )

    rows = []
    for name, sbox in items:
        ddt = sbox.difference_distribution_table()
        ddt.add_to_entry(0, 0, -ddt[0, 0])

        sizes = {label: encode(ddt) for label, encode in SIZE_ENCODINGS}
        ratios = {other: sizes["min_dfa"] / sizes[other] for other in OTHERS}
        rows.append((name, sbox.input_size(), entropy(ddt), sizes, ratios))

    return rows


def write_tex(rows, path):
    lines = []
    lines.append(r"\documentclass{article}")
    lines.append(r"\usepackage{longtable}")
    lines.append(r"\usepackage{booktabs}")
    lines.append(r"\usepackage[landscape,margin=1cm]{geometry}")
    lines.append(r"\begin{document}")
    lines.append("")
    lines.append(r"\section*{Per-S-box storage and ratios}")
    lines.append("")
    lines.append(r"Sizes are in bytes. The first six numeric columns give the encoding sizes; "
                 r"the last five give the ratio $\mathrm{min\_dfa} / \mathrm{other}$ "
                 r"(values $<1$ mean min\_dfa is smaller).")
    lines.append("")
    lines.append(r"\footnotesize")
    lines.append(r"\setlength{\tabcolsep}{3pt}")
    lines.append(r"\begin{longtable}{lrrrrrrrr|rrrrr}")
    lines.append(r"\toprule")
    header = [
        "sbox", "$n$", "$H$",
        "entropy", "dense", "bitmap", "wavelet", "dfa", "min\\_dfa",
        r"$\frac{\mathrm{min\_dfa}}{\mathrm{entropy}}$",
        r"$\frac{\mathrm{min\_dfa}}{\mathrm{dense}}$",
        r"$\frac{\mathrm{min\_dfa}}{\mathrm{bitmap}}$",
        r"$\frac{\mathrm{min\_dfa}}{\mathrm{wavelet}}$",
        r"$\frac{\mathrm{min\_dfa}}{\mathrm{dfa}}$",
    ]
    lines.append(" & ".join(header) + r" \\")
    lines.append(r"\midrule")
    lines.append(r"\endfirsthead")
    lines.append(r"\toprule")
    lines.append(" & ".join(header) + r" \\")
    lines.append(r"\midrule")
    lines.append(r"\endhead")

    for name, n, h, sizes, ratios in rows:
        cells = [
            escape(name),
            str(n),
            f"{h:.3f}",
            f"{sizes['entropy']/8:.1f}",
            f"{sizes['dense']/8:.1f}",
            f"{sizes['bitmap']/8:.1f}",
            f"{sizes['wavelet']/8:.1f}",
            f"{sizes['dfa']/8:.1f}",
            f"{sizes['min_dfa']/8:.1f}",
            f"{ratios['entropy']:.3f}",
            f"{ratios['dense']:.3f}",
            f"{ratios['bitmap']:.3f}",
            f"{ratios['wavelet']:.3f}",
            f"{ratios['dfa']:.3f}",
        ]
        lines.append(" & ".join(cells) + r" \\")

    lines.append(r"\bottomrule")
    lines.append(r"\end{longtable}")
    lines.append("")
    lines.append(r"\section*{Ratio summary}")
    lines.append("")
    lines.append(r"For each ratio $\mathrm{min\_dfa} / \mathrm{other}$ across the "
                 f"{len(rows)} S-boxes: best (smallest), median, and worst (largest).")
    lines.append("")
    lines.append(r"\normalsize")
    lines.append(r"\begin{center}")
    lines.append(r"\begin{tabular}{lrrr}")
    lines.append(r"\toprule")
    lines.append(r"ratio & best & median & worst \\")
    lines.append(r"\midrule")
    for other in OTHERS:
        values = [r[4][other] for r in rows]
        best = min(values)
        worst = max(values)
        med = statistics.median(values)
        label = f"$\\mathrm{{min\\_dfa}} / \\mathrm{{{other}}}$"
        lines.append(f"{label} & {best:.3f} & {med:.3f} & {worst:.3f} \\\\")
    lines.append(r"\bottomrule")
    lines.append(r"\end{tabular}")
    lines.append(r"\end{center}")
    lines.append("")
    lines.append(r"\end{document}")

    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    rows = collect()
    write_tex(rows, "res.tex")
