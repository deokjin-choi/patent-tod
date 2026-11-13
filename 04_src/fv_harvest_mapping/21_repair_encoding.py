"""인코딩 오류 복구. 20_fetch_fulltext.py 초기 버전은 UTF-8 페이지를 Latin-1로 읽어 저장했다.

Latin-1 해석은 바이트를 그대로 보존하므로 되돌릴 수 있다. 저장한 원본 HTML을 고치고 본문 JSON을 다시 만든다.
네트워크 요청은 하지 않는다.

실행: conda run -n scenario-space python 21_repair_encoding.py
"""

from __future__ import annotations

import gzip
import json

from config import FULLTEXT_DIR, RAW_HTML_DIR
from gp_parse import parse_patent_html


def main() -> None:
    fixed = kept = 0
    for raw_path in sorted(RAW_HTML_DIR.glob("*.html.gz")):
        html = gzip.decompress(raw_path.read_bytes()).decode("utf-8")
        try:
            repaired = html.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            kept += 1  # 이미 올바른 UTF-8 문자열
            continue
        if repaired == html:
            kept += 1
            continue
        raw_path.write_bytes(gzip.compress(repaired.encode("utf-8")))
        gid = raw_path.name.removesuffix(".html.gz")
        json_path = FULLTEXT_DIR / f"{gid}.json"
        if json_path.exists():
            old = json.loads(json_path.read_text(encoding="utf-8"))
            doc = parse_patent_html(repaired)
            doc.update({k: old[k] for k in ("google_id", "lens_id", "url", "fetched_at")})
            json_path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        fixed += 1
    print(f"복구 {fixed}건, 그대로 둔 것 {kept}건")


if __name__ == "__main__":
    main()
