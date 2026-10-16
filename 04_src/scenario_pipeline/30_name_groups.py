"""Stage 3 — LLM names for latent groups. Labels only; no later script reads this.

Representatives: Mahalanobis-nearest k to the group center. The two largest
groups also get far-from-center patents. The LLM reads PSE; KG entities are
contrast only. Contract: docs/02_stage_specs.md D7.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from collections import Counter

import numpy as np
import pandas as pd

import config as cfg
from lib import (
    CODE_FENCE,
    CODE_FENCE_END,
    ensure_out,
    load_patents,
    write_json,
)

SYSTEM = """You name latent technology groups found in patents.
Read the PSE essays (problem / solution function / structure / implementation / effect). That is the main evidence.
Knowledge-graph entities are only a hint for what this group uses that neighbors do not.
Do not use CPC codes as the name.
Do not copy a patent title as the name.
Write names in Korean, concrete and technical (not "AI 기술" or "엣지 컴퓨팅" alone).
Reply with a single JSON object, no markdown:
{"name": "짧은 이름", "one_line": "한 줄 설명", "distinguishing_entities": "이 그룹을 가르는 개념 2~5개, 쉼표"}"""


def _require_stage2() -> tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    x_path = cfg.OUT / "10_x.npy"
    resp_path = cfg.OUT / "20_resp.npy"
    idx_path = cfg.OUT / "10_index.csv"
    if not x_path.exists() or not resp_path.exists() or not idx_path.exists():
        raise SystemExit("단계 1–2 산출물이 없다. 10_build_features.py 와 20_fit_bgmm.py 를 먼저 실행하라.")
    x = np.load(x_path)
    resp = np.load(resp_path)
    index = pd.read_csv(idx_path)
    if not (len(index) == x.shape[0] == resp.shape[0]):
        raise SystemExit(f"행 수 불일치 index={len(index)} x={x.shape} resp={resp.shape}")
    return x, resp, index


def mahalanobis2(points: np.ndarray, mu: np.ndarray, var: np.ndarray) -> np.ndarray:
    return ((points - mu) ** 2 / np.clip(var, 1e-8, None)).sum(axis=1)


def pick_representatives(x: np.ndarray, hard: np.ndarray, n_hard: np.ndarray) -> dict[int, dict]:
    large = set(np.argsort(-n_hard)[: cfg.NAME_N_LARGE_GROUPS].tolist())
    chosen: dict[int, dict] = {}
    for g in range(hard.max() + 1):
        members = np.where(hard == g)[0]
        pts = x[members]
        mu = pts.mean(axis=0)
        var = pts.var(axis=0)
        dist = mahalanobis2(pts, mu, var)
        order = np.argsort(dist)
        k_core = min(cfg.NAME_TOP_CENTRAL, len(members))
        core = members[order[:k_core]].tolist()
        far: list[int] = []
        if g in large and len(members) > k_core:
            n_far = min(cfg.NAME_N_FAR_LARGE, len(members) - k_core)
            far = members[order[::-1][:n_far]].tolist()
            far = [i for i in far if i not in core][: cfg.NAME_N_FAR_LARGE]
        chosen[g] = {"core": core, "far": far, "is_large": g in large, "n": int(len(members))}
    return chosen


def clip(text: str, n: int) -> str:
    text = " ".join(str(text).split())
    if len(text) <= n:
        return text
    return text[: n - 1].rstrip() + "…"


def group_entity_counts(patents: list[dict], hard: np.ndarray, index: pd.DataFrame) -> list[Counter]:
    pub_to_i = {str(p): i for i, p in enumerate(index["publication_number"].astype(str))}
    k = int(hard.max()) + 1
    counts = [Counter() for _ in range(k)]
    for rec in patents:
        i = pub_to_i.get(rec["publication_number"])
        if i is None:
            continue
        g = int(hard[i])
        for head, _rel, tail in rec["triples_v2"]:
            if head:
                counts[g][head] += 1
            if tail:
                counts[g][tail] += 1
    return counts


def distinguishing(counts: list[Counter], g: int, k_show: int = 8) -> list[str]:
    own = counts[g]
    others: Counter = Counter()
    for h, c in enumerate(counts):
        if h != g:
            others.update(c)
    scored = []
    for ent, n in own.most_common(40):
        score = n / (1.0 + others.get(ent, 0))
        scored.append((score, n, ent))
    scored.sort(reverse=True)
    return [ent for _s, _n, ent in scored[:k_show]]


def format_patent(rec: dict, role: str) -> str:
    pse = rec["pse"]
    lines = [
        f"[{role}] {rec['publication_number']}",
        f"title: {clip(rec.get('title') or '', 160)}",
    ]
    for slot in cfg.PSE_SLOTS:
        lines.append(f"{slot}: {clip(pse.get(slot) or '', cfg.NAME_PSE_CHARS)}")
    return "\n".join(lines)


def build_prompt(
    g: int,
    spec: dict,
    recs: dict[int, dict],
    top_entities: list[str],
    dist_entities: list[str],
    prior_names: list[str],
    n_hard: int,
    top_cpc: str,
) -> str:
    blocks = [format_patent(recs[i], "core") for i in spec["core"]]
    blocks += [format_patent(recs[i], "periphery") for i in spec["far"]]
    prior = ", ".join(prior_names) if prior_names else "(none yet)"
    return f"""Group {g}  (n_patents={n_hard}, large={spec['is_large']})
Already used names (do not repeat): {prior}
Frequent CPC (do not use as the name): {top_cpc or "(none)"}
Frequent KG entities in this group: {", ".join(top_entities) or "(none)"}
Entities more typical of this group than others: {", ".join(dist_entities) or "(none)"}

