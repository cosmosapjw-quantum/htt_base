# Decision gate — report of the `physmath-research-harness:decision-gate-reviewer` subagent (HTT observable-bridge run, htt_base a55036ad), 2026-10-27

## 0. Inputs and independent checks (reviewer's own)

- Read: state/{RESEARCH_STATE, EVIDENCE_LEDGER, CLAIM_AUDIT, HYPOTHESIS_GRAPH, VALIDATION, VERIFICATION_DESIGN, NEGATIVE_RESULTS}.md, review/ADVERSARIAL_REVIEW.md, validation/{validate_bridges.py, results.json}.
- The verbatim 29-HOLD list was recovered via `git show a55036ad:docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/POST_PUBLICATION_CHECKPOINT_20261026/README.md` (local clone checked out at f1007dd3). L03's text explicitly states "PR4/FFP9 substitution is insufficient"; H04/V04 explicitly require the R23-SN response.
- T-11 reproduced independently from the a55036ad file evidence/sources/H03_SOURCE_TOMOGRAPHY.json: |D_w|/H_w (0.0443/0.0398/0.0363/0.0259), raw/debiased ‖Q_w‖_F/H_w, noise floors (0.0093/0.0092/0.0115/0.0176), eigenvalues, STF χ² (47.7/92.0/117.1/18.8), Kalbouneh-axis separations (16°/19°/25°), celestial-pole separations (28°/14°/12°), FP-deletion ΔSTF5 = 1.50/2.00/2.73/2.71 km/s/Mpc. Findings: (a) basis-order CONCERN resolved — the producer stores `STF2_matrix_km_s_Mpc` and ‖STF5‖₂ = ‖Q‖_F to < 1e−4; (b) the window-4 row quoted the −0.0212 eigenvector's axis while the 37° angle belongs to the +0.0157 eigenvector (axis 107.2°, +31.4°); window 4 is noise-dominated; nothing downstream changes.
- Arithmetic: |D_w|/H_w × z_w ≈ 0.0011/0.0016/0.0022/0.0021 → effective dipole velocities ≈ 330/480/650/620 km/s — a 1/z_w boost/bulk column is the natural first design (H-0).

## 1. Decisions per hypothesis

### H-0 — PROMOTE (new package V-0)
Evidence linkage: boost d.o.f. E-X01 §5 eqs (5.1)–(5.7); v_o, bulk E-X03; saved coordinates, covariance, bulk-response design E-I04; mocks E-I09/E-X09. The 1/z_w form has no CLAIM_AUDIT row → add C-OPT-06. Physical validity: standard referent (N-003); consistent with the falling CF4 dipole. Mathematical validity: linear design change; 6 parameters leave 6 dof; boost and bulk columns both decline with z → quantify collinearity; fix the radial form of the bulk term in advance. Novelty: none (required control). Testability: (a) now on cached inputs; (b) needs mocks through the exact H03 operator. Robustness: (a) conditional on the inherited metric; only (b) decisive. Tractability: (a) minutes; (b) days + data request. Assumption burden: low. Remaining uncertainty: SDSS PV mocks carry the SDSS footprint; CF4 mocks on request. Dissent: 6 parameters on 12 coordinates can reach τ by count → pre-register pass as T_min ≤ τ AND v_o within 2σ of 188 ± 22 km/s AND bulk compatible with 520 ± 91 km/s. Unresolved risks: inherited covariance; mock availability; collinearity; M-07.

### H-1 — REOPEN_HYPOTHESIS (restate as H-1Q, quadrupole only; dipole handed to H-0)
Evidence linkage: C-OPT-01/02 SUPPORTED; C-OPT-04 PARTIALLY but read as identity; C-OPT-05 PARTIALLY (own inference); dipole premise contradicted (N-003). Physical validity: quadrupole half sound; dipole half fails; T-11: inner window at the linear rms, windows 2–3 exceed 2.4×/4.5× conditional on the inherited covariance. Mathematical validity: T-01/02/03 PASS; T-11 reproduced; depth prediction in CONCERN. Novelty: modest; new content = exact-operator mock null + eigenframe test. Testability: V-1 explicit; CF4-independent reconstructions reach only z ≲ 0.06. Robustness: weak (axes 12–28° from the celestial south pole; FP deletion moves the STF block by the signal size; working covariance). Tractability: medium. Assumption burden: comoving emitters; linear theory; constant per-method zero points; diagonal covariance. Dissent: quadrupole half passed T-11 in the inner window and V-1 is ready → the rewrite is one paragraph and V-1 step 9 proceeds unchanged under H-1Q. Unresolved risks: shared covariance problem; no independent reconstruction at z > 0.06; T-11 archive.

