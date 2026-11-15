"""과일·채소 수확 특허 매핑 설정. 경로는 저장소 루트 기준이다."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]

SOURCE_CSV = REPO / "05_data" / "agri" / "Planting_harvesting_storage_US.csv"

DATA = REPO / "05_data" / "agri" / "fv_harvest"
SCOPE_CSV = DATA / "scope.csv"
FULLTEXT_DIR = DATA / "fulltext"
RAW_HTML_DIR = DATA / "raw_html"
FETCH_LOG = DATA / "fetch_log.csv"
LLM_INPUT_DIR = DATA / "llm_input"

PROMPT_DIR = ROOT / "prompts"
# 예전 버전을 다시 돌릴 때: PROMPT_VERSION=v2 conda run -n scenario-space python ...
PROMPT_VERSION = os.environ.get("PROMPT_VERSION", "v5")
TASK = "fv_harvest"

# v3부터 독립 청구항을 본문 앞에 붙인다. 청구항은 발명의 경계를, 본문은 그 부품이 하는 일을 알려 준다.
INDEPENDENT_CLAIMS_IN_INPUT = PROMPT_VERSION not in ("v1", "v2")
# v4부터 카드의 청구항 표시를 매핑 전에 코드로 바로잡는다(claim_check.py).
# v5는 매핑 프롬프트만 고쳤다(F1 순서 편향). 카드 프롬프트는 v4와 같다.
VERIFY_CLAIM_TAGS = PROMPT_VERSION not in ("v1", "v2", "v3")
# 독립 청구항 묶음의 최대 글자 수. 넘으면 뒤를 자른다.
CLAIMS_MAX_CHARS = 4_000

# 프롬프트에 넣는 특허 본문의 최대 글자 수. 넘으면 배경기술 절을 앞부분만 남기고, 그래도 넘으면 뒤를 자른다.
MAX_PATENT_CHARS = 200_000
# 줄일 때 남기는 배경기술 절의 글자 수. 발명이 풀려는 문제는 대개 배경기술 절에 적혀 있다.
BACKGROUND_KEEP_CHARS = 3_000
BACKGROUND_HEADINGS = ("BACKGROUND", "PRIOR ART", "DESCRIPTION OF RELATED ART", "RELATED ART")

# 과일·채소 수확으로 보는 CPC 범위. 접두 일치로 판정한다.
# 출처: USPTO CPC scheme A01D (https://www.uspto.gov/web/patents/classification/cpc/html/cpc-A01D.html)
SCOPE_GROUPS: dict[str, dict[str, list[str]]] = {
    # A01D46: 과일·채소 따기, 나무·관목 털기. 목화(46/08–46/18)는 뺀다.
    "picking": {
        "include": ["A01D46/", "A01D2046/"],
        "exclude": [
            "A01D46/08", "A01D46/10", "A01D46/12", "A01D46/14", "A01D46/16", "A01D46/18",
        ],
    },
    # A01D45: 서 있는 작물의 수확 가운데 과일·채소 하위 그룹만.
    "standing_vegetable": {
        "include": [
            "A01D45/001",  # 작업자 운반 장치
            "A01D45/002",  # 파인애플
            "A01D45/006",  # 토마토
            "A01D45/007",  # 아스파라거스
            "A01D45/008",  # 오이
            "A01D45/22",   # 콩
            "A01D45/24",   # 완두
            "A01D45/26",   # 양배추·상추·방울양배추
            "A01D45/28",   # 시금치
        ],
        "exclude": [],
    },
    # A01D13–33: 뿌리작물 캐기. 땅콩(A01D29)은 뺀다.
    "root_crop": {
        "include": [
            "A01D13/", "A01D15/", "A01D17/", "A01D19/", "A01D21/", "A01D23/",
            "A01D25/", "A01D27/", "A01D31/", "A01D33/",
        ],
        "exclude": [],
    },
    # A01D51: 땅에 떨어진 작물 모으기 가운데 사과·견과, 감자·비트 적재.
    "ground_gathering": {
        "include": ["A01D51/002", "A01D51/005"],
        "exclude": [],
    },
}

# Google Patents 요청 간격(초). 연속 요청이면 차단되므로 1초 이상을 지킨다.
REQUEST_INTERVAL_SEC = 1.0
REQUEST_TIMEOUT_SEC = 30
MAX_RETRIES = 4
BACKOFF_BASE_SEC = 30.0
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
)
