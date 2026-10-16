# 02. 단계별 실행 스펙

> 각 단계는 **입력 파일 → 수식 → 출력 파일(컬럼까지) → 통과 게이트** 로 닫는다.
> 게이트를 통과하지 못하면 다음 단계로 넘어가지 않는다. 왜 이 값인지는 `01_open_decisions.md`, 한 장 계약은 `03_locked_spec.md`.
> 파라미터 이름은 `config.py`의 상수명과 1:1로 일치한다.
> 수식 경로의 결정(D1–D6, D8–D16)은 2026-08-29에 닫혔다. D7(명명)만 계산 경로 밖이다.

기호: 특허 $i = 1..N$ ($N = 1412$), 그룹 $g = 1..K$, 창 $w \in \{W1, W2, W3\}$, 시나리오 $s \subseteq \{1..K\}$.

---

## 단계 1 — 벡터 입력 $x$ 구성 · `10_build_features.py`

### 입력
- `data/pse_knowlege_graph_modifiy/*.json` (1,412)
- `data/knowlege_graph_entity_relation/final_standardization_results.json`
- `data/knowlege_graph_entity_relation/Entity_embeddings.npy` (28755, 768)
- `data/knowlege_graph_entity_relation/Sub_Relation_embeddings.npy` (2634, 768)

### 블록 구성

| 블록 | 원 차원 | 내용 |
|---|---:|---|
| `TXT` | 5 × 768 = **3,840** | `all-mpnet-base-v2`로 p/s/e 5칸을 **각각** 인코딩해 concat (D4 확정) |
| `KG` | 3 × 768 = 2,304 → `KG_DIM` | 트리플 벡터 $v_{it} = [e_h ; e_r ; e_t] \in \mathbb{R}^{2304}$의 특허 단위 **평균 pooling** |
| `CPC` | 113 + 1 | subclass multi-hot + 결측 플래그 |

- 트리플 pooling은 평균. 개수 편차(중위 14, 최대 40)는 평균이 흡수한다. max pooling은 이상치에 끌리므로 쓰지 않는다.
- v2 트리플이 0개인 7건은 `KG` 블록을 결측 처리하고 블록 평균으로 대치, `kg_missing=1` 플래그를 남긴다.

### 정규화와 축소 (순서를 바꾸지 말 것)

1. 블록별 z-score 표준화
2. 블록별 L2 정규화 → 블록 간 스케일 등화
3. 블록 가중 $w = (w_{TXT}, w_{KG}, w_{CPC})$, 기본 $(1,1,1)$
4. concat 후 PCA → $d$ = `PCA_DIM` (30)

### 출력

| 파일 | 내용 |
|---|---|
| `out/10_x.npy` | $(N, d)$ float64. 행 순서는 `10_index.csv`와 일치 |
| `out/10_index.csv` | `row, publication_number, filing_year, pub_year, window, assignee, n_triples_v2, n_cpc, kg_missing` |
| `out/10_blocks.npz` | PCA 이전 블록별 행렬 (인코더 교체 실험용) |
| `out/10_manifest.json` | 블록 차원, 설명분산, 가중치, 시드, 입력 파일 해시 |

### 게이트
- `10_index.csv` 행 수 == 1,412, `publication_number` 중복 0
- PCA 누적 설명분산을 기록. \(d\)는 GMM 예산(`PCA_DIM=30`, \(K\le 11.8\))으로 고정. 붕괴 하한 `PCA_MIN_EXPLAINED=0.35`. 복원 60%는 \(d\approx 82\)가 되어 쓰지 않는다 (2026-09-02 PoC)
- 임베딩 정렬 assert 통과 (`00_data_facts.md` §5)
- **주성분별 블록 기여도를 기록.** TXT(3,840d)가 KG(2,304d)·CPC(114d)보다 원 차원이 크므로, 상위 10개 주성분이 TXT에서만 나오면 블록 표준화가 실패한 것이다 → `BLOCK_WEIGHTS` 재조정
- GPU 인코딩 결과 해시를 `10_manifest.json`에 기록 (재현성)

---

## 단계 2 — 베이지안 GMM · `20_fit_bgmm.py`

### 수식
`sklearn.mixture.BayesianGaussianMixture`, `weight_concentration_prior_type='dirichlet_process'`.
책임도 $r_{ig} = P(g \mid x_i)$, $\sum_g r_{ig} = 1$.

