# labels_v5 분류 체계 (한글)

원본: `labels_v5.json` (프롬프트 `{{OPTIONS}}` 및 스키마 enum과 동일).  
용도: 카드 패스·매핑 패스에서 LLM이 고를 수 있는 **분류 항목 → 허용값 → 의미**를 한글로 정리한 참고 문서.

---

## 1. 전체 분류 체계

| 구분 | 항목 | 역할 |
|---|---|---|
| 발명 유형 | `subject.type` | 장치·방법·시스템 구분 |
| 기능 | `functions.verb` | 수행하는 기능 동사 |
| 기능 | `functions.flow` | 물질·에너지·신호 구분 |
| 기능 | `functions.actor` | 기능 수행 주체 |
| 기능 | `functions.role` | 주기능·보조기능 |
| 문제·효과 | `statement.type` | 해결 문제와 주장된 효과 |
| 작물 | `target_categories` | 대상 작물 유형 |
| 장치 형태 | `form_factor` | 물리적 장치 형태 |
| 동력 | `power_source` | 동력 공급 방식 |
| 환경 | `operating_environment` | 사용 환경 |
| 인프라 | `infrastructure_requirements` | 필요한 기반 조건 |
| 장비 의존성 | `host_dependency` | 외부 장비 필요 여부 |
| 분석 범위 | `scope.category` | 과일·채소 수확 관련성 |
| 하위 기능 | `subfunction.relation` | 특허의 기능 기여 관계 |
| 하위 기능 | `subfunction.actor` | 하위 기능 수행 주체 |
| 분리 원리 | `detachment_principle.values` | 작물 분리 메커니즘 |
| 신뢰도 | `overall_confidence` | 분류 결과의 근거 수준 |

총 **17개** 항목. 이 가운데 기능 동사(`functions.verb`)가 가장 세분화된 분류이고, 다른 항목들은 수행 주체·기술 구현·적용 조건 등을 설명한다.

---

## 2. 기능 동사 — `functions.verb`

**45개** · Hirtz et al. (2002) functional basis 축약 체계.

기능을 **물질(Material)·에너지(Energy)·신호(Signal)**에 대한 작용으로 표현한다. 45개 동사는 모두 같은 수준이 아니다. 일부는 **상위 일반 동사**, 일부는 **구체 하위 동사**이다. 맞는 하위 동사가 있으면 상위 동사 대신 하위를 쓰도록 명시되어 있다.

### 계층 요약

| 군 | 일반(상위) | 구체(하위) |
|---|---|---|
| 분리 | `separate` | `divide`, `extract`, `remove` |
| 분산 | `distribute` | — |
| 유입·유출 | — | `import`, `export` |
| 이동·전달 | `transfer` | `transport`, `transmit` |
| 방향·운동 | `guide` | `translate`, `rotate`, `allow_dof` |
| 결합 | `couple` | `join`, `link` (+ `mix`) |
| 작동·제어 | `regulate` | `actuate`, `increase`, `decrease` |
| 변경·처리 | `change` | `increment`, `decrement`, `shape`, `condition` |
| 차단 | `stop` | `prevent`, `inhibit` |
| 변환 | `convert` | — |
| 저장·공급 | — | `store`, `contain`, `collect`, `supply` |
| 감지 | `sense` | `detect`, `measure` |
| 정보 표시 | `indicate` | `track`, `display` |
| 정보 처리 | — | `process` |
| 안정·고정 | — | `stabilize`, `secure`, `position` |

### 허용 값과 의미

