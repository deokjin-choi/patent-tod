"""현재 all_core(94)에, 관련·저널 기준을 통과한 최근 논문만 더 붙인다."""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from curate_core import STRAND_LABEL, field, journal_score, parse_bib
from fetch_bib import (
    MAILTO,
    MATCH_MIN,
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
    oa_search_title,
    s2_abstracts,
    to_bib,
)

# 후보 검토·추가 검색에서 제목이 본 연구와 맞는 최근 문헌.
SEEDS = {
    "01_tmo_morphology": [
        ("Technology opportunity analysis using hierarchical semantic networks and dual link prediction", 2023),
        ("Two-stage technology opportunity discovery for firm-level decision making: GCN-based link-prediction", 2022),
        ("Exploring a technology ecology for technology opportunity discovery: A link prediction approach using patent information", 2021),
        ("Discovering firm technology opportunities by machine learning prediction method based on patent analysis", 2025),
    ],
    "02_kg_embedding": [
        ("From technology hierarchies to convergence prediction: Integrating graph learning into multi-layer networks", 2025),
        ("Predicting technology convergence patterns in different industry segments: A multi-layer network approach", 2025),
        ("A framework armed with node dynamics for predicting technology convergence", 2024),
    ],
    "03_temporal_validation": [
        ("Forecasting emerging technologies using data augmentation and deep learning", 2020),
        ("An exploration method for technology forecasting that combines link prediction with graph representation", 2024),
        ("Forecasting future bigrams and promising patents: introducing text-based link prediction", 2022),
        ("A novel technology life cycle analysis method based on LSTM and CRF", 2024),
        ("Identification of promising inventions considering the quality of knowledge accumulation", 2020),
        ("Combining machine learning and main path analysis to identify research front: from the perspective of knowledge network", 2022),
        ("Early identification of emerging technologies: A machine learning approach using multiple patent indicators", 2018),
    ],
    "04_scenario_quality": [
        ("Foresighting Scenarios for Green Hydrogen in Portugal: Systematization of Potential Future Configurations", 2025),
        ("Does the intuitive logics method – and its recent enhancements – produce “effective” scenarios?", 2013),
        ("How to design and evaluate future-oriented methods", 2021),
        ("Quality criteria for scenario methods", 2021),
        ("Evaluating scenarios: a review of approaches", 2020),
        ("Scenario quality assessment", 2022),
        ("A review of data-driven scenario planning", 2023),
        ("Text mining and scenario planning", 2021),
        ("Computational scenario planning", 2022),
        ("Artificial intelligence and scenario planning", 2024),
        ("Morphological analysis in futures studies", 2021),
        ("General morphological analysis in practice", 2022),
        ("Defining and assessing the quality of scenarios", 2020),
        ("Improving the quality of scenario planning", 2021),
        ("Cross-impact balances and scenario analysis", 2021),
        ("Plausibility in scenario planning: a review", 2022),
    ],
}

SEARCH = {
    "03_temporal_validation": [
        "forecasting emerging technologies deep learning patents",
        "technology forecasting link prediction patent graph",
    ],
    "04_scenario_quality": [
        "scenario planning quality criteria futures",
        "morphological analysis foresight scenario",
        "data-driven scenario planning text mining",
        "artificial intelligence scenario planning foresight",
    ],
}


def existing_dois():
    text = (OUT / "all_core.bib").read_text(encoding="utf-8")
    return set(x.lower() for x in re.findall(r"^  doi = \{([^}]+)\}", text, re.M))


def existing_titles():
    recs = parse_bib(OUT / "all_core.bib")
    return {re.sub(r"[^a-z0-9]+", " ", r["title"].lower()).strip() for r in recs}


def title_ok(title, strand):
    t = title.lower()
    if strand == "01_tmo_morphology":
        return ("opportunity" in t and ("technolog" in t or "patent" in t)) or ("morpholog" in t and "patent" in t)
    if strand == "02_kg_embedding":
        return any(x in t for x in ("convergence", "knowledge graph", "embedding", "link prediction", "similar"))
    if strand == "03_temporal_validation":
        return any(x in t for x in ("forecast", "emerging", "life cycle", "research front", "promising invention", "predict"))
    if strand == "04_scenario_quality":
        return ("scenario" in t or "foresight" in t or "morpholog" in t) and any(
            x in t for x in ("quality", "evaluat", "criteria", "plausib", "consist", "planning", "method", "morpholog", "text mining", "data-driven", "artificial intelligence")
        )
    return False


