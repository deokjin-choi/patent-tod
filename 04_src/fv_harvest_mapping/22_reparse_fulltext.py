"""저장한 원본 HTML에서 본문 JSON을 다시 만든다. 파서(gp_parse.py)를 고친 뒤에 쓴다. 네트워크 요청은 하지 않는다.

실행: conda run -n scenario-space python 22_reparse_fulltext.py
"""

from __future__ import annotations

import gzip
import json

from config import FULLTEXT_DIR, RAW_HTML_DIR
from gp_parse import parse_patent_html

KEEP = ("google_id", "lens_id", "url", "fetched_at")


def main() -> None:
    n = 0
    for json_path in sorted(FULLTEXT_DIR.glob("*.json")):
        old = json.loads(json_path.read_text(encoding="utf-8"))
        raw_path = RAW_HTML_DIR / f"{old['google_id']}.html.gz"
        doc = parse_patent_html(gzip.decompress(raw_path.read_bytes()).decode("utf-8"))
        doc.update({k: old[k] for k in KEEP})
        json_path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        n += 1
    print(f"다시 만든 본문 {n}건")


if __name__ == "__main__":
    main()
