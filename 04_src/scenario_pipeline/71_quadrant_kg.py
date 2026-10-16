"""Display KG for quadrants: one node per latent group, not a hero pair.

Does not change pair_prob or P(s). Reads 60_pair_novel.csv / 60_pair_typical.csv
and 70_quadrants.csv. Contract: display-only, docs/04_run_status.md.

|s|=n is shown as an n-partite graph: one surface entity per group in s,
edges taken from the pair tables so endpoints stay consistent across pairs.
"""

from __future__ import annotations

import sys
from itertools import combinations

import pandas as pd

import config as cfg
from lib import ensure_out, write_json

CORNERS = ("existing", "opportunity", "contradiction", "review")
QUAD_KO = {
    "existing": "기존",
    "opportunity": "기회",
    "contradiction": "모순",
    "review": "검토",
}


def parse_groups(raw: str) -> tuple[int, ...]:
    return tuple(int(x) for x in str(raw).split("|") if str(x).strip() != "")


def pair_key(a: int, b: int) -> tuple[int, int]:
    return (a, b) if a < b else (b, a)


def load_names() -> dict[int, str]:
    path = cfg.OUT / "30_group_names.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    out: dict[int, str] = {}
    for rec in df.itertuples(index=False):
        short = str(rec.name).split("(")[-1].rstrip(")") if "(" in str(rec.name) else str(rec.name)
        out[int(rec.group)] = short
    return out


def selected_by_group(path) -> dict[int, set[str]]:
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    hit = df[df["selected"] == 1] if "selected" in df.columns else df
    out: dict[int, set[str]] = {}
    for rec in hit.itertuples(index=False):
        out.setdefault(int(rec.group), set()).add(str(rec.entity))
    return out


def lookup_pair(table: pd.DataFrame, a: int, b: int) -> pd.DataFrame:
    hit = table[((table["g1"] == a) & (table["g2"] == b)) | ((table["g1"] == b) & (table["g2"] == a))]
    return hit.sort_values("rank")


def _ends(rec: dict) -> tuple[tuple[int, str], tuple[int, str]]:
    return (int(rec["src_g"]), str(rec["h"])), (int(rec["dst_g"]), str(rec["t"]))


def _apply(rec: dict, nodes: dict[int, str], require_unique: bool) -> list[tuple[int, str]] | None:
    trial: list[tuple[int, str]] = []
    seen_e: dict[str, int] = {}
    for g, e in _ends(rec):
        if g in nodes and nodes[g] != e:
            return None
        if require_unique:
            owner = [gg for gg, ee in nodes.items() if ee == e]
            if owner and owner[0] != g:
                return None
            if e in seen_e and seen_e[e] != g:
                return None
        seen_e[e] = g
        trial.append((g, e))
    return trial


def _cand_score(rec: dict, prefer_high_n: bool, selected: dict[int, set[str]]) -> tuple:
    n_sel = sum(1 for g, e in _ends(rec) if e in selected.get(g, set()))
    nsum = float(rec["novelty"])
    return (n_sel, nsum if prefer_high_n else -nsum, -int(rec["rank"]))


