# 생성 목록

기준 R8의 정적 목록이다. 모든 버전은 CLI의 `--ref all`과 `--limit -1`로 조회한다.
표의 ID는 `show`/`history`의 인자다. 상태는 원문 기록 또는 정적 분류이며 실행·증명 완료 판정이 아니다.

- 모듈과 기능: 2,257개 버전 레코드
  - [1–100](lists/feature-001.md)
  - [101–200](lists/feature-002.md)
  - [201–300](lists/feature-003.md)
  - [301–400](lists/feature-004.md)
  - [401–500](lists/feature-005.md)
  - [501–600](lists/feature-006.md)
  - [601–700](lists/feature-007.md)
  - [701–800](lists/feature-008.md)
  - [801–900](lists/feature-009.md)
  - [901–1000](lists/feature-010.md)
  - [1001–1100](lists/feature-011.md)
  - [1101–1200](lists/feature-012.md)
  - [1201–1300](lists/feature-013.md)
  - [1301–1400](lists/feature-014.md)
  - [1401–1500](lists/feature-015.md)
  - [1501–1600](lists/feature-016.md)
  - [1601–1700](lists/feature-017.md)
  - [1701–1800](lists/feature-018.md)
  - [1801–1900](lists/feature-019.md)
  - [1901–2000](lists/feature-020.md)
  - [2001–2100](lists/feature-021.md)
  - [2101–2200](lists/feature-022.md)
  - [2201–2257](lists/feature-023.md)
- 이식·마이그레이션 원문 기록: 281개 버전 레코드
  - [1–100](lists/port-001.md)
  - [101–200](lists/port-002.md)
  - [201–281](lists/port-003.md)
- 분석 진입점 후보: 356개 버전 레코드
  - [1–100](lists/analysis-001.md)
  - [101–200](lists/analysis-002.md)
  - [201–300](lists/analysis-003.md)
  - [301–356](lists/analysis-004.md)
- 명제·증명 기록·후보: 1,875개 버전 레코드
  - [1–100](lists/proposition-001.md)
  - [101–200](lists/proposition-002.md)
  - [201–300](lists/proposition-003.md)
  - [301–400](lists/proposition-004.md)
  - [401–500](lists/proposition-005.md)
  - [501–600](lists/proposition-006.md)
  - [601–700](lists/proposition-007.md)
  - [701–800](lists/proposition-008.md)
  - [801–900](lists/proposition-009.md)
  - [901–1000](lists/proposition-010.md)
  - [1001–1100](lists/proposition-011.md)
  - [1101–1200](lists/proposition-012.md)
  - [1201–1300](lists/proposition-013.md)
  - [1301–1400](lists/proposition-014.md)
  - [1401–1500](lists/proposition-015.md)
  - [1501–1600](lists/proposition-016.md)
  - [1601–1700](lists/proposition-017.md)
  - [1701–1800](lists/proposition-018.md)
  - [1801–1875](lists/proposition-019.md)
- 계획·예비 구현: 932개 버전 레코드
  - [1–100](lists/plan-001.md)
  - [101–200](lists/plan-002.md)
  - [201–300](lists/plan-003.md)
  - [301–400](lists/plan-004.md)
  - [401–500](lists/plan-005.md)
  - [501–600](lists/plan-006.md)
  - [601–700](lists/plan-007.md)
  - [701–800](lists/plan-008.md)
  - [801–900](lists/plan-009.md)
  - [901–932](lists/plan-010.md)
- 구체적 후속 확인 항목: 17개 버전 레코드
  - [1–17](lists/update-001.md)

전체 코드 심볼은 용량과 탐색성을 위해 DB/CSV로 제공한다. 예:

```bash
python3 -B scripts/project_catalog.py export --kind code --ref all --limit -1 --format csv --output /tmp/all-code-versions.csv
```
