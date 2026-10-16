# 관계 4개를 축으로 한 혼합 EM (1,412건)

축은 사람이 키워드로 고르지 않는다. v1 관계 네 종류가 축이다.  
수준 개수 \(K\)와 수준 프로필은 코퍼스에서 고른다.  
특허→셀은 한 칸 하드 할당이 아니라 축별 책임도의 **곱**이다.

```bash
conda activate scenario-space
cd em_mcmc
python run_kg_em.py
```

표: `out_kg_em/`. 그림: `figures_kg_em/`.

관측: 각 관계의 목적어 head(+ 구성 축은 주어 head)와, 같은 자리의 에세이 칸 토큰.  
problem←`problem`, structure←`solution_structure`, how it runs←`solution_function`+`solution_implementation`, effect←`effect`.  
빈칸 문구(`core operation logic` 등)는 버린다.

---

## 한 줄

소프트 매핑은 돌아간다. 1,412건 중 **1,402**건이 네 축 모두에 토큰이 있어 셀 확률을 받는다.  
다만 EM이 나눈 수준은 **시나리오 보기**라기보다, 네 칸 위에 앉은 **토픽**에 가깝다.  
\(K\)도 “진짜 수준이 6개”가 아니라, 허용 상한 6에서 held-out이 아직 올라가는 쪽에 가깝다. effect만 5에서 꺾인다.

---

## 무엇을 고정했고, 무엇이 데이터에서 나왔나

| | 출처 |
|---|---|
| 축 4개 | v1 관계. EM이 찾지 않음 |
| 수준 개수 \(K\) | 축마다 held-out 가능도 (학습 80% / 평가 20%) |
| 수준 이름 | 성분 상위 단어. 사람이 `edge`/`cloud`를 안 적음 |
| \(P(\text{수준}\mid\text{특허})\) | 축별 다항 혼합의 E-단계 |
| \(P(\text{셀}\mid\text{특허})\) | 네 축 책임도의 곱 (축 독립 가정) |

에세이 문장을 다섯 번째 축으로 쌓지 않았다. 같은 자리의 **관측을 살리는 텍스트**로만 썼다.

![어휘 구성](../figures_kg_em/20_feature_mix.png)

| 축 | 어휘 | head / 주어 / 에세이 | 토큰 없는 특허 | 특허당 평균 토큰 |
|---|---:|---|---:|---:|
| problem | 127 | 47 / 0 / 80 | 6 | 7.5 |
| structure | 230 | 112 / 38 / 80 | 2 | 11.9 |
| how it runs | 170 | 90 / 0 / 80 | 0 | 21.8 |
| effect | 218 | 138 / 0 / 80 | 2 | 8.3 |

그래프 head는 넣었다. 혼합이 실제로 붙잡는 질량은 에세이 고빈도 단어(`data`, `learning`, `system`) 쪽에 더 많다.

![빈 축](../figures_kg_em/20_empty_axis.png)

토큰이 없는 축은 그 축의 수준에 **균등**을 준다. 이번 실행에서는 거의 없다.

---

## 수준 개수는 코퍼스가 고른다

\(K=2\ldots6\). 평가 가능도가 가장 큰 \(K\)를 쓴 뒤, 전체 데이터로 다시 맞춘다.

![K 선택](../figures_kg_em/21_k_selection.png)

| 축 | 고른 K | held-out loglik / 문서 |
|---|---:|---:|
| problem | **6** (상한) | −32.87 |
| structure | **6** (상한) | −51.40 |
| how it runs | **6** (상한) | −86.70 |
| effect | **5** | −35.13 (K=6은 −35.14로 조금 더 나쁨) |

problem / structure / how it runs 는 K를 올릴수록 평가 가능도가 계속 오른다. “수준이 6개”가 아니라 **상한에 걸린 것**이다. 에세이 토큰이 토픽을 계속 쪼갤 여지가 있다는 뜻이다. effect만 5에서 한 번 꺾인다.

셀 수는 \(6\times6\times6\times5=\) **1,080**.

---

## 축마다 소프트 소속

인용한 예의 “저전력 70% / 30%”가 여기서는 \(P(\text{수준}\mid\text{특허})\)다.

![축별 확신](../figures_kg_em/21_axis_confidence.png)

| 축 | 평균 \(\max r\) | \(\max r \ge 0.8\) 비율 |
|---|---:|---:|
| problem | 0.83 | 66% |
| structure | 0.91 | 81% |
| how it runs | 0.93 | 86% |
| effect | 0.87 | 75% |

축 위에서는 꽤 뾰족하다. 한 특허가 한 축에서 두 수준에 넓게 걸치는 경우는, 키워드 골격의 unmapped 문장보다 적다. 소프트는 **셀 곱**에서 더 살아난다. 네 축을 곱하면 최선 셀 확률 평균은 **0.63**이다 (아래).

![수준 점유](../figures_kg_em/21_level_occupancy.png)

![수준 단어](../figures_kg_em/21_level_words.png)

성분 상위 단어(사람이 붙인 이름이 아님):

