# Federated learning pilot slice

Edge AI 코퍼스에서 federated learning 관련 문헌만 모은 작업 폴더.

- 원본: `data/edge-ai-all-2010-2025.csv` (50,000건)
- 유지: **4,467**건 (제목 매칭 3,467 / 초록만 매칭 1,000)
- raw 서지 복사: `2,590` → `fetched/`
- PSE 그래프 복사: `264` → `pse/`

포함: federated/federal/federation learning, FedAvg/FedProx, vertical/horizontal/hierarchical federated, 연합학습.
제외: MEC federation, federated neutral host (학습이 아닌 연합).

검색 규칙과 연도·관할 집계는 `filter.json`.
손코딩·미니 파일럿은 `patents_slim.csv`를 쓰는 편이 낫다.

Python은 루트 README와 같이 `conda activate scenario-space` 다음 실행한다.
