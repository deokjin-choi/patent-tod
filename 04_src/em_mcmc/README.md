# EM / MCMC 검증 골격

이 폴더는 **준 글**(CASI의 EM·MCMC를 시나리오 공간에 연결하는 메모)을
작은 Edge AI 코퍼스에서 **그대로 돌려 보는 실험**이다.

FL 파일럿, PSE 그래프, 임베딩, Autoencoder는 쓰지 않는다.

## 이 골격이 검증하는 네 문장

1. 가장 기본 데이터는 **키워드 빈도 벡터**다 (TF 카운트 + CPC 0/1 + 피인용).
2. **EM**은 특허를 미리 정한 시나리오 셀에 **확률로 얹는다**.
3. **MCMC**는 (a) 특허를 기술 원천의 혼합체로 분해하고, (b) 양립 제약을 반영해 가능 셀을 샘플한다.
4. 샘플·점유의 경험적 분포로 **Coverage / Balance / Diversity**를 재고, 열린 조합 공간에는 **missing-species (Chao1)** 를 붙인다.

축은 글에서 든 Edge AI 예시를 그대로 쓴다: **저전력, 경량화, 실시간성**.

## 돌리는 법

저장소 공통: 먼저 conda 환경 `scenario-space` 를 켠다. 루트 `README.md` 실행 환경과 같다.

```bash
conda activate scenario-space
cd em_mcmc
python run_all.py
```

numpy는 이 환경에 있으면 된다. 원본 `data/edge-ai-all-2010-2025.csv`에서 초록 있는 행 400건을
시드 42로 뽑아 `em_mcmc/data/patents.csv`에 둔다. 두 번째부터는 같은 파일을 다시 쓴다
(`00_prepare_data.py`는 매번 다시 샘플한다).

단계만 따로:

```bash
python 00_prepare_data.py   # 400건 샘플
python 01_build_matrix.py   # 키워드 행렬
python 02_run_em.py         # 셀 확률 매핑
python 03_run_mcmc.py       # 혼합 + 제약 샘플
python 04_quality.py        # 지표 + ASCII 리포트
python plot_results.py      # figures/ PNG (이미 out/ 이 있을 때)
python run_pse_review.py    # modify JSON 슬롯 집계 → out_pse/
python run_kg_v1_review.py  # knowledge_graph v1 head 집계 → out_kg_v1/
python run_kg_em.py         # v1 관계=축, 혼합으로 수준·소프트 셀 → out_kg_em/
```

끝난 뒤 볼 것: [docs/results.md](docs/results.md) (그림 해석), `out/04_report.txt`.

## 첫 실행에서 나온 것 (시드 42, n=400)

이 숫자는 버그가 아니라, 글의 방법을 **랜덤 Edge AI 400건 + 작은 사전**에 얹으면 생기는 모습이다.

- 키워드가 1개라도 걸린 문헌: **89 / 400**. 나머지 311은 사전에 안 걸림 → EM에서 `unmapped`.
- 가설 쌍 `high × compact` 공출현 **0건** → MCMC가 그 칸을 거의 죽임 (coverage 8→6).
- 키워드 지문 37종, Chao1 ≈ 133, 다음 문헌이 새 지문일 확률 ≈ 0.27.
- 자세한 막대는 `out/04_report.txt`.


## 읽을 순서

1. [docs/concept.md](docs/concept.md) — 각 단계가 무엇을 하고, 무엇을 기대해도 되는지 (ASCII)
2. [docs/results.md](docs/results.md) — 이번 실행 그림과 해석
3. [docs/outputs.md](docs/outputs.md) — 산출 파일 ↔ 해석 (그림 링크 포함)
4. [docs/pse_slot_review.md](docs/pse_slot_review.md) — modify JSON 1,412건 슬롯 검토
5. [docs/kg_v1_review.md](docs/kg_v1_review.md) — knowledge_graph v1 only, head로 보기 후보 (축)
6. [docs/kg_em_review.md](docs/kg_em_review.md) — 관계 4개=축, 혼합 EM으로 수준·소프트 셀
7. [data/README.md](data/README.md) — 데이터 층

## 폴더

```
em_mcmc/
  data/           사전, 제약, 샘플 특허
  docs/           개념과 산출물 안내
  out/            실행 결과 (재생성)
  00_prepare_data.py
  01_build_matrix.py
  02_run_em.py
  03_run_mcmc.py
  04_quality.py
  run_all.py
  run_pse_review.py     # modify JSON 칸별 집계
  run_kg_v1_review.py   # v1 목적어 head 집계
  run_kg_em.py          # 축별 혼합 + 셀 소프트 맵
  out_pse/ figures_pse/
  out_kg_v1/ figures_kg_v1/
  out_kg_em/ figures_kg_em/
```
