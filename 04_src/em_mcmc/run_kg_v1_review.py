"""KG v1 head review. Does not read pse. Does not rerun keyword EM."""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

for name in ("12_kg_v1_heads.py", "13_kg_v1_plots.py"):
    print("=" * 60, name)
    runpy.run_path(str(ROOT / name), run_name="__main__")
print("Done. Read docs/kg_v1_review.md")
