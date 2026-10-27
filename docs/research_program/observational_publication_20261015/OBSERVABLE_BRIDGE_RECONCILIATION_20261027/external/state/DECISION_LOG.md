# DECISION_LOG

Decisions issued by the independent `physmath-research-harness:decision-gate-reviewer` subagent (did not produce the candidates), 2026-10-26/27, recorded here by the main session. "PROMOTE" = promote to the next-action list / formalization of a verification package; no decision is a physical acceptance. Full gate text: `review/DECISION_GATE.md`.

## D-001

DATE: 2026-10-27
DECISION: `promote`
OBJECT: H-0 — ΛCDM physical null for the H03 window dipoles (observer boost + radius-dependent bulk flow, 1/z_w columns; optional z_w 𝔮_1 column) under a mock-derived correlated covariance. New verification package V-0.
EVIDENCE_REVIEWED: E-X01 §5 (boost d.o.f.), E-X03/E-X03b (v_o = 188 ± 22 km/s, bulk 520 ± 91 km/s, falling dipole), E-I04 (saved coordinates, 36×36 covariance, 9×3 bulk-response design), E-I09/E-X09 (mocks), T-11 (effective dipole velocities ≈ 330/480/650/620 km/s from |D_w|/H_w × z_w).
RATIONALE: standard referent of a Hubble dipole (N-003); required control absent from the original hypothesis space; step (a) executable now on cached inputs.
ALTERNATIVES_CONSIDERED: keep H-1's −A/(cH) dipole (invalid for dust); H-7's 𝔮_1 (wrong depth trend as dominant term).
UNRESOLVED_RISKS: step (a) stays conditional on the inherited diagonal 250 km/s metric; boost (1/z_w) and bulk (R_w b) columns both decline with z → collinearity must be quantified; a per-window bulk saturates 12 coordinates, so the radial form must be fixed in advance; 6 parameters on 12 coordinates can reach τ by count → pre-register pass as T_min ≤ τ AND v_o within 2σ of 188 ± 22 km/s AND bulk compatible with 520 ± 91 km/s; SDSS PV mocks carry the SDSS footprint; CF4-selection mocks on request; M-07.
NEXT_GATE: V-0 pre-registration → execute (a) → verification-design review of (b) when mocks are available. Add CLAIM_AUDIT row C-OPT-06 (boost dipole law: 1/z_w term plus O(z⁰) aberration term; E-X01 §5, E-X02 full text).

## D-002

DATE: 2026-10-27
DECISION: `reopen` (REOPEN_HYPOTHESIS → restate as H-1Q)
OBJECT: H-1 PV-shear bridge.
EVIDENCE_REVIEWED: C-OPT-01/02 SUPPORTED; C-OPT-04 PARTIALLY (same object class, not identity); C-OPT-05 PARTIALLY (T-05 own inference); N-003 (dipole premise contradicted by established theory); T-11 (inner window at linear rms; windows 2–3 exceed it 2.4×/4.5× conditional on the inherited covariance; axes 12–28° from the celestial south pole; FP deletion moves the STF block by the signal size).
RATIONALE: quadrupole half sound and testable (V-1); dipole half uses an invalid premise and the written claim reads C-OPT-04 as an identity. The rewrite is one paragraph; V-1 step 9 proceeds unchanged under H-1Q.
ALTERNATIVES_CONSIDERED: PROMOTE as written (would formalize an invalid dipole premise); REJECT (would discard a live, cheap test).
UNRESOLVED_RISKS: physics vs covariance artefact vs footprint/method leakage undecided; no CF4-independent reconstruction beyond z ≈ 0.06; CF4 double counting with E-X03/06/07; T-11 archived only after the gate (now `validation/t11_h03_tomography.py`).
NEXT_GATE: restated H-1Q (quadrupole only; C-OPT-04 as same object class; H-1n as co-equal competitor; T-11 as baseline) → V-1 step 9 after the V-0(b) covariance.

## D-003

