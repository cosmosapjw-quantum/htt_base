# R48-T23 local-agent 재개 프롬프트

기준일 2026-11-09 (Asia/Seoul)  
저장소: cosmosapjw-quantum/htt_base  
Branch: research/r48-tensorized-observational-convergence-20261109  
PR #572: open/draft, merge 금지  
직전 노드: R48-T22. 먼저 실제 branch HEAD와 tree SHA를 조회한다.

## 목표와 scope

이번 연구는 BASS solver 개발이 아니다. normal-frame momentum constraint에서 Bianchi 대수 데이터가 flux/tilt로 어떻게 투영되는지, 어떤 local observables가 남는지, 그 정보가 공동 posterior의 HTT x,Q,Pi,F,G_F 안에 보존되는지 검증한다.

금지 scope: Einstein-fluid evolution, BASS solver, Boltzmann hierarchy, LOS/CMB transfer, Cobaya/MCMC, real-data likelihood or family identification.

## 0. Worktree safety

branch, HEAD, remotes, worktree status, modified/untracked files, commit tree를 먼저 저장한다. 다른 작업물은 reset/clean/stash/overwrite하지 않는다. 현재 branch가 다르거나 dirty면 추가 승인 전 변경 금지.

## 1. Exact-head commands

    PYTHONPATH=htt:. python -m pytest -q htt/bass/diagnostics/test_bianchi_similarity.py tests/r48/test_bianchi_fivevar_identifiability_mock.py
    PYTHONPATH=htt:. python -m compileall -q htt/bass/diagnostics scripts/r48 tests/r48

Record exact commit/tree, Python/NumPy/pytest versions, commands, exit codes, stdout/stderr, durations and SHA256 for every changed file. Exact checkout test must not be confused with earlier scratch-package tests.

## 2. Adversarial mathematical review

1. Verify Loop-D momentum constraint M_i=kappa*q_i and q_i=(rho+p)*Gamma^2*beta_i.
2. Class A map M=((n2-n3)S23,(n3-n1)S13,(n1-n2)S12). Prove trace-shift kernel; examine exceptional shear strata.
3. Class B map and determinant 3*(S11*S12*S13+S23*(S12^2+S13^2)). Characterize determinant-zero strata.
4. Exact inversion r=beta/(1-beta^2), beta=2r/(1+sqrt(1+4r^2)).
5. II/IX pair has same M and tilt for identical S and enthalpy but different 3-Ricci eigenvalues.
6. Flat I/VII0 and open V/VIIh controls only in their isotropic FLRW local-metric embeddings.
7. Confirm frame arrows: beta_RM=beta_NM, beta_MO=-beta_NM, beta_RO=0 only for the declared collinear inverse-boost assignment.
8. Distinguish normal-congruence H(n), spacetime Ricci focusing R_ab k^a k^b, and intrinsic 3-R_ij.
9. Verify equal-covariance binary LLR sufficiency and target-specific KL statement.
10. Recompute nuisance projection; an unrestricted nuisance parallel to geometry contrast annihilates this mock's label direction.

## 3. Five-view integrity

All five views derive from one posterior table and preserve shared sample_id.
- x: sample-wise STF shear, tilt, mixed functionals and explicitly typed mock carriers.
- Q: instantaneous constraint/frame status; real anchors and dynamics unavailable.
- Pi: posterior and same-pipeline zero-tilt matched-null exceedance.
- F: posterior-mean-centered support and explicitly synthetic anchors.
- G_F: full posterior/data cross-window covariance; identity transport is mock-only.
No product of five pseudo-likelihoods.

## 4. One bounded sensitivity sweep

Vary curvature noise 0.5/1/2, enthalpy 0.5/1/2, Class-B determinant through zero, Class-A off-diagonal shear towards zero, cross-carrier correlations, label prior .2/.5/.8, and parallel/nonparallel nuisance columns. Report MI, MAP, Brier, rank-SBC, target KL, singular values and failure conditions. Do not label it an observational forecast.

## 5. Deliverables and stop

Create:
- INDEPENDENT_BIANCHI_HTT_OBSERVABILITY_REVIEW_KO.md
- BIANCHI_OBSERVABILITY_SENSITIVITY_REPORT.json
- REPOSITORY_BIANCHI_FIVEVAR_TEST_RECEIPT.json

At most one bounded repair after a reproduced failure. Keep analytic, numerical, implementation and runtime/environment failures separate. If exact checkout and hosted workflow pass, mark R48-T23 PASS_SCOPED; otherwise preserve the blocker. Stop before any solver or real-data task.
