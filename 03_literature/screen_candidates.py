"""후보 bib를 관련성·저널·연도로 걸러 추가 후보 표를 만든다."""

import re
from collections import defaultdict
from pathlib import Path

BIB = Path(__file__).resolve().parent / "bib"

JOURNALS = {
    "technological forecasting and social change": 3,
    "technovation": 3,
    "research policy": 3,
    "scientometrics": 3,
    "journal of informetrics": 3,
    "futures": 3,
    "ieee transactions on engineering management": 3,
    "r and d management": 3,
    "r&d management": 3,
    "technology analysis and strategic management": 3,
    "technology analysis & strategic management": 3,
    "expert systems with applications": 3,
    "advanced engineering informatics": 3,
    "computers in industry": 3,
    "world patent information": 3,
    "journal of engineering design": 3,
    "design studies": 3,
    "design science": 3,
    "information processing and management": 3,
    "journal of the association for information science and technology": 3,
    "journal of the american society for information science and technology": 3,
    "knowledge-based systems": 3,
    "information sciences": 2,
    "foresight": 2,
    "european journal of operational research": 3,
    "decision support systems": 3,
    "journal of cleaner production": 2,
    "energy research and social science": 2,
    "energy research & social science": 2,
    "global environmental change": 3,
    "climatic change": 2,
    "energy policy": 2,
    "nature": 3,
    "nature communications": 3,
    "nature machine intelligence": 3,
    "science": 3,
    "proceedings of the national academy of sciences": 3,
    "scientific reports": 1,
    "plos one": 1,
    "ieee access": 1,
    "sustainability": 1,
    "applied sciences": 0,
}

POS = {
    "01_tmo_morphology": [
        "technology opportunity", "technological opportunity", "morpholog", "patent map",
        "patent vacuum", "vacant", "sao", "technology opportunity discovery", "tod",
        "unoccupied", "keyword-based", "function-based tod", "novelty-focused patent",
        "technology opportunity analysis", "opportunity identification",
    ],
    "02_kg_embedding": [
        "knowledge graph", "embedding", "patent similar", "link prediction",
        "technology convergence", "technet", "recombin", "combinatorial",
        "semantic network", "patent distance", "knowledge flow", "graph embedding",
        "problem-solution", "technology combination",
    ],
    "03_temporal_validation": [
        "forecast accuracy", "emerging technolog", "out-of-sample", "predictability",
        "early identification", "leakage", "retrospective", "validation",
        "technology forecast", "emerging clusters", "life cycle",
    ],
    "04_scenario_quality": [
        "scenario", "morphological analysis", "cross consistency", "plausib",
        "scenario quality", "scenario set", "foresight", "consistency",
        "intuitive logics", "cross-impact", "scenario discovery",
    ],
}

MUST = [
    "patent", "technolog", "scenario", "foresight", "forecast", "morpholog",
    "opportunity", "convergence", "knowledge graph", "embedding",
]
NOISE = [
    "strawberry", "ovarian", "ultrasound", "aphasia", "drone detection",
    "traditional chinese medicine", "tamil", "third-grade", "cfrp composite",
    "sustaining members", "job demand", "management accounting",
    "electric power enterpr", "micromechanics", "cell and gene therapy",
    "eco industrial park", "writing assessment",
]


def field(e, name):
    m = re.search(rf"^  {name} = \{{(.*)\}}\s*,?\s*$", e, re.M | re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip(" {}") if m else ""


def parse(path):
    text = path.read_text(encoding="utf-8")
    out = []
    for e in re.split(r"(?=@\w+\{)", text):
        if not e.strip().startswith("@"):
            continue
        title, journal = field(e, "title"), field(e, "journal")
        year_s, doi = field(e, "year"), field(e, "doi").lower()
        abstract, keywords = field(e, "abstract"), field(e, "keywords")
        author = field(e, "author")
        strand = keywords.split(";")[0].strip() if keywords else path.stem.replace("_candidates", "")
        out.append({
            "title": title, "journal": journal, "year": int(year_s) if year_s.isdigit() else 0,
            "doi": doi, "abstract": abstract, "author": author, "strand": strand,
            "raw": e, "src": path.name,
        })
    return out


def jnorm(s):
    s = s.lower().replace("&", "and")
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def journal_score(name):
    n = jnorm(name)
    if n in JOURNALS:
        return JOURNALS[n]
    for k, v in JOURNALS.items():
        if k in n or n in k:
            return v
    return 0


def rel_score(r):
    blob = f"{r['title']} {r['abstract']}".lower()
    if any(x in blob for x in NOISE):
        return 0
    if not any(x in blob for x in MUST):
        return 0
    hits = sum(1 for p in POS.get(r["strand"], []) if p in blob)
    extra = 0
    if "patent" in blob and ("opportunity" in blob or "morpholog" in blob or "scenario" in blob):
        extra += 2
    if "patent" in blob and ("knowledge graph" in blob or "embedding" in blob or "link prediction" in blob):
        extra += 2
    if "scenario" in blob and ("quality" in blob or "consistenc" in blob or "morpholog" in blob):
        extra += 2
    if r["year"] >= 2020:
        extra += 1
    if r["year"] >= 2023:
        extra += 1
    return hits + extra


def main():
    core = []
    for p in sorted(BIB.glob("0*.bib")):
        if "_candidates" in p.name:
            continue
        core.extend(parse(p))
    seen = set()
    core_u = []
    for r in core:
        k = r["doi"] or r["title"].lower()
        if k in seen:
            continue
        seen.add(k)
        core_u.append(r)
    cands = []
    for p in sorted(BIB.glob("*_candidates.bib")):
        cands.extend(parse(p))

    ranked = []
    for r in cands:
        k = r["doi"] or r["title"].lower()
        if k in seen:
            continue
        rel, js = rel_score(r), journal_score(r["journal"])
        if rel < 3 or js < 2:
            continue
        r["rel"], r["js"] = rel, js
        ranked.append(r)

    ranked.sort(key=lambda x: (-(x["year"] >= 2020), -x["js"], -x["rel"], -x["year"]))
    print(f"core_unique {len(core_u)}")
    print(f"candidates_kept {len(ranked)}")
    by = defaultdict(list)
    for r in ranked:
        by[r["strand"]].append(r)
    for s, items in by.items():
        print(f"\n===== {s} n={len(items)} =====")
        for r in items:
            print(f"{r['year']} js{r['js']} rel{r['rel']} | {r['journal'][:40]:40} | {r['title'][:95]}")


if __name__ == "__main__":
    main()
