"""scenario_pipeline 전역 설정.

모든 결정값은 이 파일에만 둔다. 스크립트 안에 숫자를 박지 않는다.
2026-08-29 잠김. 계약은 docs/03_locked_spec.md, 근거는 docs/01_open_decisions.md.
D7(LLM 명명)만 계산 경로 밖이라 LLM_PROVIDER=None.
"""

from pathlib import Path

# --------------------------------------------------------------------------
# 경로
# --------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent

PSE_KG_DIR = ROOT / "data" / "pse_knowlege_graph_modifiy"
STD_DIR = ROOT / "data" / "knowlege_graph_entity_relation"

STD_RESULTS = STD_DIR / "final_standardization_results.json"
ENTITY_EMB = STD_DIR / "Entity_embeddings.npy"          # (28755, 768)
SUBREL_EMB = STD_DIR / "Sub_Relation_embeddings.npy"    # (2634, 768)
KG1REL_EMB = STD_DIR / "KG1_Relations_embeddings.npy"   # (4, 768)

LENS_CSV = ROOT / "data" / "edge-ai-all-2010-2025.csv"  # 1412건 중 404건만 매칭 (D2)

OUT = HERE / "out"
FIG = HERE / "figures"

SEED = 42

# --------------------------------------------------------------------------
# 단계 1 — 벡터 입력
# --------------------------------------------------------------------------

PSE_SLOTS = (
    "problem",
    "solution_function",
    "solution_structure",
    "solution_implementation",
    "effect",
)

# D4 확정(2026-08-29): 신경 인코더 사용. "tfidf_svd" 는 대조군으로만 유지
TEXT_ENCODER = "sentence_transformer"

# 기존 Entity/Sub_Relation 임베딩이 768d 이므로 같은 차원 인코더를 쓴다
ST_MODEL = "sentence-transformers/all-mpnet-base-v2"   # 768d
ST_FALLBACK = "sentence-transformers/all-MiniLM-L6-v2"  # 384d, 다운로드 실패 시
ST_DIM = 768
ST_BATCH = 32
ST_NORMALIZE = True         # 슬롯별 임베딩 L2 정규화

# TEXT_ENCODER == "tfidf_svd" 인 대조군 실행에만 쓰이는 값
TXT_DIM = 128               # 슬롯당 차원. 5슬롯 concat -> 640
TFIDF_MIN_DF = 3
TFIDF_MAX_DF = 0.6
TFIDF_NGRAM = (1, 2)

KG_TRIPLE_POOL = "mean"      # 트리플 벡터 [e_h; e_r; e_t] 의 특허 단위 pooling
KG_DIM = 128                 # 2304 -> PCA 축소

CPC_LEVEL = "subclass"       # subclass = 113종. "full"(2679종)은 초희소하여 비권장
CPC_MISSING_FLAG = True

BLOCK_WEIGHTS = {"TXT": 1.0, "KG": 1.0, "CPC": 1.0}

# PoC N=1412. GMM(diag) 예산: K_eff <= N/(4d).
# 유효 K 8~15를 열려면 d <= 1412/(4*8)=44, 상한 K=12를 열려면 d <= 29.4.
# d=30 → K<=11.8. 복원 60%는 d≈82·K<=4 가 되어 PoC에서 쓰지 않는다.
PCA_DIM = 30
PCA_MIN_EXPLAINED = 0.35     # 붕괴 하한. 복원 목표가 아님. 실측 30d ≈ 0.42

# --------------------------------------------------------------------------
# 단계 2 — 베이지안 GMM
# --------------------------------------------------------------------------

K_MAX = 30                   # DP 절삭 상한. "그룹이 30개"라는 뜻이 아니다
COVARIANCE_TYPE = "diag"     # N=1412 에서 full 은 불가
WEIGHT_CONCENTRATION_PRIOR_TYPE = "dirichlet_process"
WEIGHT_CONCENTRATION_PRIOR = 1.0 / K_MAX
N_INIT = 10
MAX_ITER = 1000
TOL = 1e-3

MIN_GROUP_WEIGHT = 1.0 / (2 * K_MAX)   # 유효 그룹 판정
MIN_GROUP_PATENTS = 20
STABILITY_SEEDS = (42, 43, 44, 45, 46)
ARI_GATE = 0.60

# --------------------------------------------------------------------------
# 단계 3 — LLM 명명 (계산 경로 아님. 라벨만, 이후 수식은 읽지 않는다)
# --------------------------------------------------------------------------

NAME_TOP_CENTRAL = 5         # 그룹 중심(마할라노비스) 최근접
NAME_N_FAR_LARGE = 2         # 큰 그룹만 중심에서 먼 특허
NAME_N_LARGE_GROUPS = 2      # n_hard 기준 상위 그룹 수
NAME_TOP_ENTITIES = 8        # 대표 특허 KG에서 자주 나온 표면 엔티티
NAME_PSE_CHARS = 360         # 슬롯당 프롬프트 최대 문자
LLM_PROVIDER = "ollama"
LLM_MODEL = "mistral:latest"
OLLAMA_URL = "http://127.0.0.1:11434"
LLM_TEMPERATURE = 0.0

# --------------------------------------------------------------------------
# 단계 4 — 시간축
# --------------------------------------------------------------------------

DATE_FIELD = "filing_date"   # publication_date 는 민감도 분석
WINDOWS = {                  # filing 기준. 2018 이전 55건, 2025 6건은 제외
    "W1": (2019, 2020),
    "W2": (2021, 2022),
    "W3": (2023, 2024),
}
TREND_WINDOW_LAST = "W3"
DIRICHLET_ALPHA0 = 1.0
TREND_MODE = "persistence"   # "linear" 는 창 3개로 과적합 위험 -> 민감도용

