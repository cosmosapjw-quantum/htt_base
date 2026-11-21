# R93 | 제3차 이론 10 · 코딩 10 연구 루프의 실제 수행 결과

2026-11-21 KST. 기준 연구 브랜치 research/r69-observable-physics-bridges-20261118, 시작 HEAD dd715302300d8f9f6c3e8a198c6ba768d694a43c. 원래 R78 과학 SSOT SHA256 = 90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11. 원본 60 nodes, 129 edges, NEXT_ID SQ-CF4와 과학 상태는 불변이다. R93은 실행한 source-bounded 이론·계산 연구이며 60노드 전체 과학적 acceptance 완료가 아니다.

## 이론 R1–R10의 실제 경로

R1: SQ-CF4·P1–P6·PHY01–07 목표와 Bianchi native transfer lane을 분리하고 기존 과학 정본을 고정.

R2: BASS, R49, R90–R92, R91 Plik-lite, Legacy 24 ZIP과 Mayukh 3판의 실제 source를 대조하고 Saadeh/Pontzen/Aluri 문헌의 적용 범위를 검토.

R3: CMB 999개 SMICA signal MC와 300개 재사용 noise, Commander의 제한된 MC, true normal-frame shear, conditional source STF의 의미를 구별.

R4: 세 경쟁 경로를 실행 후보로 선정: BASS–HTT Codazzi normalization, CF4 old boost 역변환, 정확한 Gaunt L=2 masked harmonic. Full-res E/B pilot과 legacy 불량 BiPoSH는 반례 경로.

R5: BASS 정규화에서 Sigma=sigma/H, N=n/H, A=a/H, qhat=kappa*q/H²에 대해

\[
\mathcal C_{\rm BASS}^a=3A_b\Sigma^{ab}+\epsilon^{abc}N_{bd}\Sigma_c{}^d-\hat q^a,
\qquad
(D_b\sigma^{ba}+\kappa q^a)/H^2=-\mathcal C_{\rm BASS}^a.
\]

동일 상태의 두 독립 구현을 12 Bianchi canonical/singular strata × 5 shears/flux/rotations = 60 cases에 적용. identity 최대 잔차 2.66e-15, SO(3) covariance 최대 잔차 4.44e-15. Matter EOS·DEC 허용성은 별도 의무.

R6: Legacy Mayukh formula zc=(1+zobs)/(1+beta cosθ)-1은 정확한 SR factor의 gamma를 빠뜨린다. 동일 부호 규약 아래 zc=(1+zobs)/[gamma(1+beta cosθ)]-1. 실제 CF4 35,970개 방향과 redshift를 이용해 beta=0.001일 때 95백분위 low-z 거리모듈러스 누락 효과 7.2171e-5 mag, beta=0.003일 때 6.5714e-4 mag 계산. 이는 \(d_L\propto z\) 저적색편이 근사다.

R7: 기존 K1 PR-150의 정확히 재생 가능한 NSIDE64 캐시로 SMICA signal 999개와 noise 300개를 모두 사용. 원본 FITS 603.384 GB를 다시 복사하지 않았다. 공통 PR3 temperature mask를 관측/MC 동일 적용, weighted monopole/dipole 제거, a_lm (Lmax48), 사전 고정 네 다중극 구간 (2–8,9–16,17–32,33–46)의 signed Gaunt L2 coupling을 계산했다. 잡음 재사용 999개 전체와 서로 다른 noise ID 300개를 구분해 leave-one-out MC rank를 도출했다. 20D 결합 rank는 300-noise 0.322259 (96/300 exceed)이고 반복-noise 999개는 0.249 (248/999 exceed). 탐색적 처리-조건부 랭크이며 신호 검출 증거가 아니다.

