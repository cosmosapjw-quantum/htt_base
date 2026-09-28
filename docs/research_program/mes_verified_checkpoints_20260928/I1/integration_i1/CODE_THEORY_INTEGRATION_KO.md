# I1의 현재 코드 연결 위치

고정 source: htt_base main cc162c804eecb3c588efc6edadbe057a8a67301f. Source-subset 정적 읽기이며 production 실행·수정이 아니다.

| 소비할 내용 | 기존 source | 이번 연결 판단 |
|---|---|---|
| exact J0/J1/J2, L_B | incoming R2 final §§3–4 | 기존 이론 재사용. 새 weak law로 다시 세지 않음 |
| omega=w0+p×a/2, timejet 소거 Z | incoming R5 KINEMATIC §§3–6 | fixed homogeneous geometry/tilt 전제. general-congruence rank12와 분리 |
| I1 A_(B,p), P_p A^-1 residual image | TARGET_RESPONSE_THEORY_KO.md Eqs.4–12 | 새로 명시한 조합. production adapter 미작성 |
| nuisance projected response rank | htt/htt/htt/infer/nuisance_rank.py | 전문 읽음. NumPy covariance whitening→SVD nuisance projector→rank의 diagnostic 부품. 실제 physical response·covariance를 공급하지 않음. positive-definite covariance 요구; I1의 수학적 직합 norm을 관측 covariance로 넣을 수 없음 |
| same-state confidence image | htt/htt/htt/infer/r9_confidence_image.py | 전문 읽음. 실제 JointCoverageEvent, covered JET variables, 동일 region, uncertain anchor 보존을 요구. 없는 event를 새 이론식으로 생성할 수 없음 |
| conditional source image | htt/src/common/conditional_source_image.py 및 MES R7 docs | 원격 전수목록/선택 취득 및 integration의 범위 기록 확인. BOX4 calibration q-proxy를 I1의 physical residual로 소비하지 않음 |
| T9 full/packed와 mixed | R10 unmerged branch 반환문 | 별도 sign/normalization/eligibility 범위. I1은 production T9를 호출하지 않으므로 그 old-sign 결과에 의존하지 않음. 새 I1 검산으로 기존 T9 admission을 열지 않음 |

## 실제 다음 입력 계약

후속 concrete target은 그대로 Z=sigma-STF(p a^T)다. 필요한 변수는 target-frame B moments rho,m,M2,M4; same-state p 및 geometry의 w0; residual r0,r1,r2의 source·시간/공간 미분 결합; 해당 공통 uncertainty/domain이다. Isotropic limit에서는 Z에 r0가 필요 없지만 anisotropic response에서는 H coupling을 보존한다.

Frame/source/normalization metadata만으로 residual의 유계성이 보장되지 않는다. target-frame rho>0 및 invertibility의 충분조건/직접 singular-value bound와 uncertainty의 joint image를 확인해야 한다. Realization 또는 confidence 주장에는 별도의 matter/Einstein·sampling law가 필요하다.

현재 코드가 이 source를 소비한다는 증거는 없으므로 구현 완료로 표시하지 않는다. 필요한 미래 adapter는 위 입력으로 A와 Z의 집합을 구성하고, source 미확보·singular inconsistent·unbounded target·rho=0 상태를 구분해야 한다. Full solver 개발을 공통 선행조건으로 추가하지 않는다.

Repository native CAS4/registered assignments의 과거 blocker는 해당 run의 상태다. 이 외부 이론 산출물은 그 기록을 수정하거나 대체하지 않는다. 기존 primary checkout 정책을 보존하며 새 clone/worktree 없이 문서·파일 identity를 전달한다.