def spanning_graph(
    groups: tuple[int, ...],
    pools: list[list[dict]],
    pairs: list[tuple[int, int]],
    prefer_high_n: bool,
    selected: dict[int, set[str]],
) -> tuple[dict[int, str], list[dict], bool]:
    """n nodes + consistent tree; leftover pairs stay as evidence triples."""
    parent = {g: g for g in groups}

    def find(g: int) -> int:
        while parent[g] != g:
            parent[g] = parent[parent[g]]
            g = parent[g]
        return g

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    nodes: dict[int, str] = {}
    chosen: list[dict] = []
    used_pair: set[tuple[int, int]] = set()
    ranked: list[tuple[tuple, int, dict]] = []
    for i, recs in enumerate(pools):
        for rec in recs:
            ranked.append((_cand_score(rec, prefer_high_n, selected), i, rec))
    ranked.sort(key=lambda x: x[0], reverse=True)

    def commit(rec: dict, role: str) -> None:
        copy = dict(rec)
        copy["edge_role"] = role
        for g, e in _ends(rec):
            nodes[g] = e
        chosen.append(copy)

    for _sc, i, rec in ranked:
        if len(chosen) >= len(groups) - 1:
            break
        a, b = pairs[i]
        pk = pair_key(a, b)
        if pk in used_pair:
            continue
        src, dst = int(rec["src_g"]), int(rec["dst_g"])
        if find(src) == find(dst):
            continue
        if _apply(rec, nodes, True) is None:
            continue
        commit(rec, "tree")
        used_pair.add(pk)
        union(src, dst)

    if len({find(g) for g in groups}) > 1:
        for _sc, i, rec in ranked:
            if len({find(g) for g in groups}) == 1:
                break
            a, b = pairs[i]
            pk = pair_key(a, b)
            if pk in used_pair:
                continue
            src, dst = int(rec["src_g"]), int(rec["dst_g"])
            if find(src) == find(dst):
                continue
            if _apply(rec, nodes, False) is None:
                continue
            commit(rec, "tree")
            used_pair.add(pk)
            union(src, dst)

    for i, recs in enumerate(pools):
        pk = pair_key(*pairs[i])
        if pk in used_pair:
            continue
        pick = None
        role = "cycle"
        for rec in recs:
            if _apply(rec, nodes, False) is not None:
                pick = rec
                break
        if pick is None:
            pick = recs[0]
            copy = dict(pick)
            copy["edge_role"] = "evidence"
            chosen.append(copy)
        else:
            commit(pick, role)
        used_pair.add(pk)

    unique = len(nodes) == len(groups) and len(set(nodes.values())) == len(groups)
    return nodes, chosen, unique


def joint_graph(
    groups: tuple[int, ...],
    source: pd.DataFrame,
    prefer_high_n: bool,
    selected: dict[int, set[str]],
    k: int,
) -> tuple[dict[int, str], list[dict], bool] | None:
    pairs = list(combinations(groups, 2))
    pools: list[list[dict]] = []
    for a, b in pairs:
        hit = lookup_pair(source, a, b).head(k)
        if hit.empty:
            return None
        pools.append(hit.to_dict("records"))

    def search(require_unique: bool) -> tuple[dict[int, str], list[dict], tuple] | None:
        best: tuple[dict[int, str], list[dict], tuple] | None = None

        def bt(i: int, nodes: dict[int, str], chosen: list[dict]) -> None:
            nonlocal best
            if i == len(pairs):
                n_unique = len(set(nodes.values()))
                n_sel = sum(1 for g, e in nodes.items() if e in selected.get(g, set()))
                nsum = sum(float(c["novelty"]) for c in chosen)
                score = (n_unique, n_sel, nsum if prefer_high_n else -nsum)
                if best is None or score > best[2]:
                    best = (dict(nodes), list(chosen), score)
                return
            for rec in pools[i]:
                trial = _apply(rec, nodes, require_unique)
                if trial is None:
                    continue
                added = []
                for g, e in trial:
                    if g not in nodes:
                        nodes[g] = e
                        added.append(g)
                chosen.append(rec)
                bt(i + 1, nodes, chosen)
                chosen.pop()
                for g in added:
                    del nodes[g]

        bt(0, {}, [])
        return None if best is None else (best[0], best[1], best[2])

    found = search(True)
    unique = True
    role = "joint"
    if found is None:
        found = search(False) if len(pairs) <= 3 else None
        unique = False
    if found is None:
        nodes, edges, unique = spanning_graph(groups, pools, pairs, prefer_high_n, selected)
        for g in groups:
            if g in nodes:
                continue
            for recs in pools:
                for rec in recs:
                    for gg, e in _ends(rec):
                        if gg == g:
                            nodes[g] = e
                            break
                    if g in nodes:
                        break
        return nodes, edges, unique and len(nodes) == len(groups) and len(set(nodes.values())) == len(groups)
    nodes, edges, _score = found
    tagged = []
    for rec in edges:
        copy = dict(rec)
        copy["edge_role"] = role
        tagged.append(copy)
    return nodes, tagged, unique and len(set(nodes.values())) == len(groups)


