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

        for j in range(4):
            model.addConstr(sum_output >= s["x"][j])
            model.addConstr(sum_input >= s["y"][j])

    model.update()


def hamming_dist(vars, bits):
    return gurobipy.quicksum((1 - v) if b else v for v, b in zip(vars, bits))


def ddt_entry(a, b):
    if (a, b) == (0, 0):
        return 16

    val = {}

    for k in range(NBITS):
        val[2 * k] = bool((a >> (NBITS - 1 - k)) & 1)
        val[2 * k + 1] = bool((b >> (NBITS - 1 - k)) & 1)

    return int(ADD_DDT.restrict(val).value)


def callback(model, where):
    if where != GRB.Callback.MIPSOL:
        return

    seen = model._seen

    for s in model._sboxes:
        xv = [int(round(model.cbGetSolution(v))) for v in s["x"]]
        yv = [int(round(model.cbGetSolution(v))) for v in s["y"]]

        a = int("".join(map(str, xv)), 2)
        b = int("".join(map(str, yv)), 2)

        entry = ddt_entry(a, b)

        if entry == 0:
            if ("bad", a, b) not in seen:
                seen.add(("bad", a, b))

                for t in model._sboxes:
                    model.cbLazy(hamming_dist(t["x"] + t["y"], xv + yv) >= 1)

            continue

        P0, P1 = COST[entry]

        if ("cost", a, b) not in seen:
            seen.add(("cost", a, b))

            for t in model._sboxes:
                dt = hamming_dist(t["x"] + t["y"], xv + yv)

                model.cbLazy(t["p0"] - P0 + dt >= 0)
                model.cbLazy(P0 - t["p0"] + dt >= 0)
                model.cbLazy(t["p1"] - P1 + dt >= 0)
                model.cbLazy(P1 - t["p1"] + dt >= 0)


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

    args = parser.parse_args()
    file = Path(f"./models/prince_{args.model}_2_{args.mode}.lp")

    model = gurobipy.read(str(file))

    if args.mode == "full":
        model.optimize()
    else:
        model.Params.LazyConstraints = 1
        model.Params.Presolve = 0

        model._sboxes = collect_sboxes(model)
        model._seen = set()

        add_activity_constraints(model, model._sboxes)

        model.optimize(callback)
