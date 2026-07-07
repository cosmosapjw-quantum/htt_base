# 외부 감사 반영 매트릭스 v5

이 파일은 공개 보고서 본문에 드러내기 위한 수사적 장치가 아니라, 감사자가 지적한 누락 항목이 어떤 과학적 보강으로 반영되었는지 확인하기 위한 내부 추적표이다.

| 감사 지적 | v5 반영 위치 | 처리 방식 |
|---|---|---|
| 등록된 성분과 정규화가 부족함 | Registered component vector | \(m g=(\Sigma^2,W^2,\Omega_{tilt},\Omega_{k,aniso})\), 계수 \(c=(1,-1,1,1)\), parent constraint route 명시 |
| P1 전체 성분 요구와 P18 rank-2 도달성 충돌 | P26/P31 partial-identification | 점추정 대신 identified interval/set 정리로 해소 |
| MES bound와 rank nullspace의 경로 혼동 | P27 MES-rank route reconciliation | MES ceiling과 row-space identification을 서로 다른 map으로 분리 |
| shear-memory 식이 Weyl 전기부를 생략함 | P13 revised theorem | \(E_{ab}\), residual, closure 조건을 명시하고 축약형의 유효 범위를 제한 |
| posterior pushforward가 null directions prior에 노출됨 | P28 prior-exposure theorem | likelihood가 null 성분에 무관하면 posterior도 그 성분을 학습하지 못함을 증명 |
| e-value finite-cover 조합 근거 부족 | P29 finite-cover lemma | convex combination e-value와 union-bound summary 명시 |
| \(F,G_F,\Pi,m g\) 분석 방법론 부족 | Data-analysis map section, P33/P34 | 식별집합, denominator sensitivity, delta method, covariance propagation 서술 |
| 최소 로컬 검산 필요 | Local Method Validation Checks | dust oracle, response-rank toy, e-value MC, identified interval 예시를 no-download 실행으로 생성 |
| 공개 보고서에 내부 방어적 용어가 보임 | public prose lint | 방어적 문구를 정의역/식별성/허용집합 용어로 대체 |
