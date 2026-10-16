# 03. 잠긴 실행 계약 (2026-08-29)

> 이 문서가 구현 시 단일 계약이다. 수식·단위·게이트만 적는다. 왜 이렇게 됐는지는 `01_open_decisions.md`, 숫자의 근거는 `00_data_facts.md`, 파일 컬럼은 `02_stage_specs.md`.
> **실행 상태·다음 단계:** `04_run_status.md`. 단계 1–8은 구현·실행됨. 주장은 아직 지지되지 않음.

## 한 줄

1,412건의 PSE/상세 KG를 임베딩해 **베이지안 GMM으로 latent group을 찾고**, 상세 KG로 **feasibility 스코어러를 학습**한 뒤, 그룹 부분집합을 **전수 열거**해 $P(s) \propto P_{\mathrm{trend}}(s)\, F_{\min}(s)^{\beta}$ 를 계산하고, **현재 점유(엔티티 클러스터 공유)** 와 교차해 사분면을 만든 다음, **창 2개 슬라이딩 윈도우**로 검증한다.

## 객체

| 기호 | 정의 |
|---|---|
| $i$ | 특허. $N=1412$. 표본은 이 1,412건 자체이며 Edge AI 50k의 확률 표본이 아니다 |
| $x_i \in \mathbb{R}^{30}$ | P/S/E 5칸 각각 `all-mpnet-base-v2`(768d) + KG 평균 pooling + CPC subclass. 블록 z-score → L2 → concat → PCA 30 |
| $r_{ig}$ | BGMM 책임도. $\sum_g r_{ig}=1$. diag 공분산, $K_{\max}=30$, 유효 $K$는 $\pi_g \ge 1/60$ 그리고 hard ≥ 20 |
| $s \subseteq \{1,\ldots,K\}$, $\lvert s\rvert\in\{2,3,4\}$ | 시나리오. 크기별로 따로 정규화·보고 |
| $\pi_g(w)$ | 창 $w$ 내 평균 $r_{\cdot g}$. 창별 합 = 1. 기준일 `filing_date`. $W1=2019$–$20$, $W2=2021$–$22$, $W3=2023$–$24$ |
| $\hat\pi_g$ | $\dfrac{1/K + \sum_{i\in W_{\mathrm{last}}} r_{ig}}{1 + \lvert W_{\mathrm{last}}\rvert}$ |
| $P_{\mathrm{trend}}(s)$ | $\prod_{g\in s}\hat\pi_g$ (결합 신규성은 넣지 않는다) |
| $\mathrm{score}(h,r,t)$ | 동결 768d → PCA 64d → $\phi=[h\odot r\odot t;\; h\odot t;\; h\odot r;\; r\odot t]$ → 로지스틱. isotonic 후 `prob` |
| $\mathrm{pair}(g_1,g_2)$ | 교차 후보 상위 10개 `prob`의 평균. 그룹 내부 쌍 제외. **PoC 단위는 v2 표면 엔티티** (`04_run_status.md`). `entity_mapping` 정수 0–129는 쓰지 않음 |
| $F_{\min}(s)$ | $\min_{g_1<g_2}\mathrm{pair}$. 사분면의 기본 축. $F_{\mathrm{mean}}$은 병기 |
| $P(s)$ | $\propto P_{\mathrm{trend}}(s)\cdot F_{\min}(s)^{\beta}$, $\beta=1$. **전수 열거**, 크기별 정규화 |
| $\mathrm{occ}(s)$ | $\sum_{c=1}^{130}\min_{g\in s} u_{gc}$. $u_g$는 그룹의 130-클러스터 L1 프로필. 출원인·CPC·soft곱은 보조 |

이 단계를 MCMC라고 부르지 않는다.

## 계산 경로 (단계 3은 라벨 전용, 건너뛴다)

```
10  x_i          → 20  r_ig, K
                 → 40  π_g(w), π̂_g
                 → 50/51  F 스코어러
                 → 60  pair(g1,g2)
                 → 61  전 후보 P(s)
                 → 70  occ × P 사분면
                 → 80  창 2개 검증 + F 제거 대조군
```

## 사분면 (크기 $\lvert s\rvert$별 삼분위, 중간 1/3은 보류)

| | $P(s)$ 하위 1/3 | $P(s)$ 상위 1/3 |
|---|---|---|
| $\mathrm{occ}$ 상위 1/3 | 이상·오류 검토 | 기존 기술 |
| $\mathrm{occ}$ 하위 1/3 | 모순 공간 | **미래 기회 공간** |

## 검증 (누수 금지)

학습 $\le W1$ → 평가 $W2$, 학습 $\le W2$ → 평가 $W3$.
창별로 다시: PCA, BGMM, $F$, $\hat\pi$, $\mathrm{occ}$.
동결: 문장 인코더.
재생성 불가(한계로 명시): 표준화 매핑 130/50, 사전학습 인코더의 학습 데이터.

주 지표: Lift@k, 기회 칸 실현율, 모순 칸 침범율, AUC.
**반드시** $F$ 제거 대조군(`no_F`)과 추세 제거 대조군(`no_trend`)을 같은 표에 둔다. $F$ 제거 대비 개선이 없으면 단계 5의 기여를 주장하지 않는다.

## 구현이 막히면 돌아가는 게이트 (요지)

| 단계 | 실패 조건 | 의미 |
|---|---|---|
| 1 | PCA 30d 설명분산 < 35%, 또는 주성분이 TXT만 | \(d\)는 GMM \(K\) 예산. 복원 60%는 쓰지 않음 |
| 2 | 유효 $K > 1412/(4d)$, 또는 시드 ARI 중위 < 0.60 | $d$ 또는 $K_{\max}$ |
| 5 | held-out PR-AUC < 0.80, 또는 경로 C 대비 개선 없음 | \(F\)를 "기술적 가능성"이라 부르지 말 것. **2026-09-02 PoC: PR-AUC 0.29, C는 이김 → 관측 유사도로 진행. relation 별도 인코딩은 후속** |
| 7 | 사분면 한 칸이 비거나, $\mathrm{occ}_{\mathrm{ent}}$와 $F_{\min}$ 상관 > 0.7 | 점유를 출원인 판본으로 올려라 |
| 8 | `no_F` 대비 개선 없음 | 단계 5 기여 없음. 그 사실을 결과로 쓴다 |

## 환경 제약 (2026-09-02 재검증)

- conda `scenario-space`. `sentence-transformers==6.0.0`, `torch==2.11.0+cu128`.
- 드라이버 CUDA 12.9 (576.88), **RTX 4060 GPU 사용**. P/S/E 7,060개는 1회 인코딩 후 `out/10_blocks.npz`에 캐시.
- 스크립트는 `scipy`/`sklearn`을 `torch`보다 먼저 import한다. 2.13.0+cu130에서 보이던 `CXXABI_1.3.15`는 현재 빌드에서 재현되지 않음.
- import 순서와 캐시 규칙은 `02_stage_specs.md` 단계 1 게이트.

## 구현 상태 (2026-09-03)

`80_sliding_window.py` 포함 1–8은 구현·실행됨. 단계 5의 \(F\)는 게이트 0.80을 못 넘겼고, 6-b의 \(F_{\min}\)은 순위를 거의 바꾸지 않는다. 단계 7 기회 칸은 크기 2에서 2건뿐이며 \(F_{\min}\) 기여로 읽지 않는다. 단계 8은 W1에서 그룹 1개, W2→W3에서 시나리오 4개라 기회 실현율을 못 쟀고 `full≡no_F`다. 다음 작업은 `04_run_status.md` §7.