DATE: 2026-10-27
DECISION: `promote` (manifest before any run)
OBJECT: H-2 external polarized Bianchi atlas via AniLoS/AniCLASS; verification package V-2 amended.
EVIDENCE_REVIEWED: C-ATLAS-03 SUPPORTED (code inspected at line level); E-X10/E-X12 (comparator, polarization scale); E-I11 (gap); C-ATLAS-05 held as hypothesis, not premise; T-08 static PASS; N-005 (execution blocked in-session).
RATIONALE: the only lane whose blocking payload (B02/R23-ATLAS) is producible with public code today; manifest cost small; the T_irr gap goes into scope ("verified subset").
ALTERNATIVES_CONSIDERED: wait for ANICOSMO/Planck templates (not public); BASS as sole producer (forbidden as native inside htt_base; admissible only as cross-check, and only if it emits polarized VII_h output).
UNRESOLVED_RISKS: silent normalization (β_init = 1, Φ_i = −1 per unit IC → (σ/H)_0 map undefined) or parity error propagating into B04 injections; single-m Bianchi-frame output with stale docstrings; fixed handedness; V as sqrth ≈ 1e5 limit; IX forced to ℓ_max = 3; coupled vs decoupled background; regular/irregular identity of the cached BIANCHI v1.1 fixture; M-03; the atlas's use (B03–B05) is gated by L03, which cannot be cleared as written.
NEXT_GATE: pre-registered manifest + fixture mode identity → external smoke run (owner's machine) → convention-light validation against Pontzen–Challinor 2007 C_ℓ shapes, EE/BB ratio, TB/EB sign (primary independent check; BASS optional) → grid decision.

## D-004

DATE: 2026-10-27
DECISION: `reject` (as a bridge/verification package; keep the literature law for K03)
OBJECT: H-3 astrometric nonradial response law bounding S; V-4 withdrawn.
EVIDENCE_REVIEWED: C-PM-01/02 SUPPORTED; C-PM-03 INFERENCE_ONLY (audit-rule breach as payload); T-04 PASS (correct arithmetic in the wrong regime); N-001.
RATIONALE: window-scale S has no distance-independent PM response at Gpc; global S is excluded 8–9 orders below astrometric reach; V-4's pass criterion is unreachable and uninformative.
ALTERNATIVES_CONSIDERED: wait for Gaia DR4/DR5 (no foreseeable gain against 1e−10).
UNRESOLVED_RISKS: K03's ω/curl item closes only with an explicit statement that a quasar-tied frame absorbs global rotation (established theory, one paragraph); M-04 not needed for closure.
NEXT_GATE: none; K03 closure note (next-action 8).

## D-005

DATE: 2026-10-27
DECISION: `reopen` (REOPEN_EVIDENCE on M-01; on confirmation PROMOTE as an explicit L03-redefinition proposal)
OBJECT: H-4 PR4/NPIPE release-matched null lane.
EVIDENCE_REVIEWED: C-L03-01 PARTIALLY (M-01 unconfirmed); C-L03-02 SUPPORTED; E-X18, E-X19; L03 text ("PR4/FFP9 substitution is insufficient").
RATIONALE: strongest evidence in the set and a crisp cheap test (|C_ℓ^{(A−B)×full}| < 1 % at ℓ ≤ 5), but the documentation statement is required for the foreground half of the genealogy, and this gate cannot grant the L03 redefinition.
ALTERNATIVES_CONSIDERED: PROMOTE now (label would hide the contract boundary); FFP10 full-mission-only null (Planck 2018 VII practice).
UNRESOLVED_RISKS: single Commander foreground model (zero foreground variance); significance capped near 3σ (1/600) or 2.3σ (1/100); per-realization low-ℓ E suppression; data volume; all L01 SMICA/PR3 results would be re-derived; redefinition is the owner's decision.
NEXT_GATE: M-01 settled (document + triplet cross-spectrum) → re-entry with a written L03-redefinition proposal.

## D-006

DATE: 2026-10-27
DECISION: `reopen` (REOPEN_EVIDENCE: M-02 as a dimensional ρ)
OBJECT: H-5 bounded foreground-moment class; V-6 amended.
EVIDENCE_REVIEWED: E-I06 SUPPORTED; C-FG-02 PARTIALLY; reviewer's expectation radius 0.1–1 μK vs 0.379 μK target.
RATIONALE: ρ must be a norm in M = diag(d_i²) = amplitude × Var(β) × ln²(ν/ν₀) at ℓ ≤ 5 inside the mask, not σ(β) alone; a remainder bound (third order, multi-component) is required or the result is unusable either way.
ALTERNATIVES_CONSIDERED: run the "one line of algebra" as written (under-specified).
UNRESOLVED_RISKS: pivot dependence (β_s = −3, β_d = 1.5, T_d = 20 K); informative failure likely; H-4 and H-5 not combinable as independent foreground statements.
NEXT_GATE: dimensional ρ + one PySM d1/s1 remainder check through the 7-channel design → re-entry.

## D-007

DATE: 2026-10-27
DECISION: `reject` (standalone); the 𝔮_1 column survives inside V-0
OBJECT: H-7 second-order cosmography as the depth law; V-3 withdrawn.
EVIDENCE_REVIEWED: E-X01, E-X03, E-X04 SUPPORTED; E-I04 (T_⊥ = 15.316 > 12.59 for the depth-slope design); T-06 PASS; N-002.
RATIONALE: valid theory, wrong dominant mechanism (dipole falls with depth, 𝔮_1 grows ∝ z); vorticity terms contentless; the 9-parameter joint fit reaches τ by count; only Pantheon+ q_dip is non-circular.
ALTERNATIVES_CONSIDERED: Heinesen-weighted column instead of ad hoc D_z (rescales a column already linear in z_w; rank and T_⊥ barely move).
UNRESOLVED_RISKS: degeneracy of the ∝ z column with FP-fraction/composition columns; M-07 (Q_1 boost contamination unread).
NEXT_GATE: none as a hypothesis; a column in V-0.

## D-008 (programme-level reading recorded by the gate)

DATE: 2026-10-27
DECISION: `hold` (no candidate approaches a physical claim)
OBJECT: HTT observational programme, lanes H/K/V/L/B.
RATIONALE: ‖Ŝ_app‖_F = 0.0327 and T = 23.4 have undefined significance until a mock-derived covariance exists; the only independent dataset (Pantheon+, λ_1 = 0.021 ± 0.011; H_2/H_0 = 0.0 ± 1.3 %) is consistent with zero at 2σ; windows 1–3 quadrupole axes lie within 12–28° of the celestial south pole. Contract boundary: this gate cannot redefine L03 (PR4 lane) or H04/V04 (public Pantheon+ parameters in place of the nominal SALT2 binding); both are owner decisions.
NEXT_GATE: next-action list in `state/CLOSEOUT.md` (items 1–8).
