"""The frozen gate2_analysis.py, with two mappings: Layer 2 seed 1000 is run
p2d_oracle_L02_s1000_a2 and Layer 6 seed 1000 is run p2d_oracle_L06_s1000_a2.
The interrupted p2d_oracle_L02_s1000 and p2d_oracle_L06_s1000 have no results
and are never read as results."""
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gate2_analysis as G  # noqa: E402

_rid = G.rid
RERUNS = {(2, 1000): "p2d_oracle_L02_s1000_a2", (6, 1000): "p2d_oracle_L06_s1000_a2"}
G.rid = lambda a, s: RERUNS.get((a, s)) or _rid(a, s)

if __name__ == "__main__":
    G.main()
