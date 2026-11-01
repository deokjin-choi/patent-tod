# 매핑·영상 검색식

> 2026-10-28. WIPO Agrifood 랜드스케이프(2024) 부록 B의 Mapping/imagery 식을 Lens에서 다시 돌리기 위한 기록이다.
> 보고서 원문은 같은 폴더의 PDF, 요약은 [2024_key-findings.md](2024_key-findings.md).
> 대상은 삼성 등 특정 출원인이 아니다. 하위영역 정의 그대로다.

WIPO는 Orbit(Questel)으로 2004–2023년 최우선일, 국제 패밀리만 세었다. 국제 패밀리는 마지막 줄 `NOT NPN=1`, 즉 공개가 둘 이상인 패밀리다. Lens에는 문단 연산자 `P`가 없고, 여는 괄호 바로 뒤에 괄호가 오면 검색창이 거절한다. 그래서 Lens 식은 같은 필드 안의 `AND`로 풀었고, `crop*` 대신 `crop OR crops`를 썼다. `crop*`는 영상을 자른다는 cropping까지 잡는다.

2026-10-28에 Lens 두 식 모두 검색은 됐다. 각각 수십만 건이다. 한 번에 받을 수 있는 상한은 약 5만 건이라, 관련도 순 상위 5만 건은 쓰지 않는다. Simple family로 묶은 뒤, Earliest Priority Date로 합이 5만 미만인 연도 묶음을 여러 번 받는다. 화면 건수가 5만보다 큰데 파일이 5만이면 잘린 것이니 버린다. 두 식을 합쳐 패밀리 번호가 같은 행을 지운 다음, 우선일 연도마다 패밀리 번호를 해시해 5로 나눈 나머지가 0인 것만 남기면 약 20%다.

## Orbit 원문

부록 B, Mapping/imagery. `+`는 한 글자 이상, `?`는 한 글자 이내, `P`는 같은 문단이다. `/DESC`와 `/ODES`는 명세서까지 포함한다.

```text
1
(AGRICULTUR+ OR FARMING OR CULTIVA+ OR HORTICULTURE OR CROP? OR FARMLAND
 OR FARM? OR HUSBANDRY OR LIVESTOCK? OR POULTRY)/TI/AB/CLMS/OBJ/DESC/ODES
AND (G06T+ OR G06V+ OR G06Q-050/02 OR H04N+)/IPC/CPC

2
(AGRICULTUR+ OR FARMING OR CULTIVA+ OR HORTICULTURE OR CROP? OR FARMLAND
 OR FARM? OR HUSBANDRY OR LIVESTOCK? OR POULTRY)
P (MAP? OR MAPPING OR IMAGE? OR IMAGERY OR IMAGING)/TI/AB/CLMS/OBJ

3
(AGRICULTUR+ OR FARMING OR CULTIVA+ OR HORTICULTURE OR CROP? OR FARMLAND
 OR FARM? OR HUSBANDRY OR LIVESTOCK? OR POULTRY)/TI/AB/CLMS/OBJ/DESC/ODES
AND (G01C-021+ OR G01S-017+ OR G01S-019+ OR H04W-004+)/IPC/CPC

4
(GEOSPATIAL)/TI/AB/CLMS/DESC/ODES/OBJ
AND (AGRICULTUR+ OR FARMING OR CULTIVA+ OR HORTICULTURE OR CROP? OR FARMLAND
     OR FARM? OR HUSBANDRY OR LIVESTOCK? OR POULTRY)/TI/AB/CLMS/DESC/ODES/OBJ

5
(AGRICULTUR+ OR FARMING OR CULTIVA+ OR HORTICULTURE OR CROP? OR FARMLAND
 OR FARM? OR HUSBANDRY OR LIVESTOCK? OR POULTRY)/TI/AB/CLMS/DESC/ODES/OBJ
AND ((SATELLITE?) P (MAP? OR MAPPING OR IMAGE? OR IMAGERY OR IMAGING))/TI/AB/CLMS/DESC/ODES/OBJ

6
(AGRICULTUR+ OR FARMING OR CULTIVA+ OR HORTICULTURE OR CROP? OR FARMLAND
 OR FARM? OR HUSBANDRY OR LIVESTOCK? OR POULTRY)
P (SATELLITE? OR GLOBAL_POSITION+_SYSTEM? OR GEOGRAPHIC_INFORMATION_SYSTEM?)
/TI/AB/CLMS/DESC/ODES/OBJ

7  1 OR 2 OR 3 OR 4 OR 5 OR 6
8  7 AND EPD>2003
9  8 NOT NPN=1
```

