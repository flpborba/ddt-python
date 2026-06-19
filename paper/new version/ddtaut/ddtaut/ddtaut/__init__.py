"""ddtaut -- cryptanalytic tables (DDT/LAT/BCT) as reduced quaternary automata."""
from .automaton import TableAutomaton
from . import encoding, tables, queries, validate

__all__ = ["TableAutomaton", "encoding", "tables", "queries", "validate"]