def print_graph(
    names: str,
    size: int,
    quadrant: str,
    occ: float,
    p_norm: float,
    nodes: dict[int, str],
    edges: list[dict],
    labels: dict[int, str],
    unique: bool,
) -> None:
    tag = QUAD_KO.get(quadrant, quadrant)
    flag = "" if unique else "  [노드 문자열 중복 — 후보가 안 맞물림]"
    print(f"       {names.replace('|', ' + ')}  (|s|={size})  {tag}  occ={occ:.3f}  P={p_norm:.3f}{flag}", flush=True)
    print("         nodes:", flush=True)
    for g in sorted(nodes):
        print(f"           [{labels.get(g, str(g))}]  {nodes[g]}", flush=True)
    print("         edges:", flush=True)
    for rec in edges:
        src, dst = int(rec["src_g"]), int(rec["dst_g"])
        a = labels.get(src, str(src))
        b = labels.get(dst, str(dst))
        role = str(rec.get("edge_role", "joint"))
        extra = ""
        if role == "evidence":
            extra = f"    [{nodes.get(src, rec['h'])} / {nodes.get(dst, rec['t'])} 노드와 끝점 불일치 — 쌍 증거]"
        print(
            f"           {a} —{rec['r']}→ {b}    "
            f"N={float(rec['novelty']):.2f} F={float(rec['prob']):.3f}  ({role}){extra}",
            flush=True,
        )


