# R92 -> 제3차 연구 루프: local scientific coding agent 인계

## 1. 실행 기준

작업 checkout: /home/cosmosapjw/Dropbox/bianchi/htt_base
연구 브랜치: research/r69-observable-physics-bridges-20261118
이 패키지 작성 시작 시 기준 HEAD: 13cf6b7dbf12144d51410395bd2962f281d884b3. 실제 최신 Git HEAD는 진입 시 확인할 것.
SSOT R78 INTEGRATED_DAG.json SHA-256: 90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11
과학 DAG는 original 60 nodes/129 hard edges. R90 solver-free 17 units와 external native-transfer 5 units는 별도 overlay. 과학 완료나 START_LOCAL_AGENT 권한을 의미하지 않음.

## 2. 먼저 읽을 파일과 인덱스

- R92 과학 평가: docs/research_program/observational_publication_20261015/R92_BASS_HIGH_ELL_THIRD_PREP_20261121/ASSESSMENT_THIRD_LOOP_KO.md
- R92 curated module/source SHA: CURATED_BASS_BIANCHI_SOURCES.json
- R92 geometry/Gaunt exact toy: HIGH_ELL_L2_GAUNT_CONSTRUCTION.json
- GitHub remote refs: GITHUB_REPO_PROVENANCE.json
- Native ABI blocker: BASS_NATIVE_AND_TRANSFER_READINESS.json
- 사용자 로컬 private searchable full index: /home/cosmosapjw/Downloads/htt_r92_private_index/R92_SEARCH_INDEX.sqlite. 92,127 physical files + 164,011 archive member names, total 256,138 entries. 파일 내용을 인덱스의 단어만으로 신뢰하지 말고 실제 source를 읽기. 개인 파일의 전체 경로·텍스트를 GitHub에 일괄 공개하지 않음.
- R91 2차 solver-free 실제 관측 계산 산출물 및 R90 84 canonical compatibility witnesses.
- BASS 원본 Dossier I/II/V/VII과 integrated dossier, Class A/B tilted code 및 pure-polarization tests.
- REC original Bianchi I characteristic, REI source-typed current/opacity, 사용자 Mayukh ver3/2 compressed manuscripts/codes. 모든 원본은 read-only.

## 3. 3차 이론 R1–R10 실행 목표

R1–R3: 정의·시계·normal/observer/matter frame·원래 scientific acceptance 고정. R49와 BASS의 복사해온 스냅샷이 아닌 현재 실제 source를 사용.
R4–R5: BASS Class A/B 3-vector tilted \(a,N,\sigma,q,\pi\)와 HTT R49 Einstein constraints를 독립 수치점 및 기호식으로 대응시켜 source types와 Lie family equivalence를 정의.
R6–R7: Sachs/Jacobi finite-z optical response 및 receiver/source angular transport를 실제 계산. Type I/V/VI_-1/9/VII_h/IX canonical history에서 observer tetrad boundary를 명시하고 한계·반례 검증.
R8: R90 84개의 conditional witness가 무엇을 판별하지 못하는지 관측 응답과 Bianchi family 동치류에서 재평가. 새 소스가 있으면 새로운 명시적 conditional exclusion을 제시하되 family 발견은 보류.
R9–R10: \(x,Q,\Pi,F,G_F\)의 물리 referent/null/measure/scale/transport를 직접 연결하고 결과를 저장. 물리 \(\Pi,G_F\)가 미정이면 null/None 유지.

## 4. 3차 코딩 C1–C10 실제 경로

