# 필요와 대응의 불균형 — 측정한 선행연구

> 2026-11-03. 사회적 필요의 크기와 혁신 대응의 양을 비교한 연구다. 확인된 직접 비교는 보건이다.
> 필요의 단위는 질병 부담(DALY)이고, 대응의 단위는 논문, 연구비, 제품 개발 투자다. 특허 건수를 필요와 나눈 식은 여기 없다.
> 서지: [bib/06_need_response.bib](bib/06_need_response.bib).
> 전환 정책의 실패 이름은 [transformative_innovation_policy.md](transformative_innovation_policy.md). 원문 PDF가 있는 것은 1번뿐이고, 파일은 `06_references/need-response/`에 있다.

네 편은 같은 비교를 다른 강도로 한다. 1번과 2번은 질병별 부담 비중과 논문 비중을 나란히 놓는다. 3번은 투자액, 논문 수, DALY를 질병별로 같이 보여 주되, 하나의 불균형 지수로 닫지 않는다. 4번은 부담이 크다는 것만으로 투자가 부족하다고 말하지 않는다.

## 1. Schmallenbach 등 (2025)

Leo Schmallenbach, Maximilian Bley, Till W. Bärnighausen, Cassidy R. Sugimoto, Carolin Lerchenmüller, Marc J. Lerchenmüller. Global distribution of research efforts, disease burden, and impact of US public funding withdrawal. *Nature Medicine* 31(9), 3101–3109. [DOI 10.1038/s41591-025-03923-0](https://doi.org/10.1038/s41591-025-03923-0). 로컬 PDF `06_references/need-response/2025_schmallenbach_research-disease-burden.pdf`.

MeSH를 GBD 원인에 붙이고, 소속·사사 문자열에서 국가를 뽑을 때 GPT-4o를 쓰고 사람 표본으로 검증한 절차는 [llm_standardization.md](llm_standardization.md)에 따로 두었다. 그 절차는 보건 밖에서도 엔티티와 관계를 표준 이름에 붙일 때 참조한다.

질병별 논문 860만 건을 세계질병부담의 DALY와 연결한다. 비교는 논문 수와 DALY 원단위가 아니라, 그 질병이 전체 논문에서 차지하는 비중과 전체 DALY에서 차지하는 비중이다. 두 비중 분포의 어긋남은 Kullback–Leibler 발산으로 센다. 단면으로 보면 신생물, 신경계, 소화기 질환은 논문 비중이 부담 비중보다 크고, 심혈관, 모성·신생아, 호흡기 감염은 논문 비중이 작다. 1999–2019년에 발산이 줄었는데, 논문이 부담을 따라가서가 아니라 감염성 질병의 부담이 줄어서라고 적는다.

## 2. Yegros-Yegros 등 (2020)

Alfredo Yegros-Yegros, Wouter van de Klippe, Maria Francisca Abad-García, Ismael Rafols. Exploring why global health needs are unmet by research efforts: the potential influences of geography, industry and publication incentives. *Health Research Policy and Systems* 18, 47. [DOI 10.1186/s12961-020-00560-6](https://doi.org/10.1186/s12961-020-00560-6).

필요는 WHO 세계질병부담의 DALY, 대응은 MEDLINE 논문이다. ICD-10과 MeSH를 대응시켜 질병 부담과 논문이 같은 질병을 가리키게 한다. 고소득국에 부담이 큰 질병이 저소득국에 부담이 큰 질병보다 연구 관심이 약 열 배라고 적는다. 공공 연구의 질병 분포는 제약 산업 연구와 비슷하다. 본문은 부담과 연구가 일대일로 같아야 한다고 보지 않는다. 부담을 줄이는 일이 연구만으로 되는 것은 아니고, 이미 있는 해법이 현장에 닿지 않는 경우도 있다고 적는다.

## 3. WHO 세계보건연구개발관측소

WHO Global Observatory on Health R&D. Investments on R&D for product development and publications volume compared to DALYs for neglected diseases. [페이지](https://www.who.int/observatories/global-observatory-on-health-research-and-development/benchmarking/investments-on-r-d-for-product-development-and-publications-volume-compared-to-dalys-for-neglected-diseases).

소외질환에 대해 세 열을 같이 둔다. 2007–2016년 제품 관련 연구개발비의 연평균, 같은 기간 논문 수의 연평균, 2015년 DALY다. 투자 자료는 G-FINDER이고, 범위가 제품 개발로 좁다고 주의한다. 주혈흡충은 그 묶음에서 부담이 큰데 DALY당 투자는 7.0달러이고, 샤가스는 87.4달러라고 예시한다. 투자액과 논문 수가 같이 움직이지 않는 예도 적는다. 목적은 관계를 볼 지표를 생각하게 하는 것이고, 하나의 공식으로 불균형을 판정하지 않는다.

## 4. 미국 국립학술원 (2025)

National Academies of Sciences, Engineering, and Medicine. *Aligning investments in therapeutic development with therapeutic need: Closing the gap.* Washington, DC: National Academies Press. [DOI 10.17226/29157](https://doi.org/10.17226/29157). 개념 장은 [2장](https://nap.nationalacademies.org/read/29157/chapter/4)이다.

치료 영역의 과소투자는 세 조건이 같이 있을 때라고 둔다. 질병 부담이 크고, 있는 치료로 그 부담이 충분히 줄지 않으며, 치료제 개발 투자가 그 미충족 필요에 비해 부족하다. 부담의 측정은 하나라고 보지 않는다. 역학, 경제 부담, 건강 관련 삶의 질이 서로 다른 가치 판단을 넣고, 위원회는 단일 지표를 새로 만들지 않는다. 특허나 투자가 적다는 사실만으로 혁신이 부족하다고 두지 않는 이유가 여기 있다. 접근이 안 되는 것은 이 보고서의 미충족 필요에서 뺀다. 초점은 치료 혁신이지 보건 연구 전체가 아니다.

## 5. FAO 지표에는 DALY에 해당하는 공통 단위가 없다

DALY가 질병 목록 전체의 필요를 한 단위로 만드는 것과 같은 지표는, FAO가 관리하거나 기여하는 SDG 지표 안에 없다. 사람 수로 공식 발표되는 필요는 영양부족(2.1.1)과 식량불안정(2.1.2)이고, 목표 2의 종합 점수는 달성까지의 거리다. 근거와 2024년 수치는 [../06_references/need-response/fao-need-indicators.md](../06_references/need-response/fao-need-indicators.md).