def main() -> int:
    ensure_out()
    q_path = cfg.OUT / "70_quadrants.csv"
    novel_path = cfg.OUT / "60_pair_novel.csv"
    typical_path = cfg.OUT / "60_pair_typical.csv"
    f_path = cfg.OUT / "60_pair_examples.csv"
    ent_path = cfg.OUT / "60_group_entities.csv"
    for path in (q_path, novel_path, typical_path, f_path):
        if not path.exists():
            raise SystemExit(f"{path} 가 없다. 60 과 70 을 먼저 실행하라.")
    quad = pd.read_csv(q_path)
    novel = pd.read_csv(novel_path)
    typical = pd.read_csv(typical_path)
    ftop = pd.read_csv(f_path)
    labels = load_names()
    selected = selected_by_group(ent_path)
    corners = quad[quad["quadrant"].isin(CORNERS)].copy()
    k = int(cfg.PAIR_GRAPH_CANDIDATES)

    node_rows: list[dict] = []
    edge_rows: list[dict] = []
    printed: list[tuple] = []
    n_unique_ok = 0
    n_fallback = 0
    n_fail = 0
    n_spanning = 0
    corners = corners.sort_values(["quadrant", "size", "p_norm"], ascending=[True, True, False])

    for scen in corners.itertuples(index=False):
        groups = parse_groups(scen.groups)
        prefer_high = scen.quadrant not in {"existing", "review"}
        source = novel if prefer_high else typical
        kind = "novel" if prefer_high else "typical"
        found = joint_graph(groups, source, prefer_high, selected, k)
        if found is None:
            n_fail += 1
            continue
        nodes, edges, unique = found
        if unique:
            n_unique_ok += 1
        else:
            n_fallback += 1
        if any(str(e.get("edge_role", "joint")) != "joint" for e in edges):
            n_spanning += 1
        printed.append(
            (
                str(scen.names),
                int(scen.size),
                str(scen.quadrant),
                float(scen.occ_ent),
                float(scen.p_norm),
                nodes,
                edges,
                unique,
            )
        )
        for g in groups:
            node_rows.append(
                {
                    "scenario_id": scen.scenario_id,
                    "quadrant": scen.quadrant,
                    "size": int(scen.size),
                    "names": scen.names,
                    "group": int(g),
                    "group_label": labels.get(int(g), str(g)),
                    "entity": nodes[int(g)],
                    "selected": int(nodes[int(g)] in selected.get(int(g), set())),
                    "unique_nodes": int(unique),
                    "display": kind,
                }
            )
        for rec in edges:
            a, b = int(rec["g1"]), int(rec["g2"])
            f1 = lookup_pair(ftop, a, b).head(1)
            f_triple = ""
            if len(f1):
                r = f1.iloc[0]
                f_triple = f"{r.h} --{r.r}--> {r.t}"
            src, dst = int(rec["src_g"]), int(rec["dst_g"])
            edge_rows.append(
                {
                    "scenario_id": scen.scenario_id,
                    "quadrant": scen.quadrant,
                    "size": int(scen.size),
                    "names": scen.names,
                    "occ_ent": float(scen.occ_ent),
                    "p_norm": float(scen.p_norm),
                    "pair": f"{min(a, b)}-{max(a, b)}",
                    "display": kind,
                    "unique_nodes": int(unique),
                    "edge_role": rec.get("edge_role", "joint"),
                    "src_g": src,
                    "dst_g": dst,
                    "src_label": labels.get(src, str(src)),
                    "dst_label": labels.get(dst, str(dst)),
                    "h": rec["h"],
                    "r": rec["r"],
                    "t": rec["t"],
                    "novelty": float(rec["novelty"]),
                    "prob": float(rec["prob"]),
                    "ht_cosine": float(rec["ht_cosine"]),
                    "h_lift": float(rec["h_lift"]),
                    "t_lift": float(rec["t_lift"]),
                    "f_top1": f_triple,
                }
            )

    nodes_df = pd.DataFrame(node_rows)
    edges_df = pd.DataFrame(edge_rows)
    nodes_df.to_csv(cfg.OUT / "71_scenario_nodes.csv", index=False)
    edges_df.to_csv(cfg.OUT / "71_quadrant_kg.csv", index=False)
    n_by = edges_df.groupby(["quadrant", "size"]).size().to_dict() if len(edges_df) else {}
    write_json(
        cfg.OUT / "71_manifest.json",
        {
            "n_edge_rows": int(len(edges_df)),
            "n_node_rows": int(len(nodes_df)),
            "n_scenarios": int(corners["scenario_id"].nunique()) if len(corners) else 0,
            "display_unit": "n_partite_graph",
            "candidates_per_pair": k,
            "n_unique_nodes_ok": n_unique_ok,
            "n_duplicate_node_fallback": n_fallback,
            "n_spanning_fallback": n_spanning,
            "n_fail": n_fail,
            "existing_review_source": "60_pair_typical.csv",
            "opportunity_contradiction_source": "60_pair_novel.csv",
            "pair_prob_unchanged": True,
            "p_s_unchanged": True,
            "n_by_quadrant_size": {f"{q}|{s}": int(n) for (q, s), n in n_by.items()},
        },
    )
    print(
        f"[71] scenarios={corners['scenario_id'].nunique()} "
        f"graphs unique={n_unique_ok} dup_fallback={n_fallback} spanning={n_spanning} fail={n_fail} "
        f"edges={len(edges_df)} nodes={len(nodes_df)}",
        flush=True,
    )
    for q in CORNERS:
        sub = [p for p in printed if p[2] == q]
        print(f"[71]   {QUAD_KO[q]}  n={len(sub)}", flush=True)
        last_size = None
        for item in sub:
            if item[1] != last_size:
                print(f"     |s|={item[1]}", flush=True)
                last_size = item[1]
            print_graph(*item[:7], labels, item[7])
    print(f"[71] wrote {cfg.OUT / '71_quadrant_kg.csv'}", flush=True)
    print(f"[71] wrote {cfg.OUT / '71_scenario_nodes.csv'}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