1번이 가장 넓다. 농업 단어가 명세서 어디에든 있고 분류가 영상처리(G06T), 영상인식(G06V), 농업 경영정보(G06Q 50/02), 화상통신(H04N)이면 들어온다. 2번은 제목·초록·청구항에서 농업 단어와 지도·영상이 같은 문단에 있어야 한다.

## Lens — 분류와 농업 단어

Orbit 1번과 3번. 2026-10-28 검색됨.

```text
(earliest_priority_claim_date:[2004-01-01 TO 2023-12-31] AND title:(agricultur* OR farming OR cultivat* OR horticulture OR crop OR crops OR farmland OR farm OR farms OR husbandry OR livestock* OR poultry) AND (class_cpc.symbol:(G06T* OR G06V* OR H04N* OR G06Q50\/02) OR class_ipcr.symbol:(G06T* OR G06V* OR H04N* OR G06Q50\/02)))
OR (earliest_priority_claim_date:[2004-01-01 TO 2023-12-31] AND abstract:(agricultur* OR farming OR cultivat* OR horticulture OR crop OR crops OR farmland OR farm OR farms OR husbandry OR livestock* OR poultry) AND (class_cpc.symbol:(G06T* OR G06V* OR H04N* OR G06Q50\/02) OR class_ipcr.symbol:(G06T* OR G06V* OR H04N* OR G06Q50\/02)))
OR (earliest_priority_claim_date:[2004-01-01 TO 2023-12-31] AND claim:(agricultur* OR farming OR cultivat* OR horticulture OR crop OR crops OR farmland OR farm OR farms OR husbandry OR livestock* OR poultry) AND (class_cpc.symbol:(G06T* OR G06V* OR H04N* OR G06Q50\/02) OR class_ipcr.symbol:(G06T* OR G06V* OR H04N* OR G06Q50\/02)))
OR (earliest_priority_claim_date:[2004-01-01 TO 2023-12-31] AND description:(agricultur* OR farming OR cultivat* OR horticulture OR crop OR crops OR farmland OR farm OR farms OR husbandry OR livestock* OR poultry) AND (class_cpc.symbol:(G06T* OR G06V* OR H04N* OR G06Q50\/02) OR class_ipcr.symbol:(G06T* OR G06V* OR H04N* OR G06Q50\/02)))
OR (earliest_priority_claim_date:[2004-01-01 TO 2023-12-31] AND title:(agricultur* OR farming OR cultivat* OR horticulture OR crop OR crops OR farmland OR farm OR farms OR husbandry OR livestock* OR poultry) AND (class_cpc.symbol:(G01C21* OR G01S17* OR G01S19* OR H04W4*) OR class_ipcr.symbol:(G01C21* OR G01S17* OR G01S19* OR H04W4*)))
OR (earliest_priority_claim_date:[2004-01-01 TO 2023-12-31] AND abstract:(agricultur* OR farming OR cultivat* OR horticulture OR crop OR crops OR farmland OR farm OR farms OR husbandry OR livestock* OR poultry) AND (class_cpc.symbol:(G01C21* OR G01S17* OR G01S19* OR H04W4*) OR class_ipcr.symbol:(G01C21* OR G01S17* OR G01S19* OR H04W4*)))
OR (earliest_priority_claim_date:[2004-01-01 TO 2023-12-31] AND claim:(agricultur* OR farming OR cultivat* OR horticulture OR crop OR crops OR farmland OR farm OR farms OR husbandry OR livestock* OR poultry) AND (class_cpc.symbol:(G01C21* OR G01S17* OR G01S19* OR H04W4*) OR class_ipcr.symbol:(G01C21* OR G01S17* OR G01S19* OR H04W4*)))
OR (earliest_priority_claim_date:[2004-01-01 TO 2023-12-31] AND description:(agricultur* OR farming OR cultivat* OR horticulture OR crop OR crops OR farmland OR farm OR farms OR husbandry OR livestock* OR poultry) AND (class_cpc.symbol:(G01C21* OR G01S17* OR G01S19* OR H04W4*) OR class_ipcr.symbol:(G01C21* OR G01S17* OR G01S19* OR H04W4*)))
```

## Lens — 같은 필드의 단어

