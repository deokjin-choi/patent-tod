"""Run settings for the EM / MCMC skeleton. All paths are relative to this folder."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT / "out"

# Parent repo Lens export. This skeleton never reads the FL pilot folder.
SOURCE_PATENTS = ROOT.parent / "data" / "edge-ai-all-2010-2025.csv"

DICTIONARY = DATA / "dictionary.json"
CONSTRAINTS = DATA / "constraints.json"
PATENTS = DATA / "patents.csv"
MANIFEST = DATA / "manifest.json"

SEED = 42
N_PATENTS = 400

EM_MAX_ITER = 40
EM_TOL = 1e-4
EM_SMOOTH = 0.5

MCMC_ITERS = 250
MCMC_BURNIN = 50
MCMC_THIN = 5
ADMIXTURE_ALPHA = 0.5
ADMIXTURE_BETA = 0.5

CONSTRAINT_A = 1.0
CONSTRAINT_B = 1.0

# PSE / KG v1 review (modify folder). Not used by the keyword EM run.
PSE_MODIFY = ROOT.parent / "data" / "pse_knowlege_graph_modifiy"
ENTITY_STD = ROOT.parent / "data" / "knowlege_graph_entity_relation" / "final_standardization_results.json"
OUT_PSE = ROOT / "out_pse"
FIG_PSE = ROOT / "figures_pse"
OUT_KG = ROOT / "out_kg_v1"
FIG_KG = ROOT / "figures_kg_v1"

# Per-axis mixture on v1 relations + essay tokens. Axes are the four v1 predicates.
OUT_KG_EM = ROOT / "out_kg_em"
FIG_KG_EM = ROOT / "figures_kg_em"
KG_EM_K_MIN = 2
KG_EM_K_MAX = 6
KG_EM_MIN_DF = 5
KG_EM_MAX_HEADS = 150
KG_EM_MAX_ESSAY = 80
KG_EM_N_INIT = 8
KG_EM_HOLDOUT = 0.2
KG_EM_SEED = 42
