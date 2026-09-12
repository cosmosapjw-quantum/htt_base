# 수학적 동치 통합 전의 중복 참고 집계

2026-09-13 사용자 질의에 따른 정적 계산이다. 입력은 카탈로그 증명 목록
`4f49a900f931a379b456fff5dd727a531e037959`의 `confirmed.json`, `unconfirmed.json`이다.
명제의 수학적 동치, 실제 반증, 최신 버전의 유효성을 새로 판정하지 않았다.

| 계산 기준 | 항목 묶음 |
|---|---:|
| 기존 두 목록: 출처 내용·상태·근거별 묶음 | 40,282 |
| 명제 문면의 공백을 정규화하고 기재된 조건·가정·정의역·관례가 같은 행 통합 | 10,023 |
| 위 계산에서 철회·대체로 분류된 행 제외 | 10,012 |

두 번째 계산은 첫 번째보다 75.12% 작다. **약 1만 개의 문면상 검토 묶음**이라는
참고치이며, 수학적으로 서로 다른 명제 수의 추정 범위나 확정값이 아니다.
철회·대체 표기는 실제 반증과 같지 않으며, 이 표만으로 반증 버전을 제거했다고 말할 수 없다.

기존 두 목록 중 39,536개 묶음의 원문은 전체 명제·가정을 보증하지 않는 발췌다.
조건이 비어 있는 두 행이 같은 문장을 가졌다고 해서 같은 정의·모형을 쓴 것은 아니다.
추가 원문 후보에는 LaTeX 종료 태그 같은 비명제도 남아 있다. 반대로 다른 문장이나
다른 기호로 쓴 동일 명제는 위 계산으로 합쳐지지 않는다.

수학적 통합에는 정의·가정·양화·대상·관례의 대조, 실제 반례와 적용 버전의 확인,
명시적 대체 관계의 검토가 필요하다. 서로 다른 브랜치 사이에서 단순히 날짜가
가장 늦은 파일을 선택하면 적용 조건이나 유효한 기존 증명을 잃을 수 있다.
기존 목록은 이 후속 판단을 위해 모든 버전과 근거를 보존한다.

재현 코드:

```python
import json, re
from pathlib import Path

p = Path("docs/project_catalog/proofs")
rows = json.loads((p / "confirmed.json").read_text())
rows += json.loads((p / "unconfirmed.json").read_text())

def key(row):
    support = row.get("reviewed_support") or {}
    return (
        re.sub(r"\s+", " ", row["statement"] or "").strip(),
        json.dumps(row["conditions"], sort_keys=True, ensure_ascii=False),
        json.dumps(support.get("assumptions", []), sort_keys=True, ensure_ascii=False),
        support.get("domain", ""),
        support.get("conventions", ""),
    )

print(len(rows), len({key(row) for row in rows}))  # 40282, 10023
retained = [r for r in rows if r["reason"] not in
            {"retracted_record", "superseded_record"}]
print(len({key(row) for row in retained}))  # 10012
```
