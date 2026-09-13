# Model and effort routing

권위 있는 공통 선택 규칙은 `docs/MODEL_ROUTING.md`에 있다. 이 패키지는 GPT-6 Astra 대상이다. 실제 모델 식별자, 사용자 지정, tool 가용성과 호스트 capability profile을 기록한다. 다른 모델을 이름의 유사성으로 6 Astra로 취급하지 않는다.

reasoning effort는 해당 호스트/제품이 실제 노출하는 선택지만 사용한다. 이 세션의 호스트가 노출한 `ultra` 같은 옵션을 API enum이나 다른 제품의 지원 주장으로 일반화하지 않는다. 모델명·API ID·context 한도·가격을 추정하지 않는다.

설정 변경 전 입력 품질, acceptance criterion, source 접근, tool dependency, verifier와 stop condition을 확인한다. 더 높은 effort가 개선한다는 주장은 동일 과제의 비교 증거가 있어야 한다. 설정 요청이 지원되지 않으면 명시하고 가용한 설정으로 진행하거나 필요한 입력만 요청한다. 조용히 다른 모델로 전환하지 않는다.
