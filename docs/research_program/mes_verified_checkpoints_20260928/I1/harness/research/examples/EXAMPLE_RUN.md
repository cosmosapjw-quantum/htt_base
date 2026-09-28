# Example run — illustrative, not executed

제안한 effective description이 한 관측량을 개선하지만 알려진 모델의 재매개변수화일 가능성이 있다. 목표는 원래 mechanism 직관을 보존하면서 독립 예측이나 판별력이 있는지 확인하는 것이다.

1. 원래 동기와 현재 질문을 기록한다. 탐색 중 후보 개수를 미리 고정하지 않는다.
2. 직접 읽은 원문 근거와 재매개변수화 가능성에 관한 자체 추론을 분리한다.
3. diagnostic derivation으로 변수 변환·known limit을 확인하고, 후보와 baseline이 달라지는 관측량을 찾는다.
4. 승인·가용하다면 최소 toy calculation을 실행하고 입력·오차·actual log를 남긴다.
5. owner의 자체 검토는 `OWNER_SELF_REVIEW`로 표시한다. 후보 생성·검증 설계와 분리된 실제 독립 decision reviewer가 없으면 `HOLD` + `INDEPENDENT_REVIEW_UNAVAILABLE`로 남기며 owner가 최종 PROMOTE를 승인하지 않는다.
6. 차이가 근거로 입증되지 않으면 `HOLD`/`unresolved`로 기록한다. 실제 독립 decision reviewer의 PROMOTE도 해당 다음 연구 단계로만 한정한다.

이 문서는 흐름 예시이며 가상 결과를 실제 검증 증거로 사용할 수 없다.