### 파라미터
`K_MAX=30`, `covariance_type='diag'`, `weight_concentration_prior=1/K_MAX`, `n_init=10`, `max_iter=1000`, `random_state=42`.

### 유효 그룹 판정
$\pi_g \ge 1/(2 K_{\max})$ **그리고** hard-assign 특허 수 $\ge$ `MIN_GROUP_PATENTS`(=20).
유효하지 않은 성분은 제거하고 $r$을 행 기준 재정규화한다. 이후 모든 단계의 $K$는 이 유효 $K$다.

### 출력

| 파일 | 내용 |
|---|---|
| `out/20_resp.npy` | $(N, K)$ 재정규화된 책임도 |
| `out/20_groups.csv` | `group, weight, n_hard, mean_max_resp, top_cpc_subclass, top_entity_clusters` |
| `out/20_seed_stability.csv` | `seed_a, seed_b, ari` (시드 5개 쌍별) |
| `out/20_model.json` | 유효 K, 제거된 성분, 하이퍼파라미터, lower bound |

### 게이트
- 유효 $K$ 가 $1412/(4d)$ 이하인지 확인 ($d=30$이면 11.8). 초과 시 D5로 복귀
- 시드 5개 쌍별 ARI 중위 $\ge$ `ARI_GATE`(=0.60)
- **평균 max responsibility를 반드시 기록**한다. 0.9 이상이면 D1의 붕괴 위험이 확정되므로 (a) 정의를 쓰지 않는다

---

## 단계 3 — LLM 그룹 명명 · `30_name_groups.py` (선택, 계산 경로 아님)

입력: `out/20_resp.npy`, `out/10_x.npy`, `out/10_index.csv`, PSE/KG 원본.
그룹당 대표 특허 = 중심(마할라노비스) 최근접 `NAME_TOP_CENTRAL`. n_hard 상위 `NAME_N_LARGE_GROUPS`개 그룹만 중심에서 먼 `NAME_N_FAR_LARGE`건을 추가.
LLM이 읽는 본문은 **PSE 5칸**. 지식그래프는 대표 특허의 잦은 엔티티·옆 그룹과 다른 엔티티만 보조.
출력: `out/30_group_names.csv` (`group, name, one_line, distinguishing_entities, representative_patents, n_core, n_far`), `out/30_llm_log.jsonl` (프롬프트·응답 전문).
게이트: 이름이 어떤 수치에도 입력되지 않음을 코드로 보장(다른 스크립트가 이 파일을 읽지 않는다).

---

## 단계 4 — 시간축 부착 · `40_group_time.py`

### 수식
창 점유 (창별 합 = 1):

$$
\pi_g(w) = \frac{1}{\lvert I_w\rvert}\sum_{i \in I_w} r_{ig}
$$

다음 창 예측 (Dirichlet 스무딩, $\alpha_0=1$):

$$
\hat\pi_g(W_{\mathrm{next}}) = \frac{\alpha_0/K + \sum_{i \in W_{\mathrm{last}}} r_{ig}}{\alpha_0 + \lvert W_{\mathrm{last}}\rvert}
$$

창 정의: `W1=2019–2020`, `W2=2021–2022`, `W3=2023–2024` (filing 기준). `pre2019`(55건)와 2025(6건)는 추세에서 제외.

### 출력

| 파일 | 내용 |
|---|---|
| `out/40_group_time.csv` | `group, window, n_patents, pi_window, pi_row_normalized` |
| `out/40_group_year.csv` | 연 단위 동일 표 (그림용) |
| `out/40_trend.csv` | `group, pi_W3, pi_hat_next, slope_linear` (선형 추세는 민감도용) |
| `figures/40_group_time.png` | 창별 점유 스택 + 그룹별 시계열 |

### 게이트
- 창별 $\sum_g \pi_g(w) = 1$ (오차 1e-9)
- 창당 특허 수 기록: 250 / 507 / 594 (예상). 창×그룹 셀의 기대 건수가 10 미만인 그룹 수를 보고

---

## 단계 5 — feasibility 모델

### 5-a. 데이터셋 구축 · `50_build_kg_dataset.py`

입력: v2 트리플 전량 + 표준화 매핑 + 임베딩 2종.

