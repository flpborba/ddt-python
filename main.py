"""
Solve a PRINCE differential MILP under one of five strategies that differ
in how an S-box's DDT (difference distribution table) is enforced:

  default       full DDT precompiled into the LP file.
  add-encoding  ADD-based DDT precompiled into the LP file.
  add           ADD-based DDT built at runtime on top of a reduced LP.
  add-path      reduced LP, ADD path cuts added lazily during search.
  qadd-path     reduced LP, quaternary-ADD path cuts added lazily.

The reduced LP only forbids zero-probability transitions and tracks which
S-boxes are active; the cost of every used transition is enforced either
up front (the *encoding* strategies) or as lazy cuts (the *path*
strategies).
"""

import argparse
import gurobipy
import re

from pathlib import Path
from sage.crypto.sboxes import PRINCE
from gurobipy import GRB

from differential.add import make_add
from differential.qadd import make_qadd, qtrace


ddt = PRINCE.difference_distribution_table()
ddt_full = ddt.__copy__()
ddt.add_to_entry(0, 0, -ddt[0, 0])

ADD_DDT = make_add(ddt)
ADD_DDT_FULL = make_add(ddt_full)
QADD_DDT = make_qadd(ddt)
NBITS = 4

# Probability of a non-zero DDT entry is encoded by two bits (p0, p1):
# entry 16 -> (0, 0)  ("transition is certain, no cost")
# entry  4 -> (1, 0)  (cost 2)
# entry  2 -> (0, 1)  (cost 4)
# the objective is min sum 2*p0 + 4*p1.
COST = {16: (0, 0), 4: (1, 0), 2: (0, 1)}


def collect_sboxes(model):
    """Group the LP's variables by S-box.

    Each LP file uses a flat naming convention (`xR_i`, `yR_i`, `pC_R_S`).
    This walks them once and returns a list of dicts, one per S-box, each
    holding its 4 input bits, 4 output bits, and 2 probability bits.
    """
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
    """Tie each S-box's activity bits (p0, p1) to its (x, y) bits.

    These are problem-wide constraints that hold regardless of which DDT
    encoding strategy is used. They say: at most one of (p0, p1) may be
    set; an S-box is active iff any of its x or y bits is set; and an
    active S-box must have both an active input and an active output.
    """
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
    """Walk the reduced ADD for the (a, b) transition.

    The ADD is a binary decision tree alternating between input bits
    (x_0, ..., x_{NBITS-1}) and output bits (y_0, ..., y_{NBITS-1}). The
    walk visits at most one node per bit and stops at a leaf carrying
    the DDT value (or zero, if the transition is impossible).

    Returns (path, leaf_value) where path lists the (level, bit) pairs
    actually consulted along the way.
    """
    bits = []
    for k in range(NBITS):
        bits.append((a >> (NBITS - 1 - k)) & 1)  # x_k
        bits.append((b >> (NBITS - 1 - k)) & 1)  # y_k

    node = ADD_DDT
    path = []

    while not node.is_terminal():
        bit = bits[node._index]
        path.append((node._index, bit))
        node = node._high if bit else node._low

    return path, int(node.value)


