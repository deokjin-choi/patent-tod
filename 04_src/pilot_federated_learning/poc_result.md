# POC 결과 (3–4단)

제목+초록만 사용. n=4,467. 축 이름은 그림과 같게 영어 (`aggregation`, `location`, `privacy` …).  
숫자는 **모든 연도를 한 번에** 센 것. 시간창은 아직 아님.

---

## 1단계. 데이터는 쓸 만한가

**한 일:** FL 특허 4,467건의 날짜·결측만 봄.

**나온 것:** 초록 없음 11건, 날짜·CPC 없음 0. 우선권은 2019부터 늘고 **2022가 봉우리**.

![priority year](out/figures/01_priority_year.png)

**의미:** 코퍼스는 깨지지 않았다. 이후 표가 이상하면 데이터가 아니라 매핑 규칙 쪽을 보면 된다.

---

## 2단계. 축이 초록에 보이는가

**한 일:** 특허마다 네 축에 값을 붙이거나 `unknown`.

| 축 | 질문 | 값 |
|---|---|---|
| partition | 데이터를 어떻게 나누나 | horizontal / vertical |
| aggregation | 모델을 누가 합치나 | central / hierarchical / decentralized |
| privacy | 뭘로 숨기나 | dp / crypto / tee |
| location | 학습이 어디서 도나 | device / edge / cloud |

**나온 것:** 값이 붙는 비율이 축마다 크게 다르다.

![axis known vs unknown](out/figures/02_axis_known.png)

파랑 = 값이 있음. 회색 = 모름.

- location 19% · aggregation 14% · privacy 11% · **partition 2%**

**의미:** 초록은 “어디서 / 누가 합치나 / 어떻게 숨기나”는 가끔 적고, **수평/수직 분할은 거의 안 적는다.** 모름이 많은 것은 실패가 아니다.

특허 하나가 축을 몇 개나 채우나:

![how many axes filled](out/figures/03_n_known.png)

- 0개 60% · 1개 33% · 2개 7% · 3개 13건 · **4개 0건**

**의미:** 네 선택을 한 칸으로 닫는 표는 지금은 못 만든다. 볼 것은 **한 축**과 **두 축 짝**이다.

값이 있을 때만, 무엇이 붙나 (`unknown` 제외):

![level mix](out/figures/04_level_mix.png)

**의미:** 칸마다 분모가 다르다. 막대 높이를 칸끼리 비교하면 안 된다.  
같은 칸 안에서는: aggregation은 central이 많고, privacy는 dp≈crypto, tee는 적고, location은 edge가 제일 많다.

---

## 3단계. 어떤 조합이 많이 나오나 (점유)

**한 일:** 두 축이 **둘 다 값이 있는 행만** 세서 칸에 앉힌다. 아직 “빈 칸 = 기회”라고 읽지 않음.

![pair occupancy](out/figures/05_pair_heatmaps.png)

| 짝 | 둘 다 앎 | 칸 |
|---|---:|---|
| aggregation × location | 146 | 9칸 전부 참 |
| aggregation × privacy | 90 | 9칸 전부 참 |
| privacy × location | 74 | 9칸 전부 참 |

진한 칸: `central + edge` (39), `central + dp` (44).

**의미:** 값이 잘 붙는 세 짝에서는 **빈 칸이 없다.** 4단에서 할 일은 0칸을 모순/gap으로 가르는 게 아니라, **드믄 칸**을 찾는 것이다.

partition이 들어간 짝:

![partition pairs](out/figures/06_partition_heatmaps.png)

둘 다 아는 행이 4~14건뿐. 여기 0은 “같이 못 쓴다”가 아니라 **초록이 수평/수직을 안 적어서 표본이 없다.**

**의미:** 4단에서는 partition을 빼고, aggregation · privacy · location만 쓴다.

---

## 4단계. 숫자로 의심 칸 표시 (아직 읽기 전)

**한 일:** 위 세 짝(27칸)에서 횟수와 lift를 셈.

lift = 실제 횟수 ÷ (각 level 빈도로 기대하는 횟수).  
모집단은 그 짝에서 둘 다 값이 있는 행 (146 / 90 / 74).  
lift=1 이면 “각자 나온 만큼 우연히 겹친 양”.  
횟수 1~2 이거나 lift < 0.5 이면 빨간 칸. **칸은 지우지 않음.**

![suspect cells](out/figures/07_step4_suspects.png)