positive: 정상 3-튜플 20,919건 (표면 수준). 각 트리플에 `publication_number`, `filing_year`, `window`, `h_cluster`, `r_std_bucket`, `t_cluster`를 함께 기록한다 — 단계 8의 시간 분할과 단계 6의 클러스터 집계가 이 컬럼을 쓴다.

negative: tail 40% / head 40% / relation 20%, 배수 1:5, filtered, 엔티티는 빈도 비례 샘플링, **관계 교체는 표면 수준이며 같은 STD 버킷 제외**.

분할: 시간 기반. 기본은 `filing_year <= 2022` 학습 / `>= 2023` 평가. 단계 8은 창별로 다시 만든다.

| 파일 | 내용 |
|---|---|
| `out/50_triples.csv` | `pos_neg, h, r, t, h_idx, r_idx, t_idx, h_cluster, r_std, t_cluster, publication_number, filing_year, window, split, corrupt_type` |
| `out/50_dropped.csv` | 비정형 352건 |
| `out/50_audit_sample.csv` | 수작업 감사용 negative 100건 (`D9` 필수) |

### 5-b. 학습·캘리브레이션 · `51_fit_feasibility.py`

경로 (A) — D8 확정: 엔티티·관계 768d → PCA `EMB_DIM`(=64) → 특징

$$
\phi(h,r,t) = [h \odot r \odot t \;;\; h \odot t \;;\; h \odot r \;;\; r \odot t] \in \mathbb{R}^{256}
$$

→ `LogisticRegression(C=1.0, max_iter=2000)`. 첫 블록만 쓰면 가중 DistMult와 동등.

경로 (C) baseline: 130×50×130 표준 트리플의 관측 빈도·PMI 기반 점수 (학습 없음).

캘리브레이션: held-out에 isotonic regression → `prob`. `score`와 `prob` 컬럼을 분리 유지.

| 파일 | 내용 |
|---|---|
| `out/51_model.npz` | PCA 행렬, 로지스틱 계수, isotonic 노드 |
| `out/51_eval.json` | filtered MRR, Hits@1/3/10, PR-AUC, ROC-AUC, Brier, ECE, 경로(C) 대비 개선폭 |
| `out/51_score_dist.csv` | positive/negative 점수 분포 |
| `figures/51_calibration.png` | 신뢰도 곡선 |

### 게이트
- held-out PR-AUC $\ge$ `PRAUC_GATE`(=0.80). 미달이면 D8/D9 재검토
- 경로 (C) baseline 대비 PR-AUC 개선이 없으면 **경로 (A)를 쓸 이유가 없다** — 이 사실을 기록하고 D8로 복귀
- ECE $\le$ 0.05
- negative 100건 수작업 감사 결과가 `docs/`에 기록되어 있어야 함

---

## 단계 6 — 시나리오 공간

### 6-a. 그룹 쌍 교차 점수 · `60_pair_scores.py`

1. 그룹 프로필 $u_g$ = 전체 특허 v2 **표면 엔티티 문자열**(head/tail)을 responsibility 가중 L1. `entity_mapping` 정수(0–129)는 **쓰지 않는다**. 임베딩 조회만 같은 파일의 키(문자열)로 한다.
2. 그룹 엔티티 = $u_{ge}/\bar u_e$ lift 상위, `PAIR_MASS_MIN`(=0.002) · `PAIR_LIFT_MIN`(=1.3), 상한 `TOP_CLUSTERS`(=20), 문자열 길이 ≤ `PAIR_ENTITY_MAX_CHARS`(=50). `PAIR_CLUSTER_MODE=lift_surface`.
3. 관계 후보 $R_{cand}$ = 누적 언급 질량 `REL_MASS`(=0.80)를 덮는 상위 표면 관계
4. 쌍 $(g_1,g_2)$의 후보 = $\mathrm{dist}(g_1)$ × $\mathrm{dist}(g_2)$ × $\lvert R_{cand}\rvert$ × 양방향, **내부 쌍 제외**
5. 같은 명사 `(h,t)` 제외: 짧은 이름 포함, 또는 `PAIR_SAME_NOUN_STEMS`(client/device/server/node/model) 공유. 이름 규칙이 못 잡는 임베딩 동의어만 코사인 \(\ge\) `PAIR_COS_MAX`(=0.80). `PAIR_UNIQUE_HT`이면 `(h,t)`당 최댓값 관계만 남긴 뒤 상위 `TOPK_PAIR`(=10) 평균