### H-2 — PROMOTE (formalize V-2; manifest before any run)
Evidence linkage: C-ATLAS-03 SUPPORTED (line-level); E-X10/E-X12; E-I11; C-ATLAS-05 correctly a hypothesis. Physical validity: linear nearly-isotropic regime, regular modes only; cannot produce T_irr (Saadeh's tightest VII_h bound); Bianchi I and scalars excluded → verified subset. Mathematical validity: T-08 static PASS; convention risks concrete (anilos.py 287, 310, 330–333, 471, 571, 615, 795, 828, 1127). Novelty: procedural. Testability: V-2 pass/kill exist, but criterion (iii) presumes BASS produces polarized VII_h output → make Pontzen–Challinor C_ℓ shapes, EE/BB ratio and TB/EB sign the primary independent check; BASS optional. Robustness: fragile to convention mismatch and retrofit; mitigated by pre-registration. Tractability: smoke run hours (owner's machine); grid days. Assumption burden: regular modes suffice; coupled vs decoupled unsettled; fixture mode identity unknown. Dissent: use (B03–B05) gated by L03 which cannot be cleared as written → effort may strand; subset omits the dominant comparator mode. Answer: only lane whose blocking payload is producible with public code today. Unresolved risks: silent normalization/parity error into B04 injections; BASS cross-check possibly unavailable; M-03.

### H-3 — REJECT (as a bridge/verification package; keep the literature law for K03)
Evidence linkage: C-PM-01/02 SUPPORTED; C-PM-03 INFERENCE_ONLY used as payload; bounding claim unsupported (N-001). Physical validity: law correct; application fails for both readings of S. Mathematical validity: T-04 PASS — correct arithmetic in the wrong regime. Testability: V-4 pass unreachable (Gaia systematics ≈ 12 μas/yr) and uninformative if reached. Assumption burden: "quasars comoving with the window congruence" false by construction. Dissent: Gaia DR4/DR5; K03 written for a global-S law → the law record is a documentation action; no systematics gain makes the bound informative against 1e−10. Unresolved: K03's ω/curl item closes with the statement that a quasar-tied frame absorbs global rotation.

### H-4 — REOPEN_EVIDENCE (M-01); on confirmation PROMOTE as an explicit L03-redefinition proposal
Evidence linkage: C-L03-01 PARTIALLY; C-L03-02 SUPPORTED; claim correctly conditional. Physical validity: CMB+noise+systematics pipeline null; single Commander foreground model → zero foreground variance. Mathematical validity: p-floor 1/600 (Sevem T+P) or 1/100 (Commander T); per-realization low-ℓ E suppression must be propagated. Testability: |C_ℓ^{(A−B)×full}| < 1 % at ℓ ≤ 5 crisp and cheap. Robustness: depends on M-01; selection protocol predeclared. Tractability: documentation hours; triplet test hours; 600-sim pilot large transfer. Remaining uncertainty: L03's own text forbids PR4 substitution → H-4 supports a contract change, cannot clear L03 as written. Dissent: strongest evidence, DEFENDED, cross-spectrum settles M-01 empirically → the written statement is still needed for the foreground half and the gate cannot grant the redefinition.

### H-5 — REOPEN_EVIDENCE (M-02 as a dimensional ρ, not σ(β) alone)
Evidence linkage: E-I06 SUPPORTED; C-FG-02 PARTIALLY. Physical validity: bounded low-order moments motivated; truncation remainder unbounded without a model. Mathematical validity: ρ must be a norm in M = diag(d_i²) = amplitude × Var(β) × ln²(ν/ν₀) at ℓ ≤ 5 in the mask. Testability: crisp (radius vs 0.379 μK). Robustness: pivot dependence; remainder. Tractability: hours + one PySM d1/s1 remainder check. Remaining uncertainty: reviewer's estimate radius 0.1–1 μK → informative failure likely. Dissent: V-6 cheap → but the current text is under-specified. Unresolved: H-4 and H-5 not combinable.

### H-7 — REJECT (standalone); the 𝔮_1 column survives inside V-0
Evidence linkage: E-X01/03/04 SUPPORTED; E-I04 refutes the sole-law claim. Physical validity: wrong dominant mechanism (dipole falls with depth; 𝔮_1 grows ∝ z); vorticity terms contentless. Mathematical validity: T-06 PASS; O(z³) convergence unchecked. Testability: V-3 confounded by the dominant 1/z structure; only Pantheon+ q_dip non-circular. Dissent: E-I04 refuted an ad hoc D_z column, Kalbouneh's Q_1 published → the weighting rescales a column already linear in z_w; Q_1's boost contamination unread (M-07).

