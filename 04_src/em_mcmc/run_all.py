"""Run the skeleton in order: sample -> matrix -> EM -> MCMC -> quality."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import os
os.chdir(ROOT)

STEPS = [
    "00_prepare_data.py",
    "01_build_matrix.py",
    "02_run_em.py",
    "03_run_mcmc.py",
    "04_quality.py",
]


def main() -> None:
    for name in STEPS:
        print("\n" + "=" * 60)
        print("RUN", name)
        print("=" * 60)
        runpy.run_path(str(ROOT / name), run_name="__main__")
    print("\nDone. Read out/04_report.txt and docs/outputs.md")


if __name__ == "__main__":
    main()
