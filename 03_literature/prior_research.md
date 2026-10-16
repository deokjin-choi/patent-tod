## 연구의 목적

특허만으로 기술 지도를 만든다. 단위는 항목 × 선택지 = 칸이다. 빈 칸에는 아직 안 한 조합(기회 후보)과 같이 쓸 수 없는 조합(비어 있는 것이 정상)이 섞여 있고, 이 연구는 그 둘을 나눈다. 결과는 다시 그릴 수 있는 지도와 맞았다는 숫자이다.

## 검증할 세 가지

1. **칸을 만들 수 있는가.** 특허에서 항목·선택지를 뽑아 점유 칸과 빈 칸을 나누되, 빈 칸을 곧바로 기회로 읽지 않는다.
2. **같이 쓸 수 없는 조합을 지울 수 있는가.** 성립하지 않는 쌍을 빼 가능 공간만 남긴다. 규칙은 특허 증거로 다시 확인할 수 있어야 한다.
3. **쓸모를 숫자로 보일 수 있는가.** 제약을 넣은 지도가 덜 헷갈리는가. 과거 특허만으로 그린 지도에서, 가능한 칸은 나중에 채워지고 불가능한 칸은 비어 있는가.

## 선행연구 마인드맵: CREATE · CONSTRAIN · VALIDATE

선행연구는 세 축으로 이루어진다. 각 축을 가르는 **핵심은 "기회영역을 무엇으로 보느냐"** — 즉 다루는 **기본 단위**와, 그 단위에서 '빈 곳'이 뜻하는 바이다. 방법 이름(형태분석·토픽모델·SAO·링크예측 …)은 그다음 문제다. 예컨대 SAO 기반 연구라도 그 결과가 형태표로 매핑되면 **셀(조합) 계열의 변종**이고, 삼항 관계를 예측하면 **노드-엣지 계열**이다.

### 핵심 한눈 — 기회영역의 의미

| 축 | 기본 단위 | 기회영역(빈 곳)의 의미 | 묻는 것 |
|---|---|---|---|
| **CREATE** | 셀(조합) / 영역(위치) / 노드-엣지(관계) | 아직 없는 조합 · 저밀도 공백 · 미연결 링크 | 어디가 아직 안 채워졌나 |
| **CONSTRAIN** | 선택지 쌍 / 조합 집합 | 양립 불가라 지워야 할 곳 · 남길 대표 | 무엇이 불가능하거나 중복인가 (전문가 규칙 vs 데이터) |
| **VALIDATE** | 시나리오 묶음 / 과거–미래 창 | 품질이 낮은 곳 · 나중에 틀린 곳 | 쓸 만한가(현재 품질), 맞았나(특허로 사후 검증) |

대부분 논문은 세 축을 조금씩 걸치지만, 아래 트리는 각 논문을 **가장 특징적인 한 곳**에만 둔다. 가지마다 대표 논문 제목·저널·연도를 붙였고, 필수·옵션을 가리지 않고 방법이 MECE하게 드러나도록 모았다.

**저널 약어.** TFSC = Technological Forecasting & Social Change · ESWA = Expert Systems with Applications · TASM = Technology Analysis & Strategic Management · R&D Mgmt = R&D Management · Manag. Sci. = Management Science · J. R. Soc. Interface = Journal of the Royal Society Interface · J. Informetrics = Journal of Informetrics · IEEE TEM = IEEE Transactions on Engineering Management · IP&M = Information Processing & Management · Environ. Res. Lett. = Environmental Research Letters · JORS = Journal of the Operational Research Society · EJOR = European Journal of Operational Research · EM&S = Environmental Modelling & Software · Futures & Foresight Sci. = Futures & Foresight Science · IJFIP = International Journal of Foresight and Innovation Policy · Eur. J. Futures Res. = European Journal of Futures Research · (Scientometrics · Technovation · Futures · Sustainability · Nature · Science · Patterns · foresight · Climatic Change · World Futures Review · Service Business · NeurIPS 은 그대로).

```
CREATE — 기회 공간을 생성한다   (기본 단위 = 기회영역의 모양)
│
├─[단위: 셀/조합]  Cell — 항목×선택지 격자. 빈 곳 = 아직 없는 조합
│   ├── 이론 근거 — 발명 = 요소의 재조합
│   │     · Recombinant Uncertainty in Technological Search — Manag. Sci., 2001
│   │     · Atypical Combinations and Scientific Impact — Science, 2013
│   │     · Invention as a combinatorial process: evidence from US patents — J. R. Soc. Interface, 2015
│   ├── 키워드 형태분석 — 특허 키워드로 형태표를 짠다
│   │     · A systematic approach for identifying technology opportunities: Keyword-based morphology analysis — TFSC, 2005
│   │     · Morphology analysis for technology roadmapping: application of text mining — R&D Mgmt, 2007
│   │     · On the development of a technology intelligence tool for identifying technology opportunity — ESWA, 2007
│   │     · Exploring technological opportunities by linking technology and products: Application of morphology analysis and text mining — TFSC, 2014
│   │     · Developing new smart services using integrated morphological analysis: integration of the market-pull and technology-push approach — Service Business, 2015
│   │     · A technology opportunities analysis model: applied to dye-sensitised solar cells for China — TASM, 2013
│   │     · Discovering Technology Opportunity by Keyword-Based Patent Analysis: A Hybrid Approach of Morphology Analysis and USIT — Sustainability, 2019
│   ├── SAO·기능 기반 형태분석 — 문장요소(주어-동작-대상)를 셀로 (형태분석의 변종)
│   │     · An SAO-based text mining approach to building a technology tree for technology planning — ESWA, 2012
│   │     · An SAO-based text-mining approach for technology roadmapping using patent information — R&D Mgmt, 2012
│   │     · Technology opportunity discovery (TOD) from existing technologies and products: A function-based TOD framework — TFSC, 2015
│   │     · Subject–action–object-based morphology analysis for determining the direction of technological change — TFSC, 2016
│   │     · Combining SAO semantic analysis and morphology analysis to identify technology opportunities — Scientometrics, 2017
│   └── 분류코드 조합 — IPC/CPC 코드 조합을 셀로
│         · A novel approach to forecast promising technology through patent analysis — TFSC, 2016
│
├─[단위: 영역/위치]  Region — 저차원 투영공간의 좌표/격자. 빈 곳 = 저밀도 공백(vacuum)
│   ├── 2D 키워드 지도 공백
│   │     · An approach to discovering new technology opportunities: Keyword-based patent map approach — Technovation, 2009
│   ├── 생성지형도(GTM) 잠재공간 공백
│   │     · Development of a GTM-based patent map for identifying patent vacuums — ESWA, 2012
│   │     · Technology opportunity discovery of proton exchange membrane fuel cells based on generative topographic mapping — TFSC, 2021
│   └── 이상치·신규성 — 분포에서 벗어난 위치를 기회로
│         · Identifying technological opportunities using the novelty detection technique: a case of laser technology in semiconductor manufacturing — TASM, 2013
│         · Novelty-focused patent mapping for technology opportunity analysis — TFSC, 2014
│         · Identifying technology opportunity using SAO semantic mining and outlier detection method: A case of triboelectric nanogenerator technology — TFSC, 2023
│
└─[단위: 노드-엣지]  Node–Edge — 기술요소 노드와 관계. 빈 곳 = 아직 없는 링크
    ├── 관계 그물(semantic network) — 요소 쌍의 관계를 그물로 두고 거리·링크로 읽는다
    │     · TechNet: Technology semantic network based on patent data — ESWA, 2019   ← "pairwise relevance"
    │     · A text-embedding-based approach to measuring patent-to-patent technological similarity — TFSC, 2022   ← "patent universe as a network"
    │     · Unsupervised word embeddings capture latent knowledge from materials science literature — Nature, 2019   ← 잠재 '관계' 복원
    ├── 링크 예측으로 빈 칸·기회 추정 (한 분야 안)
    │     · Translating Embeddings for Modeling Multi-relational Data (TransE) — NeurIPS, 2013   [관계 임베딩 부품]
    │     · Two-stage technology opportunity discovery for firm-level decision making: GCN-based link-prediction approach — TFSC, 2022
    │     · Technology opportunity analysis using hierarchical semantic networks and dual link prediction — Technovation, 2023
    │     · Technology opportunity prediction based on SAO representation learning — Scientometrics, 2026
    └── 분야–분야 융합(엣지) 예측
          · Patent indicators for monitoring convergence – examples from NFF and ICT — TFSC, 2010
          · Predicting the pattern of technology convergence using big-data technology on large-scale triadic patents — TFSC, 2015
          · Anticipating technological convergence: Link prediction using Wikipedia hyperlinks — Technovation, 2018
          · Technological opportunity discovery for technological convergence based on the prediction of technology knowledge flow in a citation network — J. Informetrics, 2018
          · Machine-learning-based deep semantic analysis approach for forecasting new technology convergence — TFSC, 2020
          · (최근 GNN·다층·시공간)
              · Identification of Sustainable Convergence Technology for Batteries via Multiplex Link Prediction — IEEE TEM, 2024
              · Technology convergence prediction based on temporal heterogeneous graph neural networks — IP&M, 2024
              · Prediction of Technology Convergence on the Basis of Supernetwork — IEEE TEM, 2024
              · Forecasting technology convergence with the spatiotemporal link prediction model — Technovation, 2025
```

> **표현 substrate (세 단위 공통).** 임베딩·텍스트매칭은 그 자체가 '단위'가 아니라, 셀/영역/노드-엣지를 만들기 위한 **표현 도구**다. 벡터로 바꾼 뒤 **(a) 저차원 좌표로 투영해 밀도·공백을 보면 영역(Region)**, **(b) 쌍 유사도·링크로 읽으면 노드-엣지(Node–Edge)**가 된다. 즉 '벡터 공간의 가깝다'가 곧 기회영역이 아니라, *무엇을 읽어내느냐*(좌표의 공백 vs 쌍의 미연결)가 단위를 정한다. 그래서 같은 임베딩이라도 GTM 2D 투영이면 Region(`son2012`·`teng2021`), 최근접-이웃 그물이면 Node–Edge(`TechNet`·`hain2022`)로 갈린다. 대표 부품: Sentence-BERT (2019) · PatentSBERTa (2024) · Text matching to measure patent similarity (2017).

