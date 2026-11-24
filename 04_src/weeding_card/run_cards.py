"""제초 상세 특허 전량을 v5 카드로 만든다. 매핑은 하지 않는다.

Ollama 샘플링 옵션은 보내지 않는다. 서버에 설정된 기본값을 쓴다.
생각 모드만 끈다. 모델은 gemma4:31b-it-q4_K_M.

실행:
  /home/deokjinchoi/miniconda3/envs/scenario-space/bin/python -u 04_src/weeding_card/run_cards.py
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests
from jsonschema import Draft202012Validator

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "fv_harvest_mapping"))

import llm_ollama
from config import USER_AGENT
from gp_parse import parse_patent_html
from patent_text import render_patent
from prompt_build import card_pass

OLLAMA_URL = "http://192.168.0.2:11434/api/chat"
MODEL = "gemma4:31b-it-q4_K_M"
CSV = Path("/mnt/e/patent-tod/05_data/agri/weeding-patents-detail-2004-2026-simplefamily.csv")
ROOT = Path("/mnt/e/patent-tod/05_data/agri/weeding-patents-detail-2004-2026-simplefamily")
FULLTEXT = ROOT / "fulltext"
CARDS = ROOT / "card_v5" / "gemma4_31b-it-q4_K_M"
PROGRESS = ROOT / "progress.txt"
KST = timezone(timedelta(hours=9))


def google_id(display_key: str) -> str:
    """Lens Display Key에서 공백과 슬래시를 뺀 Google Patents 번호."""
    return "".join(display_key.split()).replace("/", "")


def now() -> datetime:
    return datetime.now(KST)


def stamp(msg: str) -> None:
    line = f"{now().strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    print(line, flush=True)
    with PROGRESS.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def fetch(session: requests.Session, gid: str) -> tuple[str, int, str]:
    url = f"https://patents.google.com/patent/{gid}/en"
    code = 0
    for attempt in range(5):
        try:
            r = session.get(url, timeout=40)
            code = r.status_code
            html = r.content.decode("utf-8", errors="replace")
        except requests.RequestException as exc:
            code, html = -1, str(exc)
        if code == 200 and "itemprop" in html:
            return "ok", code, html
        if code == 404:
            return "not_found", code, ""
        time.sleep(min(60, 5 * (2 ** attempt)))
    return "failed", code, html if isinstance(html, str) else ""


def infer(system: str, schema_fmt: dict, validator: Draft202012Validator, user: str) -> dict:
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "format": schema_fmt,
        "stream": False,
        "think": False,
    }
    t0 = time.time()
    r = requests.post(OLLAMA_URL, json=body, timeout=1800)
    r.raise_for_status()
    res = r.json()
    content = res.get("message", {}).get("content", "")
    parsed, errors = None, []
    try:
        parsed = json.loads(content)
        errors = [f"{'/'.join(map(str, e.path))}: {e.message}" for e in validator.iter_errors(parsed)]
    except json.JSONDecodeError as exc:
        errors = [f"JSON 해석 실패: {exc}"]
    return {
        "seconds": round(time.time() - t0, 1),
        "prompt_tokens": res.get("prompt_eval_count") or 0,
        "output_tokens": res.get("eval_count") or 0,
        "done_reason": res.get("done_reason"),
        "schema_errors": errors,
        "output": parsed,
        "raw": None if parsed is not None and not errors else content,
    }


def usable(path: Path) -> bool:
    if not path.exists():
        return False
    rec = json.loads(path.read_text(encoding="utf-8"))
    if rec.get("status") in ("not_found", "no_text", "failed"):
        return True
    return rec.get("output") is not None and not rec.get("schema_errors")


def main() -> None:
    FULLTEXT.mkdir(parents=True, exist_ok=True)
    CARDS.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(CSV, usecols=["Display Key", "Lens ID", "Jurisdiction", "Title"], low_memory=False)
    rows = df.to_dict("records")
    n = len(rows)
    system, schema = card_pass()
    fmt = llm_ollama.inline_refs(schema)
    validator = Draft202012Validator(schema)
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"})

    stamp(f"시작 {n}건 모델 {MODEL} 옵션 ollama_default 프롬프트 v5 카드")
    done_ok = done_bad = skipped = 0
    infer_seconds = 0.0
    infer_n = 0
    t_run = time.time()

    for i, row in enumerate(rows, 1):
        gid = google_id(str(row["Display Key"]))
        out_path = CARDS / f"{gid}.json"
        if usable(out_path):
            skipped += 1
            if i % 200 == 0:
                stamp(f"[{i}/{n}] 이미 있음 {skipped}건, 이어서 진행")
            continue
        t_item = time.time()
        ft_path = FULLTEXT / f"{gid}.json"
        status, code, html = "ok", 200, ""
        if ft_path.exists():
            doc = json.loads(ft_path.read_text(encoding="utf-8"))
        else:
            time.sleep(1.0)
            status, code, html = fetch(session, gid)
            if status != "ok":
                rec = {
                    "google_id": gid,
                    "display_key": row["Display Key"],
                    "lens_id": row["Lens ID"],
                    "status": status,
                    "http_code": code,
                    "model": MODEL,
                    "prompt_version": "v5",
                    "stage": "card",
                }
                out_path.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
                done_bad += 1
                elapsed = time.time() - t_run
                remain = n - i
                avg = elapsed / max(done_ok + done_bad, 1)
                eta = now() + timedelta(seconds=avg * remain)
                stamp(
                    f"[{i}/{n}] {gid} 본문 {status} HTTP {code} | 성공 {done_ok} 실패 {done_bad} 건너뜀 {skipped} | "
                    f"예상 종료 {eta.strftime('%m-%d %H:%M')}"
                )
                continue
            doc = parse_patent_html(html)
            doc.update({
                "google_id": gid,
                "display_key": row["Display Key"],
                "lens_id": row["Lens ID"],
                "url": f"https://patents.google.com/patent/{gid}/en",
                "fetched_at": now().isoformat(timespec="seconds"),
            })
            ft_path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")

        n_claims = len(doc.get("claims") or [])
        n_paras = sum(b.get("type") == "para" for b in doc.get("description") or [])
        if n_claims == 0 or n_paras == 0:
            rec = {
                "google_id": gid,
                "display_key": row["Display Key"],
                "lens_id": row["Lens ID"],
                "status": "no_text",
                "n_claims": n_claims,
                "n_paras": n_paras,
                "model": MODEL,
                "prompt_version": "v5",
                "stage": "card",
            }
            out_path.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
            done_bad += 1
            elapsed = time.time() - t_run
            remain = n - i
            avg = elapsed / max(done_ok + done_bad, 1)
            eta = now() + timedelta(seconds=avg * remain)
            stamp(
                f"[{i}/{n}] {gid} 청구항 {n_claims} 문단 {n_paras} 카드 생략 | 성공 {done_ok} 실패 {done_bad} | "
                f"예상 종료 {eta.strftime('%m-%d %H:%M')}"
            )
            continue

        user, meta = render_patent(doc, max_chars=13000, with_claims=True)
        try:
            rec = infer(system, fmt, validator, user)
        except Exception as exc:
            rec = {"seconds": round(time.time() - t_item, 1), "schema_errors": [str(exc)], "output": None, "done_reason": "error"}
        rec = {
            "google_id": gid,
            "display_key": row["Display Key"],
            "lens_id": row["Lens ID"],
            "status": "ok" if rec.get("output") is not None and not rec.get("schema_errors") else "schema_error",
            "prompt_version": "v5",
            "stage": "card",
            "model": MODEL,
            "options": "ollama_default",
            "think": False,
            "input_meta": meta | {"max_chars": 13000},
        } | rec
        out_path.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        ok = rec["status"] == "ok"
        done_ok += int(ok)
        done_bad += int(not ok)
        infer_n += 1
        infer_seconds += rec.get("seconds") or 0
        elapsed = time.time() - t_run
        remain = n - i
        avg = elapsed / max(done_ok + done_bad, 1)
        eta = now() + timedelta(seconds=avg * remain)
        stamp(
            f"[{i}/{n}] {gid} {rec.get('seconds')}초 {rec.get('done_reason')} 오류 {len(rec.get('schema_errors') or [])} | "
            f"성공 {done_ok} 실패 {done_bad} 건너뜀 {skipped} | "
            f"건당 {avg:.0f}초 | 예상 종료 {eta.strftime('%m-%d %H:%M')}"
        )

    stamp(f"끝 성공 {done_ok} 실패 {done_bad} 건너뜀 {skipped} 추론 {infer_n}건 {infer_seconds/max(infer_n,1):.0f}초/건")


if __name__ == "__main__":
    main()