| 기능 동사 | 군 | 의미 |
|---|---|---|
| `separate` | 분리 | 흐름이나 그 일부를 분리하는 **일반** 동사 |
| `divide` | 분리 | 하나를 둘 이상으로 나눔 (예: 줄기를 자름) |
| `extract` | 분리 | 강제로 끌어내거나 뽑음 (예: 뿌리를 흙에서 뽑음) |
| `remove` | 분리 | 원래 위치에서 일부를 제거함 (예: 잎을 제거) |
| `distribute` | 분산 | 여러 장소로 분산함 |
| `import` | 유입·유출 | 장치 외부에서 흐름을 받아들임 |
| `export` | 유입·유출 | 장치 밖으로 내보냄 |
| `transfer` | 이동·전달 | 흐름을 이동시키는 **일반** 동사 |
| `transport` | 이동·전달 | **물질**을 한 장소에서 다른 장소로 이동 |
| `transmit` | 이동·전달 | **에너지**를 한 장소에서 다른 장소로 전달 |
| `guide` | 방향·운동 | 흐름의 경로를 안내하는 **일반** 동사 |
| `translate` | 방향·운동 | 직선 방향으로 이동 |
| `rotate` | 방향·운동 | 축을 중심으로 회전 |
| `allow_dof` | 방향·운동 | 하나 이상의 방향으로 자유로운 운동 허용 |
| `couple` | 결합 | 구분 가능한 흐름들을 결합하는 **일반** 동사 |
| `join` | 결합 | 고정된 방식으로 결합 |
| `link` | 결합 | 중간 부품을 통해 연결 |
| `mix` | 결합 | 균일한 혼합물로 섞음 |
| `actuate` | 작동·제어 | 제어 신호에 반응하여 작동 시작 |
| `regulate` | 작동·제어 | 제어 신호에 따라 조절하는 **일반** 동사 |
| `increase` | 작동·제어 | 제어 신호에 따라 증가 |
| `decrease` | 작동·제어 | 제어 신호에 따라 감소 |
| `change` | 변경·처리 | 정해진 방식으로 변경하는 **일반** 동사 |
| `increment` | 변경·처리 | 정해진 방식으로 증가 |
| `decrement` | 변경·처리 | 정해진 방식으로 감소 |
| `shape` | 변경·처리 | 물질을 특정 형태로 성형 |
| `condition` | 변경·처리 | 세척·건조·냉각 등 사용에 맞게 처리 |
| `stop` | 차단 | 흐름을 멈추거나 차단하는 **일반** 동사 |
| `prevent` | 차단 | 흐름 자체를 방지 |
| `inhibit` | 차단 | 일부는 통과시키면서 강하게 억제 |
| `convert` | 변환 | 한 형태의 흐름을 다른 형태로 변환 |
| `store` | 저장·공급 | 나중에 사용하도록 축적 |
| `contain` | 저장·공급 | 정해진 공간이나 경계 안에 유지 |
| `collect` | 저장·공급 | 한 장소로 모음 |
| `supply` | 저장·공급 | 저장된 흐름을 공급 |
| `sense` | 감지 | 흐름을 인지하는 **일반** 동사 |
| `detect` | 감지 | 존재나 상태를 감지 |
| `measure` | 감지 | 크기나 양을 측정 |
| `indicate` | 정보 표시 | 흐름에 관한 정보를 사용자에게 알리는 **일반** 동사 |
| `track` | 정보 표시 | 시간에 따라 관찰·기록 |
| `display` | 정보 표시 | 눈으로 볼 수 있도록 표시 |
| `process` | 정보 처리 | 정해진 절차로 정보 처리 (예: 영상에서 위치 계산) |
| `stabilize` | 안정·고정 | 위치나 경로가 변하지 않도록 안정화 |
| `secure` | 안정·고정 | 단단히 고정하거나 파지 |
| `position` | 안정·고정 | 특정 위치나 방향으로 배치 |

예: 사과 줄기를 칼날로 자르면 `divide`, 카메라로 사과를 찾으면 `detect`, 그리퍼로 잡으면 `secure`.

`cutting`은 기능 동사가 아니라 **분리 원리(`detachment_principle`)**의 값이다. `divide`는 *무슨 기능인가*, `cutting`은 *어떤 방식으로 분리하는가*를 나타낸다.

---

## 3. 나머지 분류 항목

### 3.1 발명 유형 — `subject.type`

| 허용 값 | 의미 |
|---|---|
| `apparatus` | 기계·장치·도구 |
| `method` | 작업 수행 방법 |
| `system` | 여러 장치가 함께 작동하는 시스템 |
| `apparatus_and_method` | 장치와 사용 방법 모두 발명으로 제시 |
| `other` | 위에 해당하지 않음 |

### 3.2 기능의 대상 — `functions.flow`

| 허용 값 | 의미 |
|---|---|
| `material` | 물리적 물체나 물질(과일·토양·수확 헤드 등) |
| `energy` | 기계·전기·유압 등의 에너지 |
| `signal` | 영상·위치·제어 명령 등의 정보 |

### 3.3 기능 수행 주체 — `functions.actor`

동력원을 기준으로 판정한다.

| 허용 값 | 의미 |
|---|---|
| `invention` | 발명 장치 자체의 동력·제어로 수행 |
| `host_machine` | 발명이 장착된(또는 함께 쓰는) 외부 기계가 자체 동력으로 수행 |
| `human` | 사람이 근력으로 수행(손작업, 모터 없는 도구·인력 발명 포함) |
| `both` | 동력 장치와 사람이 같은 동작의 일부를 각각 수행 |
| `not_specified` | 명세서에 명확하지 않음 |

