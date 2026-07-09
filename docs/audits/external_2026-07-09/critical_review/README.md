# HTT v6 제공 연구 비판 심사 번들

이 번들은 업로드된 `external_audit_research_report_v6.pdf` 및 동봉 zip 패키지를 기준으로 만든 독립 심사 자료야. 원 저장소의 코드를 재사용하지 않고, 보고서의 핵심 수학·통계 주장 몇 개를 검증하거나 반례를 찾는 작은 수치 실험을 포함했어.

## 구성

- `critical_review_ko.md`: 수학, 물리 해석, 통계, 데이터 해석, 독창성, 출판가능성에 대한 상세 비판 심사.
- `reviewer_report_template.md`: 실제 저널 심사평 형식의 요약 판정.
- `revision_checklist.csv`: 우선순위별 수정 권고와 검증 기준.
- `theorem_candidates.md`: 추가로 증명 가능한 정리 후보와 증명/실험 경로.
- `scripts/`: 실행 가능한 독립 검증 코드.
- `outputs/experiment_results.json`: 여기서 이미 실행한 수치 실험 결과.
- `outputs/package_integrity_audit.json`: 업로드 zip의 재현성/무결성 감사 결과.

## 실행 방법

```bash
cd htt_v6_critical_review_bundle
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/run_all_experiments.py --out outputs/experiment_results.json
```

업로드된 원 패키지를 별도로 풀어둔 뒤 재현성 감사를 하려면:

```bash
python scripts/audit_package_integrity.py /path/to/external_audit_research_report_20260708_v6 \
  --out outputs/package_integrity_audit.json
```

## 중요한 해석

이 코드들은 원 연구의 원본 구현이 아니야. 보고서가 주장하는 형식 구조가 실제로 어떤 조건에서 맞고, 어떤 조건에서 약해지거나 반례가 생기는지를 점검하는 독립 감사용 witness야. 특히 `gf_joint_interval` 실험은 보고서의 P36 문장 중 “strict whenever” 형태의 너무 강한 주장을 반례로 깬다.
