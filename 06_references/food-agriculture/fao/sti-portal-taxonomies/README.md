# ATIO 지식베이스 분류 CSV

2026-10-27에 [STI Portal 분류 내보내기](https://sti-portal.fao.org/taxonomies-list)에서 받았다.

이 포털은 FAO 과학혁신포럼 2025 소프트론칭용 알파다. 사이트에 FAO 공식 산출이 아니고, 데이터 품질과 AI 사용이 FAO 기준 검토를 마치지 않았다고 적혀 있다. 용어 설명 열에는 생성 모델이 붙인 문장이 들어 있다.

| 파일 | 축 |
|---|---|
| `type.csv` | 혁신이 어떤 기제로 작동하는가. 1층은 기술·금융·사회·정책·제도 |
| `use_cases.csv` | 어떤 필요에 쓰이는가 |
| `forms_of_innovations.csv` | 제품, 농법, 서비스, 플랫폼처럼 어떤 꼴로 전달되는가 |
| `innovation_stages.csv` | 출현 전, 출현, 성숙, 퇴장 |
| `readiness_levels.csv` | 아이디어부터 비통제 현장 검증까지 |
| `adoption_levels.csv` | 채택 수준 |
| `afs_themes.csv` | FAO 사업 주제 |
| `afs_challenges.csv` | 농식품체계의 도전 |

`parent_target_id`가 상위 항목의 `tid`다.
