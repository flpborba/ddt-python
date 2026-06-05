"""
Solve a PRINCE MILP model for 2 rounds.
"""

import argparse
import gurobipy

from pathlib import Path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "-m",
        "--model",
        type=int,
        default=0,
        help="PRINCE model (0-3, default: 0)"
    )

    args = parser.parse_args()
    file = Path(f"./models/prince_{args.model}_2_full.lp")

    model = gurobipy.read(str(file))
    model.optimize()
