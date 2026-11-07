# 필요와 혁신 대응 — 대응 규칙의 원문

> 2026-11-03. 사회적 필요와 혁신 대응을 어떻게 대응시키는지를 기관 원문이 적어 둔 폴더다.
> 농식품 사례 자료는 [../food-agriculture/README.md](../food-agriculture/README.md)에 있다. 이 폴더의 셋 중 FAO 논문만 농식품 특허를 다루고, 나머지 둘은 지속가능발전목표 전반의 대응 규칙이다.
> PDF는 Git에 올리지 않는다. 아래 링크가 공식 원문이다.

| 파일 | 원문 | 무엇이 무엇에 대응되는가 |
|---|---|---|
| `2025_fao_sdg-indicators-progress.pdf` | FAO. 2025. *Tracking progress on food and agriculture-related SDG indicators 2025.* [DOI 10.4060/cd5832en](https://doi.org/10.4060/cd5832en) | 관리 지표 22개를 지표별로 본다. 목표 2만 달성 거리의 종합 점수가 있고, 사람 수의 필요는 2.1.1과 2.1.2다. 정리는 [fao-need-indicators.md](fao-need-indicators.md). |
| `2025_schmallenbach_research-disease-burden.pdf` | Schmallenbach 등. 2025. *Nature Medicine* 31(9), 3101–3109. [DOI 10.1038/s41591-025-03923-0](https://doi.org/10.1038/s41591-025-03923-0) | 질병별 논문 비중과 DALY 비중을 비교한다. 어긋남은 Kullback–Leibler 발산이다. 읽는 노트는 `03_literature/need_response_measurement.md`. GPT-4o로 MeSH·소속·사사를 표준 범주에 붙이고 사람이 검증한 절차는 `03_literature/llm_standardization.md`. |
| `2026-03_wipo_ipc-technology.csv` | WIPO IPC–Technology Concordance, 2026년 3월판. 공식 파일은 같은 폴더의 `2026-03_wipo_ipc-technology.xlsx`. 받은 주소는 [ipc_technology.xlsx](https://www.wipo.int/documents/2948119/3215563/ipc_technology.xlsx). 방법 설명은 `2008_wipo_ipc-technology-concept.pdf`, [공개 쪽](https://www.wipo.int/en/web/ip-statistics). | IPC 기호 하나를 35개 기술 분야, 5개 상위 부문 중 하나에만 붙인다. 771행. SDG로 넘기는 열은 없다. |
| `2026-08_wipo_ipc-green-technology.csv` | WIPO Green Technology Inventory for Statistical Use, 2026년 8월판. 공식 파일은 `2026-08_wipo_ipc-green-technology.xlsx`. 받은 주소는 [green-ipc-technology.xlsx](https://www.wipo.int/documents/d/ip-statistics/docs-en-green-ipc-technology.xlsx). 방법 설명은 `2026_wipo_ipc-green-technology-method.pdf`, [공개 쪽](https://www.wipo.int/en/web/ip-statistics). | IPC를 녹색기술 5개 부문, 36개 기술에 붙인다. 한 기술에 IPC가 여러 개고, 한 IPC가 여러 기술에 나올 수 있다. `Y02`는 이 표에 없다. |
| `2026_fao-gerits_agrifood-patent-taxonomy.pdf` | Gerits, H., Mongeau, C., Zhang, Y., Pesce, V., Fabi, C., Chuluunbaatar, D. 2026. *New insights on agricultural innovation paths based on a data-driven taxonomy of technologies.* FAO. ICAS 회의 논문, 12쪽. [PDF](https://www.isi-next.org/media/abstracts/icas-x-2026_fcab78ef6ff3b86d8c02e5609b736239.pdf). 기관 설명은 [FAO 데이터랩](https://www.fao.org/datalab/ai-and-innovation/technology-and-innovation-mapping/en) | 특허 제목·초록에서 기술(어떻게)과 용도(무엇을 위해, “To …”로 시작하는 문장)를 분리한다. 용도의 맨 위는 식품 가치사슬 단계다. 얇음은 이렇게 묶인 용도 칸의 특허가 적은 자리다. ATIO 지식베이스의 데이터 기반 분류층이다. |
| `2021_un-iatt_sti-sdg-roadmaps.pdf` | UN IATT. 2021. *Guidebook for the Preparation of Science, Technology and Innovation for SDGs Roadmaps.* [PDF](https://sdgs.un.org/sites/default/files/2021-06/GUIDEBOOK_COMPLETE_V03.pdf) | 나라의 SDG 격차와 과학기술혁신 역량·기술·병목을 로드맵의 현재 진단 단계에서 함께 본다. 특허를 목표에 붙이는 검색식은 없다. |

17개 목표 전체는 [sdgs.md](sdgs.md)에 있다. FAO가 지표를 관리하는 목표는 2, 5, 6, 12, 14, 15다. 빈곤 목표(1)에는 관리 지표가 없고, 토지 보유권(1.4.2)과 재해 경제 손실(1.5.2)에 기여 기관이다.

FAO STI 포털이 혁신 하나에 유형과 용도를 같이 붙이는 분류는 사례 폴더의 `food-agriculture/fao/sti-portal-taxonomies/`에 있다. 포털은 용도를 혁신이 어떤 필요에 쓰이는가로 정의하고, 아직 논의 중이라고 적는다.
