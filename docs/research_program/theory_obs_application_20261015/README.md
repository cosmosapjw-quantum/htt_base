# HTT 기존 이론 -> 실제 관측 분석, 2026-10-15

이 연구 단위는 새 이론의 무조건적 승격이나 Planck/Bianchi 검출이 아니라, 이미 보존된 이론식의 적용 가능성을 실제 관측자료의 연산자·설계행렬로 검정한다.

**이론 루프**: THEORY_LOOP_KO.md. Masked Lorentz generator와 covariance nuisance Fisher 단조성, CF4 절편–기울기 분리정리, 한계·원전 대조.

**코딩 루프**: CODING_LOOP_KO.md. 실제 코드·CLI·테스트·대용량 source identity·성능·후속 handoff.

**수치 결과**: results/cmb_processed_boost_v2/result.json, results/cf4_optical_design_v1/result.json, evidence/scientific_oracles.json. 첫 CMB v1은 역사적 코드/명칭 교정 전 산출물이며 현재 과학적 해석에는 v2를 사용한다.

자료 운영: 원본 FITS/CF4 raw는 /mnt/extdrive/workdir 아래에서 읽기 전용, 작업 소스/파생결과만 HTT Git 트리에 작성. 본 패키지에 대형 관측 raw는 복사하지 않는다.

**실행 범위**: 기존 PR #533에서 분기된 진행 연구. 신규 joint physical likelihood, unconditional EGS/Bianchi theorem 및 H0 추정은 포함하지 않는다.

추가 복구 계산: 유한 SMICA NSIDE64 high-mode ell6..12 이미지 rank32와 최소-norm 상쇄 witness. 결과: evidence/processed_nuisance_quotient.json; 그림: evidence/processed_nuisance_compensator.png. 물리적 full-transfer no-go 주장 아님.
