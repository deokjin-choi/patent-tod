# PSE / 지식그래프 v1 검토 (1,412건)

modify 폴더만 사용. `pse` 다섯 칸은 파일마다 채워져 있고, 집계는 **`knowledge_graph`(v1)** 의 목적어만 셈.
v2는 보지 않음.

돌리기:

```bash
conda activate scenario-space
cd em_mcmc
python run_pse_review.py
```

표: `out_pse/`. 그림: `figures_pse/`.

---

## 한 줄

칸을 **빠뜨리지 않고** 채우는 추출은 잘 된다.  
그 칸 안의 말이 **객관식 보기**가 되는지는 아직 아니다.  
5만 건을 같은 프롬프트로 돌리면 “빈 칸 없는 그래프”는 기대할 수 있고, “바로 축 3개”는 기대하면 안 된다.

---

## 추출이 잘 되는 부분 (50만 건 전에 통과)

![커버리지](../figures_pse/10_slot_coverage.png)

| 항목 | 숫자 |
|---|---|
| 파일 | 1,412 / 1,412 읽힘 |
| `pse` 있음 | 1,412 |
| v1 그래프 있음 | 1,412 (빈 그래프 0) |
| 네 슬롯 모두 ≥1 | 1,412 중 **1,410** |
| 특허당 트리플 | 평균 7.9, 중앙값 7 |
| v1이 아닌 관계 | 6건뿐 |

스키마는 잠겨 있다. `Addresses_Problem` / `Comprises_Component` / `Implemented_By` / `Achieves_Effect` 네 가지로 거의 다 떨어진다. 5만 건을 같은 틀로 돌려도 **형식은 버틸 가능성이 크다.**

![트리플 수](../figures_pse/10_triples_per_patent.png)

특허마다 그래프가 0~1개가 아니라, 대략 5~10개 삼중항이 나온다. 양도 모자라는 편은 아니다.

---

## 축으로 바로 못 쓰는 부분

객관식 보기는 **같은 답이 여러 장에서 반복**되어야 한다. 지금은 반대다.

![반복](../figures_pse/10_slot_repeat.png)

| 슬롯 | 특허에 이 칸이 있음 | 서로 다른 문자열 | 한 번만 나온 비율 | 8단어 이상 |
|---|---:|---:|---:|---:|
| problem | 99.9% | 1,515 / 1,564 | **98.9%** | 32% |
| structure | 100% | 3,246 / 4,027 | 92.1% | **2%** (짧다) |
| how it runs | 100% | 2,574 / 2,872 | **97.7%** | 16% |
| effect | 99.9% | 2,212 / 2,645 | 93.2% | 13% |

거의 매 특허마다 다른 문장을 칸에 넣는다. 투표함을 열면 표가 1,000장이고 답이 1,000가지인 셈이다.

더 큰 문제는 **LLM이 넣은 빈칸 문구**다.

![상위 답](../figures_pse/10_slot_top_terms.png)

반복 1위가 기술 선택이 아니라 템플릿인 칸이 있다.

| 슬롯 | 가장 많이 나온 말 | 특허 수 | 성격 |
|---|---|---:|---|
| how it runs | `core operation logic` | **188** | 빈칸. “어떻게 도나”를 안 적은 것 |
| problem | `core problem concept` | 26 | 빈칸 |
| effect | `primary benefit` | 32 | 빈칸 |
| structure | `key component 1`, `key component 2` | 28, 29 | 빈칸 |

structure 쪽에는 그래도 **쓸 만한 반복**이 있다.

- `central server` 61, `server` 34, `processor` 33
- `edge servers` 24, `cloud server` 21, `edge devices` 17, `edge computing nodes` 16

위치 축 후보(device / edge / cloud / central server)는 이 칸에서 **이미 보인다.** 다만 `server`와 `central server`와 `cloud server`를 사람이 같은 보기·다른 보기로 나눠야 한다.

effect도 동의어를 합치면 축 후보가 된다.

- `reduced latency` 21
- `reduced energy consumption` 12
- `improved privacy protection` 10
- `reduced communication overhead` 9

problem / how it runs 는 지금 문자열 그대로는 축이 되기 어렵다. 긴 문장이거나 (`32%`가 8단어 이상), 빈칸 문구다.

전역 엔티티 클러스터(130개)로 접어도, 한 덩어리에 서로 다른 문제가 섞인다. 이번 검토에서는 **클러스터 ID를 수준으로 쓰지 않는 쪽**이 맞다.

---

## 그래서 축은 어떻게 잠그나 (이 결과 기준)

지금 1,412건만으로 **바로 8칸 EM**을 돌리기보다:

1. **structure**에서 빈칸(`key component 1/2`)을 버리고, 서버·엣지·클라우드·디바이스를 보기 3~4개로 합친다.  
   → 축 후보: **처리는 어디서 하나.**
2. **effect**에서 latency / energy / privacy / communication 을 보기 몇 개로 합친다.  
   → 축 후보: **무엇을 줄이려 하나.** (한 특허가 여러 효과를 말할 수 있음)
3. **how it runs**는 `core operation logic`을 제외하고, `federated learning`, `encryption` 같은 짧은 답만 남긴다. 답이 너무 갈리면 이번엔 축에서 뺀다.
4. **problem**은 점유용 메모로 두고, 보기 축으로는 아직 안 쓴다.

이것이 “표를 보고 사람이 문항 3개를 고른다”의 이번 판 답이다. structure는 문항이 되고, 나머지는 프롬프트를 고치거나 동의어 표를 만든 뒤에야 문항이 된다.

---

## 5만 건 LLM에 넘기기 전에 고칠 것

형식은 유지해도 된다. 바꿀 것은 **목적어를 짧게, 빈칸 금지**다.

프롬프트에 넣으면 좋은 금지 예:

- `core problem concept`, `core operation logic`, `primary benefit`
- `key component 1`, `key component 2`, `main technology entity`

structure / location 은 가능하면 짧은 태그:

`on-device` / `edge` / `cloud` / `central-server` / `unknown`

effect 도 짧은 태그:

`latency` / `energy` / `privacy` / `bandwidth` / `cost` / `accuracy` / `other`

지금처럼 긴 문장을 엔티티로 넣으면, 5만 건이 되어도 hapax는 그대로다. 그래프는 “가득 찬 에세이”가 되고 시나리오 칸은 안 생긴다.

---

## 파일

| 경로 | 내용 |
|---|---|
| `out_pse/10_manifest.json` | 건수, 빈 그래프 여부 |
| `out_pse/10_slot_summary.csv` | 슬롯별 반복·길이 |
| `out_pse/10_slot_top.csv` | 상위 문자열·클러스터 |
| `out_pse/10_patent_slots.csv` | 특허마다 칸이 몇 개인지 |
| `out_pse/10_objects.csv` | 트리플 전수 (감사) |
| `figures_pse/*.png` | 위 그림 |