```
CONSTRAIN — 가능하지 않은 후보를 지운다   (무엇을, 그리고 '무엇으로' 지우느냐)
│
├─[입력: 전문가 규칙/점수]  양립성 제약 — 사람이 쌍의 양립성·영향을 매겨 컷한다
│   ├── 교차영향 점수 (cross-impact) — 쌍마다 영향 점수 → 동시 만족 조합만 남김
│   │     · Cross-impact balances: A system-theoretical approach to cross-impact analysis — TFSC, 2005
│   │     · Improving environmental change research with systematic techniques for qualitative scenarios (CIB on SRES) — Environ. Res. Lett., 2012
│   └── 교차일관성 쌍 제거 (cross-consistency) — 논리·현실상 모순 쌍 삭제
│         · Problem structuring using computer-aided morphological analysis — JORS, 2006
│         · Modeling Alternative Futures with General Morphological Analysis — World Futures Review, 2011
│         · Scenario modelling with morphological analysis (CCA: 내부+외부 일관성) — TFSC, 2017
│
├─[입력: 데이터]  데이터로 "이 조합은 어렵다"를 추정 — 특허/문헌에서 가능성을 읽어 컷
│   ├── 실현가능성 점수 (지표·인용으로 조합을 채점해 낮은 것을 거름)
│   │     · Development of New Technology Forecasting Algorithm: Hybrid Approach for Morphology Analysis and Conjoint Analysis of Patent Information — IEEE TEM, 2007
│   │     · Subject–action–object-based morphology analysis for determining the direction of technological change (8개 지표) — TFSC, 2016
│   │     · Combining SAO semantic analysis and morphology analysis to identify technology opportunities (feasibility score) — Scientometrics, 2017
│   └── 연관규칙·역량 기반 거르기 (공출현 패턴으로 가능/불가·대다수 제거)
│         · Product opportunity identification based on internal capabilities using text mining and association rule mining — TFSC, 2016
│         · Predicting the pattern of technology convergence using big-data technology on large-scale triadic patents (Association Rule, 대다수 제거) — TFSC, 2015
│
└─[공간 축소]  대표·다양성 선택 — 가능 공간이 클 때 대표만 남긴다
      · Identification of a small reliable and efficient set of consistent scenarios — EJOR, 2003
      · Thinking inside the box: A participatory, computer-assisted approach to scenario discovery — TFSC, 2009
      · Choosing diverse sets of plausible scenarios in multidimensional exploratory futures techniques — Futures, 2015
      · Choosing small sets of policy-relevant scenarios by combining vulnerability and diversity approaches — EM&S, 2016
```

> **CONSTRAIN의 실제 지형 (주의).** 제약을 거는 '입력'은 둘로 갈린다. 전통적인 양립성 제약(CIB·CCA)은 **전문가가** 쌍 규칙·점수를 넣는다. 데이터 기반 쪽은 특허에서 **실현가능성 점수**(SAO 지표·인용)나 **연관규칙**(공출현)으로 조합을 거르지만, 이들은 대부분 *soft* — 즉 '순위를 매겨 낮은 것을 뺀다'이지, "공출현이 한 번도 없으니 **금지**"라는 *hard* 제약을 특허 증거만으로 세운 연구는 사실상 없다. 이 'hard 제약을 특허로 추정'하는 자리가 이 프로젝트가 메우는 CONSTRAIN의 핵심 빈틈이다 (본문 2항 "입력이 특허인 경우는 거의 없다"와 같은 지적).

```
VALIDATE — 만들어진 공간을 평가한다   (언제·무엇으로 재느냐)
│
├─[현재 시점]  묶음의 품질 — 다 담았나 / 안 몰렸나 / 다른가 / 그럴듯한가   (대부분 시나리오 플래닝 계열)
│   ├── 유형·기법 지도 (평가 범위를 먼저 고정)
│   │     · An updated scenario typology — Futures, 2003
│   │     · Scenario types and techniques: Towards a user's guide — Futures, 2006
│   │     · The current state of scenario development: an overview of techniques — foresight, 2007
│   │     · Defining scenario — Futures & Foresight Sci., 2018
│   ├── 품질 기준 (관련성·일관성·개연성·추적성)
│   │     · Scenario building: Uses and abuses — TFSC, 2010
│   │     · Plausibility indications in future scenarios — IJFIP, 2013
│   │     · New outlooks in traceability and consistency of integrated scenarios — Eur. J. Futures Res., 2015
│   │     · The Scenario Quality Assessment Method: A New Technique for Verifying the Quality of Scenarios — Futures & Foresight Sci., 2024
│   │     · Does the intuitive logics method – and its recent enhancements – produce "effective" scenarios? — TFSC, 2012
│   └── 포괄성·다양성·불확실성 폭
│         · A review of scenario planning — Futures, 2012
│         · Reinvigorating the scenario technique to expand uncertainty consideration — Climatic Change, 2016
│         · Scenario techniques for energy and environmental research: An overview of recent developments to broaden the capacity to deal with complexity and uncertainty — EM&S, 2017
│
└─[미래 시점]  나중에 맞았나 — 과거 창의 지도를 이후 자료로 채점
    ├── 사후 채점의 원칙 (옛 예측 평가 + 미래정보 누수 금지)
    │     · What can past technology forecasts tell us about the future? — TFSC, 2002
    │     · An examination of factors affecting accuracy in technology forecasts — TFSC, 2012
    │     · Long-term forecasts of military technologies for a 20–30 year horizon: An empirical assessment of accuracy — TFSC, 2018
    │     · Leakage and the reproducibility crisis in machine-learning-based science — Patterns, 2023   [누수 경고]
    │     · Linking generative AI and morphological analysis to conduct foresight evaluation — foresight, 2026
    │
    ├── ★특허로 검증★ — 과거 특허로 만든 예측을 '이후 특허'로 채점 (이 프로젝트와 가장 가까운 선례)
    │   ├── 예측한 조합/셀이 이후 특허에 나타났나
    │   │     · Subject–action–object-based morphology analysis for determining the direction of technological change (예측 상위 조합이 2012–2014 특허에 실제 출현) — TFSC, 2016
    │   │     · Exploring technology opportunities by visualizing patent information based on generative topographic mapping and link prediction (예측 칸 vs 실제 개발 칸 비교) — TFSC, 2018
    │   ├── 예측한 군집/분류가 이후에 형성됐나 (미래정보 미사용)
    │   │     · Prediction of emerging technologies based on analysis of the US patent citation network (1991년까지 데이터 군집 ⊂ 1997 신설 class) — Scientometrics, 2012
    │   │     · The Emerging Clusters Model: A tool for identifying emerging technologies across multiple patent systems (전향 정보 없이 탐지) — Research Policy, 2014
    │   └── 예측한 유망/신흥 특허가 이후에 인용·실현됐나
    │         · Early identification of emerging technologies: A machine learning approach using multiple patent indicators — TFSC, 2017
    │         · Forecasting future bigrams and promising patents: introducing text-based link prediction (유망 특허가 유의하게 더 인용됨) — foresight, 2022
    │         · A novel approach to forecast promising technology through patent analysis — TFSC, 2016
    │
    └── [대상이 '칸'이 아닌 이웃] 신흥·수명·진보를 채점 (사후 검증 습관은 같되 대상이 다름)
          · What is an emerging technology? — Research Policy, 2015
          · Stochastic technology life cycle analysis using multiple patent indicators — TFSC, 2016
          · Emergence scoring to identify frontier R&D topics and key players — TFSC, 2018
          · Identification of promising inventions considering the quality of knowledge accumulation: a machine learning approach — Scientometrics, 2020
          · Forecasting emerging technologies: Use of bibliometrics and patent analysis — TFSC, 2006
          · How predictable is technological progress? — Research Policy, 2016
```

> 읽는 법. **CREATE**는 기본 단위로 갈린다 — 셀(조합: 형태분석·SAO·분류코드), 영역(위치: 2D지도·GTM·이상치), 노드-엣지(관계: 의미망·링크예측·융합). 세 계열은 "빈 곳"을 각각 *아직 없는 조합 / 저밀도 공백 / 미연결 링크*로 달리 읽는다. 영역과 노드-엣지는 둘 다 벡터 임베딩을 쓸 수 있어 헷갈리기 쉬운데, 가르는 기준은 '벡터가 있느냐'가 아니라 **읽어내는 대상**이다 — *좌표의 공백*을 보면 영역, *쌍의 미연결 링크*를 보면 노드-엣지다(위 「표현 substrate」 주 참조). **CONSTRAIN**은 '무엇으로' 지우느냐로 갈린다 — 전문가 규칙(CIB·CCA), 데이터 기반 추정(실현가능성 점수·연관규칙), 공간 축소(대표·다양성). 다만 데이터 기반은 대개 soft(점수·순위)이고, 특허 공출현만으로 hard 금지를 세운 예는 드물다. **VALIDATE**는 시점으로 갈린다 — 현재의 묶음 품질(대부분 시나리오 플래닝 계열), 미래의 사후 적중. 미래 쪽은 다시 ① 사후 채점 원칙(+누수 금지), ② **★특허로 검증★**(과거 특허로 만든 예측을 이후 특허로 채점 — 조합/셀·군집/분류·유망특허 세 갈래), ③ 대상이 '칸'이 아닌 이웃(신흥·수명·진보)으로 나뉜다. 특허 기반 사후 검증 선례는 ②에 분명히 있으나, 그 대상은 '예측 조합의 출현·군집·유망특허'이지 **가능/불가능 칸의 사후 점유**는 아니다 — 바로 거기가 비어 있다. 이 프로젝트는 세 축을 **같은 특허·같은 규칙으로 한 번에** 잇되, CREATE에서는 셀을 단위로 삼고, CONSTRAIN의 입력을 특허로 두며, VALIDATE에서는 '가능 칸이 이후 특허로 채워지고 불가능 칸이 비어 있는지'를 채점한다 (문서 끝 「그래서 이 연구가 메우는 자리」 참조).

## 선행연구가 필요한 이유

세 줄기는 이미 있으나 서로 떨어져 있다. 특허로 칸을 만드는 연구는 불가능을 지우지 않고, 불가능을 지우는 연구는 규칙을 전문가가 넣으며, 품질을 말하는 연구는 이야기·성장 곡선·유망 특허를 대상으로 한다. 같은 특허와 같은 규칙으로 셋을 한 번에 하는 자리가 비어 있다.

**필수**는 세 검증이 물려받는 절차·정의·결과이다. **옵션**은 추출 도구나 옆 질문과의 경계이며, 없어도 세 질문은 남는다.

## 1. 칸을 어떻게 만들고, 빈 칸을 왜 기회로 읽어 왔는가

이 항목은 지도의 단위를 고정한다. 칸은 항목과 선택지를 하나씩 고른 조합이다. 특허가 그 칸에 있으면 점유이고, 없으면 빈 칸이다. 앞선 연구들은 그 빈 칸을 기술 기회로 읽었다.

이 연구가 확인하는 것은 두 가지이다. 왜 기술을 조합의 칸으로 보는가. 특허에서 그 칸을 만들고 빈 칸을 기회로 읽어 온 절차가 어디까지이며, 어디가 비어 있는가.

### 1-1. 칸을 만드는 이유

칸을 만드는 이유는 빈 자리가 있어 보여서가 아니다. 발명 자체가 기존 요소의 조합이라는 연구가 있다. 새 조합은 가치 있을 수 있다. 그 말이 모든 새 조합이 기술적으로 가능하다는 뜻은 아니다. 가능한 조합과 불가능한 조합을 나누는 절차는 2항이다.