### 3.4 기능의 역할 — `functions.role`

| 허용 값 | 의미 |
|---|---|
| `main` | 발명의 주목적에 해당하는 핵심 기능 |
| `auxiliary` | 주기능을 지원하는 보조 기능 |

### 3.5 해결 문제와 효과 — `statement.type`

`problems[].type`과 `effects[].type`에 공통으로 적용(9개).

| 허용 값 | 의미 |
|---|---|
| `labor_or_cost` | 노동량·인건비·기타 비용 |
| `damage_or_quality_loss` | 작물·식물·토양 손상 또는 품질 손실 |
| `throughput_or_speed` | 처리량·작업 속도 |
| `accuracy_or_selectivity` | 선택적 수확·위치 정밀도·감지 오류 |
| `safety_or_ergonomics` | 안전·작업자 부담·인체공학 |
| `reliability_or_maintenance` | 고장·마모·막힘·유지보수 |
| `adaptability_to_crop_or_terrain` | 작물·지형·재배 조건 적응성 |
| `energy_or_resource_use` | 연료·전력·물 등 자원 사용 |
| `other` | 기타 |

### 3.6 대상 작물 — `target_categories`

| 허용 값 | 의미 및 예시 |
|---|---|
| `tree_fruit` | 사과·감귤·체리·올리브·대추 등 나무 과일 |
| `vine_or_bush_fruit` | 포도·블루베리·라즈베리·키위 등 |
| `fruiting_vegetable` | 토마토·고추·오이·멜론·딸기 등 |
| `leafy_vegetable` | 상추·배추·시금치·브로콜리·아스파라거스 등 |
| `root_vegetable` | 감자·당근·양파·마늘·고구마 등 |
| `other_vegetable` | 콩·완두·단옥수수·버섯 등 |
| `tree_nut` | 아몬드·호두·피칸·헤이즐넛 등 |
| `grain_or_oilseed` | 밀·곡물용 옥수수·대두·유채 등 |
| `forage_or_grass` | 건초·사일리지·잔디 등 |
| `fiber_crop` | 면화·아마·대마 등 |
| `industrial_crop` | 사탕무·사탕수수·담배·홉·치커리 뿌리 등 |
| `other` | 기타 작물 |
| `not_specified` | 작물 미명시 |

### 3.7 장치 형태 — `form_factor`

| 허용 값 | 의미 |
|---|---|
| `handheld_tool` | 손으로 들고 사용하는 도구 |
| `walk_behind_or_pushed` | 보행자가 밀거나 안내하는 장비 |
| `worker_platform_or_cart` | 작업자가 탑승해 수확하는 플랫폼·카트 |
| `tractor_mounted_or_towed` | 트랙터 장착형·견인형 |
| `self_propelled_harvester` | 운전자가 조종하는 자주식 수확기 |
| `mobile_robot` | 자율적으로 이동·작업하는 로봇 |
| `stationary_installation` | 온실 레일 등 고정 설치형 |
| `component_only` | 수확 헤드·센서 등 부품만 해당 |
| `not_specified` | 형태 불명확 |

### 3.8 동력원 — `power_source`

| 허용 값 | 의미 |
|---|---|
| `human_power` | 사람의 근력 |
| `battery_electric` | 배터리 전력 |
| `combustion_engine` | 자체 내연기관 |
| `tractor_pto_or_hydraulics` | 트랙터·호스트의 PTO·유압 |
| `grid_electric` | 외부 전력망 |
| `pneumatic_compressor` | 압축공기 |
| `other` | 기타 명시된 동력 |
| `not_specified` | 동력원 미명시 |

### 3.9 작동 환경 — `operating_environment`

| 허용 값 | 의미 |
|---|---|
| `open_field` | 노지 |
| `orchard` | 과수원 |
| `vineyard` | 포도원 |
| `greenhouse_or_indoor` | 온실·실내 |
| `other` | 기타 |
| `not_specified` | 미명시 |

### 3.10 인프라 요구사항 — `infrastructure_requirements`

| 허용 값 | 의미 |
|---|---|
| `trellis_or_planar_canopy` | 지주·평면 수관 형태 필요 |
| `row_or_bed_layout` | 특정 이랑·줄 간격 필요 |
| `rails_or_tracks` | 레일·궤도 필요 |
| `precise_positioning_gps` | GPS 등 정밀 위치 측위 필요 |
| `network_connectivity` | 데이터 네트워크 연결 필요 |
| `other` | 기타 |
| `none_stated` | 명시된 요구사항 없음 |

### 3.11 외부 장비 의존성 — `host_dependency`

