#!/usr/bin/env python3
"""Build the DDT, LAT, and BCT automata for every S-box in the SageMath library
and write a per-S-box CSV of compression ratios. Each automaton is checked
cell-by-cell against its dense table before its size is recorded.

Usage:  python scripts/sweep_library.py [out.csv]
"""
import csv
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sage.crypto.sboxes import sboxes  # noqa: E402

from ddtaut import TableAutomaton, tables, validate  # noqa: E402

FIELDS = ["name", "n", "delta", "ddt_states", "ddt_ratio",
          "lin", "lat_states", "lat_ratio", "lat_values",
          "beta", "bct_states", "bct_ratio"]


def measure(table, n):
    aut = TableAutomaton.from_matrix(table, n)
    assert validate.cells_equal_table(aut, table)
    cells = (1 << n) * (1 << n)
    return aut, round(cells / aut.num_states(), 2)


def row_for(name, sbox):
    if int(sbox.input_size()) != int(sbox.output_size()):
        return None
    ddt_tab, n = tables.ddt(sbox)
    cells = (1 << n) * (1 << n)
    rec = {"name": name, "n": n, "delta": tables.differential_uniformity(ddt_tab)}
    ddt_aut, rec["ddt_ratio"] = measure(ddt_tab, n)
    rec["ddt_states"] = ddt_aut.num_states()

    lat_tab, _ = tables.lat(sbox)
    lat_aut, rec["lat_ratio"] = measure(lat_tab, n)
    rec["lat_states"] = lat_aut.num_states()
    rec["lat_values"] = lat_aut.distinct_values()
    rec["lin"] = tables.linearity(lat_tab)

    if sbox.is_permutation():
        bct_tab, _ = tables.bct(sbox)
        bct_aut, rec["bct_ratio"] = measure(bct_tab, n)
        rec["bct_states"] = bct_aut.num_states()
        rec["beta"] = tables.boomerang_uniformity(bct_tab)
    else:
        rec["bct_states"] = rec["bct_ratio"] = rec["beta"] = ""
    return rec


def main(out_path):
    t0 = time.time()
    rows = []
    for name in sorted(sboxes, key=lambda k: (sboxes[k].input_size(), k)):
        rec = row_for(name, sboxes[name])
        if rec is not None:
            rows.append(rec)
    with open(out_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows to {out_path} in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "sbox_tables_full.csv")