# --------------------------------------------------------------------------
# 단계 5 — feasibility 모델
# --------------------------------------------------------------------------

FEAS_PATH = "A_fixed_emb_logreg"   # A | B_torch_mlp | C_cluster_pmi
EMB_DIM = 64                       # 768 -> PCA
FEAT_BLOCKS = ("hrt", "ht", "hr", "rt")   # phi(h,r,t)
LOGREG_C = 1.0
LOGREG_MAX_ITER = 2000

NEG_RATIO = 5
NEG_MIX = {"tail": 0.4, "head": 0.4, "relation": 0.2}
NEG_RELATION_LEVEL = "surface"     # 표면 2634종 수준에서 교체
NEG_EXCLUDE_SAME_STD_BUCKET = True # requires 와 prevents 가 같은 버킷(STD_REL_8)
NEG_ENTITY_SAMPLING = "frequency"  # uniform 은 hapax 만 뽑는다
NEG_FILTERED = True
NEG_AUDIT_SAMPLE = 100             # 수작업 감사 필수

KG_SPLIT_TRAIN_MAX_YEAR = 2022     # 단계 8 은 창별로 다시 만든다
CALIBRATION = "isotonic"
PRAUC_GATE = 0.80
ECE_GATE = 0.05

# --------------------------------------------------------------------------
# 단계 6 — 시나리오 공간
# --------------------------------------------------------------------------

REP_PATENTS = 10             # 그룹당 KG 수집용 대표 특허 (빈도 머리 모드 잔존)
TOP_CLUSTERS = 20            # 그룹당 선정 클러스터 상한
REL_MASS = 0.80              # 관계 후보: 누적 언급 질량 80% 를 덮는 상위 표면 관계
EXCLUDE_INTRA_GROUP = True   # 그룹 내부 쌍 제외
TOPK_PAIR = 10               # 쌍 점수 = 상위 k 후보 prob 평균
PAIR_COS_MAX = 0.80          # 이름 규칙이 못 잡는 임베딩 동의어만
PAIR_UNIQUE_HT = True        # top-k 는 (h,t) 당 최댓값 관계 하나만
PAIR_NAME_CONTAIN_MIN = 4    # 짧은 이름이 이 길이 이상이면 포함 관계로 동일 명사
PAIR_SAME_NOUN_STEMS = (
    "client",
    "device",
    "server",
    "node",
    "model",
)
PAIR_CLUSTER_MODE = "lift_surface"  # 표면 엔티티 lift. 130 매핑 ID 를 쓰지 않는다
PAIR_MASS_MIN = 0.002        # 표면 어휘용. 0.005 는 130칸 질량이라 여기선 G2/G4 가 비었다
PAIR_LIFT_MIN = 1.3          # 선정 후보의 최소 lift (평균 그룹 대비)
PAIR_ENTITY_MAX_CHARS = 50   # 문장형 슬롯 덤프를 엔티티에서 제외

# 삽화용 새로움 N. pair_prob / P(s) 에는 넣지 않는다.
PAIR_NOVEL_F_MIN = 0.40      # F 하한. 통과만. 순위는 N
PAIR_NOVEL_TOPK = 10
PAIR_GENERIC_REL_STEMS = (
    "connect",
    "enable",
    "share",
    "receive",
    "allow",
    "access",
    "forward",
)
PAIR_GENERIC_REL_PENALTY = 0.25
PAIR_ROLE_TEMPLATE_PENALTY = 0.20  # 양쪽이 client/device/server/node/model 이고 흔한 동사
# |s|=n 삽화: 그룹당 노드 1개. 쌍 후보 top-k 안에서 끝점이 맞물리는 조합만. P(s)에 안 넣음
PAIR_GRAPH_CANDIDATES = 10

SCENARIO_SIZES = (2, 3, 4)
SEARCH_MODE = "enumerate"    # "mcmc" 는 |s|>=5 확장 시에만
BETA = 1.0                   # 민감도 {0.5, 1, 2}
BETA_SENSITIVITY = (0.5, 1.0, 2.0)

MCMC_CHAINS = 4              # SEARCH_MODE == "mcmc" 일 때만
MCMC_STEPS = 200_000
MCMC_BURNIN_FRAC = 0.2
MCMC_THIN = 10
MCMC_RANK_CORR_GATE = 0.95   # 열거 결과와의 순위 상관

# --------------------------------------------------------------------------
# 단계 7 — 사분면
# --------------------------------------------------------------------------

OCC_PRIMARY = "entity_cluster"   # entity_cluster | assignee | cpc | soft_product
OCC_REPORT_ALL = True            # 네 지표 모두 계산해 병기
ASSIGNEE_EXCLUDE = ("(no assignee found)",)   # 106건
TERCILE_BY_SIZE = True           # 크기 |s| 별로 삼분위
MIN_CELL_CANDIDATES = 10         # 게이트

# --------------------------------------------------------------------------
# 단계 8 — 슬라이딩 윈도우
# --------------------------------------------------------------------------

SLIDING = (                      # (학습창 상한, 평가창)
    ("W1", "W2"),
    ("W2", "W3"),
)
REFIT_PER_WINDOW = ("pca", "bgmm", "feasibility", "trend", "occupancy")
FROZEN_ACROSS_WINDOWS = ("sentence_encoder",)         # 동결이므로 재적합 불필요 (D4)
KNOWN_LEAKAGE = (                                     # 창별 재생성 불가 (D16)
    "standardization_mapping_130_50",
    "pretrained_encoder_training_data",
)
GROUP_MATCHING = "hungarian_cosine"
LIFT_KS = (10, 50, 100)
BOOTSTRAP_N = 1000               # 창이 2개뿐이라 CI 필수
ABLATIONS = ("full", "no_F", "no_trend")
