# data/

이 폴더의 행은 **문헌**이다. 시나리오 공간 자체가 아니다.

```
dictionary.json     축·수준·키워드 문구 (사람이 잠근 사전)
constraints.json    가설 양립 금지 쌍 (아직 사실이 아님)
patents.csv         원본 Lens export에서 뽑은 400건 (실행 후 생김)
manifest.json       샘플 규칙, 시드, 원본 경로 (실행 후 생김)
```

`patents.csv`는 FL 슬라이스가 아니다. 초록이 있는 Edge AI 문헌을
reservoir sample로 골랐다. 다시 뽑으려면 `python3 00_prepare_data.py`.

열:

| 열 | 쓰는 곳 |
|---|---|
| display_key | 감사 키 |
| title, abstract | 키워드 카운트 |
| cpc | 이진 접두 플래그 |
| cited_by | 영향력 숫자 (행렬에 붙임, 모형 가중치는 아직 아님) |
| priority_date / year | 나중 시간창용. 이번 골격은 안 씀 |

임베딩 파일은 두지 않는다. 기본형은 희소 카운트다.
