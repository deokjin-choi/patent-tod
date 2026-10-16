"""Inventory PSE/KG v1 slots. Does not rerun keyword EM/MCMC."""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

for name in ("10_pse_slot_inventory.py", "11_pse_slot_plots.py"):
    print("=" * 60, name)
    runpy.run_path(str(ROOT / name), run_name="__main__")
print("Done. Read out_pse/ and docs/pse_slot_review.md")
