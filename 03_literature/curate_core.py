"""후보를 먼저 가리고, 부족한 최근 문헌만 OpenAlex로 보강해 all_core.bib를 다시 쓴다.

기준: 본 연구(특허 형태/기회, KG·임베딩 조합, 시간축 검증, 시나리오 공간 품질)와
직접 관련 + 분야 저널 이상 + 가능하면 2020 이후.
목표: 고유 논문 약 100편.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fetch_bib import (
    MAILTO,
    OA,
    OUT,
    ROOT,
    clean_abstract,
    crossref_abstract,
    doi_of,
    get_json,
    inverted_to_text,
    make_key,
    openaire_abstract,
    s2_abstracts,
    to_bib,
)

BIB = OUT
LOG = ROOT / "curation_log.json"

JOURNAL_SCORE = {
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
    "information processing & management": 3,
    "journal of the association for information science and technology": 3,
    "journal of the american society for information science and technology": 3,
    "knowledge-based systems": 3,
    "european journal of operational research": 3,
    "decision support systems": 3,
    "quantitative science studies": 3,
    "nature": 3,
    "nature communications": 3,
    "nature machine intelligence": 3,
    "science": 3,
    "proceedings of the national academy of sciences": 3,
    "pnas": 3,
    "foresight": 2,
    "journal of cleaner production": 2,
    "energy research and social science": 2,
    "energy research & social science": 2,
    "global environmental change": 3,
    "climatic change": 2,
    "energy policy": 2,
    "environmental modelling and software": 2,
    "environmental modelling & software": 2,
    "journal of data and information science": 2,
}

# 부분 일치로 'science'가 의학 저널을 통과하지 않게, 별칭만 둔다.
JOURNAL_ALIASES = {
    "technological forecasting & social change": "technological forecasting and social change",
    "ieee trans. on engineering management": "ieee transactions on engineering management",
}

POS = {
    "01_tmo_morphology": [
        "technology opportunity", "technological opportunity", "morpholog",
        "patent map", "patent vacuum", "sao", "technology opportunity discovery",
        "opportunity identification", "vacant technolog", "keyword-based patent",
        "function-based", "novelty-focused patent",
    ],
    "02_kg_embedding": [
        "knowledge graph", "embedding", "patent similar", "link prediction",
        "technology convergence", "technet", "recombin", "combinatorial",
        "semantic network", "patent distance", "graph embedding",
        "problem-solution", "technology combination",
    ],
    "03_temporal_validation": [
        "forecast accuracy", "emerging technolog", "out-of-sample", "predictability",
        "early identification", "leakage", "retrospective", "technology forecast",
        "emerging clusters", "validation of", "sliding window",
    ],
    "04_scenario_quality": [
        "scenario quality", "scenario set", "general morphological", "cross consistency",
        "plausib", "intuitive logics", "cross-impact", "scenario discovery",
        "scenario planning", "foresight", "morphological analysis",
    ],
}

NEEDLE = [
    "patent", "technolog", "scenario", "foresight", "forecast", "morpholog",
    "opportunity", "convergence", "knowledge graph", "embedding",
]
NOISE = [
    "strawberry", "ovarian", "ultrasound", "aphasia", "drone detection",
    "traditional chinese medicine", "tamil studies", "third-grade",
    "sustaining members", "management accounting", "cell and gene therapy",
    "teledermatology", "canis familiaris", "mycoheterotrophy", "dinosaur",
    "pharmacogenetic", "covid-19", "hydrocarbon", "soil and cartographic",
    "dermatolog", "pathology", "balloon dilatation", "intravascular",
    "neuroscience", "spiritual responsibility", "mushroom dialectics",
    "public health genomics", "asthma", "phosphogypsum",
]

EXTRA_SEARCH = {
    "01_tmo_morphology": [
        "technology opportunity discovery patent morphology",
        "technology opportunity analysis patent SAO",
        "patent vacuum morphological analysis",
        "keyword-based morphology analysis patent",
    ],
    "02_kg_embedding": [
        "patent knowledge graph technology opportunity",
        "link prediction technology convergence patent",
        "patent embedding technological similarity",
    ],
    "03_temporal_validation": [
        "emerging technology identification patents machine learning",
        "technology forecast accuracy patents validation",
        "predicting technology convergence out-of-sample",
    ],
    "04_scenario_quality": [
        "general morphological analysis scenario foresight",
        "scenario quality consistency diversity foresight",
        "patent analysis scenario planning morphological",
        "data-driven scenario development text mining",
    ],
}

# 갈래별 최근 논문 목표 추가 수 (core 79 + 약 25)
QUOTA = {
    "01_tmo_morphology": 8,
    "02_kg_embedding": 6,
    "03_temporal_validation": 6,
    "04_scenario_quality": 6,
}

STRAND_LABEL = {
    "01_tmo_morphology": "특허 기반 형태분석·기술 기회 분석 (TMO/TOA)",
    "02_kg_embedding": "특허 지식그래프·임베딩·조합 기반 기술 기회/융합 예측",
    "03_temporal_validation": "기술 예측의 시간축·사후 검증",
    "04_scenario_quality": "형태분석 시나리오 공간·시나리오 세트 품질 기준",
}


def field(entry, name):
    m = re.search(rf"^  {name} = \{{(.*)\}}\s*,?\s*$", entry, re.M)
    return (m.group(1).strip().strip("{}") if m else "")


def parse_bib(path):
    recs = []
    for e in re.split(r"(?=@\w+\{)", path.read_text(encoding="utf-8")):
        if not e.strip().startswith("@"):
            continue
        year = field(e, "year")
        recs.append({
            "title": field(e, "title"),
            "journal": field(e, "journal") or field(e, "booktitle"),
            "year": int(year) if year.isdigit() else 0,
            "doi": field(e, "doi").lower(),
            "abstract": field(e, "abstract"),
            "author": field(e, "author"),
            "strand": (field(e, "keywords").split(";")[0].strip() or path.stem.replace("_candidates", "")),
            "raw": e if e.endswith("\n") else e + "\n",
            "src": path.name,
        })
    return recs


def jnorm(name):
    n = name.lower().replace("&", "and")
    n = re.sub(r"[^a-z0-9]+", " ", n).strip()
    return JOURNAL_ALIASES.get(n, n)


def journal_score(name):
    return JOURNAL_SCORE.get(jnorm(name), 0)


def blob_of(r):
    return f"{r.get('title', '')} {r.get('abstract', '')}".lower()


def relevant(r, min_hits=2):
    blob = blob_of(r)
    if any(x in blob for x in NOISE):
        return False
    if not any(x in blob for x in NEEDLE):
        return False
    hits = sum(1 for p in POS.get(r["strand"], []) if p in blob)
    if "patent" in blob and ("opportunity" in blob or "morpholog" in blob):
        hits += 1
    if "scenario" in blob and ("morpholog" in blob or "consistenc" in blob or "quality" in blob):
        hits += 1
    if "patent" in blob and ("link prediction" in blob or "embedding" in blob or "convergence" in blob):
        hits += 1
    return hits >= min_hits


def work_to_rec(w, strand):
    src = ((w.get("primary_location") or {}).get("source") or {}).get("display_name") or ""
    return {
        "title": w.get("title") or "",
        "journal": src,
        "year": w.get("publication_year") or 0,
        "doi": doi_of(w) or "",
        "abstract": clean_abstract(inverted_to_text(w.get("abstract_inverted_index"))),
        "author": "",
        "strand": strand,
        "work": w,
        "src": "openalex",
    }


def oa_recent(query, year_from=2020):
    flt = (
        f"title_and_abstract.search:{query},"
        f"publication_year:{year_from}-2026,type:article"
    )
    data = get_json(OA, {"filter": flt, "per-page": 25, "sort": "cited_by_count:desc", "mailto": MAILTO})
    return (data or {}).get("results", [])


def fill_abstracts(recs):
    missing = [r["doi"] for r in recs if r.get("work") and not r.get("abstract") and r.get("doi")]
    s2 = s2_abstracts(missing) if missing else {}
    for r in recs:
        if r.get("abstract") or not r.get("doi"):
            continue
        if r["doi"] in s2:
            r["abstract"] = clean_abstract(s2[r["doi"]])
            continue
        for fetch in (openaire_abstract, crossref_abstract):
            a = clean_abstract(fetch(r["doi"]))
            if a:
                r["abstract"] = a
                break
        if r.get("work") and not r.get("abstract"):
            r["abstract"] = clean_abstract(inverted_to_text(r["work"].get("abstract_inverted_index")))


def pick(items, n, seen):
    chosen = []
    for r in items:
        key = r["doi"] or r["title"].lower()
        if not r["title"] or key in seen:
            continue
        if journal_score(r["journal"]) < 2:
            continue
        if not relevant(r, min_hits=2):
            continue
        seen.add(key)
        chosen.append(r)
        if len(chosen) >= n:
            break
    return chosen


def main():
    core = []
    for p in sorted(BIB.glob("0*.bib")):
        if "_candidates" in p.name:
            continue
        core.extend(parse_bib(p))
    seen = set()
    core_u = []
    for r in core:
        k = r["doi"] or r["title"].lower()
        if not r["title"] or k in seen:
            continue
        seen.add(k)
        r["role"] = "core"
        core_u.append(r)

    cands = []
    for p in sorted(BIB.glob("*_candidates.bib")):
        cands.extend(parse_bib(p))
    cands.sort(key=lambda r: (-(r["year"] >= 2020), -journal_score(r["journal"]), -r["year"]))

    added = defaultdict(list)
    for strand, n in QUOTA.items():
        pool = [r for r in cands if r["strand"] == strand]
        chosen = pick(pool, n, seen)
        for r in chosen:
            r["role"] = "from_candidate"
        added[strand].extend(chosen)

    searched = []
    for strand, queries in EXTRA_SEARCH.items():
        need = QUOTA[strand] - len(added[strand])
        if need <= 0:
            continue
        found = []
        for q in queries:
            for w in oa_recent(q):
                rec = work_to_rec(w, strand)
                rec["query"] = q
                found.append(rec)
        fill_abstracts(found)
        found.sort(key=lambda r: (-journal_score(r["journal"]), -(r["year"] or 0), -((r.get("work") or {}).get("cited_by_count") or 0)))
        extra = pick(found, need, seen)
        for r in extra:
            r["role"] = "from_search"
        added[strand].extend(extra)
        searched.extend(extra)

    fill_abstracts([r for rs in added.values() for r in rs if r.get("work")])

    final = core_u + [r for rs in added.values() for r in rs]
    used = set()
    by_strand = defaultdict(list)
    for r in final:
        by_strand[r["strand"]].append(r)

    all_txt = []
    for strand in STRAND_LABEL:
        parts = []
        for r in by_strand[strand]:
            if r.get("work"):
                src = "openalex"
                if r.get("abstract"):
                    src = "openalex"
                parts.append(to_bib(r["work"], make_key(r["work"], used), strand, r.get("abstract") or "", src, r["role"]))
            else:
                raw = r["raw"]
                raw = re.sub(r"^  keywords = \{.*\}\s*,?\s*$", f"  keywords = {{{strand}; {r['role']}}},", raw, flags=re.M)
                key_m = re.search(r"^@\w+\{([^,]+),", raw, re.M)
                if key_m:
                    old = key_m.group(1)
                    new = old
                    n = 1
                    while new in used:
                        n += 1
                        new = f"{old}{n}"
                    used.add(new)
                    raw = raw.replace(f"{{{old},", f"{{{new},", 1)
                parts.append(raw if raw.endswith("\n") else raw + "\n")
        header = f"% {STRAND_LABEL[strand]}\n\n"
        (BIB / f"{strand}.bib").write_text(header + "\n".join(parts), encoding="utf-8")
        all_txt.extend(parts)

    (BIB / "all_core.bib").write_text("\n".join(all_txt), encoding="utf-8")

    summary = {
        "core_kept": len(core_u),
        "added_from_candidates": sum(1 for rs in added.values() for r in rs if r["role"] == "from_candidate"),
        "added_from_search": sum(1 for rs in added.values() for r in rs if r["role"] == "from_search"),
        "total": len(final),
        "by_strand": {s: len(by_strand[s]) for s in STRAND_LABEL},
        "year_2020plus": sum(1 for r in final if r["year"] >= 2020),
        "additions": [
            {
                "strand": r["strand"],
                "year": r["year"],
                "journal": r["journal"],
                "title": r["title"],
                "doi": r["doi"],
                "role": r["role"],
            }
            for rs in added.values()
            for r in rs
        ],
    }
    LOG.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in summary if k != "additions"}, ensure_ascii=False, indent=2))
    print("\nADDITIONS")
    for a in summary["additions"]:
        print(f"{a['year']} | {a['strand'][3:18]:14} | {a['role']:16} | {a['journal'][:36]:36} | {a['title'][:80]}")


if __name__ == "__main__":
    main()