추가 산출: `out/60_group_entities.csv` (`group, entity_idx, entity, u, lift, selected`)

| 파일 | 내용 |
|---|---|
| `out/60_pair_scores.csv` | `g1, g2, pair_prob, topk_mean, n_candidates, observed_overlap` |
| `out/60_pair_examples.csv` | 쌍별 상위 10 트리플 (`h, r, t, ht_cosine, h_lift, t_lift, prob`) — **해석의 근거** |
| `out/60_group_entities.csv` | 그룹별 표면 엔티티 \(u\), lift, 선정 여부 |
| `figures/60_pair_heatmap.png` | $K \times K$ 쌍 점수 히트맵 |

게이트: `60_pair_examples.csv`의 상위 트리플을 읽어 사람이 "말이 되는가"를 확인. 여기서 무의미하면 뒤 단계 전부 무의미하다.

### 6-b. 시나리오 열거·확률 · `61_scenario_space.py`

상태공간: $\lvert s\rvert \in \{2,3,4\}$ 부분집합 **전수 열거** (D13 확정 — 이 단계를 MCMC라고 부르지 않는다).

$$
F_{\min}(s) = \min_{\mathrm{pair}}, \quad F_{\mathrm{mean}}(s) = \operatorname{mean}_{\mathrm{pair}}, \quad
P(s) \propto \Bigl(\prod_{g\in s}\hat\pi_g\Bigr) \cdot F_{\min}(s)^{\beta}
$$

$\beta$ = `BETA`(=1.0), 정규화는 크기 $\lvert s\rvert$별로 따로 한다.

| 파일 | 내용 |
|---|---|
| `out/61_scenarios.csv` | `scenario_id, groups, names, size, p_trend, f_min, f_mean, p_unnorm, p_norm, rank_in_size` |
| `out/61_space_manifest.json` | 후보 수, 크기별 정규화상수, $\beta$, 열거/MCMC 여부, $\beta$ 순위 상관 |
| `figures/61_scenario_scatter.png` | PoC: $x=F_{\min}$, $y=P_{\mathrm{trend}}$ (크기별). $x=\mathrm{occ}$ 는 단계 7 |

게이트
- 후보 수가 `00_data_facts.md` §8의 열거표와 일치
- MCMC를 켠 경우 열거 결과와 순위 상관 $\ge 0.95$
- $\beta \in \{0.5, 1, 2\}$에서 상위 20 시나리오의 겹침을 기록

---

## 단계 7 — 사분면 · `70_quadrants.py`

### 현재 점유 (D1 확정: 엔티티 클러스터 공유)
그룹 클러스터 프로필 $u_g \in \mathbb{R}^{130}$ (responsibility 가중 빈도, L1 정규화):

$$
\mathrm{occ}_{\mathrm{ent}}(s) = \sum_{c=1}^{130} \min_{g \in s} u_{gc}
$$

보조: $\mathrm{occ}_{\mathrm{asg}}(s)$ = $s$의 모든 그룹에 특허를 가진 출원인 수 (no-assignee 106건 제외), $\mathrm{occ}_{\mathrm{cpc}}(s)$ = 공유 subclass 질량, $\mathrm{occ}_{\mathrm{soft}}(s) = \sum_i \prod_{g\in s} r_{ig}$ (붕괴 진단용).

### 분류
두 축 모두 **크기 $\lvert s\rvert$별 삼분위**. 중간 1/3은 `undecided`.

| 파일 | 내용 |
|---|---|
| `out/70_quadrants.csv` | `scenario_id, groups, size, occ_ent, occ_asg, occ_cpc, occ_soft, p_norm, occ_tercile, p_tercile, quadrant` |
| `out/70_quadrant_counts.csv` | 사분면 × 크기별 후보 수 |
| `out/70_occ_agreement.csv` | 네 점유 지표 간 Spearman 상관 |
| `figures/70_quadrants.png` | 사분면 산점도 (라벨은 단계 3의 이름) |

