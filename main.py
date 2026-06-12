"""
Solve a PRINCE MILP model for 2 rounds.
"""

import argparse
import gurobipy
import re

from pathlib import Path
from sage.crypto.sboxes import PRINCE
from gurobipy import GRB

from differential.add import make_add


ddt = PRINCE.difference_distribution_table()
ddt.add_to_entry(0, 0, -ddt[0, 0])

ADD_DDT = make_add(ddt)
NBITS = 4
COST = {16: (0, 0), 4: (1, 0), 2: (0, 1)}


def collect_sboxes(model):
    sboxes = {}

    for var in model.getVars():
        if m := re.match(r"^x(\d+)_(\d+)$", var.VarName):
            r = int(m[1])
            r_bit = int(m[2])

            s = r_bit // 4
            s_bit = r_bit % 4

            bits = sboxes \
                .setdefault((r, s), {}) \
                .setdefault("x", [None] * 4)

            bits[s_bit] = var

        elif m := re.match(r"^y(\d+)_(\d+)$", var.VarName):
            r = int(m[1])
            r_bit = int(m[2])

            s = r_bit // 4
            s_bit = r_bit % 4

            bits = sboxes \
                .setdefault((r, s), {}) \
                .setdefault("y", [None] * 4)

            bits[s_bit] = var

        elif m := re.match(r"^p([01])_(\d+)_(\d+)$", var.VarName):
            c = m[1]
            r = int(m[2])
            s = int(m[3])

            sbox = sboxes.setdefault((r, s), {})

            sbox[f"p{c}"] = var

    return [sboxes[key] for key in sorted(sboxes)]


def add_activity_constraints(model, sboxes):
    for s in sboxes:
        p_sum = s["p0"] + s["p1"]
        model.addConstr(p_sum <= 1)

        for v in s["x"] + s["y"]:
            model.addConstr(p_sum >= v)

        sum_input = gurobipy.quicksum(s["x"])
        sum_output = gurobipy.quicksum(s["y"])

        model.addConstr(p_sum <= sum_input + sum_output)

        for j in range(4):
            model.addConstr(sum_output >= s["x"][j])
            model.addConstr(sum_input >= s["y"][j])

    model.update()


def ddt_trace(a, b):
    bits = {}
    for k in range(NBITS):
        bits[2 * k] = (a >> (NBITS - 1 - k)) & 1
        bits[2 * k + 1] = (b >> (NBITS - 1 - k)) & 1

    node = ADD_DDT
    path = []

    while not node.is_terminal():
        i = node._index
        v = bits[i]
        path.append((i, v))
        node = node._high if v else node._low

    return path, int(node.value)


def path_disagreement(sbox, path):
    terms = []

    for i, b in path:
        var = sbox["x"][i // 2] if i % 2 == 0 else sbox["y"][i // 2]
        terms.append((1 - var) if b else var)

    return gurobipy.quicksum(terms)


def hamming_disagreement(sbox, xv, yv):
    terms = []

    for v, b in zip(sbox["x"], xv):
        terms.append((1 - v) if b else v)
    for v, b in zip(sbox["y"], yv):
        terms.append((1 - v) if b else v)

    return gurobipy.quicksum(terms)


def callback_hamming(model, where):
    if where != GRB.Callback.MIPSOL:
        return

    seen = model._seen

    for s in model._sboxes:
        xv = [int(round(model.cbGetSolution(v))) for v in s["x"]]
        yv = [int(round(model.cbGetSolution(v))) for v in s["y"]]

        a = int("".join(map(str, xv)), 2)
        b = int("".join(map(str, yv)), 2)

        if (a, b) == (0, 0):
            continue

        _, entry = ddt_trace(a, b)
        key = (a, b)

        if key in seen:
            continue

        seen.add(key)

        if entry == 0:
            for t in model._sboxes:
                model.cbLazy(hamming_disagreement(t, xv, yv) >= 1)

            continue

        P0, P1 = COST[entry]

        for t in model._sboxes:
            dt = hamming_disagreement(t, xv, yv)

            model.cbLazy(t["p0"] - P0 + dt >= 0)
            model.cbLazy(P0 - t["p0"] + dt >= 0)
            model.cbLazy(t["p1"] - P1 + dt >= 0)
            model.cbLazy(P1 - t["p1"] + dt >= 0)


def callback_path(model, where):
    if where != GRB.Callback.MIPSOL:
        return

    seen = model._seen

    for s in model._sboxes:
        xv = [int(round(model.cbGetSolution(v))) for v in s["x"]]
        yv = [int(round(model.cbGetSolution(v))) for v in s["y"]]

        a = int("".join(map(str, xv)), 2)
        b = int("".join(map(str, yv)), 2)

        if (a, b) == (0, 0):
            continue

        path, entry = ddt_trace(a, b)
        key = (tuple(path), entry)

        if key in seen:
            continue

        seen.add(key)

        if entry == 0:
            for t in model._sboxes:
                model.cbLazy(path_disagreement(t, path) >= 1)

            continue

        P0, P1 = COST[entry]

        for t in model._sboxes:
            dt = path_disagreement(t, path)

            model.cbLazy(t["p0"] - P0 + dt >= 0)
            model.cbLazy(P0 - t["p0"] + dt >= 0)
            model.cbLazy(t["p1"] - P1 + dt >= 0)
            model.cbLazy(P1 - t["p1"] + dt >= 0)


CALLBACKS = {"hamming": callback_hamming, "path": callback_path}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "mode",
        choices=("reduced", "full"),
        default="reduced",
        help="model type (default: reduced)"
    )

    parser.add_argument(
        "-m",
        "--model",
        type=int,
        default=0,
        help="PRINCE model (0-3, default: 0)"
    )

    parser.add_argument(
        "-r",
        "--rounds",
        type=int,
        default=2,
        help="number of rounds (default: 2)"
    )

    parser.add_argument(
        "-c",
        "--cuts",
        choices=("hamming", "path"),
        default="hamming",
        help="reduced-mode lazy-cut style (default: hamming)"
    )

    args = parser.parse_args()
    file = Path(f"./models/prince_{args.model}_{args.rounds}_{args.mode}.lp")

    model = gurobipy.read(str(file))

    if args.mode == "full":
        model.optimize()
    else:
        model.Params.LazyConstraints = 1

        model._sboxes = collect_sboxes(model)
        model._seen = set()

        add_activity_constraints(model, model._sboxes)

        model.optimize(CALLBACKS[args.cuts])
