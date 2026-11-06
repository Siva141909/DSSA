"""The frozen gate2_analysis.py, with one mapping: Layer 2 seed 1000 is run
p2d_oracle_L02_s1000_a2. The interrupted p2d_oracle_L02_s1000 has no results
and is never read as a result."""
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gate2_analysis as G  # noqa: E402

_rid = G.rid
G.rid = lambda a, s: "p2d_oracle_L02_s1000_a2" if (a, s) == (2, 1000) else _rid(a, s)

if __name__ == "__main__":
    G.main()