게이트
- 네 칸 모두 후보 수 $\ge$ 10. 한 칸이 비면 D1 또는 D12로 복귀
- `occ_soft`가 사실상 전부 0인지 확인 → D1의 근거를 결과로 확정
- `occ_ent` vs `occ_asg` Spearman을 보고. 0.3 미만이면 "현재 점유"의 정의가 결론을 좌우한다는 뜻이므로 두 버전 결과를 모두 낸다
- **`occ_ent` vs `f_min` 상관을 보고.** 둘 다 같은 엔티티 임베딩 자산에서 나오므로 인위적 상관이 생길 수 있다. $\lvert\rho\rvert > 0.7$이면 사분면이 사실상 한 축이라는 뜻이므로 `occ_asg` 판본을 주 결과로 올린다 (D1)

---

## 단계 8 — 슬라이딩 윈도우 검증 · `80_sliding_window.py`

### 프로토콜
| 학습창 | 평가창 |
|---|---|
| $\le$ W1 (2019–20, 250건) | W2 (2021–22, 507건) |
| $\le$ W2 (2019–22, 757건) | W3 (2023–24, 594건) |

창별로 **다시** 만드는 것: PCA, BGMM, feasibility 학습 트리플, $\hat\pi_g$, $\mathrm{occ}(s)$.
창별로 만들 필요가 **없는** 것: 문장 인코더 (동결, 이 코퍼스로 학습하지 않음 — D4의 부수 이득).
창별로 만들 수 **없는** 것: ① 표준화 매핑 130/50 (전 기간 생성, 생성 코드 없음) ② 사전학습 인코더의 학습 데이터 → 둘 다 **잔존 누수로 명시** (D16).

민감도: `TEXT_ENCODER="tfidf_svd"` 대조군을 같은 창 설정으로 돌려, 인코더 종류가 검증 결론을 바꾸는지 본다.

창 간 그룹 대응: 헝가리안 매칭(비용 = 중심 간 코사인 거리), 대응표와 매칭 품질을 `out/80_group_matching.csv`에 남긴다. 매칭 실패 그룹은 `unmatched`로 두고 지표에서 제외한다.

### 지표
| 지표 | 정의 |
|---|---|
| `lift_at_k` | $P(s)$ 상위 $k$의 이후 점유 증가 평균 / 전체 평균 ($k \in \{10, 50, 100\}$) |
| `opportunity_realization` | "희귀 & 고확률" 칸에서 이후 점유가 오른 비율 |
| `contradiction_intrusion` | "희귀 & 저확률" 칸에서 이후 점유가 오른 비율 (낮아야 함) |
| `auc` | 이후 점유 증가 여부를 $P(s)$로 판별 |
| `ablation_no_F` | $P_{\mathrm{trend}}$만으로 계산한 동일 지표 |
| `ablation_no_trend` | $F_{\min}$만으로 계산한 동일 지표 |

| 파일 | 내용 |
|---|---|
| `out/80_window_metrics.csv` | `train_window, eval_window, metric, value, ablation` |
| `out/80_group_matching.csv` | 창 간 그룹 대응 |
| `out/80_scenario_outcomes.csv` | 시나리오별 사전 확률 / 사후 점유 변화 |
| `figures/80_lift_curve.png` | lift 곡선 + ablation |

게이트
- `ablation_no_F` 대비 개선이 없으면 단계 5의 기여를 주장할 수 없다 — 결과에 그대로 쓴다
- `contradiction_intrusion` < `opportunity_realization` 이어야 사분면 해석이 성립
- 창이 2개뿐이라 신뢰구간이 넓다. 부트스트랩 CI를 반드시 붙인다

---

## 산출물 요약 (감사용 최소 집합)

| 파일 | 없으면 재현 불가 |
|---|---|
| `out/10_manifest.json` | 블록·시드·입력 해시 |
| `out/20_model.json` + `20_seed_stability.csv` | 그룹 정의의 안정성 |
| `out/50_triples.csv` + `50_audit_sample.csv` | negative의 정당성 |
| `out/51_eval.json` | $F$가 학습됐다는 증거 |
| `out/60_pair_examples.csv` | 교차 관계가 해석 가능하다는 증거 |
| `out/61_scenarios.csv` | 공간 전수 (열거이므로 전량 보존 가능) |
| `out/70_occ_agreement.csv` | "현재 점유" 정의의 민감도 |
| `out/80_window_metrics.csv` | 검증 결론 |
