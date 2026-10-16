# 지식그래프 v1 검토 (1,412건)

modify 폴더 JSON의 **`knowledge_graph`(v1)** 만 읽는다. 에세이 칸, v2 열린 동사는 보지 않는다.

돌리기:

```bash
conda activate scenario-space
cd em_mcmc
python run_kg_v1_review.py
```

표: `out_kg_v1/`. 그림: `figures_kg_v1/`.

집계 규칙: 관계 네 종류(`Addresses_Problem` / `Comprises_Component` / `Implemented_By` / `Achieves_Effect`)의 **목적어**만 본다. 주어는 특허당 거의 하나라서 보기 재료가 아니다. 빈칸 문구(`core operation logic` 등)는 버린 뒤, 목적어의 **마지막 내용 토큰 1~2개(head)** 로 접어 반복을 센다.

---

## 한 줄

칸을 **빠뜨리지 않고** 채우는 추출은 잘 된다.  
그 칸 안의 말이 **객관식 보기**가 되는지는 아직 아니다.  
같은 틀로 5만 건을 돌려도 “빈 칸 없는 그래프”는 기대할 수 있고, “바로 축 3개”는 기대하면 안 된다.  
전체 문자열 hapax는 92~99%다. head로 접어도 81~89%로만 내려간다. 반복되는 head가 보기 **후보**이고, 사람이 합치고 버려야 문항이 된다.

---

## 추출이 잘 되는 부분 (대량 추출 전에 통과)

| 항목 | 숫자 |
|---|---|
| 파일 | 1,412 / 1,412 읽힘 |
| v1 그래프 있음 | 1,412 (빈 그래프 0) |
| 네 슬롯 모두 ≥1 | 1,412 중 **1,410** |
| 특허당 트리플 | 평균 7.88, 중앙값 7 |
| 특허당 서로 다른 주어 | 평균 1.25, 중앙값 1 |
| 특허당 서로 다른 목적어 | 평균 7.83 |
| v1이 아닌 관계 언급 | 14건 |

스키마는 잠겨 있다. 네 관계로 거의 다 떨어진다. 5만 건을 같은 틀로 돌려도 **형식은 버틸 가능성이 크다.**

주어는 재사용되고 목적어가 갈린다. 축·보기의 재료는 **목적어**다. 관계 종류가 문항 후보, head가 보기 후보다.

---

## 축으로 바로 못 쓰는 부분

객관식 보기는 **같은 답이 여러 장에서 반복**되어야 한다. 전체 문자열은 반대다. head로 접으면 어휘는 줄어들지만, 한 번만 나온 비율은 여전히 높다.

![hapax](../figures_kg_v1/12_hapax_full_vs_head.png)

![unique](../figures_kg_v1/12_unique_full_vs_head.png)

| 슬롯 | 특허에 이 칸이 있음 | 버린 빈칸 | 서로 다른 전체 문자열 (hapax) | 서로 다른 head (hapax) |
|---|---:|---:|---:|---:|
| problem | 99.9% | 26 | 1,514 (**99.0%**) | 1,196 (**88.7%**) |
| structure | 100% | 65 | 3,242 (92.2%) | 2,456 (80.9%) |
| how it runs | 100% | **204** | 2,572 (**97.7%**) | 2,054 (**87.3%**) |
| effect | 99.9% | 33 | 2,210 (93.3%) | 1,666 (81.9%) |

how it runs 에서 빈칸을 가장 많이 버렸다. 그래도 남은 head hapax는 87%다. 접기만으로 객관식이 되지는 않는다.

![상위 head](../figures_kg_v1/12_head_top.png)

반복 상위는 슬롯마다 성격이 다르다.

| 슬롯 | 가장 많이 나온 head | 특허 수 | 성격 |
|---|---|---:|---|
| problem | `federated learning` | **67** | 문제라기보다 방법. 문항과 답이 엇갈림 |
| structure | `central server` | 62 | 위치·구성. 보기 후보 |
| how it runs | `model parameters` | 22 | 짧지만 모호. 1위가 약함 |
| effect | `privacy protection` | 52 | 효과. 보기 후보 |

structure 쪽에는 **쓸 만한 반복**이 있다.

