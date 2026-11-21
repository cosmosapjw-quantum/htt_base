# R90 / 원전과 이론·코딩 20단계의 실제 수행 범위

**원본 authority**: R78 60 nodes/129 edges (immutable), R47, R49, R62, R89의 검증된 scoped 증거를 재사용. R90은 별도 17개 solver-free / 5개 external-transfer 작업 overlay이며 원본 science acceptance를 승격하지 않음.

## 외부 원전과 도입 모델

1. Pontzen, Bianchi universes, http://www.scholarpedia.org/article/Bianchi_universes : Lie classification과 Einstein shear/anisotropic stress, transfer 필요성.
2. Pontzen & Challinor (2007), https://arxiv.org/abs/0706.2075 : Bianchi low-ell CMB T/E/B의 계층 및 편광. 원전의 편광 계산을 R90이 대체했다는 주장은 금지.
3. Fleury, Pitrou & Uzan (2015), https://arxiv.org/abs/1410.8473 : Bianchi I Sachs/Jacobi, direction/redshift drift. R89 optics 독립 검증 oracle. 아직 전 구간의 독립 수치 대조는 미수행.
4. Bradley & Eriksson (2006), https://doi.org/10.1103/PhysRevD.73.044008 : tilted Bianchi V 물리 source 모델 참고.
5. Cosmicflows-4 (2023), https://iopscience.iop.org/article/10.3847/1538-4357/ac94d8 : 발표된 method별 거리 moduli는 전역 MCMC intercalibration 이후 결과. 원본 upstream calibration posterior가 아님.
6. Quaia 2024, https://iopscience.iop.org/article/10.3847/1538-4357/ad1328 와 https://zenodo.org/records/10403370 : public selection maps는 상대적 선택함수. 세 파일만 ~/Downloads/htt_r90_minimal_inputs에 다운로드, 파일 checksum 검증, 외장하드·PR4 대량 다운로드 금지.

## 과거 작업의 계승과 비판

- R47은 geodesic-temperature Bianchi I morphology와 band-limited orbit likelihood를 허용하되, 그 일치가 고유 family 식별은 아니라고 명시.
- R49는 Class A/B 일반 3-vector tilt, Einstein constraint 및 배경 dynamics를 구현하고 조건부 multi-probe posterior를 계산했다. 모델의 transfer-conditional 성격은 유지.
- R62는 CF4 35,970 source-selected groups의 7개 nuisance 공분산, 95% 공동 ellipsoid 및 class witness 210개를 보고했고, apparent tensor와 source eigenframe이 관측 mask에서 다를 수 있음을 구성적으로 검증.
- R89는 완전한 CF4, Gaia, 5 radio survey 및 일부 CMB 원자료 분석과 조건부 covariance/null 결과를 보존.

## R1–R10

R1 연구 범위·R78 원본 고정. R2 원전·R47/R49/R62/R89 비교. R3 관측 STF 대 물리 shear·Lie type·CMB transfer 의미 구별. R4 q=0 canonical Codazzi 및 자유 q tilt 대안 모델 구성. R5 SO(3) 회전과 Cholesky-whitened 15D GLS 투영 유도. R6 Jacobi/exceptional VI rank, 정규화·퇴화 검산. R7 R62 7개 nuisance×12개 canonical/singular representative의 실제 계산 및 7 PHY 수치 검산. R8 84 compatibility witness, 고유한 family attribution 미성립 판정. R9 수학→코드·five-view typed 계약. R10 조건부 결과와 잔여 소스/모델 문제 보존.

## C1–C10

C1 SHA/branch 기준선. C2 R62·G07·R49 수식↔소스 함수 대응. C3 SVD nullspace·GLS·rotation 수치 구성. C4 SF-P1..P6와 SF-PHY-01..07 및 별도 B02..B05 전송 lane. C5 실행 가능한 R90 계산 코드 5개. C6 R90 targeted 회귀 및 R49/R78/R89. C7 물리 가정·극한 확인. C8 실제 7×12 계산 시간·기억 사용량·Quaia 전체 49,152×2 pixel 검산. C9 동일 호스트 자체 리뷰, native subagent NOT_RUN. C10 create-only JSON, block ledger, 다운로드 receipt, 재실행 계약 및 선택적 Git 게시.

## Claim boundary

관측 tensor x와 물리 normal shear σ가 동일하다는 관계는 별도의 source-specific transfer가 요구하는 **조건부 가정**. 일반 tilted matter q가 무제한이면 Codazzi q=M(N,a)σ의 대수적 충족만으로 family를 배제할 수 없고, 실제 EOS/DEC·유한-z optics·source covariance를 결합해야 한다. 현재 Q는 통계적 body, F는 선언된 Gaussian estimator measure, Pi 및 G_F는 물리적 근거 부재로 null이다. 84/84는 family-identification 성공이 아닌 source-conditioned consistency의 수치 결과.
