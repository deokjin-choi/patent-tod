# 결과 분석 (방법론과 분리)

`10_build_features.py` … `80_*.py` 는 계산 경로다. 이 폴더는 **산출물을 읽고 해석·논문용 그림을 그린다.**
파이프라인 진행 상태는 `../docs/04_run_status.md` (2026-09-03: 1–8 실행됨, 다음은 창 그룹 접힘 민감도와 표시 그래프 다양성).
여기 스크립트가 `out/`을 덮어쓰거나 단계 스크립트를 import 하지 않는다. `_diag_50.py`는 예외로 단계 모듈을 읽어 50공간 진단을 찍는다.

```bash
conda activate scenario-space
python analysis/a20_soft_membership.py
```