C1: R78 SHA, 현 브랜치, BASS/REC/REI 각 HEAD와 원래 tracked dirty를 확인. 다른 repo의 사용자 코드를 절대 수정하지 말 것.
C2: BASS source 함수·식 ↔ HTT R49 및 R91 source carrier의 exact coordinate/clock/units 매핑. 독립 원전 인용 포함.
C3: \(q=\mathcal C(N,a)\sigma\), unit/c/metric signature(-+++), frame angular generator sign, null observer energy 검증.
C4: NATIVE_RUST / GEOMETRIC_FORWARD / HIGH_L_BIPOSH / OBSERVATIONAL_SOURCE / RECOMBINATION_OWNER lane을 독립적으로 배치. 원본 R78 dependency 수정 금지.
C5: 먼저 완전한 구현 가능한 하나의 실제 bridge (예: Type I Sachs/finite-z + BASS screen operator). Fake native Boltzmann 출력 금지.
C6: 독립 limiting-case oracle 및 targeted tests.
C7: 실제 high-l \(L=2\) covariance \( \ell\leftrightarrow\ell\pm2\) toy와 PR3 mask/beam/foreground injection 테스트, matched MC가 없으면 source null은 HOLD.
C8: 실제 \(\ell_\max=4,6,8\) hierarchy cutoff numerical convergence. 현 BASS는 lmax=6, native wheel SBOM/RF00 mismatch가 있으므로 먼저 provenance-locked wheel/owner environment를 복구해야 함. 개발용 override로 생산 PASS 선언 불가.
C9: 수식·물리·구현의 구체적 실제 반례/수치 진단을 한 번 adversarial 검토; native independent agent가 실제 가용할 때만 child dispatch.
C10: 실제 검증된 bounded 결과만 원래 research branch에 selective commit/push, 원래 60-node claim status 보존.

## 5. High-ell 세 갈래와 stop conditions

A. Data/BipoSH path: R91 PlikLite는 \(C_\ell\)-only 고-\(\ell\) scalar reference이며 phase data가 없다. PR3 실제 maps 기반 BipoSH \(L=2\) off-diagonal estimator를 기존 mask와 native matched MC를 이용해 구현. Legacy fsky-only estimator를 calibrated covariance로 승격 금지.
B. Native coherent model path: BASS/REC/REI photon transfer의 실제 source+geodesic+polarization+opacity가 충족되면 고-\(\ell\) physically coherent CMB T/E/B까지 확장. 기존 R49 조건부 transfer가 all-m full native Bianchi transfer가 아님을 명시.
C. Reference FLRW path: Cobaya/CAMB/PlikLite 재사용으로 background C_ell과 nuisance benchmark만 제공. Bianchi family attribution 대체 금지.

## 6. 현재 사실로 확정한 기술적 차단과 행동

- BASS 현재 lmax6, selected pure polarization tests 3 PASS. 원래 native BASS env에서 high-l l4 test 1 PASS/1 FAIL, missing rayon symbol; 별도 로컬 RF02B-R4 wheel은 심볼이 있지만 SBOM byte identity mismatch로 fail-closed. Installed binary의 소유권은 BASS 원래 repo. 설치·업그레이드/원본 변경은 별도 BASS-native scope에서만 수행. 원래 코드를 HTT로 복사하지 말고 source adapter로 연결.
- REC had existing tracked dirty files, branches/PRs mixed DRAFT/HOLD, raw output source not automatically accepted.
- One REC ZIP corrupt central-directory: do not extract, report unresolved. Five large TARs previously deferred but second-pass listing succeeded.
- No large full PR4/NPIPE download. 다른 공개 입력을 받으려면 파일별 SHA/size/official release 확인 후 /home/cosmosapjw/Downloads/에만 다운. 외장하드에는 신규 쓰기 금지.

## 7. Reproduction

In HTT checkout with exported PYTHONPATH=., PYTHONDONTWRITEBYTECODE=1:
- .venv/bin/python -B scripts/r92/prepare_third_loop.py --check
- .venv/bin/python -B -m pytest -p no:cacheprovider -q tests/obsstat/test_r92_bass_third_prep.py
- .venv/bin/python -B docs/research_program/observational_publication_20261015/R78_UNIFIED_SCIENCE_DAG_20261119/validate_unified.py --strict-authority
- .venv/bin/python -B scripts/r91/run_second_cycle.py --check

Acceptance: 7 roots indexed; ZIP/TAR 753/754 interpreted with one exact error; 256138 private search entries, 9 related GitHub metadata; curated 34 local sources + HTT scientific code + archive samples content hashed; symbolic high-l toy computed; BASS native runtime blocker labeled correctly. The 3rd 20-stage full science campaign is NOT_STARTED by this handoff.

Output per completed bounded unit: formula and model scope, actual source/experiment hash, units/frame, stdout/test evidence, conditional claim, unmet source/null, precise next owner action. No 60/60 SCIENCE PASS or novel Bianchi family detection without matched physical inference.
