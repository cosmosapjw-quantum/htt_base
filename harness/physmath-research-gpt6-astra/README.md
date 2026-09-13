# Phys–Math Research Harness for GPT-6 Astra

v4.0.0은 GPT-5.6 v3.1.0 원본의 연구 목적과 phase 구조를 보존하면서, 단일 실행자가 승인된 연구를 완료하고 필요한 문맥만 읽도록 정리한 배포판이다. 모델 자체의 속도·비용·과학적 성능 향상을 측정한 결과는 아니다. **모델 간 실증 성능: `NOT_EVALUATED`.**

## 시작

1. `PROJECT_INSTRUCTIONS.md`를 공통 지침으로 읽고 `state/RESEARCH_STATE.md`에 현재 목표·동기·범위·근거 포인터를 적는다.
2. `docs/MODEL_ROUTING.md`로 실제 모델에 맞는 버전을 선택한다. 모델 identity를 모르면 추정하지 않는다.
3. 짧은 국소 연구는 `prompts/quick/ultralight.md`, 승인된 다단계 작업은 `prompts/00_integrated_work_run.md`로 실행한다.
4. 현재 필요한 phase만 읽고 실제 유도·계산·검증까지 진행한다. 완료 또는 blocker에서 상태와 결과를 전달한다.

```bash
python3 tools/validate_workspace.py
```

새 연구용 초기 상태를 만들 때 `tools/init_workspace.py --project "연구 이름"`을 쓸 수 있다. 기존 state는 기본 보존된다. 기존 state를 의도적으로 초기화할 때만 `--force`를 사용한다. 템플릿 직접 복사도 가능하다.

## 운영 변화

- 공통 core + 현재 phase + 필요한 source를 읽고, 증거 포인터로 장기 상태를 복원한다.
- 탐색은 원래 동기와 대안을 보존하며, 수렴은 명시 scope와 criterion에 따른다.
- 연구계약·문헌·감사·가설·검산·실행·판정을 구분하되 phase마다 재승인받지 않는다.
- 진단 유도는 탐색 중 허용한다. 미검증 가설을 확정 결과로 승격하지 않는다.
- 독립 검토의 실제 수행 여부를 표시하며 리뷰 재귀와 증거 없는 재시도를 제한한다. 승인된 수정 자체를 횟수로 제한하지 않는다.

`docs/MIGRATION_NOTES.md`, `docs/MIGRATION_EVIDENCE.md`, `docs/MODEL_REGRESSION.md`에 변경·근거·검증 한계를 기록한다. `.agents/skills/`는 원본 v3.1.0의 byte를 보존한 참고자료다. 패키지 구조 검사 통과는 과학 연구나 모델 성능의 검증을 뜻하지 않는다.