def path_disagreement(sbox, path):
    """Linear expression counting how many of the path's bits differ from
    the values they had on the traced solution.

    Used as a Hamming-distance-style separator: if the original solution
    is invalid, then any *other* solution must disagree on at least one
    bit on the path; if it is valid with cost (P0, P1), then any
    solution that agrees on all path bits must have the same cost.
    """
    terms = []

    for i, b in path:
        var = sbox["x"][i // 2] if i % 2 == 0 else sbox["y"][i // 2]
        terms.append((1 - var) if b else var)

    return gurobipy.quicksum(terms)


def qpath_disagreement(sbox, qpath):
    """Same as `path_disagreement`, but for a QADD path.

    A QADD level groups (x_k, y_k) into a single quaternary symbol, so
    each step of `qpath` contributes two bit-disagreement terms.
    """
    terms = []

    for k, sym in qpath:
        xb = (sym >> 1) & 1
        yb = sym & 1
        xv = sbox["x"][k]
        yv = sbox["y"][k]

        terms.append((1 - xv) if xb else xv)
        terms.append((1 - yv) if yb else yv)

    return gurobipy.quicksum(terms)


def make_path_callback(trace, disagreement):
    """Build a lazy-cut callback for a path-based DDT separator.

    `trace(a, b)` walks a decision diagram and returns `(path, entry)`.
    `disagreement(sbox, path)` turns a path into a Hamming-style linear
    expression on that S-box's variables.

    Whenever Gurobi finds a candidate integer solution, the callback
    inspects every S-box: if the (a, b) transition is impossible, every
    S-box receives a `disagreement(...) >= 1` cut so that no other S-box
    may pick this same illegal pattern; otherwise the callback enforces
    that any other S-box agreeing on the path must carry the same
    (p0, p1) cost.
    """
    def callback(model, where):
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

            path, entry = trace(a, b)
            key = (tuple(path), entry)

            if key in seen:
                continue

            seen.add(key)

            if entry == 0:
                for t in model._sboxes:
                    model.cbLazy(disagreement(t, path) >= 1)

                continue

            P0, P1 = COST[entry]

            for t in model._sboxes:
                dt = disagreement(t, path)

                model.cbLazy(t["p0"] - P0 + dt >= 0)
                model.cbLazy(P0 - t["p0"] + dt >= 0)
                model.cbLazy(t["p1"] - P1 + dt >= 0)
                model.cbLazy(P1 - t["p1"] + dt >= 0)

    return callback


callback_path = make_path_callback(
    trace=ddt_trace,
    disagreement=path_disagreement,
)

callback_qpath = make_path_callback(
    trace=lambda a, b: qtrace(QADD_DDT, a, b, NBITS),
    disagreement=qpath_disagreement,
)


def collect_add_nodes(root):
    """Return every node reachable from `root` (terminals included)."""
    nodes = {}
    stack = [root]
    while stack:
        n = stack.pop()
        if n._id in nodes:
            continue
        nodes[n._id] = n
        if not n.is_terminal():
            stack.append(n._low)
            stack.append(n._high)
    return nodes


def add_addmip_constraints(model, sboxes):
    """Encode the ADD as a flow MILP, replicated for every S-box.

    Each non-terminal ADD node `n` gets two flow variables per S-box:
    `flow_low[n]` is the flow that takes the low edge (bit = 0), and
    `flow_high[n]` the flow that takes the high edge. The encoding then
    enforces, for every S-box independently:

      1. exactly one path is taken from the root,
      2. flow conservation at every internal node,
      3. an edge can only carry flow if the matching bit picks it,
      4. the impossible-transition leaf carries no flow,
      5. the (p0, p1) probability bits match the leaf the path lands on.
    """
    nodes = collect_add_nodes(ADD_DDT_FULL)
    decisions = [nid for nid, n in nodes.items() if not n.is_terminal()]
    leaves = [nid for nid, n in nodes.items() if n.is_terminal()]
    root_id = ADD_DDT_FULL._id

    # For each node, list the parent edges that point at it.
    parents = {nid: [] for nid in nodes}
    for nid in decisions:
        n = nodes[nid]
        parents[n._low._id].append((nid, "low"))
        parents[n._high._id].append((nid, "high"))

    for s_idx, s in enumerate(sboxes):
        bit_var = lambda i: s["x"][i // 2] if i % 2 == 0 else s["y"][i // 2]

        # Flow variables: one pair per non-terminal node.
        flow_low = {}
        flow_high = {}

        for nid in decisions:
            flow_low[nid] = model.addVar(
                lb=0,
                ub=1,
                vtype=GRB.CONTINUOUS,
                name=f"flo_s{s_idx}_n{nid}"
            )

            flow_high[nid] = model.addVar(
                lb=0,
                ub=1,
                vtype=GRB.CONTINUOUS,
                name=f"fhi_s{s_idx}_n{nid}"
            )

        def flow(pid, edge):
            return flow_low[pid] if edge == "low" else flow_high[pid]

        # (1) Exactly one path leaves the root.
        model.addConstr(flow_low[root_id] + flow_high[root_id] == 1)

        # (2) Flow conservation at every other non-terminal node.
        for nid in decisions:
            if nid == root_id:
                continue

            inflow = gurobipy.quicksum(flow(p, e) for p, e in parents[nid])
            model.addConstr(flow_low[nid] + flow_high[nid] == inflow)

        # (3) Couple edge selection to the matching bit value.
        for nid in decisions:
            n = nodes[nid]
            xi = bit_var(n._index)
            model.addConstr(flow_high[nid] <= xi)
            model.addConstr(flow_low[nid] <= 1 - xi)

        # Inflow per leaf, grouped by leaf value.
        leaf_inflow = {}

        for tid in leaves:
            v = int(nodes[tid].value)

            leaf_inflow[v] = gurobipy.quicksum(
                flow(p, e) for p, e in parents[tid]
            )

        # (4) The impossible-transition leaf must not be reached.
        if 0 in leaf_inflow:
            model.addConstr(leaf_inflow[0] == 0)

        # (5) Couple p0 / p1 to the leaf the path lands on.
        p0_terms = []
        p1_terms = []

        for v, expr in leaf_inflow.items():
            if v == 0:
                continue

            p0v, p1v = COST[v]

            if p0v:
                p0_terms.append(expr)
            if p1v:
                p1_terms.append(expr)

        model.addConstr(s["p0"] == gurobipy.quicksum(p0_terms))
        model.addConstr(s["p1"] == gurobipy.quicksum(p1_terms))

    model.update()


def run(strategy, model_idx, rounds, seed):
    """Load the right LP for `strategy` and solve it."""
    lp_kind = {"default": "full", "add-encoding": "add"}.get(strategy, "reduced")
    file = Path(f"./models/prince_{model_idx}_{rounds}_{lp_kind}.lp")

    model = gurobipy.read(str(file))
    model.Params.Seed = seed

    if strategy in ("default", "add-encoding"):
        model.optimize()
        return model

    model._sboxes = collect_sboxes(model)
    add_activity_constraints(model, model._sboxes)

    if strategy == "add":
        add_addmip_constraints(model, model._sboxes)
        model.optimize()
    else:
        model.Params.LazyConstraints = 1
        model._seen = set()

        cb = callback_path if strategy == "add-path" else callback_qpath
        model.optimize(cb)

    return model


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "strategy",
        choices=("default", "add-encoding", "add", "add-path", "qadd-path"),
        help="solving strategy"
    )

    parser.add_argument(
        "-m",
        "--model",
        type=int,
        default=0,
        help="PRINCE XOR model (0-2, default: 0)"
    )

    parser.add_argument(
        "-r",
        "--rounds",
        type=int,
        default=2,
        help="number of rounds (default: 2)"
    )

    parser.add_argument(
        "-s",
        "--seed",
        type=int,
        default=0,
        help="Gurobi random seed (default: 0)"
    )

    args = parser.parse_args()
    run(args.strategy, args.model, args.rounds, args.seed)