- `central server` 62, `server` 36, `processor` 35
- `edge servers` 34, `cloud server` 29, `edge devices` 24
- `computing nodes` 21, `iot devices` 18, `client devices` 17, `edge nodes` 16

위치 축 후보(device / edge / cloud / central server)는 이 칸에서 **이미 보인다.** 다만 `server`와 `central server`와 `cloud server`를 사람이 같은 보기·다른 보기로 나눠야 한다.

effect도 동의어를 합치면 축 후보가 된다.

- `privacy protection` 52, `data privacy` 17, `privacy preservation` 9
- `reduced latency` 22, `response time` 11, `time delay` 7
- `energy consumption` 22, `power consumption` 13
- `communication overhead` 12, `communication efficiency` 12
- `resource utilization` 30 (포괄적이라 보기인지 쓰레기인지 사람이 정함)

problem 1위 `federated learning` 67은 방법명이다. `federal learning` 12는 같은 말의 오타에 가깝다. 이 칸의 문자열을 그대로 문제 축 보기로 쓰면 문항이 흔들린다.

how it runs 는 `federated learning` 21, `homomorphic encryption` 7, `differential privacy` 5처럼 짧은 답이 섞여 있지만, 1위가 `model parameters`이고 `operation logic` 16은 빈칸의 잔재다. 지금 문자열 그대로는 축이 되기 어렵다.

전역 엔티티 클러스터(130개)로 접어도, 한 덩어리에 서로 다른 문제가 섞인다. 이번 검토에서는 **클러스터 ID를 수준으로 쓰지 않는 쪽**이 맞다.

---

## 그래서 축은 어떻게 잠그나 (이 결과 기준)

지금 1,412건만으로 **바로 8칸 EM**을 돌리기보다:

1. **structure**에서 빈칸을 버리고, 서버·엣지·클라우드·디바이스를 보기 3~4개로 합친다.  
   → 축 후보: **처리는 어디서 하나.**
2. **effect**에서 latency / energy / privacy / communication 을 보기 몇 개로 합친다.  
   → 축 후보: **무엇을 줄이려 하나.** (한 특허가 여러 효과를 말할 수 있음)
3. **how it runs**는 빈칸·`operation logic`을 제외하고, `federated learning`, `encryption` 같은 짧은 답만 남긴다. 답이 너무 갈리면 이번엔 축에서 뺀다.
4. **problem**은 점유용 메모로 두고, 보기 축으로는 아직 안 쓴다. `federated learning`을 이 칸의 보기로 쓰지 않는다.

이것이 “표를 보고 사람이 문항 3개를 고른다”의 이번 판 답이다. structure는 문항이 되고, effect는 합치면 문항이 되며, 나머지는 추출을 짧게 고치거나 동의어 표를 만든 뒤에야 문항이 된다.

---

## 5만 건 추출에 넘기기 전에 고칠 것

형식(주어–관계 네 종류–목적어)은 유지해도 된다. 바꿀 것은 **목적어를 짧게, 빈칸 금지**다. 가능하면 추출 단계에서 이미 head에 가까운 태그를 받게 한다.

금지하면 좋은 예:

- `core problem concept`, `core operation logic`, `primary benefit`
- `key component 1`, `key component 2`, `main technology entity`

structure / location 은 가능하면 짧은 태그:

`on-device` / `edge` / `cloud` / `central-server` / `unknown`

effect 도 짧은 태그:

`latency` / `energy` / `privacy` / `bandwidth` / `cost` / `accuracy` / `other`

지금처럼 긴 문장을 목적어로 넣으면, 5만 건이 되어도 hapax는 그대로다. 그래프는 “가득 찬 에세이”가 되고 시나리오 칸은 안 생긴다.

---

## 파일

| 경로 | 내용 |
|---|---|
| `out_kg_v1/12_manifest.json` | 건수, 빈 그래프 여부, 주어/목적어 수 |
| `out_kg_v1/12_head_summary.csv` | 슬롯별 전체 문자열 vs head hapax |
| `out_kg_v1/12_head_top.csv` | 슬롯별 상위 head |
| `out_kg_v1/12_heads.csv` | 트리플 전수 (head 포함, 감사) |
| `figures_kg_v1/*.png` | 위 그림 |