Core patents are closest to the group center. Periphery patents (if any) are farthest; they must not dominate the name.

{chr(10).join(blocks)}
"""


def parse_llm_json(text: str) -> dict:
    raw = text.strip()
    if "```" in raw:
        raw = CODE_FENCE.sub("", raw)
        raw = CODE_FENCE_END.sub("", raw)
    start, end = raw.find("{"), raw.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("JSON object not found in LLM output")
    obj = json.loads(raw[start : end + 1])
    if not isinstance(obj, dict):
        raise ValueError("LLM JSON is not an object")
    name = str(obj.get("name") or "").strip()
    if not name:
        raise ValueError("empty name")
    return {
        "name": name,
        "one_line": str(obj.get("one_line") or "").strip(),
        "distinguishing_entities": str(obj.get("distinguishing_entities") or "").strip(),
    }


def ollama_chat(prompt: str) -> str:
    payload = {
        "model": cfg.LLM_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "options": {"temperature": float(cfg.LLM_TEMPERATURE), "num_predict": 500},
    }
    req = urllib.request.Request(
        cfg.OLLAMA_URL.rstrip("/") + "/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise SystemExit(
            f"Ollama 에 연결할 수 없다 ({cfg.OLLAMA_URL}). "
            f"`ollama serve` 와 모델 `{cfg.LLM_MODEL}` 을 확인하라. 원인: {exc}"
        ) from exc
    msg = body.get("message") or {}
    content = msg.get("content")
    if not content:
        raise SystemExit(f"Ollama 응답이 비었다: {body!r}"[:400])
    return str(content)


def main() -> int:
    if not cfg.LLM_PROVIDER:
        print("[30] LLM_PROVIDER 가 None 이라 건너뛴다.", flush=True)
        return 0
    ensure_out()
    x, resp, index = _require_stage2()
    hard = resp.argmax(axis=1)
    n_hard = np.bincount(hard, minlength=resp.shape[1])
    print(f"[30] groups={resp.shape[1]} n_hard={n_hard.tolist()} provider={cfg.LLM_PROVIDER} model={cfg.LLM_MODEL}", flush=True)

    chosen = pick_representatives(x, hard, n_hard)
    print("[30] load patents", flush=True)
    patents = load_patents()
    recs = {i: rec for i, rec in enumerate(patents)}
    if patents[0]["publication_number"] != str(index.loc[0, "publication_number"]):
        by_pub = {rec["publication_number"]: rec for rec in patents}
        recs = {i: by_pub[str(pub)] for i, pub in enumerate(index["publication_number"].astype(str))}

    ent_counts = group_entity_counts(patents, hard, index)
    groups_meta = pd.read_csv(cfg.OUT / "20_groups.csv") if (cfg.OUT / "20_groups.csv").exists() else None

    rows = []
    log_path = cfg.OUT / "30_llm_log.jsonl"
    if log_path.exists():
        log_path.unlink()
    prior_names: list[str] = []

    for g in range(resp.shape[1]):
        spec = chosen[g]
        top_ent = [e for e, _ in ent_counts[g].most_common(cfg.NAME_TOP_ENTITIES)]
        dist_ent = distinguishing(ent_counts, g)
        top_cpc = ""
        if groups_meta is not None:
            hit = groups_meta.loc[groups_meta["group"] == g]
            if not hit.empty:
                top_cpc = str(hit.iloc[0].get("top_cpc_subclass") or "")
        prompt = build_prompt(
            g, spec, recs, top_ent, dist_ent, prior_names, int(n_hard[g]), top_cpc
        )
        print(f"[30] naming group={g} core={len(spec['core'])} far={len(spec['far'])}", flush=True)
        raw = ollama_chat(prompt)
        try:
            parsed = parse_llm_json(raw)
        except (ValueError, json.JSONDecodeError) as exc:
            print(f"[30] JSON parse fail group={g}: {exc}; retry once", flush=True)
            raw = ollama_chat(prompt + "\n\nReturn ONLY the JSON object.")
            parsed = parse_llm_json(raw)

        pubs = [recs[i]["publication_number"] for i in spec["core"] + spec["far"]]
        row = {
            "group": g,
            "name": parsed["name"],
            "one_line": parsed["one_line"],
            "distinguishing_entities": parsed["distinguishing_entities"],
            "representative_patents": "|".join(pubs),
            "n_core": len(spec["core"]),
            "n_far": len(spec["far"]),
            "n_hard": int(n_hard[g]),
            "is_large": bool(spec["is_large"]),
        }
        rows.append(row)
        prior_names.append(f"{g}:{parsed['name']}")
        with log_path.open("a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {"group": g, "prompt": prompt, "response": raw, "parsed": parsed},
                    ensure_ascii=False,
                )
                + "\n"
            )
        print(f"[30] g={g} name={parsed['name']}", flush=True)

    out = pd.DataFrame(rows)
    out.to_csv(cfg.OUT / "30_group_names.csv", index=False)
    write_json(
        cfg.OUT / "30_manifest.json",
        {
            "provider": cfg.LLM_PROVIDER,
            "model": cfg.LLM_MODEL,
            "temperature": cfg.LLM_TEMPERATURE,
            "n_central": cfg.NAME_TOP_CENTRAL,
            "n_far_large": cfg.NAME_N_FAR_LARGE,
            "n_large_groups": cfg.NAME_N_LARGE_GROUPS,
            "primary_text": "PSE",
            "kg_role": "contrast_entities_only",
            "note": "Label only. Later stages must not read 30_group_names.csv.",
        },
    )
    print(f"[30] wrote {cfg.OUT / '30_group_names.csv'}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
