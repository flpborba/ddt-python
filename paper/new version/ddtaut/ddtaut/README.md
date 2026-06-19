# ddtaut — cryptanalytic tables as reduced quaternary automata

Represents the DDT, LAT, and BCT of an S-box as a reduced ordered multi-terminal
quaternary decision diagram, and answers cryptanalytic queries by automata
intersection without materialising the dense table.

## Layout
    ddtaut/
      encoding.py    quadrant encoding (single source of truth: sigma = 2*a + b)
      automaton.py   TableAutomaton: reduced, level-aware MTBDD over Sigma={0,1,2,3}
      tables.py      build DDT / LAT / BCT from a Sage SBox or a raw lookup list
      queries.py     query-automaton library + joint-traversal engine
      validate.py    brute-force oracle + cell-by-cell round-trip check
    scripts/
      sweep_library.py   representation sweep over sage.crypto.sboxes -> CSV
      run_queries.py     validated query suite (DDT, LAT, BCT)
      figures_data.py    data behind the paper's figures (no Sage required)
    tests/
      test_selftest.py   automaton == table, and queries == brute force

## Use
    python tests/test_selftest.py        # no Sage needed
    python scripts/figures_data.py       # no Sage needed
    python scripts/run_queries.py        # needs SageMath
    python scripts/sweep_library.py out.csv   # needs SageMath