## 2. DECISION_LOG entries (recorded in state/DECISION_LOG.md)

1. H-0 PROMOTE; H-1 REOPEN_HYPOTHESIS (→ H-1Q); H-2 PROMOTE (manifest-first); H-3 REJECT; H-4 REOPEN_EVIDENCE (M-01); H-5 REOPEN_EVIDENCE (M-02 dimensional); H-7 REJECT.
2. V-3 and V-4 withdrawn; V-0 created; V-1 restated under H-1Q; V-2 amended (manifest first; Pontzen–Challinor primary; BASS optional; fixture mode-identity step).
3. T-11 archived after the gate (`validation/t11_h03_tomography.py`, `validation/t11_results.json`); window-4 axis row corrected; basis-order CONCERN resolved.
4. CLAIM_AUDIT additions pending: C-OPT-06 (boost dipole law); C-H03-02 (T-11 window results, conditional). E-X02 to be read in full.
5. Audit-rule compliance: C-PM-03 moot after REJECT; T-05 keeps its own-inference label; M-07 affects H-0, H-1Q, H-7.
6. Programme-level reading: no candidate approaches a physical claim; ‖Ŝ_app‖_F = 0.0327 and T = 23.4 have undefined significance until a mock-derived covariance exists; Pantheon+ consistent with zero at 2σ; windows 1–3 axes within 12–28° of the celestial south pole.
7. Reproducibility: 29-HOLD README path recorded in RESEARCH_STATE.
8. Contract boundary: the gate cannot redefine L03 (PR4 lane) or H04/V04 (public Pantheon+ in place of the nominal SALT2 binding); owner decisions.

## 3. Ordered next-action list

1. V-0(a): refit the 12 saved dipole coordinates with {constant dipole (3), 1/z_w boost/bulk (3), optional z_w 𝔮_1 (3)} under the inherited 36×36 covariance; report T_min per design, which column carries the reduction, fitted v_o vs 188 ± 22 km/s, bulk vs 520 ± 91 km/s, column conditioning. Pre-register pass/kill first. Zero new data; minutes.
2. Ledger/audit repair: quote the boost dipole equation (E-X01 §5 eqs 5.1–5.7; read E-X02 full text), extract Kalbouneh §6 normalization (M-07) → C-OPT-06 row and C-OPT-04 normalization. Hours.
3. V-5 steps 1–5: NPIPE §5 / NERSC README statement on shared input sky per index (M-01); then (A−B)×full cross-spectrum at ℓ ≤ 5 on 2–3 Nside-16 triplets (030 mc_00200 partly cached). Hours plus a small download.
4. V-6 (amended): dimensional ρ from Planck 2018 XI / Int. XXII dispersions and ℓ ≤ 5 dust/synchrotron amplitudes in the mask → identified-set radius vs 0.379 μK; then one PySM d1/s1 remainder pass through the 7-channel design. Hours to a day.
5. Restate H-1 as H-1Q (quadrupole only; C-OPT-04 as same object class; H-1n as co-equal competitor; T-11 as baseline). Hours.
6. V-2 manifest pre-registration (β_init → (σ/H)_0 via nteb_tensor at η_0, T_CMB factor, Euler convention, phase, handedness, coupled/decoupled background, mode identity, IC) + fixture mode identity from provenance; then the external AniLoS smoke run `Anilos({'sqrth':0.1,'Omega_K':1e-6}).tensor_solver(); alm_tensor(10)` with Pontzen–Challinor convention-light validation; BASS cross-check only if BASS emits polarized VII_h output. Owner's machine; a day.
7. V-0(b)/V-1 step 9: run mocks through the exact H03 operator (same 35,970 positions, 19 nuisance columns, D metric) for a correlated covariance and a null distribution of (D_w, Q_w); SDSS PV mocks now (footprint caveat), request the 64 CF4-selection mocks (Duangchan 2026) and CF4TF/combined mocks; then eigenframe vs a CF4-independent reconstruction (2M++-type, z ≲ 0.06). Days plus data request; decides H-0 vs H-1Q vs H-1n.
8. K03 closure note: literature nonradial law (Darling 2014; Marcori et al. 2018), no-sensitivity statement for window-scale and global S, one paragraph on vorticity being unobservable against a quasar-tied frame; withdraw V-4; do not spend the CRF3 sample on an S bound. Hours.

## 4. Mapping of the 29 residual HOLDs

DATA = clearable with obtainable data; THEORY = clearable with established theory; REDEF = redefinition required (HOLD as written cannot be met); PROC = procedural/irreversible; NA = not addressed.