| 허용 값 | 의미 |
|---|---|
| `standalone` | 독립적으로 작동 |
| `general_attachment` | 다양한 기계에 부착 가능한 장치 |
| `specific_platform` | 특정 유형의 기계에 의존 |
| `not_specified` | 불명확 |

### 3.12 분석 대상 범위 — `scope.category`

| 허용 값 | 의미 |
|---|---|
| `fruit_or_vegetable_harvest` | 식용 과일·채소 수확(식용 뿌리작물·떨어진 과일 수집 포함) 및 그 전용 부품·부속 |
| `industrial_crop` | 산업용 원료 작물 수확(면화 등 섬유, 사탕무·사탕수수·담배·홉·치커리 뿌리 등) |
| `grain_forage_or_grass` | 곡물·유지작물·사료·건초·잔디 수확 |
| `tree_nut_only` | 견과류만 수확(과일 없음) |
| `non_harvest_task` | 솎기·가지치기·적엽·방제·수분·파종·그루터기·잔재 제거 등 비수확 작업 |
| `post_harvest_handling` | 수확 후 더미 적재·선별·세척·포장·저장 등 |
| `unclear` | 카드만으로는 범위 판단 불명확 |

### 3.13 하위 기능 기여 관계 — `subfunction.relation`

| 허용 값 | 의미 |
|---|---|
| `direct` | 독립 청구항에 기재된 구성요소가 해당 기능을 **직접 수행**(기계 동력·인력 모두 포함) |
| `support` | 청구항 구성요소가 기능을 직접 수행하지는 않으나, 사람·호스트 기계의 수행을 **지원** |
| `not_mentioned` | 청구항 발명이 수행도 지원도 하지 않음(독립 청구항 밖의 동작 포함) |

### 3.14 하위 기능 수행 주체 — `subfunction.actor`

옵션 집합은 `functions.actor`와 같다. 여기서는 **F1–F4 각 하위 기능**의 수행 주체를 판정한다.

| 허용 값 | 의미 |
|---|---|
| `invention` | 발명 장치 자체가 수행 |
| `host_machine` | 외부 장착 기계가 수행 |
| `human` | 사람이 수행 |
| `both` | 사람과 동력 장치가 함께 수행 |
| `not_specified` | 수행 주체 불명확 |

### 3.15 작물 분리 원리 — `detachment_principle.values`

F3(작물을 식물·토양에서 분리)의 **기술적 메커니즘**. F3가 `direct` 또는 `support`일 때만 원리를 고르고, F3가 `not_mentioned`이면 `not_applicable`만 쓴다.

| 허용 값 | 의미 |
|---|---|
| `cutting` | 칼날·가위·톱으로 절단 |
| `twisting` | 회전시켜 줄기 분리 |
| `pulling` | 잡아당겨 분리 |
| `shaking_or_vibration` | 진동·흔들기로 낙하시킴 |
| `suction_or_pneumatic` | 공기 흐름·진공으로 분리 |
| `digging_or_lifting` | 토양을 파거나 들어 올려 뿌리작물 분리 |
| `combing_or_stripping` | 빗살·갈퀴로 훑어서 분리 |
| `other` | 기타 원리 |
| `not_specified` | F3는 수행하지만 원리 미명시 |
| `not_applicable` | F3가 언급되지 않음(이 값만 단독 사용) |

### 3.16 전체 분류 신뢰도 — `overall_confidence`

| 허용 값 | 의미 |
|---|---|
| `high` | 모든 분류를 뒷받침하는 근거가 명확 |
| `medium` | 일부 분류의 근거가 부족 |
| `low` | 여러 분류에 대한 근거가 부족 |

LLM이 카드·매핑 근거의 **충분성**을 스스로 평가하는 범주이며, 통계적으로 보정된 정확도·확률이 아니다.

---

## 부록. 항목별 허용값 개수 (`labels_v5.json` 대조)

| 항목 | 개수 |
|---|---|
| `subject.type` | 5 |
| `functions.verb` | 45 |
| `functions.flow` | 3 |
| `functions.actor` | 5 |
| `functions.role` | 2 |
| `statement.type` | 9 |
| `target_categories` | 13 |
| `form_factor` | 9 |
| `power_source` | 8 |
| `operating_environment` | 6 |
| `infrastructure_requirements` | 7 |
| `host_dependency` | 4 |
| `scope.category` | 7 |
| `subfunction.relation` | 3 |
| `subfunction.actor` | 5 |
| `detachment_principle.values` | 10 |
| `overall_confidence` | 3 |
| **합계(항목)** | **17** |
