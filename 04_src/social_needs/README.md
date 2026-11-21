# 소농 사회적 수요 분석

LSMS-ISA 조화 패널(`05_data/agri/lsms-worldbank/`)로 소규모·저소비·고가족노동 농가를 식별하고 비교집단과 대조한다. 원자료는 읽기만 한다. 보고서와 표, 그림은 `01_paper/2026-winter/social-needs/`에 둔다.

실행은 conda 환경 `scenario-space`에서 한다.

```bash
conda activate scenario-space
cd 04_src/social_needs
python audit_build.py
python analyze.py
```

`audit_build.py`가 가구-계절 프레임을 `out/hh_season.pkl`에 만들고, `analyze.py`가 최근 비교 가능한 회차를 가구 단위로 합쳐 집단, 회귀, 표를 만든다. `out/`은 git에서 빠진다. `statsmodels`가 회귀의 군집 표준오차에 쓰인다.

| 스크립트 | 역할 |
|---|---|
| `config.py` | 경로, 면적·노동 화면 |
| `audit_build.py` | 키·결측·상수성 검증, 필지를 가구-계절로 합산 |
| `analyze.py` | 집단 정의, 비교, 회귀, Alkire–Foster, 그림 |