def work_ok(w, strand):
    src = ((w.get("primary_location") or {}).get("source") or {}).get("display_name") or ""
    # Futures & Foresight Science는 분야 저널로 인정
    js = journal_score(src)
    if "futures and foresight science" in src.lower() or "futures & foresight science" in src.lower():
        js = max(js, 2)
    if js < 2:
        return False
    title = w.get("title") or ""
    return title_ok(title, strand)


def fetch_work(title, year):
    w, score = oa_search_title(title, year)
    return w if w else None


def oa_search(query):
    flt = f"title_and_abstract.search:{query},publication_year:2020-2026,type:article"
    data = get_json(OA, {"filter": flt, "per-page": 20, "sort": "cited_by_count:desc", "mailto": MAILTO})
    return (data or {}).get("results", [])


def abstracts_for(works):
    out = {}
    for w in works:
        a = clean_abstract(inverted_to_text(w.get("abstract_inverted_index")))
        out[w["id"]] = a
    missing = [doi_of(w) for w in works if not out[w["id"]] and doi_of(w)]
    s2 = s2_abstracts(missing)
    for w in works:
        d = doi_of(w)
        if out[w["id"]] or not d:
            continue
        if d in s2:
            out[w["id"]] = clean_abstract(s2[d])
            continue
        a = clean_abstract(openaire_abstract(d)) or clean_abstract(crossref_abstract(d))
        out[w["id"]] = a
    return out


def main():
    have_doi = existing_dois()
    have_title = existing_titles()
    chosen = defaultdict(list)
    seen = set(have_doi)

    for strand, seeds in SEEDS.items():
        for title, year in seeds:
            tnorm = re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()
            if tnorm in have_title:
                continue
            w = fetch_work(title, year)
            if not w or not work_ok(w, strand):
                continue
            d = doi_of(w)
            if (d and d in seen) or not d:
                continue
            seen.add(d)
            chosen[strand].append(w)
            print(f"[seed] {w.get('publication_year')} {strand} {(w.get('title') or '')[:80]}")

    for strand, queries in SEARCH.items():
        for q in queries:
            for w in oa_search(q):
                d = doi_of(w)
                title = w.get("title") or ""
                tnorm = re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()
                if not d or d in seen or tnorm in have_title:
                    continue
                if not work_ok(w, strand):
                    continue
                seen.add(d)
                chosen[strand].append(w)
                print(f"[search] {w.get('publication_year')} {strand} {title[:80]}")

    works = [w for ws in chosen.values() for w in ws]
    absmap = abstracts_for(works)
    used = set(re.findall(r"^@\w+\{([^,]+),", (OUT / "all_core.bib").read_text(encoding="utf-8"), re.M))

    added_txt = defaultdict(list)
    for strand, ws in chosen.items():
        for w in ws:
            key = make_key(w, used)
            txt = to_bib(w, key, strand, absmap.get(w["id"], ""), "mixed", "recent_add")
            added_txt[strand].append(txt)

    all_core = (OUT / "all_core.bib").read_text(encoding="utf-8")
    extra_all = []
    for strand, parts in added_txt.items():
        path = OUT / f"{strand}.bib"
        cur = path.read_text(encoding="utf-8")
        path.write_text(cur.rstrip() + "\n\n" + "\n".join(parts), encoding="utf-8")
        extra_all.extend(parts)
    if extra_all:
        (OUT / "all_core.bib").write_text(all_core.rstrip() + "\n\n" + "\n".join(extra_all), encoding="utf-8")

    n_old = len(re.findall(r"^@\w+\{", all_core, re.M))
    n_new = n_old + len(extra_all)
    log = {
        "before": n_old,
        "added": len(extra_all),
        "after": n_new,
        "by_strand_added": {s: len(v) for s, v in added_txt.items()},
        "titles": [
            {"strand": s, "year": w.get("publication_year"), "title": w.get("title"), "doi": doi_of(w)}
            for s, ws in chosen.items()
            for w in ws
        ],
    }
    (ROOT / "add_recent_log.json").write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: log[k] for k in log if k != "titles"}, indent=2))


if __name__ == "__main__":
    main()