Gaunt 정의의 \(\ell'=\ell+2\) 선택규칙은

\[
G=(-1)^m\sqrt{\frac{5(2\ell+1)(2\ell'+1)}{4\pi}}
\begin{pmatrix}\ell&2&\ell'\\0&0&0\end{pmatrix}
\begin{pmatrix}\ell&2&\ell'\\-m&M&m'\end{pmatrix},
\quad m'=m-M.
\]

Y20 modulation 0.1 주입 시 네 구간의 A20 평균 변화는 +0.0692, +0.0826, +0.0777, +0.0772이다.

R8: Full resolution NSIDE2048 SMICA MC 00000 + noise00000 + 공통 mask와 NSIDE64 캐시 a_lm을 같은 low-order removal로 대조했다. 상대 coefficient 차이는 0.46%, 1.30%, 2.23%, 4.09% (네 위 구간 순서). 따라서 NSIDE64의 \(\ell=33..46\)은 high-l full-resolution precision이 아니다. 원본 NSIDE2048 Q/U, polarization common mask로 observed SMICA와 하나의 FFP10 CMB+noise MC에 대한 spin2 E/B를 실제 계산했다. 단 1개 MC이며 E/B null, mask leakage 보정, beam/foreground source는 미완료.

R9: Legacy bianchi_departure_v091 BipoSH estimator는 old A20에 양수 \(|a_{\ell m}|^2\)를 누적한다. 999개에서 old pseudo-A20은 모두 양수 (평균 0.9534)인 반면 진짜 signed Gaunt의 중심화된 A20은 구간별 음수 비율 49.75~50.85%. Legacy API/자료구조 재사용 가능, 원 추정량/p-value는 폐기 판정. Legacy 재딥스캔: 2,913 files, 24 ZIP, 4,320 archive members, 1,005 Python AST, 5,325 local FTS indexes. 네 압축 archive에서 extracted member와 1,294개 바이트 identity 일치.

R10: 기존 60-node science state/6-paper/7-PHY를 유지한 WORK_DAG_60_EVIDENCE.json, 이번 연구 source hashes와 해석, 재실행 scripts, private full alm/index, 다음 필요한 독립 물리 계산을 보존.

## 코딩 C1–C10

C1 HTT/R78 SHA, R92 HEAD, K1 source cache ID 고정.
C2 실제 BASS/HTT R49 Codazzi, Mayukh source, PR150 mask/alm, legacy BiPoSH를 읽고 수식·데이터·코드 매핑.
C3 물리 H-normalization, relativistic gamma, exact 3j quadrupolar coupling, empirical LOO rank 코드 설계.
C4 512 MB K1 validated cache와 300 unique noise ID를 primary로 선택. 전체 999 noise-reuse는 sensitivity only.
C5 7개 실제 신규 계산 스크립트: BASS signed Codazzi, CF4 gamma, full 999 T-alm/BipoSH, one-pair fullres QA, one-pair E/B, legacy estimator counterexample, legacy full-index.
C6 R93 targeted tests와 R78/R90–R92 scoped regression.
C7 independent fullres NSIDE2048 and SO3 signed identity, Y20 injection 및 beta=0 limit 실측 검산.
C8 source SHA, noise reuse cycle, cache A_lm residual, full 999 MC coverage, private NPZ identity 확인.
C9 bounded self-audit. Native independent agent dispatch는 이 호스트의 현재 도구에 없음: NOT_RUN.
C10 검증 산출물 selective commit/push, remote HEAD 비교 (실제 결과는 이후 최종 보고).

## 사용자 요청의 여섯 대주제·일곱 PHY와 과학적 claim ceiling

- P2: SMICA FFP10 온도 조건부 high-l a_lm/BipoSH 실제 새 계산. Commander release-matched all-sky null과 전구간 polarization/beam response 미완성.
- P3: CF4 35,970 source gamma correction과 기존 R36 저-k PV/R27 calibration quotient 계승. Upstream calibration·selection 및 독립 heldout 미확보.
- P5: BASS/HTT R49 전체 Class A/B geometric Codazzi code consistency 60 cases. Full physical tilted species EOS/optics, unique family attribution 미확보.
- P1/P4/P6: R90/R91 과거 full source-qualified conditional 결과 재사용, 새 물리적 acceptance 승격 없음.
- PHY01–07: R90에서 수행한 7개 source-conditional/constructed results를 재사용. Native polarized all-m hierarchy는 별도 lane.
- 기존 R89 반환 18 reused / 4 source-diagnostic / 9 input-block / 29 dependency-block 불변, R78 60 과학노드 완료 60/60은 거짓이므로 주장하지 않음.

## 다음 과학적 의무

1. 999개 실제 raw NSIDE2048 T/Q/U를 필요한 Lmax에서 streaming full-res harmonic으로 처리. Mask/beam/source matching과 300 unique-noise MC, repeat-noise sensitivity를 포함하고 K1 cache alias를 독립 통제해야 한다. 현재 full 999 T-NSIDE64 complete, full 999 E/B 및 high-res T는 NOT_RUN.
2. BASS–HTT on-shell Codazzi 일치에서 physical tilted EOS/DEC 및 finite-z Sachs/Jacobi source-forward 모형으로 확장. 이것이 family attribution에 직접 필요하다.
3. Legacy invalid A20 대신 source-matched L=2 BipoSH와 full mask mode-coupling, release-qualified null 구성. C_l power-only Plik-lite는 phase/shape likelihood 대체 불가.
4. SQ-CF4 upstream calibration/whole PV/selection/heldout, Commander release-matched full MC 문제는 계속 BLOCKED_INPUT.

이번 연구는 재현 가능한 bounded R1–R10+C1–C10 science computation route를 수행했지만 원래 60 science DAG 전체 물리적 작업의 완료는 아니다.