위 줄 = 횟수, 아래 줄 = lift. 빨간 테두리 + `*` = 의심 6칸.

| 칸 | 횟수 | lift | 숫자상 이유 |
|---|---:|---:|---|
| hierarchical + device | 5 | 0.41 | 기대(~12건)보다 적음 |
| central + tee | 2 | 0.54 | 횟수 적음 |
| hierarchical + tee | 1 | 1.39 | 횟수 적음 |
| decentralized + tee | 2 | 3.60 | 횟수 적음 (같이 붙는 편) |
| tee + device | 1 | 1.23 | 횟수 적음 |
| tee + edge | 1 | 0.51 | 횟수 적음 |

**의미:** TEE 칸이 1~2인 주된 이유는 그 표에서 `privacy=tee`가 5건뿐이라서다. 짝이 금지여서가 아니다. `decentralized+tee`는 적은데 lift가 높아, “나오면 그 짝으로 쓴다”에 가깝다.

---

## 5단계. 빨간 칸 특허를 읽으면

제목·초록을 건별로 봤다. 판은 세 가지: **코딩 오류** / **실제 사용** / **거의 빈 가능 칸**.

문서 수 ≠ 발명 수일 수 있다 (같은 우선권, 거의 같은 초록).

### hierarchical + device (5문서)

숫자상 가장 의미 있는 칸 (lift 0.41). 읽으면 대부분 매핑 실수.

| 문헌 | 우선권 | 판 | 실제로 |
|---|---|---|---|
| CN 116567824 A | 2023-05 | 코딩 오류 | hierarchical **edge** network. user equipment 때문에 location=device |
| CN 118018178 A | 2023-10 | 코딩 오류 | UE → satellite/edge → central. device가 문장 앞에 먼저 붙음 |
| CN 120196640 A | 2025-03 | 코딩 오류 | hierarchical **knowledge distillation**. aggregation 토폴로지 아님 |
| WO 2023/093238 A1 | 2021-11 | 실제에 가까움 (1세트) | RAN hierarchical FL. 배포는 **UE 또는 base station** |
| WO 2023/093235 A1 | 2021-11 | 위와 같은 날 | 같은 계열, 같은 구조 |

**의미:** 모순이 아니다. 오류 3건을 빼면 발명 1개만 남는다. 그 1건은 “안 씀”이 아니라 UE를 선택지로 연 예다. 지금은 **가능 칸이 거의 비어 있다** 정도. gap인지는 시간창이 필요.

### 나머지 5칸 (TEE) — 문헌 6건, 발명은 더 적음

| 칸 | 문헌 | 우선권 | 판 | 실제로 |
|---|---|---|---|---|
| central + tee | CN 120146158 A | 2025-05 | **실제 사용** | client TEE + 암호 → central server |
| central + tee | CN 119248878 A | 2024-09 | **실제 사용** | 참가자 TEE + central aggregator |
| decentralized + tee | US 2022/0374763 A1 | 2021-05 | **실제 사용** | 집계를 여러 TEE로 나눔 |
| decentralized + tee | WO 2022/243871 A1 | 2021-05 | 같은 발명 | 위와 초록이 같음 |
| hierarchical + tee, tee + edge | CN 120342739 A | 2025-05 | 오류 / 약함 | hierarchical는 보호 계층. edge cluster는 맞음. TEE는 한 줄 |
| tee + device | WO 2021/051629 A1 | 2019-09 | 코딩 오류 | TEE는 coordinator(집계 쪽). device는 participating UE |

**의미:** TEE 빨간 칸의 핵심은 gap이 아니다. `central+tee`와 `decentralized+tee`는 그 짝을 진짜로 쓴다. 적은 것은 TEE 표본이 작아서. `hierarchical+tee`와 `tee+device`는 매핑이 만든 칸에 가깝다.

---

## 지금 말할 수 있는 것

1. 초록 grain에서는 4차원 칸이 안 닫힌다. 본편은 짝 표다.
2. 값이 있는 세 짝은 칸이 다 차 있어서, 빈 칸을 모순/gap으로 가르는 그림이 안 나온다.
3. 의심 6칸은 “지우라는 표시”가 아니라 “읽으라는 표시”였다.
4. 읽은 뒤: **실제 사용** = `central+tee`, `decentralized+tee`. **거의 빈 가능 칸 후보** = `hierarchical+device`. 나머지는 코딩 오류.
5. 시간창으로 볼 후보는 `hierarchical+device` 쪽이다.
