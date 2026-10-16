"""갈래별 선행연구를 OpenAlex에서 찾아 초록 포함 BibTeX로 저장한다.

초록 우선순위: OpenAlex → Semantic Scholar → Crossref.
출력: literature/bib/<strand>.bib (핵심), <strand>_candidates.bib (키워드 검색 후보), all_core.bib
"""

import hashlib
import html
import json
import os
import re
import time
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

import requests

from seeds import STRANDS

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "bib"
CACHE = ROOT / "cache"
MAILTO = "deokjin.choi@gmail.com"
OA = "https://api.openalex.org/works"
S2_BATCH = "https://api.semanticscholar.org/graph/v1/paper/batch"
CROSSREF = "https://api.crossref.org/works/"
OPENAIRE = "https://api.openaire.eu/graph/v1/researchProducts"
KEY_FILES = (
    ROOT / ".env",
    Path.home() / ".config" / "scenario-space" / "openalex.env",
)


def load_openalex_key():
    if os.environ.get("OPENALEX_API_KEY"):
        return os.environ["OPENALEX_API_KEY"].strip()
    for path in KEY_FILES:
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            if name.strip() == "OPENALEX_API_KEY":
                return value.strip().strip("'\"")
    return None


OA_KEY = load_openalex_key()
MATCH_MIN = 0.85
MAX_ABSTRACT = 5000
CANDIDATES_PER_QUERY = 25
CANDIDATE_MIN_YEAR = 2005

session = requests.Session()
session.headers["User-Agent"] = f"scenario-space-lit/0.1 (mailto:{MAILTO})"


def get_json(url, params=None, tries=8):
    path = CACHE / (hashlib.sha1(json.dumps([url, params], sort_keys=True).encode()).hexdigest() + ".json")
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    if OA_KEY and "api.openalex.org" in url:
        params = {**(params or {}), "api_key": OA_KEY}
    for i in range(tries):
        try:
            r = session.get(url, params=params, timeout=30)
        except requests.RequestException:
            time.sleep(2 * (i + 1))
            continue
        if r.status_code == 200:
            data = r.json()
            path.write_text(json.dumps(data), encoding="utf-8")
            return data
        if r.status_code in (429, 500, 502, 503):
            time.sleep(4 * (i + 1))
            continue
        return None
    return None


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").lower()
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def oa_search_title(title, year):
    q = re.sub(r"[^\w\s-]", " ", title)
    data = get_json(OA, {"search": q, "per-page": 10, "mailto": MAILTO})
    best, best_score = None, 0.0
    for w in (data or {}).get("results", []):
        score = SequenceMatcher(None, norm(title), norm(w.get("title"))).ratio()
        if w.get("publication_year") and abs(w["publication_year"] - year) <= 2:
            score += 0.02
        if score > best_score:
            best, best_score = w, score
    return (best, best_score) if best_score >= MATCH_MIN else (None, best_score)


def oa_candidates(query):
    flt = f"title_and_abstract.search:{query},publication_year:>{CANDIDATE_MIN_YEAR - 1},type:article"
    data = get_json(OA, {"filter": flt, "per-page": CANDIDATES_PER_QUERY, "mailto": MAILTO})
    return (data or {}).get("results", [])


def inverted_to_text(inv):
    if not inv:
        return ""
    pos = {}
    for word, idxs in inv.items():
        for i in idxs:
            pos[i] = word
    return " ".join(pos[i] for i in sorted(pos))


def doi_of(w):
    d = w.get("doi") or ""
    return d.replace("https://doi.org/", "").lower() or None


def s2_abstracts(dois):
    out = {}
    dois = [d for d in dois if d]
    for k in range(0, len(dois), 400):
        chunk = dois[k : k + 400]
        for i in range(8):
            try:
                r = session.post(
                    S2_BATCH,
                    params={"fields": "abstract,externalIds"},
                    json={"ids": [f"DOI:{d}" for d in chunk]},
                    timeout=60,
                )
            except requests.RequestException:
                time.sleep(5)
                continue
            if r.status_code == 200:
                for d, rec in zip(chunk, r.json()):
                    if rec and rec.get("abstract"):
                        out[d] = rec["abstract"]
                break
            time.sleep(5 * (i + 1))
    return out


def openaire_abstract(doi):
    data = get_json(OPENAIRE, {"pid": doi}, tries=3)
    for rec in (data or {}).get("results", []):
        descs = [d for d in rec.get("descriptions") or [] if d and len(d) > 200]
        if descs:
            return max(descs, key=len)
    return ""


def crossref_abstract(doi):
    data = get_json(CROSSREF + doi, {"mailto": MAILTO}, tries=3)
    a = ((data or {}).get("message") or {}).get("abstract")
    if not a:
        return ""
    a = re.sub(r"<jats:title>.*?</jats:title>", " ", a, flags=re.S)
    a = re.sub(r"<[^>]+>", " ", a)
    return re.sub(r"\s+", " ", html.unescape(a)).strip()


def clean_abstract(a):
    a = re.sub(r"\s+", " ", a or "").strip()
    a = re.sub(r"^(abstract|summary)[:.\s]+", "", a, flags=re.I)
    return a if len(a) <= MAX_ABSTRACT else ""


def tex_escape(s):
    s = s or ""
    s = s.replace("{", "(").replace("}", ")")
    for ch in "&%$#_":
        s = s.replace(ch, "\\" + ch)
    return s


def author_list(w):
    names = []
    for a in w.get("authorships", []):
        n = (a.get("author") or {}).get("display_name") or a.get("raw_author_name")
        if not n:
            continue
        parts = n.split()
        names.append(f"{parts[-1]}, {' '.join(parts[:-1])}" if len(parts) > 1 else n)
    return names