| 연도 | 저널 | 제목 | 핵심 내용 | 이 연구에서의 위치 | 원문 |
|---:|---|---|---|---|---|
| 2001 | Management Science | Recombinant Uncertainty in Technological Search | 발명의 기술적 불확실성을, 발명가가 익숙하지 않은 부품과 부품 조합을 탐색하는 과정에서 나온다고 정의하고, 새 조합은 평균적으로 덜 유용하지만 성과의 흩어짐이 큼을 특허 인용으로 보인다. | 기술 기회를 조합으로 보는 이론적 이유다. 조합이 가능하다고 자주 쓰인다는 뜻은 아니다. | [원문](https://doi.org/10.1287/mnsc.47.1.117.10671) |
| 2013 | Science | Atypical Combinations and Scientific Impact | 1,790만 편 논문에서 참고문헌 저널 쌍의 흔함과 낯섦을 계산해, 영향력이 큰 논문은 흔한 조합 위에 소수의 낯선 조합을 더한 형태임을 보인다. | 새 조합이 가치 있을 수 있다는 근거다. 모든 낯선 조합이 가능한 것은 아니다. 그 구분이 이 연구다. | [원문](https://doi.org/10.1126/science.1240474) |
| 2015 | Journal of the Royal Society Interface | Invention as a combinatorial process: evidence from US patents | 1790–2010년 미국 특허의 기술 코드 조합을 집계해, 발명은 기존 코드의 재결합이며 새 조합의 공간은 사실상 무한하지만 대부분의 발명은 익숙한 조합임을 보인다. | 조합이 비유가 아니라 특허에서 관측된다는 근거다. | [원문](https://doi.org/10.1098/rsif.2015.0272) |

### 1-2. 특허로 형태표를 만들고, 없는 칸을 기회로 읽은 연구

이 연구의 비교 대상이다.

하는 일은 이렇다. 공개 문헌과 특허에서 기술 기회를 본다. 그중 형태분석은 특허에서 반복되는 말을 모아 항목과 선택지를 만들고, 각 특허를 하나의 조합에 대응시킨다. 특허가 있는 조합과 없는 조합을 나눈 뒤, 없는 조합을 기술 기회로 정의한다.

한계는 분명하다. 없는 자리에는 아직 안 한 조합과 같이 쓸 수 없는 조합이 같이 들어 있다. 이 연구들은 그 둘을 규칙으로 나누지 않는다. 지도가 나중에 맞았는지도 거의 확인하지 않는다.

| 연도 | 저널 | 제목 | 핵심 내용 | 이 연구에서의 위치 | 원문 |
|---:|---|---|---|---|---|
| 1995 | Technological Forecasting and Social Change | Technology opportunities analysis | 공개 논문·특허 데이터베이스를 계량해 신기술 활동 프로파일을 만드는 절차를 제시함으로써, 기술 기회의 입력을 전문가 의견이 아니라 공개 문헌으로 둔다. | 특허로 기술 기회를 보자는 출발점이다. 조합의 칸은 아직 없다. | [원문](https://doi.org/10.1016/0040-1625(95)00022-3) |
| 2005 | Technological Forecasting and Social Change | A systematic approach for identifying technology opportunities: Keyword-based morphology analysis | 특허 키워드를 요인분석해 형태표(항목×선택지)를 만들고, 특허가 있는 조합과 없는 조합을 나눈 뒤 없는 조합을 기술 기회로 정의한다. | 이 연구의 직접 비교 대상이다. 칸은 같으나, 같이 쓸 수 없는 조합을 지우지 않는다. | [원문](https://doi.org/10.1016/j.techfore.2004.08.011) |
| 2007 | IEEE Transactions on Engineering Management | Development of New Technology Forecasting Algorithm: Hybrid Approach for Morphology Analysis and Conjoint Analysis of Patent Information | 키워드 형태표에서 만든 새 조합에 컨조인트 분석으로 우선순위를 주고, 특허 인용으로 기술적 실현 가능성을 따로 매겨 기회 후보를 고른다. | 빈 칸에 점수를 주는 선례다. 점수가 높아도 기술적으로 불가능한 칸일 수 있다. | [원문](https://doi.org/10.1109/tem.2007.900796) |
| 2007 | R&D Management | Morphology analysis for technology roadmapping: application of text mining | 특허와 제품 문서에서 형태를 뽑아 제품 형태와 기술 형태를 맞추고, 그 조합으로 기술 로드맵의 새 제품·기술 구성을 채운다. | 형태표를 계획 문서에 쓰는 선례다. 표가 맞았는지는 나중에 확인하지 않는다. | [원문](https://doi.org/10.1111/j.1467-9310.2007.00493.x) |
| 2007 | Expert Systems with Applications | On the development of a technology intelligence tool for identifying technology opportunity | 형태분석으로 대안을 만들고 컨조인트 분석으로 순위를 매기는 절차를 소프트웨어로 고정해, 기회 후보를 빈 조합으로 출력한다. | 같은 일을 도구로 만든 예다. 기회와 불가능을 나누는 규칙은 없다. | [원문](https://doi.org/10.1016/j.eswa.2007.06.022) |
| 2013 | Technology Analysis and Strategic Management | A technology opportunities analysis model: applied to dye-sensitised solar cells for China | 특허를 연구개발(형태), 경쟁(출원인), 시장(패밀리) 세 층으로 나누고, 층마다 활동이 약한 구간을 기술 기회로 표시하는 절차를 제시한다. | 기회 분석을 단계로 나눈 예다. 단계 안에 제약 검사와 사후 확인은 없다. | [원문](https://doi.org/10.1080/09537325.2013.850155) |
| 2014 | Technological Forecasting and Social Change | Exploring technological opportunities by linking technology and products: Application of morphology analysis and text mining | 기술 기회를 새 기술 예측과 기존 기술의 제품 적용으로 나누고, 후자를 형태분석과 텍스트마이닝으로 수행해 기존·적용·이종 제품 후보를 낸다. | ‘새 기술’과 ‘있는 기술의 새 쓰임’을 나눈다. 이 연구의 칸은 기술 선택지의 조합이다. | [원문](https://doi.org/10.1016/j.techfore.2013.10.013) |
| 2015 | Service Business | Developing new smart services using integrated morphological analysis: integration of the market-pull and technology-push approach | 한 형태표에 시장(사용자 요구) 축과 기술 축을 같이 넣어, 두 축이 만나는 조합으로 새 스마트 서비스 아이디어를 체계적으로 만든다. | 형태표에 기술 밖 축을 넣는 예다. 이 연구의 파일럿은 특허 안의 기술 선택만 다룬다. | [원문](https://doi.org/10.1007/s11628-015-0281-2) |
| 2015 | Technological Forecasting and Social Change | Technology opportunity discovery (TOD) from existing technologies and products: A function-based TOD framework | 특허에서 제품·기술·기능을 지식베이스로 묶고, 기능 유사도로 기존 기술이나 제품에서 아직 이어지지 않은 기회 경로를 출력한다. | 기능을 축으로 쓰는 선례다. 기능 조합이 가능한지는 검사하지 않는다. | [원문](https://doi.org/10.1016/j.techfore.2015.04.012) |
| 2019 | Sustainability | Discovering Technology Opportunity by Keyword-Based Patent Analysis: A Hybrid Approach of Morphology Analysis and USIT | 특허로 형태표를 만든 뒤 발명 발상법의 원리로 표를 확장해, 그중 새 기술 아이디어가 되는 조합을 기회 후보로 남긴다. | 형태표에 사람 규칙을 더하는 예다. 규칙은 특허에서 추정하지 않고 외부에서 가져온다. | [원문](https://doi.org/10.3390/su12010136) |

### 1-3. 빈 칸을 그대로 기회로 읽으면 뜻이 모호하다는 지적

형태표의 빈 칸을 기회로 읽는 관행에 대한 비판이다. 빈 칸은 키워드 묶음으로만 남아, 무엇이 기회인지 사람이 다시 해석해야 한다. 이 지적이, 이 연구가 빈 칸의 뜻을 가능과 불가능으로 나눠야 하는 이유이다.

| 연도 | 저널 | 제목 | 핵심 내용 | 이 연구에서의 위치 | 원문 |
|---:|---|---|---|---|---|
| 2014 | Technological Forecasting and Social Change | Novelty-focused patent mapping for technology opportunity analysis | 특허 지도의 빈 칸은 해석이 모호하다고 보고, 단어 사용의 이상치로 신규 특허를 수치화해 빈 칸 대신 기회 신호로 쓴다. | 빈 칸 해석이 모호하다는 비판이다. 이 연구가 빈 칸의 뜻을 나눠야 하는 이유와 같다. | [원문](https://doi.org/10.1016/j.techfore.2014.05.010) |

## 2. 같이 쓸 수 없는 조합을 어떤 절차로 지우는가

이 항목이 제약의 원형이다.

하는 일: 항목과 선택지를 모두 펼친다. 그다음 “이 선택지와 저 선택지는 같이 성립하지 않는다”는 쌍을 지운다. 남은 것이 가능 공간이다. 시나리오는 그 공간 안의 칸이지, 긴 이야기가 아니다.

이 절차는 오래전부터 있었다. 다만 규칙을 **전문가가 넣었다.** 같은 전문가, 같은 날이 아니면 지도가 달라진다.

이 연구가 바꾸는 부분: 규칙의 주입력을 특허로 둔다. 한 특허 안에 두 선택지가 같이 나오면 양립의 증거이다. 한 번도 같이 나오지 않았다고 바로 금지로 올리지는 않는다. 금지는 논리 규칙이거나, 사람이 소수 표본을 확인해 올릴 때만 올린다.

### 2-1. 양립하지 않는 쌍을 지우는 절차

가능 공간을 닫는 절차이다. 전문가가 쌍마다 영향이나 모순을 매기고, 그 규칙을 통과한 조합만 시나리오로 남긴다.

| 연도 | 저널 | 제목 | 핵심 내용 | 이 연구에서의 위치 | 원문 |
|---:|---|---|---|---|---|
| 2005 | Technological Forecasting and Social Change | Cross-impact balances: A system-theoretical approach to cross-impact analysis | 전문가가 항목 선택지 쌍마다 영향을 점수로 매기고, 그 점수를 동시에 만족하는 조합만 그럴듯한 시나리오로 남기는 교차영향 균형 분석을 정의한다. | 쌍 제약과 같은 발상이다. 이 연구는 전문가 점수 대신 특허에서의 공출현과 규칙을 쓴다. | [원문](https://doi.org/10.1016/j.techfore.2005.06.005) |
| 2006 | Journal of the Operational Research Society | Problem structuring using computer-aided morphological analysis | 항목과 선택지를 모두 펼친 뒤 논리적으로 양립하지 않는 쌍을 컴퓨터로 제거하고, 남은 조합을 문제의 가능 해 집합으로 정의한다. | 가능 공간을 닫는 절차의 원형이다. 입력은 전문가 판단이고, 이 연구는 특허다. | [원문](https://doi.org/10.1057/palgrave.jors.2602177) |
| 2011 | World Futures Review | Modeling Alternative Futures with General Morphological Analysis | 일반 형태분석으로 다차원 선택지 전체를 한 지도에 올리고, 시나리오를 이야기 문장이 아니라 양립 규칙을 통과한 조합으로 정의한다. | 시나리오를 이야기 한 편이 아니라 조합의 지도로 두는 근거다. | [원문](https://doi.org/10.1177/194675671100300105) |
| 2012 | Environmental Research Letters | Improving environmental change research with systematic techniques for qualitative scenarios | 이야기 시나리오의 가정이 서로 모순될 수 있음을 보이고, 교차영향 균형으로 가정 사이 일관성을 점수화해 이야기만으로는 일관성이 확인되지 않음을 보인다. | 이야기 시나리오도 일관성 검사가 필요하다는 근거다. 이 연구는 이야기 대신 칸으로 그 검사를 한다. | [원문](https://doi.org/10.1088/1748-9326/7/4/044011) |
| 2017 | Technological Forecasting and Social Change | Scenario modelling with morphological analysis | 항목·선택지를 형태분석으로 전부 열거해 해 공간을 정의하고, 논리적으로나 현실적으로 모순인 조합을 제거한 나머지만 일관된 시나리오 부류로 분류한다. | 이 연구가 하려는 ‘제약을 건 공간’과 가장 가깝다. 다른 점은 제약을 특허 증거로 추정한다는 것이다. | [원문](https://doi.org/10.1016/j.techfore.2017.05.016) |

### 2-2. 가능 공간이 클 때 대표를 고르는 절차

규칙을 통과한 칸이 수백 개일 때의 다음 절차이다. 이 연구는 먼저 공간 전체를 정의하고, 줄이기는 그다음이다.

| 연도 | 저널 | 제목 | 핵심 내용 | 이 연구에서의 위치 | 원문 |
|---:|---|---|---|---|---|
| 2003 | European Journal of Operational Research | Identification of a small reliable and efficient set of consistent scenarios | 전문가가 매긴 일관성 점수로 모순 없는 시나리오를 만든 뒤, 그 집합이 클 때 정보를 덜 잃고 크기가 작은 대표 집합을 고르는 알고리즘을 제시한다. | 공간이 너무 클 때 묶음을 줄이는 선례다. 이 연구는 먼저 공간 전체를 정의하고, 줄이기는 그다음이다. | [원문](https://doi.org/10.1016/j.ejor.2003.08.054) |
| 2015 | Futures | Choosing diverse sets of plausible scenarios in multidimensional exploratory futures techniques | 형태 공간에서 양립 가능한 조합이 수백 개일 때, 그럴듯함을 유지하면서 서로 거리가 먼 소수 조합을 고르는 다양성 기준을 정의한다. | 가능 공간이 클 때 다양성을 유지하며 고르는 예다. 고르기 전에 불가능 칸을 빼는 순서가 이 연구와 같다. | [원문](https://doi.org/10.1016/j.futures.2015.12.003) |

## 3. 칸의 묶음이 좋은지, 나중에 맞았는지를 어떤 이름으로 재는가

지도를 그럴듯하게 그리는 것과, 그 지도가 읽을 만하고 나중에 맞았는지를 보이는 것은 다른 일이다.

이 항목은 목적에서 말한 두 확인의 이름이다. 제약을 넣은 지도가 덜 헷갈리는지는 묶음의 품질 이름에서 온다. 과거 시점의 지도가 이후 특허와 맞는지는 예측을 나중에 채점하는 습관에서 온다.

### 3-1. 묶음이 좋은지의 이름

시나리오 문헌은 문장 한 편의 문장이 좋은지보다, **묶음 전체**가 좋은지를 묻는다. 반복되는 조건은 네 가지이다.

- 다 담았는가.
- 한쪽으로 몰리지 않았는가.
- 서로 다른가.
- 서로 맞고, 그럴듯한가.

대부분은 워크숍 결과물에 대한 점검표이다. 특허 칸에 같은 이름을 계산식으로 붙인 연구는 거의 없다.

최근에는 텍스트와 생성 모형이 시나리오 **문장**을 쓴다. 이 연구는 그 문장을 결과로 받지 않는다. 결과로 받는 것은 가능 공간과, 그 공간이 이후 특허와 맞는지이다.

생성 모형으로 예전 형태분석 보고서를 사후에 평가한 논문이 하나 있다. 평가는 하되, 채점 자료는 생성 모형이 아니라 이후 특허로 한다는 점이 이 연구와의 차이다.

| 연도 | 저널 | 제목 | 핵심 내용 | 이 연구에서의 위치 | 원문 |
|---:|---|---|---|---|---|
| 2003 | Futures | An updated scenario typology | 시나리오를 목표, 시간 범위, 공간 범위, 데이터 성격으로 유형화해, 유형이 다르면 만드는 방법과 평가 기준도 달라야 함을 정리한다. | 시나리오라는 말의 범위를 정하는 글이다. 이 연구는 그중 조합으로 된 미래만 다룬다. | [원문](https://doi.org/10.1016/s0016-3287(02)00090-3) |
| 2006 | Futures | Scenario types and techniques: Towards a user's guide | 시나리오를 사용자가 원하는 지식으로 나누어, 무엇이 일어날지(예측), 무엇이 일어날 수 있는지(탐색), 목표에 어떻게 갈지(규범)에 생성·일관성 기법을 대응시킨다. | 이 연구는 ‘무엇이 가능한가’ 쪽에 선다. 목표를 정해 놓고 이야기를 쓰지 않는다. | [원문](https://doi.org/10.1016/j.futures.2005.12.002) |
| 2007 | foresight | The current state of scenario development: an overview of techniques | 문헌의 시나리오 기법을 8개 범주, 23개 변종으로 분류하고, 범주마다 쓰는 입력·산출과 장단점을 표로 정리한다. | 기법 지도다. 이 연구가 쓰지 않는 기법(이야기 작성, 워크숍만으로 끝내기)을 구분하게 한다. | [원문](https://doi.org/10.1108/14636680710727516) |
| 2008 | DIE Studies | Methods of Future and Scenario Analysis: Overview, Assessment, and Selection Criteria | 미래·시나리오 분석 기법을 한자리에 모아 평가하고, 상황에 따라 어떤 기법을 쓸지 고르는 기준을 정리한다. | 기법을 고르는 점검표다. 이 연구는 그 점검표의 품질 항목을 특허 칸의 숫자로 바꾼다. | [원문](https://www.idos-research.de/en/studies/article/methods-of-future-and-scenario-analysis-overview-assessment-and-selection-criteria/) |
| 2009 | Technological Forecasting and Social Change | Thinking inside the box: A participatory, computer-assisted approach to scenario discovery | 제안 정책이 실패하는 모형 입력 영역을 시나리오로 정의하고, 이해관계자가 시뮬레이션 결과에서 그 영역을 데이터마이닝으로 찾게 하는 절차를 제시한다. | 사람 참여와 계산을 같이 쓴 예다. 이 연구에서 사람 판단은 소수 표본 검수에만 쓴다. | [원문](https://doi.org/10.1016/j.techfore.2009.08.002) |
| 2010 | Technological Forecasting and Social Change | Scenario building: Uses and abuses | 시나리오가 의사결정에 쓰이려면 관련성, 일관성, 개연성 세 조건을 통과해야 한다고 정의하고, 조건이 없으면 산출이 쓰이지 않는다고 본다. | 품질 이름의 출처다. 이 연구는 그 이름을 특허 칸에 대한 숫자로 바꾼다. | [원문](https://doi.org/10.1016/j.techfore.2010.06.007) |
| 2012 | Futures | A review of scenario planning | 정성 시나리오와 정량 시나리오를 입력·산출·장단점으로 비교하고, 정량 방법이 만든 많은 원시 조합을 줄이고 문장으로 다듬는 단계가 따로 필요하다고 정리한다. | 공간이 커지는 문제를 분명히 한다. 이 연구는 제약을 넣어 칸 수를 줄인다. | [원문](https://doi.org/10.1016/j.futures.2012.10.003) |
| 2012 | Technological Forecasting and Social Change | Does the intuitive logics method – and its recent enhancements – produce “effective” scenarios? | 조직 시나리오 작업의 목표를 문헌에서 뽑고, 표준 기법인 직관적 논리가 이해와 관점 전환은 돕지만 의사결정 개선은 잘 달성하지 못함을 평가한다. | 잘 쓴 이야기가 곧 좋은 시나리오는 아니라는 문제 제기다. | [원문](https://doi.org/10.1016/j.techfore.2012.09.003) |
| 2013 | International Journal of Foresight and Innovation Policy | Plausibility indications in future scenarios | 시나리오의 품질 기준을 과거 사실의 참·거짓과 구분하고, 중심 기준을 개연성(일어날 수 있다는 증거가 충분한가)으로 정의한 뒤 표시 항목으로 조작한다. | 그럴듯함을 품질 기준으로 둔 글이다. 이 연구는 그럴듯함을 제약 통과 여부로 조작한다. | [원문](https://doi.org/10.1504/ijfip.2013.058611) |
| 2015 | European Journal of Futures Research | New outlooks in traceability and consistency of integrated scenarios | 통합 시나리오의 품질을 추적 가능성(산출이 어떤 가정에서 나왔는지 되짚히는가)과 일관성(가정과 결과가 모순되지 않는가) 두 기준으로 정의한다. | 다시 계산할 수 있어야 한다는 요구의 출처다. 이 연구가 규칙과 표를 남기는 이유다. | [원문](https://doi.org/10.1007/s40309-015-0077-6) |
| 2016 | Environmental Modelling & Software | Choosing small sets of policy-relevant scenarios by combining vulnerability and diversity approaches | 많은 계산 시나리오 중 소수만 고를 때, 제안 정책이 실패하는 취약 시나리오와 미래 공간을 넓게 덮는 다양한 시나리오를 동시에 고르는 최적화 방법을 제시한다. | 다양성과 유용성을 같이 보는 예다. 이 연구의 다양성은 점유된 칸이 형태적으로 퍼져 있는지다. | [원문](https://doi.org/10.1016/j.envsoft.2016.06.011) |
| 2016 | Technological Forecasting and Social Change | Extending the knowledge base of foresight: The contribution of text mining | 포사이트 입력을 인터뷰·보고서로 제한하지 않고, 텍스트마이닝으로 대량 문서의 주제와 관계를 집계해 로드맵과 시나리오 단계에 넣자고 제안한다. | 텍스트를 시나리오 입력으로 쓰는 선례다. 출력은 여전히 이야기 시나리오인 경우가 많다. | [원문](https://doi.org/10.1016/j.techfore.2016.10.017) |
| 2016 | Climatic Change | Reinvigorating the scenario technique to expand uncertainty consideration | 소수 시나리오는 미래 불확실성의 일부만 담는다고 보고, 다차원 불확실성 공간을 넓히고 사용자가 그 공간을 읽게 하며 그 개선을 반복 평가할 것을 제안한다. | 제약을 너무 세게 걸면 공간이 가짜로 작아진다는 경고다. | [원문](https://doi.org/10.1007/s10584-015-1585-x) |
| 2017 | Environmental Modelling & Software | Scenario techniques for energy and environmental research: An overview of recent developments to broaden the capacity to deal with complexity and uncertainty | 에너지·환경의 계산 시나리오 기법을, 복잡성(요인과 상호작용이 많음)과 깊은 불확실성(확률을 부여하기 어려움)을 다루는 능력으로 분류해 리뷰한다. | 계산으로 시나리오를 다루는 흐름의 지도다. 입력 데이터는 에너지 모형이지 특허가 아니다. | [원문](https://doi.org/10.1016/j.envsoft.2017.07.017) |
| 2018 | Futures & Foresight Science | Defining scenario | 시나리오의 정의를 새로 늘리지 말고 기존 정의의 공통 요소(미래, 외생 요인, 가능하고 그럴듯한 이야기, 서로 다른 대안의 집합)로 합성하자고 제안한다. | 용어 혼란을 피하라는 경고다. 이 문서는 그래서 칸, 제약, 가능 공간을 먼저 정의한다. | [원문](https://doi.org/10.1002/ffo2.3) |
| 2020 | Technological Forecasting and Social Change | Scenario development using web mining for outlining technology futures | 시나리오의 첫 단계인 주제 범위와 핵심 영향 요인 선정을 웹 마이닝과 문서 군집으로 대체해, 영향 요인 후보를 시나리오 축의 입력으로 쓴다. | 입력을 자동화한 예다. 이 연구는 입력 자동화보다, 만든 공간의 검사에 비중을 둔다. | [원문](https://doi.org/10.1016/j.techfore.2020.120086) |
| 2023 | Futures & Foresight Science | AI‐assisted scenario generation for strategic planning | ChatGPT로 전략 시나리오 초안을 생성하고, 초안 작성과 요인 나열은 대신할 수 있으나 시나리오 작업 전체를 대신하지는 못함을 실무 기록으로 남긴다. | 생성 모형이 시나리오 문장을 쓸 수 있게 된 최근 상황이다. 이 연구는 그 문장을 결과로 받지 않는다. | [원문](https://doi.org/10.1002/ffo2.148) |
| 2024 | Futures & Foresight Science | The Scenario Quality Assessment Method: A New Technique for Verifying the Quality of Scenarios | 시나리오가 의사결정에 쓰이기 전에 엄밀성 항목을 순서대로 점검하고 통과 여부를 기록하는 시나리오 품질 평가법(SQAM)을 절차로 정의한다. | 품질을 절차로 만든 최근 예다. 이 연구는 그 절차를 특허 칸의 지표로 구체화한다. | [원문](https://doi.org/10.1002/ffo2.205) |
| 2026 | foresight | Linking generative AI and morphological analysis to conduct foresight evaluation | 1976년 형태분석 미래 보고서를 생성 모형으로 현재 세계와 비교하는 사후 평가 절차를 정의하고, 어느 미래상이 나중에 맞았는지를 수치로 매긴다. | 형태분석 결과를 나중에 평가한 드문 예다. 이 연구는 생성 모형 대신 이후 특허로 평가한다. | [원문](https://doi.org/10.1108/fs-02-2025-0027) |

### 3-2. 나중에 맞았는지를 채점하는 습관

옛 예측을 나중에 채점한 연구와, 채점이 공정하려면 무엇을 미리 정해 두어야 하는지를 말한 연구이다.

채점할 때 지킬 규칙이 하나 있다. 2018년까지의 특허로 지도를 만들었다면, 2019년 이후 특허는 지도를 만드는 데 쓰면 안 된다. 미래 정보가 들어가면 점수가 좋아 보여도 확인이 아니다. Kapoor (2023)가 그 경고이다.

**가능 칸이 채워졌는지, 불가능 칸을 침범했는지를 채점한 논문은 없다.** 그 채점이 이 연구의 핵심이다. 성장 곡선, 신흥 기술, 유망 특허를 채점한 논문은 대상이 다르므로 옵션에 둔다.

| 연도 | 저널 | 제목 | 핵심 내용 | 이 연구에서의 위치 | 원문 |
|---:|---|---|---|---|---|
| 2002 | Technological Forecasting and Social Change | What can past technology forecasts tell us about the future? | 1967년에 발표된 기술 혁신 예측 100건을 2000년 시점에서 채점해, 제때 실현된 예측은 절반 미만이므로 기술 예측은 사후 채점이 필요하다고 결론낸다. | 예측은 사후 채점이 필요하다는 근거다. 이 연구는 이야기 예측이 아니라 칸의 점유를 채점한다. | [원문](https://doi.org/10.1016/s0040-1625(02)00186-5) |
| 2012 | Technological Forecasting and Social Change | An examination of factors affecting accuracy in technology forecasts | 과거 기술 예측 표본에서 정확도에 통계적으로 영향을 준 요인은 방법(정량이 정성보다 나음)과 예측 기간뿐이었음을 추정한다. | 무엇을 미리 정해 두어야 채점이 공정한지의 참고다. | [원문](https://doi.org/10.1016/j.techfore.2012.10.026) |
| 2018 | Technological Forecasting and Social Change | Long-term forecasts of military technologies for a 20–30 year horizon: An empirical assessment of accuracy | 1990년대에 2020년을 목표로 한 군사기술 예측 묶음을 실제 배치 여부로 채점해, 분야별 적중률을 수치로 제시한다. | 긴 시간을 나중에 채점한 예다. 이 연구가 되돌아보는 기간은 그보다 짧고, 대상은 특허 조합이다. | [원문](https://doi.org/10.1016/j.techfore.2018.08.001) |
| 2023 | Patterns | Leakage and the reproducibility crisis in machine-learning-based science | 기계학습의 데이터 누수를 평가 시점에 알 수 없는 정보가 학습이나 전처리에 들어가는 것으로 정의하고, 누수가 성능을 부풀린다는 것을 17개 분야 294편에서 집계한다. | 과거 시점으로 지도를 만들 때 그 이후 특허를 쓰면 안 되는 직접 근거다. | [원문](https://doi.org/10.1016/j.patter.2023.100804) |

---

## 옵션: 구현할 때 참고하는 연구

필수 세 항목이 연구 질문을 세운다. 아래 논문이 없어도 그 질문은 남는다.

찾은 이유는 세 가지이다.

- 항목과 선택지를 뽑는 도구를 고르기 위해서이다. 키워드, 문장 구조, 분류 코드, 문장 벡터는 서로 바꿀 수 있어야 한다. 도구가 바뀌어도 뒤의 검사(제약을 넣으면 지도가 나아지는가, 나중에 특허와 맞는가)는 같다.
- 옆에서 하는 예측과 경계를 긋기 위해서이다. 다음 칸 하나, 분야와 분야의 융합, 유망 특허 하나는 이 연구의 결과가 아니다.
- 예측을 나중에 확인한다는 습관을 어디서 볼 수 있는지 알기 위해서이다. 그 습관 자체는 3-2에 있다. 여기는 그 습관이 붙은 대상이 칸의 가능 공간이 아닌 경우이다.

### 옵션 1. 빈 자리를 지도, 이상 특허, 유망 기술 하나로 읽은 연구

형태표의 칸이 아니다. 2차원 지도의 빈 영역이거나, 기존 분포에서 벗어난 특허이거나, 지표로 고른 기술 하나이다. 빈 자리나 이상한 특허를 기회로 읽는 이웃이고, 이 연구가 결과로 내지 않는 것들이다.

| 연도 | 저널 | 제목 | 핵심 내용 | 이 연구에서의 위치 | 원문 |
|---:|---|---|---|---|---|
| 2009 | Technovation | An approach to discovering new technology opportunities: Keyword-based patent map approach | 특허를 키워드 벡터의 2차원 지도에 놓고 밀도가 낮은 넓은 빈 영역을 공백으로 정의한 뒤, 기술 중요성과 추세로 그 공백이 새 기술 후보인지 검사한다. | 빈 자리를 기회로 읽는 대표 예다. 그 자리가 불가능한 조합인지는 보지 않는다. | [원문](https://doi.org/10.1016/j.technovation.2008.10.006) |
| 2012 | Expert Systems with Applications | Development of a GTM-based patent map for identifying patent vacuums | 생성지형도로 특허가 없는 격자를 자동으로 찾고, 그 격자를 원래 키워드 벡터로 되돌려 빈 영역의 기술 내용을 해석한다. | 빈 영역을 눈으로 찾는 방법이다. 빈 영역이 기회인지 불가능인지는 사람이 판단한다. | [원문](https://doi.org/10.1016/j.eswa.2011.08.101) |
| 2013 | Technology Analysis and Strategic Management | Identifying technological opportunities using the novelty detection technique: a case of laser technology in semiconductor manufacturing | 특허 키워드 벡터에 신규성 탐지를 적용해, 기존 분포에서 벗어난 특허를 주관적 판단 대신 기술 기회의 증거로 삼는다. | 빈 칸 대신 ‘이상한 특허’를 기회로 보는 대안이다. 조합 공간은 아니다. | [원문](https://doi.org/10.1080/09537325.2012.748892) |
| 2016 | Technological Forecasting and Social Change | A novel approach to forecast promising technology through patent analysis | 특허를 분류 코드 조합으로 군집화한 뒤, 인용·삼극 패밀리·독립항으로 그 군집이 유망한지 판정해 기술 하나를 고른다. | 유망 기술 ‘하나’를 고르는 접근이다. 이 연구는 가능한 조합의 집합을 만든다. | [원문](https://doi.org/10.1016/j.techfore.2016.11.023) |
| 2016 | Technological Forecasting and Social Change | Product opportunity identification based on internal capabilities using text mining and association rule mining | 기업의 기존 제품 포트폴리오를 내부 역량으로 보고, 특허의 제품 연관규칙으로 그 기업이 만들 수 있는 제품 기회를 평가한다. | 기술 기회가 제품으로 이어지는지를 보는 예다. 이 연구는 제품 시장을 예측하지 않는다. | [원문](https://doi.org/10.1016/j.techfore.2016.01.011) |
| 2021 | Technological Forecasting and Social Change | Technology opportunity discovery of proton exchange membrane fuel cells based on generative topographic mapping | 연료전지 특허를 생성지형도 격자에 놓고, 특허가 없는 격자의 키워드 벡터를 추정해 아직 열리지 않은 개발 방향으로 제시한다. | 한 기술 분야에서 빈 영역을 찾는 최근 예다. 이후 특허가 그 영역을 채웠는지는 보지 않는다. | [원문](https://doi.org/10.1016/j.techfore.2021.120859) |

### 옵션 2. 특허 문장에서 기술 요소를 뽑는 연구

키워드 묶음은 “추론”, “압축”, “개인정보”처럼 주제가 된다. 주제가 곧 항목은 아니다. 항목은 **선택이 갈리는 자리**여야 한다.

이 연구들은 특허 문장에서 “무엇이 무엇을 하는가”를 뽑는다. 흔히 주어, 동작, 대상으로 읽는다. 그러면 기능이 보여서, 키워드보다 항목에 가깝다. 일부는 그 요소로 형태표의 칸까지 만든다.

뽑은 요소로 칸을 만들어도, **그 칸이 같이 성립하는지는 보지 않는다.** 이 연구가 가져가는 것은 요소를 뽑는 방법이다. 이 연구가 가진 문제-해결-효과 그래프도 같은 방향의 입력이다. 그래프 자체가 결론은 아니다.

| 연도 | 저널 | 제목 | 핵심 내용 | 이 연구에서의 위치 | 원문 |
|---:|---|---|---|---|---|
| 2012 | R&D Management | An SAO ‐based text‐mining approach for technology roadmapping using patent information | 키워드만으로는 기술의 용도가 안 보인다고 보고, 주어-동작-대상으로 기능을 뽑아 기술 로드맵의 제품·기술 층에 넣는다. | 뽑은 요소를 계획 표로 잇는 선례다. 요소 사이의 금지는 다루지 않는다. | [원문](https://doi.org/10.1111/j.1467-9310.2012.00702.x) |
| 2012 | Expert Systems with Applications | An SAO-based text mining approach to building a technology tree for technology planning | 특허 문장에서 주어-동작-대상(SAO)을 뽑아 기능과 부품이 이어지는 기술 나무를 만듦으로써, 키워드가 아니라 문장 구조로 기술 요소를 얻는다. | 키워드 대신 문장 구조로 기술 요소를 뽑는 선례다. 이 연구의 문제-해결-효과 그래프와 같은 방향이다. | [원문](https://doi.org/10.1016/j.eswa.2012.04.014) |
| 2016 | Technological Forecasting and Social Change | Subject–action–object-based morphology analysis for determining the direction of technological change | 주어-동작-대상으로 형태표의 항목과 선택지를 구성하고 여덟 지표로 조합 순위를 매긴 뒤, 상위 조합이 이후 특허에 실제로 자주 나타남을 보인다. | 문장 요소로 칸을 만든 뒤 순위를 주는 예다. 순위와 가능 여부는 다른 문제다. | [원문](https://doi.org/10.1016/j.techfore.2016.01.028) |
| 2017 | Scientometrics | Combining SAO semantic analysis and morphology analysis to identify technology opportunities | 주어-동작-대상으로 기술의 구성과 속성 형태행렬을 만들고, 실현 가능성 점수가 높은 새 조합을 기술 기회로 고른다. | 이 연구의 칸과 가장 비슷한 최근 형태 방법이다. 불가능한 조합을 빼는 단계는 없다. | [원문](https://doi.org/10.1007/s11192-017-2260-y) |
| 2023 | Technological Forecasting and Social Change | Identifying technology opportunity using SAO semantic mining and outlier detection method: A case of triboelectric nanogenerator technology | 논문과 특허에서 문제와 해법(SAO)을 뽑아 둘의 빈틈을 찾고, 논문 분포의 이상치를 더해 초기 기술 기회를 고른다. | 문장 요소와 이상 탐지를 합친 예다. 이상 특허가 곧 가능한 빈 칸은 아니다. | [원문](https://doi.org/10.1016/j.techfore.2023.122353) |
| 2026 | Scientometrics | Technology opportunity prediction based on SAO representation learning | 특허의 주어-동작-대상 그래프를 임베딩해, 위상만으로는 안 보이는 의미 관계까지 포함해 아직 없는 기술 삼항 관계를 기회로 예측한다. | 문장 요소를 임베딩과 연결한 최근 예다. 예측이 나중에 맞았는지는 이 연구가 따로 확인한다. | [원문](https://doi.org/10.1007/s11192-026-05578-1) |

### 옵션 3. 다음에 이어질 연결을 맞히는 연구

앞의 필수 연구가 빈 칸을 **찾아서 해석**한다면, 이쪽은 빈 칸이나 분야 쌍을 **예측**한다. 계산은 비슷해 보인다. 질문이 다르다.

이 연구는 “다음에 뜰 칸 하나”를 맞히지 않는다. 가능한 칸의 집합을 만든 뒤, 그 집합이 나중에 나온 특허를 얼마나 받아들이는지를 본다. 그 확인의 습관은 3-2에 있다.

#### 한 기술 안에서 다음 칸을 고르는 연구

지도의 빈 칸 중에서 유망한 칸을 고르거나, 기업이 다음에 갈 기회를 고른다.

가져갈 점: 빈 칸을 전부 같은 기회로 두지 않으려는 시도.  
가져가지 않을 점: 고른 칸 하나가 곧 답이라는 설계. 그 칸이 규칙상 가능한지는 여전히 따로 봐야 한다.

| 연도 | 저널 | 제목 | 핵심 내용 | 이 연구에서의 위치 | 원문 |
|---:|---|---|---|---|---|
| 2018 | Technological Forecasting and Social Change | Exploring technology opportunities by visualizing patent information based on generative topographic mapping and link prediction | 생성지형도의 빈 격자를 링크 예측으로 좁힌 뒤, 그 예측을 이후 실제 특허 격자와 비교해 빈 칸 예측이 맞았는지를 검사한다. | 빈 칸을 ‘다음에 채워질 칸’으로 좁힌다. 고른 칸이 기술적으로 가능한지는 제약으로 검사하지 않는다. | [원문](https://doi.org/10.1016/j.techfore.2018.01.019) |
| 2022 | Technological Forecasting and Social Change | Two-stage technology opportunity discovery for firm-level decision making: GCN-based link-prediction approach | 그래프 합성곱으로 아직 없는 기술 분류 링크를 넓게 예측한 뒤, 대상 기업의 현재 포트폴리오에 맞는 기회만 2단계에서 남긴다. | 기업 단위로 다음 기회를 맞히는 예다. 이 연구는 기업 승자가 아니라 가능한 칸의 집합을 만든다. | [원문](https://doi.org/10.1016/j.techfore.2022.121934) |
| 2023 | Technovation | Technology opportunity analysis using hierarchical semantic networks and dual link prediction | 특허의 주어-동작-대상으로 계층 의미망을 만들고, 링크 예측으로 기회를 찾은 뒤 유사도 예측으로 신규성을 매겨 후보를 좁힌다. | 의미망과 링크 예측을 기회 분석에 쓴 최근 예다. 만든 공간을 과거 시점으로 되돌려 검사하지는 않는다. | [원문](https://doi.org/10.1016/j.technovation.2023.102872) |

#### 서로 다른 분야가 만나는 융합을 맞히는 연구

이쪽은 한 분야 안의 선택지 조합이 아니다. “배터리와 안전”, “두 산업 분류”처럼 **분야와 분야의 연결**을 맞힌다.

가져갈 점: 예측은 나중에 확인해야 한다는 문제의식. 최근 논문일수록 그물을 정교하게 만들지만, 과거 시점만 쓰고 이후 특허로 채점하는 설계는 여전히 드물다.  
가져가지 않을 점: 융합 점수 자체를 이 연구의 결과로 삼는 일. 파일럿은 한 기술 분야 안의 칸이다.

| 연도 | 저널 | 제목 | 핵심 내용 | 이 연구에서의 위치 | 원문 |
|---:|---|---|---|---|---|
| 2010 | Technological Forecasting and Social Change | Patent indicators for monitoring convergence – examples from NFF and ICT | 서로 다른 분야의 특허가 같은 분류를 공유하는 정도를 융합 지표로 정의하고, 기능성 식품과 정보통신에서 분야 경계가 흐려지는지를 수치로 보인다. | 융합을 숫자로 보는 초기 예다. 이 연구의 파일럿은 한 분야 안의 선택지 조합이다. | [원문](https://doi.org/10.1016/j.techfore.2010.06.021) |
| 2015 | Technological Forecasting and Social Change | Predicting the pattern of technology convergence using big-data technology on large-scale triadic patents | 1955–2011년 삼극 특허의 분류 코드에 연관규칙과 링크 예측을 적용해, 같이 나타날 가능성이 큰 분류 쌍을 미래 융합 패턴으로 예측한다. | 분류 코드 쌍으로 융합을 맞히는 선례다. 맞힌 뒤의 사후 확인은 약하다. | [원문](https://doi.org/10.1016/j.techfore.2015.07.022) |
| 2018 | Technovation | Anticipating technological convergence: Link prediction using Wikipedia hyperlinks | 기술 분야를 위키피디아 하이퍼링크로 나타내고, 아직 연결되지 않은 분야 쌍 중 링크 예측 점수가 높은 쌍을 앞으로의 융합으로 제시한다. | 특허가 아닌 자료로 융합을 미리 보는 예다. 이 연구의 주입력은 특허다. | [원문](https://doi.org/10.1016/j.technovation.2018.06.008) |
| 2018 | Journal of Informetrics | Technological opportunity discovery for technological convergence based on the prediction of technology knowledge flow in a citation network | 이종 기술 분야 사이의 특허 인용을 지식 흐름으로 정의하고, 아직 인용이 없는 분야 쌍의 미래 흐름을 방향과 세기까지 융합 기회 후보로 예측한다. | 인용을 ‘다음에 이어질 지식’으로 읽는 예다. 인용은 가능 공간 그 자체가 아니다. | [원문](https://doi.org/10.1016/j.joi.2018.09.007) |
| 2020 | Technological Forecasting and Social Change | Machine-learning-based deep semantic analysis approach for forecasting new technology convergence | 특허 텍스트의 의미 벡터를 기계학습에 넣어 아직 같이 나오지 않은 기술 쌍의 융합 여부를 예측하고, 텍스트를 넣으면 새 융합 예측이 나아짐을 보인다. | 의미 유사도로 새 융합을 맞힌다. 유사하다고 같이 구현할 수 있는 것은 아니다. | [원문](https://doi.org/10.1016/j.techfore.2020.120095) |
| 2024 | Information Processing & Management | Technology convergence prediction based on temporal heterogeneous graph neural networks | 기술 요소의 공출현, 의미 거리, 지식 흐름, 시간을 한 이질 그래프에 넣어, 다음 시점에 새로 생길 기술 쌍을 여러 입자도로 예측한다. | 융합 예측에 시간을 넣은 최근 예다. 예측 대상은 분야 쌍이지, 제약으로 닫은 칸 전체가 아니다. | [원문](https://doi.org/10.1016/j.ipm.2024.104034) |
| 2024 | IEEE Transactions on Engineering Management | Identification of Sustainable Convergence Technology for Batteries via Multiplex Link Prediction (August 2024) | 배터리 특허를 저장, 안전, 재활용 세 층의 분류 그래프로 나누고, 층 사이 다중 링크 예측으로 세 성질이 한 기술에서 만나는 융합 후보를 찾는다. | 한 제품군 안에서 융합을 예측한 예다. 예측 칸의 사후 점유는 이 연구의 검사 항목이다. | [원문](https://doi.org/10.1109/tem.2024.3451154) |
| 2024 | IEEE Transactions on Engineering Management | Prediction of Technology Convergence on the Basis of Supernetwork | 분류 코드만의 단일 층 대신 토픽·분류·출원인을 겹친 슈퍼네트워크를 만들어, 서로 다른 성분에 있던 분류 쌍의 융합까지 예측한다. | 분류 계층을 그물에 넣는 예다. 이 연구는 분류를 축 후보로 쓸 수 있으나, 융합 점수만으로 끝내지 않는다. | [원문](https://doi.org/10.1109/tem.2024.3495655) |
| 2024 | Advanced Engineering Informatics | From technology opportunities to solutions generation via patent analysis: Application of machine learning-based link prediction | 노드 속성·관계·위상으로 미래 융합 쌍을 링크 예측한 뒤, 그 쌍의 유사 특허 초록을 묶어 기회 쌍을 구체적 기술 해법으로 변환한다. | 기회에서 해법으로 가는 최근 예다. 해법이 불가능한 조합인지를 따로 나누지는 않는다. | [원문](https://doi.org/10.1016/j.aei.2024.102944) |
| 2024 | Journal of Informetrics | A framework armed with node dynamics for predicting technology convergence | 기존 노드 사이의 링크만 맞히지 않도록, 새로 등장하는 기술 노드와 그 링크까지 예측하는 융합 예측 틀을 정의한다. | 융합 예측 모형을 정교화한 예다. 모형이 맞았는지를 재는 창 설계는 이 연구의 몫이다. | [원문](https://doi.org/10.1016/j.joi.2024.101583) |
| 2025 | Expert Systems with Applications | Predicting technology convergence patterns in different industry segments: A multi-layer network approach | 산업 구간별 다층 네트워크로 기술 융합 패턴을 예측해, 융합을 전 산업 하나의 점수가 아니라 구간마다의 패턴으로 다룬다. | 분야를 나눠 예측하는 최근 예다. 이 연구는 먼저 한 분야 파일럿에서 칸 검증을 한다. | [원문](https://doi.org/10.1016/j.eswa.2025.126994) |
| 2025 | Advanced Engineering Informatics | From technology hierarchies to convergence prediction: Integrating graph learning into multi-layer heterogeneous networks | 특허를 미세·중간·거시 기술 층으로 나누어 이질 네트워크를 만들고, 그래프 학습으로 층을 가로지르는 융합 링크를 예측한다. | 계층 정보를 융합 예측에 쓴 최근 예다. 계층은 축이 될 수 있으나, 계층 자체가 가능 공간은 아니다. | [원문](https://doi.org/10.1016/j.aei.2025.103927) |
| 2025 | Technovation | Forecasting technology convergence with the spatiotemporal link prediction model | 기술 융합 링크 예측에 공간 구조와 시간을 같이 넣어, 1–2년이 아니라 3–4년 앞의 융합 쌍까지 맞히는 모형을 정의한다. | 최신 융합 예측의 예다. 이 연구가 가져갈 것은 예측 점수가 아니라, 예측을 나중에 확인하는 습관이다. | [원문](https://doi.org/10.1016/j.technovation.2025.103289) |
| 2026 | Technological Forecasting and Social Change | Embracing technological opportunities based on heterogeneous networks: An integrated link prediction approach for technology convergence of firms | 기업·기술·텍스트 의미를 이질 네트워크에 넣고 링크 예측으로, 산업 전체가 아니라 특정 기업의 다음 융합 기회를 순위화한다. | 기업 융합 기회를 맞히는 최근 예다. 이 연구는 특정 기업의 다음 수를 맞히지 않는다. | [원문](https://doi.org/10.1016/j.techfore.2026.124701) |

#### 예측 도구 자체, 그리고 논문 그물에 쓴 연구

링크 예측은 “지금 그물을 보고 다음 선을 맞히는 문제”이다. 아래 논문은 그 문제의 정의이거나, 특허가 아닌 논문 그물에 같은 일을 한 경우이다.

위치: 도구와 참고이다. 이 연구의 질문으로 올리지 않는다.

| 연도 | 저널 | 제목 | 핵심 내용 | 이 연구에서의 위치 | 원문 |
|---:|---|---|---|---|---|
| 2007 | Journal of the American Society for Information Science and Technology | The link‐prediction problem for social networks | 한 시점의 네트워크만 보고 이후 새로 생길 링크를 맞히는 문제를 링크 예측으로 정의하고, 노드 근접성 지표가 이후 공저를 얼마나 맞히는지 비교한다. | 링크 예측이라는 도구의 정의다. 이 연구의 본론은 그 도구로 칸 하나를 맞히는 일이 아니다. | [원문](https://doi.org/10.1002/asi.20591) |
| 2012 | Scientometrics | Prediction of emerging technologies based on analysis of the US patent citation network | 미국 특허 인용 네트워크를 군집화해 기술 가지를 정의하고, 각 군집의 과거 성장으로 이후 크기와 새 재조합 군집을 예측한다. | 인용 군집의 성장을 맞히는 예다. 군집은 선택지의 조합 칸과 다르다. | [원문](https://doi.org/10.1007/s11192-012-0796-4) |
| 2020 | Proceedings of the National Academy of Sciences | Predicting research trends with semantic and neural networks with an application in quantum physics | 양자물리 논문의 개념 네트워크를 만들고, 의미 유사와 신경망으로 아직 없는 개념 쌍의 연결 확률을 계산해 다음 연구 후보를 제시한다. | 특허가 아닌 논문에서 같은 예측을 한 예다. 방법 참고이지, 이 연구의 입력은 아니다. | [원문](https://doi.org/10.1073/pnas.1914370116) |
| 2023 | Nature Machine Intelligence | Forecasting the future of artificial intelligence with machine learning-based link prediction in an exponentially growing knowledge network | 인공지능 논문의 개념 네트워크에서 링크 예측으로 다음 개념 연결을 제안하고, 이후 실제 출판과 비교할 수 있는 벤치마크를 정의한다. | 다음 연결 제안이 어디까지 가능한지의 참고다. 제안된 연결이 가능한 기술 칸인지는 별도 문제다. | [원문](https://doi.org/10.1038/s42256-023-00735-0) |

### 옵션 4. 특허를 벡터와 그물로 묶는 연구

키워드 사전을 사람이 고정하면, 사전이 바뀌는 순간 지도가 바뀐다. 그래서 문장이나 용어를 벡터로 바꿔 비슷한 특허를 모으는 방법이 나왔다.

이 방법은 **항목을 찾는 도구**로 쓸 수 있다. 도구는 바꿀 수 있어야 한다.

벡터 공간의 “가깝다”는 칸의 “같이 쓸 수 있다”와 다르다. 가까운 특허를 모아도 가능 공간이 되지는 않는다.

| 연도 | 저널 | 제목 | 핵심 내용 | 이 연구에서의 위치 | 원문 |
|---:|---|---|---|---|---|
| 2013 | NeurIPS | Translating Embeddings for Modeling Multi-relational Data | 지식 그래프의 관계 (머리, 관계, 꼬리)를 벡터 공간의 평행이동으로 학습해, 그 거리로 아직 없는 관계를 예측하는 TransE를 정의한다. | 관계 임베딩의 기본 부품이다. 이 연구의 질문은 이 부품을 더 좋게 만드는 일이 아니다. | [원문](https://papers.nips.cc/paper/5071-translating-embeddings-for-modeling-multi-relational-data) |
| 2017 | Strategic Management Journal | Text matching to measure patent similarity | 두 특허의 기술 유사도를 분류 코드 겹침이 아니라 본문 텍스트 매칭으로 정의하고, 전문가가 분류 코드보다 기술 내용에 가깝다고 검증한다. | 텍스트로 유사도를 재는 선례다. 가까운 특허가 같은 칸에 들어간다는 뜻은 아니다. | [원문](https://doi.org/10.1002/smj.2699) |
| 2019 | EMNLP | Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks | 샴 신경망으로 문장 임베딩을 만들어, 의미가 가까운 문장을 벡터 거리로 대규모 비교할 수 있게 한다. | 이 연구가 텍스트를 벡터로 바꿀 때 쓰는 기본 부품이다. 연구 질문 자체는 아니다. | [원문](https://doi.org/10.18653/v1/d19-1410) |
| 2019 | Expert Systems with Applications | TechNet: Technology semantic network based on patent data | 미국 특허 전체에서 기술 용어와 용어 관계를 추출해 대규모 기술 의미망을 만들고, 망의 거리로 유사 기술과 설계 지식을 찾는다. | 용어 그물로 기술을 표현한 선례다. 용어 그물을 선택지 표로 바꾸는 규칙은 따로 필요하다. | [원문](https://doi.org/10.1016/j.eswa.2019.112995) |
| 2019 | Nature | Unsupervised word embeddings capture latent knowledge from materials science literature | 재료과학 논문의 단어 임베딩만으로 아직 실험 기록이 없는 물질-성질 관계를 복원해, 과거 텍스트에 미래 발견의 방향이 남아 있음을 보인다. | 텍스트 벡터가 빈 관계를 암시할 수 있다는 참고다. 암시된 관계가 특허 칸의 기회인지는 별도로 확인해야 한다. | [원문](https://doi.org/10.1038/s41586-019-1335-8) |
| 2020 | arXiv | Knowledge Graph Embedding for Link Prediction: A Comparative Analysis | 지식 그래프의 빠진 사실을 예측하는 임베딩 모형 16개를 같은 데이터에서 비교해, 관계 유형마다 어떤 모형이 나은지를 정리한다. | 관계 예측 부품을 고르는 비교표다. 이 연구의 주기여는 그 부품의 성능이 아니다. | [원문](https://doi.org/10.48550/arxiv.2002.00819) |
| 2021 | Technological Forecasting and Social Change | Deep learning for patent landscaping using transformer and graph embedding | 특허 초록의 트랜스포머 임베딩과 분류 코드 그래프 임베딩을 합쳐, 랜드스케이프에 넣을 특허를 자동으로 가려내는 분류 모형을 만든다. | 현황 지도를 딥러닝으로 그리는 예다. 현황 지도는 가능한 조합의 전부가 아니다. | [원문](https://doi.org/10.1016/j.techfore.2021.121413) |
| 2021 | American Economic Review Insights | Measuring Technological Innovation over the Long Run | 한 특허의 중요도를 이전 특허와의 텍스트 거리(새로움)와 이후 특허와의 텍스트 유사(영향)의 조합으로 정의한다. | 텍스트 위치로 중요 특허를 고르는 예다. 이 연구는 중요 특허 순위가 아니라 칸의 점유를 본다. | [원문](https://doi.org/10.1257/aeri.20190499) |
| 2021 | World Patent Information | A survey on deep learning for patent analysis | 특허 딥러닝 연구 40편을 데이터, 표현, 모형, 과제(분류·검색·추출·가치)로 나누어, 어떤 도구가 어떤 일에 쓰였는지 정리한다. | 추출 도구를 고를 때의 지도다. 도구가 좋아도 칸의 검증 설계를 대신하지 않는다. | [원문](https://doi.org/10.1016/j.wpi.2021.102035) |
| 2021 | Knowledge-Based Systems | Guiding data-driven design ideation by knowledge distance | 설계 자극을 용어·문서·분야 세 층에서 찾고, 너무 가깝거나 너무 먼 자극을 지식 거리로 걸러 아이디어 탐색을 안내한다. | 거리라는 기준으로 자극을 고르는 예다. 거리는 제약(같이 쓸 수 없음)과 다른 개념이다. | [원문](https://doi.org/10.1016/j.knosys.2021.106873) |
| 2021 | Artificial Intelligence for Engineering Design, Analysis and Manufacturing | Idea generation with Technology Semantic Network | 기술 의미망에서 시드 기술과 일정 거리 안의 용어를 자극으로 뽑는 절차를 정의하고, 그 자극이 설계 아이디어의 다양성을 늘리는지 실험한다. | 의미망을 아이디어 생성에 쓴 예다. 이 연구는 아이디어 문장을 생성하지 않는다. | [원문](https://doi.org/10.1017/s0890060421000020) |
| 2022 | Technological Forecasting and Social Change | A text-embedding-based approach to measuring patent-to-patent technological similarity | 특허 본문을 문장 임베딩으로 바꾼 뒤 최근접 이웃으로 전 특허 쌍의 기술 유사도를 계산해, 특허 전체를 하나의 기술 네트워크로 나타낸다. | 임베딩 그물을 만드는 실용 예다. 그물의 점이 곧 시나리오 칸은 아니다. | [원문](https://doi.org/10.1016/j.techfore.2022.121559) |
| 2022 | Journal of Computing and Information Science in Engineering | Patent Data for Engineering Design: A Critical Review and Future Directions | 공학 설계 연구가 특허를 써 온 용도를 이론·방법·도구·전략으로 나누어 정리하고, 텍스트·그래프 방법 이후의 남은 한계를 항목으로 제시한다. | 특허를 설계 지식으로 쓰는 범위의 지도다. 이 연구가 특허로 하지 않을 일(시장 예측 등)을 가늠하게 한다. | [원문](https://doi.org/10.1115/1.4054802) |
| 2023 | Nature Human Behaviour | Accelerating science with human-aware artificial intelligence | 출판 문헌만 학습한 모형은 사람이 실제로 떠올릴 추론 범위를 놓친다고 보고, 전문가의 인지 범위 안 추론을 넣으면 미래 발견 예측이 크게 나아짐을 보인다. | 모든 조합이 아니라 실제로 닿는 조합을 봐야 한다는 경고다. 빈 칸을 전부 기회로 세지 않는 이유와 통한다. | [원문](https://doi.org/10.1038/s41562-023-01648-z) |
| 2024 | Technological Forecasting and Social Change | PatentSBERTa: A deep NLP based hybrid model for patent distance and classification using augmented SBERT | 특허 청구항을 Sentence-BERT로 임베딩해 특허 사이 거리를 정의하고, 그 거리로 의미 검색과 분류 코드 자동 부여를 수행한다. | 청구항 임베딩의 최근 예다. 분류 결과는 축 후보로 쓸 수 있으나, 그 자체가 검증은 아니다. | [원문](https://doi.org/10.1016/j.techfore.2024.123536) |

### 옵션 5. 채점 대상이 칸이 아닌 예측

신흥 기술을 정의하거나, 성장 곡선과 수명주기를 맞히거나, 유망 특허를 일찍 고른다. 사후 채점의 습관은 3-2에 있다. 여기는 채점 대상이 가능 칸과 불가능 칸이 아닌 경우이다.

| 연도 | 저널 | 제목 | 핵심 내용 | 이 연구에서의 위치 | 원문 |
|---:|---|---|---|---|---|
| 2006 | Technological Forecasting and Social Change | Forecasting emerging technologies: Use of bibliometrics and patent analysis | 과거 시계열이 없는 신기술에 대해 논문·특허 건수 곡선을 성장 곡선, 유추, 시나리오, 시스템 다이내믹스의 입력으로 넣는 전망 절차를 제시한다. | 특허를 전망의 입력으로 쓰는 고전이다. 전망이 맞았는지를 가능 공간의 칸으로 재지는 않는다. | [원문](https://doi.org/10.1016/j.techfore.2006.04.004) |
| 2008 | Technovation | Detecting emerging research fronts based on topological measures in citation networks of scientific publications | 논문 인용 네트워크를 위상 군집으로 나누고, 군집 안 중심성과 군집 사이 참여도로 떠오르는 연구 전선이 갈라지는지 점진적인지를 구분한다. | 떠오름을 그물 구조로 보는 선례다. 떠오름과 ‘가능한데 아직 없는 칸’은 다른 개념이다. | [원문](https://doi.org/10.1016/j.technovation.2008.03.009) |
| 2013 | PLoS ONE | Statistical Basis for Predicting Technological Progress | 기술 비용 하락의 대표 법칙들을 62개 기술 데이터에서 사후 예측으로 비교해, 라이트 법칙과 무어 법칙의 예측 오차가 거의 같음을 보고한다. | 기술 예측 모형도 데이터로 비교해야 한다는 근거다. 이 연구는 비용 법칙을 쓰지 않는다. | [원문](https://doi.org/10.1371/journal.pone.0052669) |
| 2014 | Research Policy | The Emerging Clusters Model: A tool for identifying emerging technologies across multiple patent systems | 여러 특허청의 인용으로 기술 군집을 만들고, 미래 인용을 쓰지 않은 채 당시 시점의 인용 증가만으로 신흥 기술을 탐지하는 모형을 정의한다. | 떠오름을 늦게 회고하지 않고 일찍 보려는 예다. 이 연구는 일찍 보는 것과 별도로, 과거 창으로 맞았는지를 확인한다. | [원문](https://doi.org/10.1016/j.respol.2014.06.006) |
| 2015 | Research Policy | What is an emerging technology? | 신흥 기술을 급진적 새로움, 비교적 빠른 성장, 일관성, 두드러진 영향, 불확실성·모호성 다섯 속성으로 정의하고, 속성별 문헌·특허 지표를 대응시킨다. | ‘신흥’이라는 말을 함부로 쓰지 말라는 기준이다. 이 연구의 빈 칸도 정의를 먼저 고정한다. | [원문](https://doi.org/10.1016/j.respol.2015.06.006) |
| 2016 | Research Policy | How predictable is technological progress? | 기술 비용의 기하급수 하락을 추세가 있는 확률보행으로 정식화하고, 53개 기술에서 예측 오차 분포가 예측 기간에 따라 어떻게 넓어지는지 닫힌 형태로 유도한다. | 예측 오차를 식으로 두는 예다. 이 연구의 오차는 비용이 아니라, 칸을 잘못 열거나 잘못 닫은 비율이다. | [원문](https://doi.org/10.1016/j.respol.2015.11.001) |
| 2016 | Technological Forecasting and Social Change | Stochastic technology life cycle analysis using multiple patent indicators | 기술 수명주기를 단일 건수 곡선의 적합으로 추정하지 않고, 여러 특허 지표를 숨은 마르코프 모형에 넣어 단계 확률로 추정한다. | 한 지표만으로 단계를 단정하지 말라는 선례다. 이 연구도 지표를 여러 개 같이 본다. | [원문](https://doi.org/10.1016/j.techfore.2016.01.024) |
| 2017 | Technological Forecasting and Social Change | Early identification of emerging technologies: A machine learning approach using multiple patent indicators | 인용이 쌓이기 전의 특허 지표만으로 신흥 기술을 식별하고, 나중에 인용으로 확인되는 신흥 기술과 비교해 조기 식별 성능을 보고한다. | 늦은 지표(인용)에만 기대지 말라는 선례다. 사후 확인은 인용 축적이 아니라 이후 특허의 칸 점유로 한다. | [원문](https://doi.org/10.1016/j.techfore.2017.10.002) |
| 2018 | Technological Forecasting and Social Change | Emergence scoring to identify frontier R&D topics and key players | 초록 용어의 신규성, 성장, 공동체 규모, 지속을 합쳐 출현 점수를 정의하고, 점수가 높은 용어를 프론티어 주제로, 그 용어를 많이 쓴 기관을 주요 주체로 출력한다. | 용어 점수로 프론티어를 표시하는 예다. 용어 점수는 칸의 제약 검사와 다르다. | [원문](https://doi.org/10.1016/j.techfore.2018.04.016) |
| 2020 | Scientometrics | Identification of promising inventions considering the quality of knowledge accumulation: a machine learning approach | 유망 발명 식별의 입력에 후방 인용 개수 대신 인용된 지식의 질을 넣고, 질 지표를 넣은 기계학습이 개수만 넣은 모형보다 나은지 비교한다. | 유망 특허를 고르는 예다. 이 연구는 유망 특허 순위 대신, 그 특허가 어느 칸에 들어가는지를 본다. | [원문](https://doi.org/10.1007/s11192-020-03710-3) |
| 2020 | Scientometrics | Forecasting emerging technologies using data augmentation and deep learning | 신흥 기술 라벨이 있는 특허가 적을 때 생성 모형으로 학습 표본을 늘린 뒤 딥러닝으로 신흥 기술을 예측하고, 증강 전후의 성능을 비교한다. | 표본이 작을 때의 예측 기법이다. 증강된 표본에 미래 정보가 섞이지 않았는지를 따로 봐야 한다. | [원문](https://doi.org/10.1007/s11192-020-03351-6) |
| 2022 | foresight | Forecasting future bigrams and promising patents: introducing text-based link prediction | 특허 본문의 단어쌍을 노드로 두고 아직 자주 같이 나오지 않는 단어쌍의 미래 증가를 링크 예측으로 계산해, 그 단어쌍을 포함한 특허를 유망 특허 후보로 고른다. | 본문 예측으로 유망 특허를 고르는 예다. 이 연구는 단어쌍의 유행이 아니라 조합 칸의 실현을 확인한다. | [원문](https://doi.org/10.1108/fs-03-2021-0078) |
| 2024 | Scientometrics | A novel technology life cycle analysis method based on LSTM and CRF | 여러 특허 지표의 시간 순서를 순환 신경망과 조건부 랜덤필드에 넣어, 곡선 적합 없이 기술 수명주기 단계와 다음 해의 단계 전이를 판정한다. | 수명주기를 서열 모형으로 보는 최근 예다. 수명주기 단계와 가능 공간의 빈 칸은 다른 질문이다. | [원문](https://doi.org/10.1007/s11192-024-04946-z) |
| 2024 | Technological Forecasting and Social Change | An exploration method for technology forecasting that combines link prediction with graph embedding: A case study on blockchain | 특허 키워드 공출현 그래프에서 링크 예측으로 미래 기술 그래프를 만들고, 그래프 임베딩과 군집으로 앞으로의 기술 주제를 가시화한다. | 한 분야에 예측 도구를 적용한 최근 사례다. 적용 후에 과거 창으로 맞았는지를 보고한 설계는 드물다. | [원문](https://doi.org/10.1016/j.techfore.2024.123736) |

---

## 그래서 이 연구가 메우는 자리

필수 세 항목을 모아 보면, 빠져 있는 일은 한 가지로 모인다.

1. 특허로 항목과 선택지를 만들어 칸을 만든다. 단위와 비교 대상은 1항이 이미 준다. 항목을 뽑는 도구는 옵션 2와 옵션 4에서 바꿀 수 있다.
2. 같이 쓸 수 없는 쌍을 지워 가능 공간을 닫는다. 절차는 2항에 있다. 입력이 특허인 경우는 거의 없다.
3. 그 공간이 읽기에 나은지 숫자로 비교한다. 이름의 출처는 3-1이다. 특허 칸에 붙은 계산은 거의 없다.
4. 과거 시점의 공간이 이후 특허와 맞는지 확인한다. 채점 습관과, 이후 자료를 학습에 넣으면 안 된다는 규칙은 3-2에 있다. 채점 대상이 가능 칸과 불가능 칸인 경우는 없다.

이 네 가지를 **한 번에, 같은 특허, 같은 규칙으로** 하는 연구가 비어 있다. 이 프로젝트는 그 빈자리를 메운다.

하지 않는 일도 위 논문들이 경계를 정해 준다.

- 빈 칸을 전부 기회로 발표하지 않는다. (1항의 한계)
- 다음 융합 점수나 유망 특허 하나를 결과로 내지 않는다. (옵션 3, 옵션 5)
- 벡터 그물을 시나리오 공간이라고 부르지 않는다. (옵션 4)
- 생성 모형으로 미래 이야기를 쓰지 않는다. (3-1)
- 지도를 만든 시점 이후의 특허로 지도를 다시 학습하지 않는다. (3-2의 Kapoor)