| HOLD | Category | Justification |
|---|---|---|
| B02 | DATA (partial, external) | Externally produced, manifested AniLoS/AniCLASS atlas (H-2) supplies the payload for regular VII_h/IX (+V, VII_0 limits); T_irr, Bianchi I, scalar modes excluded; admission is a repo procedure. |
| B03 | REDEF | Requires L03's release-matched processing law in addition to B02; L03 cannot be met as written. |
| B04 | REDEF | Downstream of B03/L03. |
| B05 | REDEF | Downstream of B04; the Planck low-ℓ likelihood itself is public (PR4 LoLLiPoP cached) but not the binding item. |
| H02 | DATA (on request) | CF4-selection mocks (64, Duangchan 2026; CF4TF/combined on request) supply targeting/rejection and PV cross-law; Stiskalek-type forward model gives the law's shape; calibration ancestry from EDD/authors (M-06). |
| H04 | REDEF | Text requires the R23-SN physical response, unobtainable from public products (author request = M-05 is the only non-redefinition route); the PV-law/PPC/covariance content is clearable with the H02 mocks (V-0b). |
| H05 | DATA | Mock-derived correlated covariance with CF4 windows and method footprints replaces the 250 km/s working metric; Wang 2026 data not required. |
| H06 | DATA (conditional on H05) | Competing model (H-0) and independent data (Pantheon+) exist; must be a new result, not a relabel of R32 H03. |
| K03 | THEORY | Nonradial/curl law is literature (Darling 2014; Marcori 2018); closure = law + no-sensitivity statement; Gaia cross-source covariance and NNR transfer buy nothing for S (N-001). |
| K04 | THEORY (conditional on H04) | Common-frame transfer is the covariant boost transformation (Heinesen §5; Maartens 2024); needs only the transfer part of R23-CONGRUENCE, not its SN binding. |
| K05 | REDEF | Demands a joint physical cross-law composing radial, PM and clock carriers; the PM carrier has no S-sensitivity in any regime, so the joint identified combination is empty at any obtainable precision. |
| K06 | REDEF | Downstream of K05. |
| L03 | REDEF | Planck 2018 released no HM FFP10 CMB realizations; the HOLD text rules out PR4/FFP9 substitution; the obtainable lane (PR4, H-4) is a redefinition. |
| L04 | REDEF | Inherits L03; under a PR4 redefinition it becomes DATA with a 1/600 (or 1/100) p-floor. |
| L05 | REDEF | Chain via L04. |
| L06 | REDEF | Chain via L05. |
| R23-ATLAS | DATA (partial, external) | Same payload as B02; "scoped source gap" closes for regular modes only. |
| R23-CONGRUENCE | REDEF | Its "nominal SN fit binding" is the R23-SN artefact set; the transport law is THEORY; PM/NNR/clock maps carry no S information (N-001). |
| R23-SN | REDEF | PS1.nml, out_train_v7_1_bd17fix/SALT2.MODEL000, FITRES binding are internal pipeline names, not public products (E-X17, M-05); the public release cannot bind the four frozen parity bounds; author request is the only alternative. |
| R25-DISTANCE-CONDITIONAL-EVIDENCE | PROC | Fit count ≥ 21 against a frozen cap of 20. |
| R25-GAIA-RELEASE-TAG-ASSOCIATION | PROC | Contemporaneous pre-PM records missing. |
| R25-PR3-FREQUENCY-TENSOR-CROSSPREDICTION | PROC | One-use native resume consumed. |
| R25-PR3-STAGED4-TENSOR-CONTRAST | PROC | Lifetime RSS/cgroup binding not establishable retroactively. |
| R26-CF4-FINAL-GROUP-CALIBRATION-RESPONSE | REDEF | Release prints DMav−DMzp = 0.147 for all noncalibrator rows; paper Eq. 8 gives 0.138; frozen 0.137 excluded. M-06 (cause) obtainable from EDD/authors but cannot make the frozen equation hold. Scientific stake is parity only: a global constant does not change ℓ ≥ 1 STF morphology (C-CF4-03). |
| R26-FULL7-STREAMED-SPIN2-QUADRATURE | PROC | One-use no-retry rule binding. |
| R26-SMICA-EXACT-PR3-IMPLICIT-ROW-PROJECTION | PROC | Frozen ≤ 20 s finalization cap not establishable retroactively. |
| V04 | REDEF | Requires R23-SN parity; the PV-law half is DATA via H04/V-0(b). |
| V05 | REDEF | Inherits V04; the matched null/prior/injection law is otherwise DATA (mock null + boost/bulk prior from H-0). |
| V06 | REDEF | Chain via V05. |

Tally: DATA 5 (B02, H02, H05, H06, R23-ATLAS); THEORY 2 (K03, K04); REDEF 16; PROC 6; NA 0.
