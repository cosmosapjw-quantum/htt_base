# R69: 물리적 x로부터 실제 Q, Π, F, G_F를 계산하는 우주론 연구

연구일 2026-11-18. Branch research/r69-observable-physics-bridges-20261118. 기준 commit d45bce72c655ecccd6165fd750e3f1bcfe69b46f (R68). 원래 6편 P1–P6의 과학 42노드와 acceptance는 수정하지 않는다. 일곱 개의 연구 축은 P1 tensorized inference, low-ell CMB morphology, radio dipole anomaly, beyond-FLRW kinematics, Bianchi/morphological classification, directional/redshift Hubble, observer boost vs global tilt다.

**사용할 정본**
- PHYSICAL_THEOREMS_KO.md: 광학 cosmography, 반구 mask leakage, Boltzmann 광자, Lorentz boost-only stress, Bianchi shear/curvature, Gaia E/B, 실제 제한적 Bianchi 조건과 source meaning.
- X_TO_FIVEVIEW_PHYSICAL_RESPONSE_KO.md: 실제 x input으로 물리적 Q, 법칙별 Π, 측도별 F와 물리적 시간수송을 요구하는 G_F의 각각을 유도·계산. Photon moment joint positive semidefinite Q, directional Hubble one-sided Q, Einstein shear signed-shape driver, closure-dependent photon F, observer/frame/kinematic source 계약.
- PHYSICAL_CLAIM_CANDIDATES.json: 일곱 연구 질문별 candidate claim, blocker, stop condition. Physics detection, new theorem 또는 Bianchi classification 주장 없음.
- RESULTS/GR_KINETIC_HEMISPHERES.json: 38,053 CF4 group unweighted sky window, exact Bianchi I test photon redshift, intensity fourth moment, R66 finite-band radiation stress boost template comparison 및 source-unqualified Gaia↔CMB counterfactual.
- RESULTS/GAIA_E1B1E2B2.json: Gaia-CRF3 actual sourcewise 16-component E1/B1/E2/B2 fit, 1,580,645 quality source, formal/per-sky-patch diagnostics; NOT validated cosmological vorticity or matter-normal shear.
- RESULTS/FIVEVIEW_X_RESPONSE_ATLAS.json: R61/R62/R63/R64/R65/R66/R69 original source results를 실제 x 입력으로 한 주제별 Q,Π,F,G_F 상태, physical versus statistical gauges, unavailable quantities.
- RESULTS/SYMBOLIC_FIVEVIEW_PHYSICS.json: symbolic shear-shape driver; radiation gauge spectrum; occupancy reference-measure effect.
- scripts/r69/physical_bridges.py, gaia_e2_b2.py, fiveview_response.py: executable numerical/observational analysis.
- tests/test_r69_physical_bridges.py, test_r69_fiveview_response.py: synthetic physics, actual source identity, numerical unit/scaling, closure integration, null status.
- REVIEW: original fresh independent reviewer findings and bounded repair evidence.
- VALIDATION.md, PROVENANCE.json: numerical status, exact source file identity and flags.

**확정 구분**
- established: GR cosmography, collisionless photon Liouville, Lorentz boost radiation stress, STF/Bianchi shear equations, Gaussian conditional score/covariance and kinematic moment realizability.
- derived: source/frame-defined x→Q mixed gauge, directional-H minimizer, shape rate D_tχ, continuum angular-occupancy response, exact x-only insufficiency of F.
- implementation verified / numerically checked: specific finite toy/regression, original CF4 38,053 window, Gaia 1,580,645 quality proper motions with sourcewise Gaussian working likelihood, source-checked R66/R61–R65 output readouts.
- unresolved: actual source-calibrated physical joint posterior, real Commander full T null/beam/DQ, Gaia redshift/AGN/scanning selection, CF4 method calibration, optical transfer and target normal-congruence shear.
- **NOT_READY_TO_SUBMIT:** no cosmological anisotropy significance, Bianchi family attribution, or physical shear/vorticity/global tilt detection.

피해야 하는 오해: F_sky의 solid-angle fraction은 photon energy fraction/parameter prior occupancy와 다른 측도다. Shared x에서 F는 선택된 event, reference measure와 closure에 종속된다. Flux-threshold, sky-map release 또는 apparent redshift labels를 원래 물리 GF(t)로 부르지 않는다. 두 물리 probe를 같은 posterior로 곱하려면 shared referent, frame, optical/kinetic response 및 cross-source covariance가 선행되어야 한다.