Orbit 2번, 4번, 5번, 6번. 농업 단어와 영상·지도, 또는 위성·위치가 제목·초록·청구항·명세서 중 같은 필드에 있는 경우다. 2026-10-28 검색됨.

```text
(earliest_priority_claim_date:[2004-01-01 TO 2023-12-31] AND title:(agricultur* OR farming OR cultivat* OR horticulture OR crop OR crops OR farmland OR farm OR farms OR husbandry OR livestock* OR poultry) AND title:(map OR maps OR mapping OR image OR images OR imagery OR imaging))
OR (earliest_priority_claim_date:[2004-01-01 TO 2023-12-31] AND abstract:(agricultur* OR farming OR cultivat* OR horticulture OR crop OR crops OR farmland OR farm OR farms OR husbandry OR livestock* OR poultry) AND abstract:(map OR maps OR mapping OR image OR images OR imagery OR imaging))
OR (earliest_priority_claim_date:[2004-01-01 TO 2023-12-31] AND claim:(agricultur* OR farming OR cultivat* OR horticulture OR crop OR crops OR farmland OR farm OR farms OR husbandry OR livestock* OR poultry) AND claim:(map OR maps OR mapping OR image OR images OR imagery OR imaging))
OR (earliest_priority_claim_date:[2004-01-01 TO 2023-12-31] AND description:(agricultur* OR farming OR cultivat* OR horticulture OR crop OR crops OR farmland OR farm OR farms OR husbandry OR livestock* OR poultry) AND description:(map OR maps OR mapping OR image OR images OR imagery OR imaging))
OR (earliest_priority_claim_date:[2004-01-01 TO 2023-12-31] AND title:(geospatial) AND title:(agricultur* OR farming OR cultivat* OR horticulture OR crop OR crops OR farmland OR farm OR farms OR husbandry OR livestock* OR poultry))
OR (earliest_priority_claim_date:[2004-01-01 TO 2023-12-31] AND abstract:(geospatial) AND abstract:(agricultur* OR farming OR cultivat* OR horticulture OR crop OR crops OR farmland OR farm OR farms OR husbandry OR livestock* OR poultry))
OR (earliest_priority_claim_date:[2004-01-01 TO 2023-12-31] AND claim:(geospatial) AND claim:(agricultur* OR farming OR cultivat* OR horticulture OR crop OR crops OR farmland OR farm OR farms OR husbandry OR livestock* OR poultry))
OR (earliest_priority_claim_date:[2004-01-01 TO 2023-12-31] AND description:(geospatial) AND description:(agricultur* OR farming OR cultivat* OR horticulture OR crop OR crops OR farmland OR farm OR farms OR husbandry OR livestock* OR poultry))
OR (earliest_priority_claim_date:[2004-01-01 TO 2023-12-31] AND title:(agricultur* OR farming OR cultivat* OR horticulture OR crop OR crops OR farmland OR farm OR farms OR husbandry OR livestock* OR poultry) AND title:(satellite OR satellites OR gps OR "global positioning" OR "geographic information"))
OR (earliest_priority_claim_date:[2004-01-01 TO 2023-12-31] AND abstract:(agricultur* OR farming OR cultivat* OR horticulture OR crop OR crops OR farmland OR farm OR farms OR husbandry OR livestock* OR poultry) AND abstract:(satellite OR satellites OR gps OR "global positioning" OR "geographic information"))
OR (earliest_priority_claim_date:[2004-01-01 TO 2023-12-31] AND claim:(agricultur* OR farming OR cultivat* OR horticulture OR crop OR crops OR farmland OR farm OR farms OR husbandry OR livestock* OR poultry) AND claim:(satellite OR satellites OR gps OR "global positioning" OR "geographic information"))
OR (earliest_priority_claim_date:[2004-01-01 TO 2023-12-31] AND description:(agricultur* OR farming OR cultivat* OR horticulture OR crop OR crops OR farmland OR farm OR farms OR husbandry OR livestock* OR poultry) AND description:(satellite OR satellites OR gps OR "global positioning" OR "geographic information"))
```

분류 필드 이름을 검색창이 거부하면 `class_cpc.symbol`과 `class_ipcr.symbol`을 빼고, 왼쪽 필터에 `G06T`, `G06V`, `H04N`, `G06Q50/02`, `G01C21`, `G01S17`, `G01S19`, `H04W4`를 건다. 두 나라 이상에 나간 패밀리만 쓰려면, 20%를 남기기 전에 관청이 하나인 패밀리를 뺀다.
