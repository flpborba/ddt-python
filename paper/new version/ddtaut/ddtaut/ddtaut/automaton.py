"""The table automaton: a reduced, ordered, multi-terminal quaternary diagram.

A square integer table ``T`` over ``2^n x 2^n`` cells is represented as an
ordered multi-terminal decision diagram over the interleaved variable order
``a_{n-1}, b_{n-1}, ..., a_0, b_0`` (see :mod:`ddtaut.encoding`). Each internal
node carries its level and four children (one per symbol); terminals carry an
integer value. Three reductions make the diagram canonical for a fixed order:

1. terminals are shared, one per distinct value (a single *dead* terminal for 0);
2. a node whose four children coincide is a don't-care and is replaced by that
   child (variable skipping);
3. two internal nodes *at the same level* with identical children are merged.

The level qualifier in rule (3) is essential: node identity is ``(level,
children)``, exactly as in an ordered BDD. Omitting it merges nodes across depths
and silently corrupts evaluation.

The construction is table-agnostic; :mod:`ddtaut.tables` supplies the DDT, LAT,
and BCT matrices that instantiate it.
"""
from __future__ import annotations

import sys
from typing import Sequence

from .encoding import ALPHABET

sys.setrecursionlimit(1 << 20)


class TableAutomaton:
    """Reduced quaternary MTBDD for a ``2^n x 2^n`` integer table."""

    __slots__ = ("n", "_kind", "_kids", "_val", "_lvl", "_index", "root", "_reachable")

    def __init__(self, table: Sequence[Sequence[int]], n: int) -> None:
        self.n = n
        self._kind: dict[int, str] = {}     # node id -> 'T' (terminal) | 'N' (internal)
        self._kids: dict[int, tuple] = {}    # internal id -> (c0, c1, c2, c3)
        self._val: dict[int, int] = {}       # terminal id -> value
        self._lvl: dict[int, int] = {}       # node id -> level (terminals: n)
        self._index: dict[tuple, int] = {}   # canonical key -> node id
        self.root = self._build(table, list(range(1 << n)), list(range(1 << n)), 0)
        self._reachable = self._reach()

    # ---- construction -----------------------------------------------------
    def _terminal(self, value: int) -> int:
        key = ("T", value)
        node = self._index.get(key)
        if node is None:
            node = len(self._index)
            self._index[key] = node
            self._kind[node] = "T"
            self._val[node] = value
            self._lvl[node] = self.n
        return node

    def _internal(self, children: tuple, level: int) -> int:
        key = ("N", level, children)
        node = self._index.get(key)
        if node is None:
            node = len(self._index)
            self._index[key] = node
            self._kind[node] = "N"
            self._kids[node] = children
            self._lvl[node] = level
        return node

    def _build(self, table, rows, cols, level) -> int:
        if level == self.n:
            return self._terminal(table[rows[0]][cols[0]])
        half = len(rows) // 2
        top, bot = rows[:half], rows[half:]
        left, right = cols[:half], cols[half:]
        children = (
            self._build(table, top, left, level + 1),
            self._build(table, top, right, level + 1),
            self._build(table, bot, left, level + 1),
            self._build(table, bot, right, level + 1),
        )
        if children[0] == children[1] == children[2] == children[3]:
            return children[0]                       # don't-care elimination
        return self._internal(children, level)

    def _reach(self) -> frozenset:
        seen, stack = set(), [self.root]
        while stack:
            node = stack.pop()
            if node in seen:
                continue
            seen.add(node)
            if self._kind[node] == "N":
                stack.extend(self._kids[node])
        return frozenset(seen)

    # ---- accessors (used by queries and figure generation) ----------------
    def is_terminal(self, node: int) -> bool:
        return self._kind[node] == "T"

    def level(self, node: int) -> int:
        return self._lvl[node]

    def value(self, node: int) -> int:
        return self._val[node]

    def child(self, node: int, sigma: int) -> int:
        return self._kids[node][sigma]

    @property
    def dead(self) -> int:
        """The shared zero terminal (reject / dead state)."""
        return self._index[("T", 0)]

    def nodes(self):
        return iter(self._reachable)

    def terminals(self):
        return (u for u in self._reachable if self._kind[u] == "T")

    # ---- metrics ----------------------------------------------------------
    def num_states(self) -> int:
        """Reachable nodes, counting internal, accepting, and the dead terminal."""
        return len(self._reachable)

    def num_transitions(self) -> int:
        """Edges of reachable internal nodes that do not point to the dead state."""
        dead = self.dead
        return sum(1 for u in self._reachable if self._kind[u] == "N"
                   for c in self._kids[u] if c != dead)

    def distinct_values(self) -> int:
        return len({self._val[u] for u in self.terminals()})

    def memory_bytes(self) -> int:
        """Footprint of the four-field state array; field width follows |S|."""
        s = self.num_states()
        width = 1 if s <= 255 else (2 if s <= 65535 else 4)
        return s * 4 * width

    # ---- evaluation -------------------------------------------------------
    def evaluate(self, a: int, b: int) -> int:
        """Return ``T[a][b]`` by walking the diagram, honouring skipped levels."""
        node = self.root
        for i in range(self.n):
            if self._kind[node] == "T":
                return self._val[node]
            if self._lvl[node] == i:
                a_bit = (a >> (self.n - 1 - i)) & 1
                b_bit = (b >> (self.n - 1 - i)) & 1
                node = self._kids[node][2 * a_bit + b_bit]
        return self._val[node]

    @classmethod
    def from_matrix(cls, table: Sequence[Sequence[int]], n: int) -> "TableAutomaton":
        return cls(table, n)
