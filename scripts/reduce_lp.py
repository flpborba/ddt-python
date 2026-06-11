"""Strip per-S-box constraints from a full PRINCE differential LP.

A "full" LP has, for every S-box, a block of 23 constraints that encode the
S-box DDT polytope (in terms of input bits x, output bits y, and cost
indicator vars p0/p1) plus an x<->y activity coupling. The "reduced" LP is
the same model with those 23 lines per S-box removed; the missing semantics
are recovered at solve time by a lazy callback driven by the DDT automaton.

This script mechanically reproduces the reduced LP from the full LP by
dropping every line that matches one of these patterns:

    1. activity coupling (x->y):   "+ 4 xR_a + ... - yR_a - ... >= 0"
    2. activity coupling (y->x):   "+ 4 yR_a + ... - xR_a - ... >= 0"
    3. cost mutex:                 "-1 p0_R_i -1 p1_R_i >= -1"
    4. DDT polytope inequalities:  any line mentioning >= 1 x, >= 1 y,
                                   AND >= 1 p variable.

Usage:
    python scripts/reduce_lp.py models/prince_2_2_full.lp out.lp
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

X_RE = re.compile(r"\bx\d+_\d+\b")
Y_RE = re.compile(r"\by\d+_\d+\b")
P_RE = re.compile(r"\bp[01]_\d+_\d+\b")

ACT_XY_RE = re.compile(r"^\s*\+ 4 x\d+_\d+(?: \+ 4 x\d+_\d+){3} (?:- y\d+_\d+ ?){4}>= 0\s*$")
ACT_YX_RE = re.compile(r"^\s*\+ 4 y\d+_\d+(?: \+ 4 y\d+_\d+){3} (?:- x\d+_\d+ ?){4}>= 0\s*$")
MUTEX_RE = re.compile(r"^\s*-1 p0_\d+_\d+ -1 p1_\d+_\d+ >= -1\s*$")


def is_sbox_constraint(line: str) -> bool:
    if ACT_XY_RE.match(line) or ACT_YX_RE.match(line) or MUTEX_RE.match(line):
        return True
    has_x = bool(X_RE.search(line))
    has_y = bool(Y_RE.search(line))
    has_p = bool(P_RE.search(line))
    return has_x and has_y and has_p


def reduce_lp(full_text: str) -> str:
    out = []
    for line in full_text.splitlines(keepends=True):
        if is_sbox_constraint(line):
            continue
        out.append(line)
    return "".join(out)


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    src, dst = Path(argv[1]), Path(argv[2])
    dst.write_text(reduce_lp(src.read_text()))
    print(f"wrote {dst} ({dst.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