| 축 | 수준 (상위 단어) | 소프트 점유 |
|---|---|---:|
| problem | time/data/real · federated learning · devices/power · privacy · edge/network · processing | 154–281 |
| structure | learning-method/server · unit/processor/memory · network/model · model/server/local · module · **edge/computing** (가장 큼, 348) | 154–348 |
| how it runs | federated training · edge/cloud · detection · **local/global/server** · device/user · edge/network | 142–287 |
| effect | **privacy** · edge 개선 · time/efficiency · federated 효율 · improved/reduced | 263–309 |

읽을 수 있는 갈림은 있다. structure의 edge vs local/server, how it runs의 federated vs local/global, effect의 privacy vs 시간/효율.  
동시에 `data`/`learning`/`system`이 여러 성분에 반복된다. 이건 **보기 3~4개로 잠근 축**이 아니라, 같은 코퍼스의 주제 덩어리다.

---

## 셀 = 네 수준의 곱 (소프트)

특허 \(i\)의 셀 \(k=(\ell_1,\ell_2,\ell_3,\ell_4)\)  
\(r_{ik} \propto \prod_d P(\ell_d \mid i)\).  
점유는 \(\sum_i r_{ik}\). 한 칸에 구겨 넣지 않는다.

| 항목 | 숫자 |
|---|---|
| 셀 | 1,080 |
| 네 축 모두 관측 있음 | **1,402 / 1,412** |
| 최선 셀 확률 평균 | 0.63 |
| 최선 셀 ≥ 0.25 | 90% |
| 소프트 점유 ≥ 1인 셀 | **287** |
| 1위 셀 비중 | 4.4% |

![상위 셀](../figures_kg_em/21_top_cells.png)

1위 셀(기대 61건, 하드 67건)은 네 축이 모두 edge 쪽으로 붙는 조합이다.

`problem: edge/network | structure: edge/computing | how: edge/network | effect: improved/edge`

2위는 federated / local-server 묶음 (기대 36건). 3위는 privacy × local/server (기대 34건).

공간이 1,080칸인데 질량이 있는 칸은 287개다. 나머지는 곱 가정 아래 **아직 안 찬 칸**이다. 지금 제약 MCMC를 안 넣었으므로, 빈 칸을 모순과 gap으로 나누지는 않는다.

![structure × effect](../figures_kg_em/21_pair_structure_effect.png)

두 축 책임도의 곱을 특허마다 더하면, 구성 수준과 효과 수준이 같이 나타나는 밀도다. 대각선처럼 한 효과가 한 구성에만 붙지는 않는다. 특허가 여러 효과를 말하기 때문이다.

---

## 이 결과로 말해도 되는 것 / 안 되는 것

말해도 되는 것:

- 이미 있는 그래프 관계와 에세이만으로, 사람 코드북 없이 **수준 혼합 + 셀 소프트 점유**를 계산할 수 있다.
- 하드 1칸 할당보다 셀 밀도가 덜 깎인다. 최선 칸 평균 0.63이 그 숫자다.
- 반복해서 보이는 덩어리는 edge 묶음, federated/local-server 묶음, privacy 묶음이다.

말하면 안 되는 것:

- “EM이 시나리오 축을 찾았다.” 축은 추출 스키마가 준 네 관계다.
- “수준이 객관식 보기다.” 성분은 토픽에 가깝고, \(K=6\)은 세 축에서 상한이다.
- “1,080칸이 형태 공간 \(S\)다.” 양립 제약이 없고, 축 독립 곱이라 같이 안 나오는 조합도 칸으로 남아 있다.

키워드 골격(사전 3×2, n=400)과 비교하면, 여기서는 unmapped가 거의 없다. 대신 칸의 의미가 사전에 잠기지 않았다.

---

## 다음에 손볼 것 (이번 실행이 가리키는 것)

1. 에세이 단일어 대신 **짧은 태그/head만** 넣으면, 성분이 `data`/`learning` 대신 location·effect 보기에 가까워질 가능성이 있다. 지금 질량은 에세이 고빈도 단어가 가져간다.
2. \(K\) 상한을 올리기보다, 축마다 **작은 \(K\)(2~4)** 를 품질(해석·시간축 검증)로 비교하는 편이 시나리오 공간에는 맞다. held-out만 보면 토픽을 계속 쪼갠다.
3. 셀 곱의 독립 가정은 강하다. 제약은 그 다음 층(지금 골격의 MCMC)이다.

---

## 파일

| 경로 | 내용 |
|---|---|
| `out_kg_em/20_manifest.json` | 건수, 에세이 연결 |
| `out_kg_em/20_feature_summary.csv` | 축별 어휘·빈 문서 |
| `out_kg_em/21_k_selection.csv` | \(K\)별 held-out |
| `out_kg_em/21_levels.csv` | 수준 태그·점유 |
| `out_kg_em/21_cells.csv` | 1,080셀 소프트/하드 점유 |
| `out_kg_em/21_r_*.npy` | 특허 × 수준 책임도 |
| `figures_kg_em/*.png` | 위 그림 |
