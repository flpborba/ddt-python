#!/usr/bin/env python3
"""Emit the numeric data behind the paper's figures: the 2x2 block-frequency
map of the PRESENT DDT (Table 1) and the reduced SEA automaton structure
(Fig. 'SEA reduced'). Pure Python; no Sage required.

Usage:  python scripts/figures_data.py
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ddtaut import TableAutomaton, tables

PRESENT_LUT = [0xC, 5, 6, 0xB, 9, 0, 0xA, 0xD, 3, 0xE, 0xF, 8, 4, 7, 1, 2]
SEA_DDT = [[0, 0, 0, 0, 0, 0, 0, 0], [0, 2, 0, 2, 0, 2, 0, 2],
           [0, 2, 2, 0, 0, 2, 2, 0], [0, 0, 2, 2, 0, 0, 2, 2],
           [0, 0, 0, 0, 2, 2, 2, 2], [0, 2, 0, 2, 2, 0, 2, 0],
           [0, 2, 2, 0, 2, 0, 0, 2], [0, 0, 2, 2, 2, 2, 0, 0]]


def present_block_frequencies():
    table, _ = tables.ddt(PRESENT_LUT)
    blocks = Counter()
    for i in range(0, 16, 2):
        for j in range(0, 16, 2):
            block = (table[i][j], table[i][j + 1], table[i + 1][j], table[i + 1][j + 1])
            blocks[block] += 1
    return table, blocks


def sea_reduced_structure():
    aut = TableAutomaton.from_matrix(SEA_DDT, 3)
    edges = []
    for u in aut.nodes():
        if not aut.is_terminal(u):
            grouped = {}
            for sigma in range(4):
                grouped.setdefault(aut.child(u, sigma), []).append(sigma)
            for target, syms in grouped.items():
                edges.append((u, "".join(map(str, syms)), target,
                              "T(%d)" % aut.value(target) if aut.is_terminal(target) else "N"))
    return aut, edges


if __name__ == "__main__":
    table, blocks = present_block_frequencies()
    print("PRESENT DDT 2x2 block frequencies (block -> count):")
    for block, count in blocks.most_common():
        print(f"  {block} : {count}")
    print(f"  distinct block patterns: {len(blocks)};  all-zero blocks: {blocks[(0,0,0,0)]}")

    aut, edges = sea_reduced_structure()
    print(f"\nSEA reduced automaton: {aut.num_states()} states, "
          f"{aut.num_transitions()} non-dead transitions")
    for src, syms, dst, kind in sorted(edges):
        print(f"  state {src} --{syms}--> {dst} [{kind}]")
