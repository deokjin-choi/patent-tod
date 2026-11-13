"""scope.csv의 특허를 Google Patents에서 한 건씩 받아 JSON으로 저장한다.

요청은 한 번에 하나, 요청 사이 간격은 config.REQUEST_INTERVAL_SEC 이상이다.
이미 받은 파일은 건너뛰므로 중간에 멈춰도 다시 실행하면 이어서 받는다.

실행:
  conda run -n scenario-space python 20_fetch_fulltext.py --limit 1
  conda run -n scenario-space python 20_fetch_fulltext.py --ids US20110252760A1
  conda run -n scenario-space python 20_fetch_fulltext.py            # 전체
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import time
from datetime import datetime, timezone

import pandas as pd
import requests

from config import (
    BACKOFF_BASE_SEC, FETCH_LOG, FULLTEXT_DIR, MAX_RETRIES, RAW_HTML_DIR, REQUEST_INTERVAL_SEC,
    REQUEST_TIMEOUT_SEC, SCOPE_CSV, USER_AGENT,
)
from gp_parse import parse_patent_html

URL = "https://patents.google.com/patent/{gid}/en"
LOG_FIELDS = ["google_id", "status", "http_code", "n_claims", "n_paras", "chars", "fetched_at"]


class Throttle:
    """직전 요청 시작 시각부터 interval초가 지나야 다음 요청을 보낸다."""

    def __init__(self, interval: float) -> None:
        self.interval = interval
        self.last = 0.0

    def wait(self) -> None:
        gap = time.monotonic() - self.last
        if gap < self.interval:
            time.sleep(self.interval - gap)
        self.last = time.monotonic()


def fetch_one(session: requests.Session, throttle: Throttle, gid: str) -> tuple[str, int, str]:
    """(status, http_code, html). 429·5xx는 지수적으로 기다렸다가 다시 시도한다."""
    for attempt in range(MAX_RETRIES + 1):
        throttle.wait()
        try:
            r = session.get(URL.format(gid=gid), timeout=REQUEST_TIMEOUT_SEC)
        except requests.RequestException as exc:
            code, html = -1, str(exc)
        else:
            # 응답 헤더에 charset이 없어 r.text는 Latin-1로 읽는다. 페이지는 UTF-8이다.
            code, html = r.status_code, r.content.decode("utf-8", errors="replace")
        if code == 200:
            return "ok", code, html
        if code == 404:
            return "not_found", code, ""
        if attempt < MAX_RETRIES:
            wait = BACKOFF_BASE_SEC * (2 ** attempt)
            print(f"  {gid}: HTTP {code}, {wait:.0f}초 뒤 다시 시도 ({attempt + 1}/{MAX_RETRIES})")
            time.sleep(wait)
    return "failed", code, ""


def append_log(row: dict) -> None:
    new = not FETCH_LOG.exists()
    with FETCH_LOG.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=LOG_FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="아직 받지 않은 것 중 앞에서 N건만")
    ap.add_argument("--ids", nargs="*", default=None, help="Google 공개번호를 직접 지정")
    args = ap.parse_args()

    scope = pd.read_csv(SCOPE_CSV)
    if args.ids:
        scope = scope[scope["google_id"].isin(args.ids)]
    FULLTEXT_DIR.mkdir(parents=True, exist_ok=True)
    todo = [r for r in scope.to_dict("records") if not (FULLTEXT_DIR / f"{r['google_id']}.json").exists()]
    if args.limit is not None:
        todo = todo[: args.limit]
    print(f"받을 특허 {len(todo)}건 (범위 {len(scope)}건, 이미 받은 것 제외)")

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"})
    throttle = Throttle(REQUEST_INTERVAL_SEC)

    RAW_HTML_DIR.mkdir(parents=True, exist_ok=True)
    for i, r in enumerate(todo, 1):
        gid = r["google_id"]
        raw_path = RAW_HTML_DIR / f"{gid}.html.gz"
        if raw_path.exists():
            status, code = "ok", 200
            html = gzip.decompress(raw_path.read_bytes()).decode("utf-8")
        else:
            status, code, html = fetch_one(session, throttle, gid)
            if status == "ok":
                raw_path.write_bytes(gzip.compress(html.encode("utf-8")))
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        n_claims = n_paras = chars = 0
        if status == "ok":
            try:
                doc = parse_patent_html(html)
            except Exception as exc:  # 파싱 실패는 원본 HTML을 남기고 다음 건으로 넘어간다
                status = "parse_error"
                print(f"  {gid}: 파싱 실패 {exc!r}")
            else:
                doc.update({"google_id": gid, "lens_id": r["Lens ID"], "url": URL.format(gid=gid), "fetched_at": now})
                n_claims = len(doc["claims"])
                n_paras = sum(b["type"] == "para" for b in doc["description"])
                chars = sum(len(c["text"]) for c in doc["claims"]) + sum(len(b["text"]) for b in doc["description"])
                if n_claims == 0 or n_paras == 0:
                    status = "ok_partial"
                (FULLTEXT_DIR / f"{gid}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        append_log({"google_id": gid, "status": status, "http_code": code, "n_claims": n_claims,
                    "n_paras": n_paras, "chars": chars, "fetched_at": now})
        print(f"[{i}/{len(todo)}] {gid} {status} 청구항 {n_claims} 문단 {n_paras} 글자 {chars:,}")


if __name__ == "__main__":
    main()