def make_key(w, used):
    authors = author_list(w)
    last = norm(authors[0].split(",")[0]).replace(" ", "") if authors else "anon"
    words = [x for x in norm(w.get("title")).split() if x not in {"a", "an", "the", "on", "of", "for"}]
    base = f"{last}{w.get('publication_year') or ''}{words[0] if words else ''}"
    key, n = base, 1
    while key in used:
        n += 1
        key = f"{base}{chr(96 + n)}"
    used.add(key)
    return key


ENTRY_TYPE = {"article": "article", "review": "article", "book": "book", "book-chapter": "incollection"}


def to_bib(w, key, strand, abstract, abs_src, role):
    src = ((w.get("primary_location") or {}).get("source") or {}).get("display_name") or ""
    bib = w.get("biblio") or {}
    etype = ENTRY_TYPE.get(w.get("type"), "article")
    if src and re.search(r"conference|proceedings|workshop|neurips|neural information", src, re.I):
        etype = "inproceedings"
    pages = "--".join(p for p in (bib.get("first_page"), bib.get("last_page")) if p)
    fields = [
        ("title", "{" + tex_escape(w.get("title") or "") + "}"),
        ("author", " and ".join(author_list(w))),
        ("booktitle" if etype in ("inproceedings", "incollection") else "journal", tex_escape(src)),
        ("year", str(w.get("publication_year") or "")),
        ("volume", bib.get("volume") or ""),
        ("number", bib.get("issue") or ""),
        ("pages", pages),
        ("doi", doi_of(w) or ""),
        ("url", w.get("doi") or w.get("id") or ""),
        ("abstract", tex_escape(abstract)),
        ("keywords", f"{strand}; {role}"),
        ("note", f"OpenAlex {w['id'].rsplit('/', 1)[-1]}; cited_by {w.get('cited_by_count', 0)}; abstract_source {abs_src or 'none'}"),
    ]
    if etype == "article" and not src:
        fields = [f for f in fields if f[0] != "journal"]
    body = ",\n".join(f"  {k} = {{{v}}}" for k, v in fields if v)
    return f"@{etype}{{{key},\n{body}\n}}\n"


def main():
    OUT.mkdir(exist_ok=True)
    CACHE.mkdir(exist_ok=True)
    log = {"unresolved": [], "counts": {}}
    seen_ids = set()
    records = {}

    for strand, spec in STRANDS.items():
        core, cands = [], []
        for title, year, *doi in spec["seeds"]:
            if doi:
                w, score = get_json(f"{OA}/doi:{doi[0]}", {"mailto": MAILTO}), 1.0
            else:
                w, score = oa_search_title(title, year)
            if not w:
                log["unresolved"].append({"strand": strand, "title": title, "year": year, "best_score": round(score, 3)})
                print(f"[miss] {strand}: {title} ({score:.2f})")
                continue
            if w["id"] in seen_ids:
                continue
            seen_ids.add(w["id"])
            core.append(w)
        for q in spec["queries"]:
            for w in oa_candidates(q):
                if w["id"] in seen_ids or not w.get("title"):
                    continue
                seen_ids.add(w["id"])
                w["_query"] = q
                cands.append(w)
        cands.sort(key=lambda w: -w.get("cited_by_count", 0))
        records[strand] = (core, cands)
        print(f"{strand}: core {len(core)}, candidates {len(cands)}")

    all_works = [w for core, cands in records.values() for w in core + cands]
    abstracts = {}
    for w in all_works:
        a = clean_abstract(inverted_to_text(w.get("abstract_inverted_index")))
        abstracts[w["id"]] = (a, "openalex" if a else "")
    missing = [doi_of(w) for w in all_works if not abstracts[w["id"]][0] and doi_of(w)]
    print(f"abstract missing after OpenAlex: {len(missing)}")
    s2 = s2_abstracts(missing)
    for w in all_works:
        d = doi_of(w)
        if not abstracts[w["id"]][0] and d in s2:
            abstracts[w["id"]] = (clean_abstract(s2[d]), "semanticscholar")
    for w in all_works:
        d = doi_of(w)
        if abstracts[w["id"]][0] or not d:
            continue
        for fetch, name in ((openaire_abstract, "openaire"), (crossref_abstract, "crossref")):
            a = clean_abstract(fetch(d))
            if a:
                abstracts[w["id"]] = (a, name)
                break
    print(f"abstract missing at end: {sum(1 for v in abstracts.values() if not v[0])}")

    used = set()
    all_core = []
    for strand, (core, cands) in records.items():
        core_txt = [to_bib(w, make_key(w, used), strand, *abstracts[w["id"]], "core") for w in core]
        cand_txt = [
            to_bib(w, make_key(w, used), strand, *abstracts[w["id"]], f"candidate: {w['_query']}") for w in cands
        ]
        header = f"% {STRANDS[strand]['label']}\n\n"
        (OUT / f"{strand}.bib").write_text(header + "\n".join(core_txt), encoding="utf-8")
        (OUT / f"{strand}_candidates.bib").write_text(header + "\n".join(cand_txt), encoding="utf-8")
        all_core += core_txt
        log["counts"][strand] = {
            "core": len(core),
            "candidates": len(cands),
            "core_no_abstract": sum(1 for w in core if not abstracts[w["id"]][0]),
            "candidates_no_abstract": sum(1 for w in cands if not abstracts[w["id"]][0]),
        }
    (OUT / "all_core.bib").write_text("\n".join(all_core), encoding="utf-8")
    (ROOT / "fetch_log.json").write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(log, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
