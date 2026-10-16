"""fetch_bib.py 결과 보정: OpenAlex 없이 돌릴 수 있다.

1. fetch_log.json의 미해결 핵심 문헌을 Crossref 제목 검색으로 찾아 해당 갈래 bib에 추가한다.
2. MAX_ABSTRACT를 넘는 초록(본문 전체가 섞인 경우)을 다른 출처로 바꾸거나 비운다.
"""

import json
import re
from difflib import SequenceMatcher

from fetch_bib import (
    MATCH_MIN,
    MAX_ABSTRACT,
    OUT,
    ROOT,
    clean_abstract,
    crossref_abstract,
    get_json,
    norm,
    openaire_abstract,
    s2_abstracts,
    tex_escape,
)

CROSSREF_SEARCH = "https://api.crossref.org/works"
ENTRY_RE = re.compile(r"(?=^@\w+\{)", re.M)


def crossref_find(title, year):
    data = get_json(CROSSREF_SEARCH, {"query.bibliographic": title, "rows": 10})
    best, best_score = None, 0.0
    for it in ((data or {}).get("message") or {}).get("items", []):
        score = SequenceMatcher(None, norm(title), norm((it.get("title") or [""])[0])).ratio()
        if score > best_score:
            best, best_score = it, score
    return best if best_score >= MATCH_MIN else None


def crossref_bib(it, key, strand, abstract, abs_src):
    year = ((it.get("issued") or {}).get("date-parts") or [[None]])[0][0]
    authors = [f"{a.get('family', '')}, {a.get('given', '')}".strip(", ") for a in it.get("author", [])]
    fields = [
        ("title", "{" + tex_escape(it["title"][0]) + "}"),
        ("author", " and ".join(authors)),
        ("journal", tex_escape((it.get("container-title") or [""])[0])),
        ("year", str(year or "")),
        ("volume", it.get("volume", "")),
        ("number", it.get("issue", "")),
        ("pages", (it.get("page") or "").replace("-", "--")),
        ("doi", it["DOI"].lower()),
        ("url", f"https://doi.org/{it['DOI']}"),
        ("abstract", tex_escape(abstract)),
        ("keywords", f"{strand}; core"),
        ("note", f"Crossref; cited_by {it.get('is-referenced-by-count', 0)}; abstract_source {abs_src or 'none'}"),
    ]
    body = ",\n".join(f"  {k} = {{{v}}}" for k, v in fields if v)
    return f"@article{{{key},\n{body}\n}}\n"


def best_abstract(doi):
    for fetch, name in ((openaire_abstract, "openaire"), (crossref_abstract, "crossref")):
        a = clean_abstract(fetch(doi))
        if a:
            return a, name
    a = clean_abstract(s2_abstracts([doi]).get(doi, ""))
    return (a, "semanticscholar") if a else ("", "")


def fix_long_abstracts(path):
    text = path.read_text(encoding="utf-8")
    parts = ENTRY_RE.split(text)
    changed = 0
    for i, ent in enumerate(parts):
        m = re.search(r"^  abstract = \{(.*)\},?$", ent, re.M)
        if not m or len(m.group(1)) <= MAX_ABSTRACT:
            continue
        doi = re.search(r"^  doi = \{(.*)\}", ent, re.M)
        a, src = best_abstract(doi.group(1)) if doi else ("", "")
        if a:
            ent = ent.replace(m.group(0), f"  abstract = {{{tex_escape(a)}}},")
        else:
            ent = ent.replace(m.group(0) + "\n", "")
        ent = re.sub(r"abstract_source \w+", f"abstract_source {src or 'none'}", ent)
        parts[i] = ent
        changed += 1
    path.write_text("".join(parts), encoding="utf-8")
    return changed


def main():
    log_path = ROOT / "fetch_log.json"
    log = json.loads(log_path.read_text(encoding="utf-8"))
    used = set()
    for p in OUT.glob("*.bib"):
        used |= set(re.findall(r"^@\w+\{([^,]+),", p.read_text(encoding="utf-8"), re.M))

    still = []
    for u in log["unresolved"]:
        it = crossref_find(u["title"], u["year"])
        if not it:
            still.append(u)
            print(f"[miss] {u['title']}")
            continue
        a, src = best_abstract(it["DOI"].lower())
        first = norm((it.get("author") or [{}])[0].get("family", "anon")).replace(" ", "")
        word = next(x for x in norm(it["title"][0]).split() if x not in {"a", "an", "the", "on", "of", "for"})
        key = f"{first}{u['year']}{word}"
        while key in used:
            key += "x"
        used.add(key)
        entry = crossref_bib(it, key, u["strand"], a, src)
        for name in (f"{u['strand']}.bib", "all_core.bib"):
            with open(OUT / name, "a", encoding="utf-8") as f:
                f.write("\n" + entry)
        log["counts"][u["strand"]]["core"] += 1
        if not a:
            log["counts"][u["strand"]]["core_no_abstract"] += 1
        print(f"[add] {key} ({src or 'no abstract'})")
    log["unresolved"] = still

    for p in sorted(OUT.glob("*.bib")):
        n = fix_long_abstracts(p)
        if n:
            print(f"[long abstract] {p.name}: {n}")
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
