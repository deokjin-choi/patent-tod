"""Per-axis mixture EM on v1 relations + essays. Does not rerun keyword EM."""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

for name in ("20_kg_em_features.py", "21_kg_em_fit.py", "22_kg_em_plots.py"):
    print("=" * 60, name)
    runpy.run_path(str(ROOT / name), run_name="__main__")
print("Done. Read docs/kg_em_review.md")
