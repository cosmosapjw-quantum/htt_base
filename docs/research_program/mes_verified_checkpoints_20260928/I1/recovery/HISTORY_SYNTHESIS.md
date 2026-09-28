# HTT/MES accumulated research recovery — source-grounded synthesis

Recovery date: 2026-09-28. Scope: the `recovery/research/history` subtree of the supplied research backup. This report is a read-only reconstruction; no remote ref, production source, scientific gate, or past outcome was changed. Statements marked **historical** are what the preserved document reports, not newly executed science.

**Coverage expansion / corrected resume authority:** Sections 1–9 reconstruct the `history` subtree only. The bounded follow-up in Sections 10–13 covers the entire 372-file outer research payload and the already-acquired current remote integration. The original thread actually ends at **MES_GENERALIZED_TENSOR_R2 V3, 2026-09-20**, not at the September 16 history packet. Current main additionally incorporates the separate September 27 R3/R4/R5 continuation. Read Sections 10–13 before using any earlier “next task” or unresolved-convention statement as the current frontier.

## 1. Recovery extent and source identity

The history subtree contains **79 regular files**, including **37 top-level archives**. Archive listing recursed through nested ZIP/TAR inputs without broad extraction: **3,047 member rows**, of which 993 occur at nested depth, and no archive-read error or budget truncation was recorded. Compressed bytes examined: 117,851,744. Limits were depth 4, 64 MiB per nested archive, and 512 MiB cumulative archive input. These are inventory figures, not counts of distinct scientific results or complete reading.

`HISTORY_ARCHIVE_INDEX.json` records the top-level files and member listings. `HISTORY_NESTED_ARCHIVE_INDEX.json` records recursive locators. All five 2026-09-16 theory packets are extracted in `recovery/latest_loops` for direct review. Their original outer archives remain intact.

The September 16 packets, the R9 integrated plan, R2 physical-response paper, R3 native benchmark, R7 interim report, catalog scan, and input-foundation report were substantively read. The 109,589-byte earlier aggregate `HTT_THEORY_RESPONSE_KO_20260907.md` was structurally searched and partly read, not re-certified in full. Earlier audit packages were inventoried with selected prose/source reading. The restoration of an archive does not certify every embedded historical source or scientific statement.

## 2. Latest theory is a sequence of revisions, not five compatible snapshots

All five packets have date 2026-09-16, but their explicit dependencies establish this logical order:

| Packet | Contribution | Later disposition |
|---|---|---|
| `htt_paper_a_theorem_loop_20260916.zip` | First-jet no-go; radial vorticity null; depth identifiability; nuisance quotient; STF2→STF3 inverse and sharp conditioning; adaptive-null counterexample | Most algebra survives; novelty of general mathematics explicitly rejected |
| `htt_cmb_kinematics_redshift_loop_20260916.zip` | Separate cosmographic and radiation lanes; low-ell temperature/brightness adapter; redshift-kernel rank | Its `dot T_ab=+sigma_ab` and positive shear-memory formula were subsequently withdrawn |
| `htt_paper_a_v2_convergence_loop_20260916.zip` | Proposed four-result paper spine: instantaneous no-inverse, bridge residual, strict-bridge rank, redshift lift | The radiation-quadrupole sign is superseded; bridge novelty is subsequently downgraded |
| `htt_paper_a_reloptics_source_seal_loop_20260916.zip` | Four-axis measurement type registry; primary-source comparison; generic/specialized hierarchy sign conflict | Closes bridge novelty as prior art; historical `BLOCKED_PHYSICS_SIGN_SEAL` |
| `BASS/htt_paper_a_geometrical_optics_mapping_loop_20260916(1).zip` | Local ray generators H,V; Sachs/Jacobi lane; endpoint radiation map; independent energy-integration T9 sign derivation | Latest preserved analytic direction; historical sign seal PASS, production T9 correction still only a candidate |

In particular, the earlier V2 closeout's “next unit: source audit Main Theorem B” was already attempted by the following two packets. Restarting that work as though untouched would regress the thread.

### Latest intended physical factorization

The final packet replaces a direct `observed CMB STF ↔ spacetime kinematics` arrow with:

1. The first jet of a specified timelike congruence determines the **local ray generators** H(e), V(e).
2. Curvature determines null-bundle Sachs/Jacobi evolution.
3. Source radiation, ray transport, Jacobi/source remapping, collisions, and endpoint observers determine intensity/temperature/polarization.
4. Observed Q/O are projections of that final sky.

Timelike shear, null optical shear, image/lensing shear, and observed CMB quadrupole are four different objects. Congruence vorticity, null twist, and screen-basis rotation are also distinct. A light cone's null twist can vanish while the timelike matter congruence has vorticity.

The local H field determines expansion, acceleration and shear (9 components), with a vorticity kernel. Adding the *ideal local* V field supplies an l=1 B-mode in the historical derivation and an ideal 12-component inverse. **The packet does not provide an operational theorem equating local V to measured endpoint proper motion or establish survival of that inverse after observer-frame rotation and calibration nuisances.** That is a meaningful next theoretical question, not a completed observational result.

The final packet has no explicit machine-readable next-work-unit ID. A defensible successor is therefore an explicitly newly named work unit: reconcile the latest theory with current repository authorities, seal direction/omega conventions, and derive the endpoint measurement/nuisance map for the proposed H,V inverse. This is an inference from the surviving frontier, not a recovered historical task ID.

## 3. The T9 sign history must be preserved correctly

The relevant old repository snapshot throughout the newest loops is:

`cosmosapjw-quantum/htt_base@50ea6d76ace70dec57b8794ab0d1cf9b8fab42cb`.

Historical inspected paths:

- `htt/bass/hierarchy/terms.py`: `T9_shear_down`, prefactor `-(ell+2)`.
- `htt/bass/hierarchy/hierarchy_rhs.py`: sums terms then applies `-a*sum_T`.
- `htt/bass/hierarchy/mode_mixing_blocks.py`: same negative `pre9`.
- `docs/lowell_bianchi_solver_reference.md`: repeats the negative sign.

The intermediate source-seal packet found that this convention gives opposite ell=2 injection to exact photon redshift, Räsänen's temperature law, specialized radiation anisotropic-stress evolution, and MES. It withdrew the previous `dot T_ab=+sigma_ab` statement under its declared positive brightness convention.

The final packet derives from the cited phase-space hierarchy:

`-Delta_l [∫ E^4 F'_(l-2) dE -(l-2)∫ E^3 F_(l-2) dE]`

with vanishing `E^4 F` endpoint term, hence a **positive LHS** coefficient. For book intensity moments this is

`+(l-1)l(l+2)/[(2l-1)(2l+1)]`,

equal to `+8/15` at l=2; for direct angular brightness coefficients it is `+(l+2)`. The physical RHS source-only oracle is therefore `dPi_2/deta=-4 a sigma Pi_0`.

Historical final labels: `PHYSICS_SIGN_SEAL=PASS`, `REPO_T9=HIGH_CONFIDENCE_SIGN_BUG_CANDIDATE`, `PRODUCTION_MUTATION=NO`. These labels are **not** evidence that the current repository still has the bug or that a patch was subsequently applied. Current source/tests/commits must decide that separately.

Required historical implementation acceptance cases were explicitly listed: isotropic-monopole/shear injection; independent energy integral with `F=exp(-E)`; normalization match to `+8/15`; a deliberate sign-flip mutation that makes the physical oracle fail. Existing packed/full parity sharing the same sign is insufficient.

An independent ell=0 documentation issue was also recorded: the special-case table said only T1/T3 survive, whereas the full equation and inspected code retain acceleration×dipole T4 and shear×quadrupole T7. Its scope is historical documentation consistency, not evidence of a current monopole implementation bug.

## 4. Reusable exact theory and surviving novelty boundaries

### Restricted boost response

For nonzero real STF2 Q, the restricted thermal-scalar first-order response is

`(B_Q beta)_abc = beta_a Q_bc + beta_b Q_ca + beta_c Q_ab -(2/5)[delta_ab(Q beta)_c+delta_ac(Q beta)_b+delta_bc(Q beta)_a]`.

The preserved algebra gives `M_Q=(Q:Q)I+(6/5)Q^2`, `(B_Q beta):Q=M_Q beta`, `B_Q*B_Q=3M_Q`, and `beta_hat=M_Q^-1(O:Q)`. This is a least-squares response projection, not proof of a physical boost origin of arbitrary O. The sharp condition bound is `kappa_2(M_Q)≤5/3`, saturated at signed Q spectrum proportional to `(-5,4,1)` up to permutation/sign. This remained the strongest exact novelty candidate after the final source audit, with priority still uncertified.

**New recovery finding, prose-level:** the theorem packet's displayed STF trace proof contains an extra `(Q beta)_c`. The actual trace of the first three terms is `2(Q beta)_c` because `Q^a_a=0`; the text writes `2(Q beta)_c+(Q beta)_c` and then concludes zero. The definition and subsequent contraction/Gram equations need not be wrong, but that printed proof line must be corrected before manuscript use. This is a direct symbolic index-reading finding, not a newly run CAS result.

### Foundational statements that are not novelty claims

- Pointwise observer velocity does not specify the first jet of a congruence; a local normalized vector-field construction proves the freedom.
- Scalar radial responses annihilate an antisymmetric velocity gradient. More radial depth does not restore this vorticity channel.
- Same angular irrep sources with sampled kernels T_z have response `T_z⊗I_d` and rank `d rank(T_z)`. Distinct bins alone do not establish practical separability.
- With unrestricted deterministic nuisance, identifiability uses `ker(qR)` and `rank[R N]-rank N`; whitening does not remove structural nulls.
- Positive-definite covariance weighting changes conditioning/precision, not the exact response kernel.
- Full adaptive procedures must be recomputed inside the null/randomization procedure unless a separate conditioning theorem justifies freezing them.

### Convention hazard that must be sealed

The first theorem packet writes `nabla_b u_a = ...+omega_ab`. The later CMB/source-seal packets write `nabla_a u_b = ...+omega_ab`. The final mapping packet states `V=-epsilon^a_bc omega^c e^b=omega×e` without explicitly binding the axial dual to one of these index orders. Transposing the derivative convention changes the antisymmetric tensor sign. This is a **convention-binding gap**; it is not, by itself, proof that the final V equation is physically false. A current theorem must define omega_ab and omega^a before quoting the curl/inverse signs.

## 5. R9 integration: usable advances and preserved counterexamples

Source: `HTT_R9_Theory_Integrated_Research_Plan_v1_KO.md` (dated 2026-09-12 UTC / 13 KST).

| Authority | Historical identity |
|---|---|
| R9 plan | commit `5e4e899c0dfa2028d81a82ca68ccd11203947470`, tree `dbfcdc9abc2298534b65f50ae6a19ab0012aa999` |
| Role catalog | commit `9b725899a25fa410e7c3686ce36afaa667d14646`, tree `508500f4eadeafcdfb316978c4a05a6b238a13f7` |
| R9 source path | `docs/research_program/tensor_joint_r9` |
| Theory candidate path | `docs/project_catalog/proofs/roles/research_proposals.json` |
| Candidate JSON blob | `0ad118ed8974c43b2de78ddeff952379e9369a51` |

The 172 candidate source intervals, 93 auxiliary propositions and 39,072 deferred role groups are **not** independent proven theorems or a completion denominator. Six proposed integration bundles are robust identifiability, stochastic information/design, shared calibration/confidence sets, morphology/rank, conditional physical image/sharpness, and new channels targeting known nulls. R9T labels are proposed work names, not evidence of already executed canonical nodes.

Three explicit historical counterexamples must survive import:

1. `r_l→0` does not ensure Fisher-tail convergence: `r_l=1/l` gives a harmonic divergent contribution. The ideal sufficient power-law condition is decay exponent greater than 1.
2. Global max-test p is not always at least the maximum local p. The preserved three-row example gives local `(1/4,1)` but global `1/4`.
3. A signed-ratio endpoint iff claim fails: on s∈[0,1], `N=-2+s`, `D=2-s` gives joint ratio −1, but independent rectangle upper endpoint −1/2 despite oppositely signed slopes. Joint-set inclusion survives; the proposed general endpoint criterion does not.

R9 also explicitly derives the distinction between fixed-source rank and law information: for a two-block isotropic Gaussian Q/O model, first-order boost Fisher is proportional to `(C2-C3)^2/(C2 C3)`, so equal powers give zero first-order covariance information despite an injective fixed-Q boost map. Gaussian law, Doppler weight, source blocks and nuisance assumptions must travel with that statement.

Another surviving conditional result is robust discrimination of compact convex whitened Gaussian mean sets: their minimum separation δ gives minimax balanced maximal error Φ(−δ/2); the result is not automatically valid for nonconvex discrepancies or state-dependent covariance. Physical sharpness is split into algebraic image, constraint-satisfying initial data, local evolution, and observables over the needed spacetime window.

## 6. Earlier science that should be integrated, not overwritten

### R2: physical response and released data

`HTT_PHYSICAL_RESPONSE_THEORY_R2_KO_20260907.md` provides:

- A transformation descends through reduction R iff it preserves `ker R`. Deleted dipole modes can alter the retained physical boost derivative, so a released map alone generally lacks the source lift needed for physical boost inference.
- True thermal temperature and intensity-linearized temperature have different quadratic coefficients; bandpass weights and frozen/refitted release operators matter.
- The boost-image projector stays well-defined at repeated nonzero Q eigenvalues even when an inverse orbit chart fails; chart refusal is not failure of all forward morphology.
- Response discrepancy must inflate confidence sets explicitly; a deterministic unknown bias is not automatically Gaussian covariance.
- Redshift and luminosity-distance frame transforms must be consistent. A raw-observable mixed-frame construction leaves a depth-independent magnitude dipole. This was an analytic oracle, not an accusation that CF4 necessarily has that processing error.

The R2 document says no new code/CAS/simulation/observational run was performed. Its formulas are historical analytic derivations, not newly tested production capabilities.

### R3: exact restricted native benchmark

`HTT_NATIVE_THEORY_R3_KO_20260907.md` selects LRS Bianchi I, two equal/opposite geodesic dust streams, collisionless initially isotropic photons, and Λ. Momentum flux cancels, anisotropic stress does not. Photons feed back into Einstein equations via exact angular stress integrals. It is a synthetic homogeneous benchmark, not a completed realistic recombination/reionization/perturbation cosmology.

It explicitly keeps c, ħ and k_B; `a_parallel gamma beta=kappa` is conserved and `dot beta=-H_parallel beta(1-beta^2)`. Normal-frame sky has exactly zero odd multipoles and a quadrupole proportional to integrated anisotropy b, not instantaneous shear dot b. Dust congruences in this chosen model are geodesic and irrotational. It therefore cannot serve as a vorticity explanation merely because it is tilted.

The source/observer optical problem includes geodesic and Jacobi equations, endpoint redshift, source-rest screen, pre-caustic domain, reciprocity and exact initial conditions. In its small-velocity FLRW response, the local/global kernel ratio has derivative `H'(z)chi(z)/c`; same depth or constant-H limits remain degenerate, and low-z splitting begins only quadratically in the ratio.

The selected-population likelihood includes light-cone intensity, selection normalizer, shared zero-point calibration and distinct Poisson/fixed-count experiments. Marginalizing a shared calibration once and conditioning on N generally do not commute. Release compression has a precise information-loss criterion through conditional scores. None of this supplies the missing actual CF4/Planck product law automatically.

### M1: CMB input/calibration frontier

The continuation packet distinguishes processed Q/O compatibility from physical beta/global-tilt inference. Its finite primary target jointly fits ell=0–5 on masked NSIDE64 pixel centers, preserves Q/O and uses one fixed boost-image fraction score. The 300 signal/noise pair experiment requires one-to-one ID pairing, qualified release equivalence, and all-row finite/defined status. Missing or undefined rows cause the full primary rank to abstain.

Historical defects include reproduced NaN handling in the old pooled-rank helper and a source-visible amplitude-based K-versus-microkelvin unit guess. These are historical findings pending current-code reconciliation. Reusing noise IDs does not create independent null rows. An additional same-map channel contributes information through its conditional response and cross-covariance, not its row count alone.

## 7. Historical implementation/audit gates cannot become current gates by copying

R7 interim audit pins branch `implementation/tensor-joint-r7-20260908`, HEAD `433433409ee95f48759fca4193b727a43bde4872`, design `89a9a901e950cb186dcfedb95a250493fe4fd6fa`. It preserves conditional qiso results and scoped reusable code but does not accept all R7 work. Findings: substring-based CAS PASS recognition, missing evidence/donor dependencies in resume fingerprints, an orbit-distance cutoff that returned zero lower bounds for actual large pools, misclassified donor failures, and incomplete exact singular-Gaussian support handling. These are findings at that SHA.

The later input-foundation packet records R8 set-valued derivative/remainder propagation, including 204 finite and 34 unrestricted fixture support queries. It also preserves synthetic orbit-pool outcomes (5 conservative non-rejections, 25 unresolved out of 30) and M301/M1000 rank intervals `[1/M,1]`. Frozen full-continuation remains historical `STOP_INVALID` because strict 60-second checkpoint requirements were exceeded; this does not invalidate every rational enclosure or imply physical-model rejection.

The R5 audit recognized real DESI BGS_ANY observational analysis and real JWST host-comparison products, while identifying coordinate/null-law/selection defects or conditional limitations. DESI's ICRS/Galactic confusion affects direction, not automatically amplitude. A weighted-count observation is not generically matched by an unweighted Poisson mock. Same-host JWST method contrast removes shared geometric-distance response; it can inform calibration without adding direct tilt response. Singular covariance boundaries impose exact constraints, not only pseudoinverse penalties.

All these remain useful **historical error/acceptance cases**. Current code must be read before calling any of them an unresolved current defect.

## 8. Catalog history and deletion semantics

The preserved database scan is pinned to `57ecfe2176bf8be28327edf500a4ca5136c6b15b`; R8 membership baseline `efc5f30666b96782f946375551f0068bb3a30f74`. It reports a 10,820,591,616-byte SQLite restored from 57 compressed parts (2,352,689,771 bytes), with SHA-256 `42942d7485d4650075b0ec6baa2059d8b8e715bea9c3d59d772c301854d20e25`. It contained 99 sources, 305,527 file versions, 1,675,716 records, 10,901,211 relations and 268 gaps.

The prior workflow already exported file metadata/query subsets and selected source locators before deleting **only its scratch restored SQLite**. It retained compressed pieces and reduced query exports. The later foundation selected 161 verified Git sources and 42 claim cards and still explicitly limited semantic reading. These are useful seeds for current delta scanning; they are not the current branch tip and not an instruction to delete authoritative remote databases or user originals.

## 9. Genuinely open science and recommended minimal continuation

1. **Current authority integration:** read the latest repository, separate code catalog and theory-role catalog authorities, then resolve superseded source identities before reusing statements.
2. **Optical measurement bridge:** distinguish the local H,V generator fields from endpoint redshift/direction drift; derive the actual response and exact frame-rotation/acceleration/selection nuisance kernel. Ideal rank 12 is not yet a measured rank-12 result.
3. **Conventions:** seal derivative index order, vorticity dual, photon propagation versus outward sky, proper-length/proper-time rates, and T9 brightness normalization. Review corrected equations rather than revive withdrawn positive shear injection.
4. **Restricted boost theorem:** correct the trace-proof typo; retain its exact response scope; perform focused primary-source novelty review if a priority claim is wanted.
5. **Operational probability laws:** product-matched CMB release/null, CF4 compression/selection/calibration law, and shared covariance remain distinct from algebraic response rank.
6. **Physical MES interpretation:** actual radiation jet/remainder, same-frame maps, and constraint-compatible endpoint realization remain prerequisites for physical sharpness; scalar low-ell morphology alone does not supply them.
7. **R3 benchmark and R9 framework:** reuse their analytic constraints as targeted oracles and alternate realizability branches; do not make completion of the entire BASS solver a gate for every independent HTT theory or conditional-observation task.

Historical independent-final-review unavailability is **not** a current runtime or reviewer availability fact. The new session can arrange a real independent review and report its actual scope. Likewise all historical numerical passes remain historical until deliberately reused with exact authority or rerun where scientifically needed.

## 10. Full outer-research payload coverage and the previously omitted continuation

The authoritative file list for this follow-up is the ZIP central directory of `HTT_MES_THREAD_BACKUP_20260928_01_RESEARCH.zip`, not the extra working directories created during recovery. It contains **373 regular members: 372 payload files and one outer MANIFEST.sha256**. All 373 paths are present in the extracted tree. Exact enumeration, roles and read depths are in `RESEARCH_372_COVERAGE.json` and `.csv`.

| Outer payload group | Files | Recovery coverage |
|---|---:|---|
| `history/` | 79 | Archive/member inventory and selected substantial readings described above |
| `mes/` | 6 | R1/R2 package/report copies and receipts; enumerated |
| `github_r10_52ab95f2/` | 75 | 74 pinned research-subtree files plus provenance; structural state scan and full MAIN review reading |
| `github_historical_snapshots/` | 99 | 25 plan files, 73 partial-execution files, one identity index; metadata and textual structure scan |
| `readable_research/MES_FRESH_OPTICAL_TENSOR_R1/` | 35 | All selected text structurally scanned; decision and continuation substantially read |
| `readable_research/MES_GENERALIZED_TENSOR_R2/` | 46 | All selected text structurally scanned; current report, state and next prompt substantively read |
| `readable_research/initial_archive_index/` | 23 | Early archive indexes/partial-chat records scanned; vendor/tar content not expanded in this follow-up |
| `index/` | 9 | Enumerated; chronology and coverage/gaps fully read |
| **Payload total** | **372** | **Complete path/role enumeration, not complete semantic audit** |

The coverage ledger currently records 196 files at programmatic headings/state/gate scan only, 123 at path/size/role inventory only, 37 archives with member inventory plus selected-source reading, and 17 selected prose/structured/partial readings at stronger or explicitly partial levels. These add to 373 including the manifest. A machine scan reading file bytes does not count as a full semantic reading. `RESEARCH_OUTER_STRUCTURAL_SCAN.json` preserves the selected lines/fields; `READABLE_RESEARCH_STRUCTURAL_SCAN.json` is the focused readable-research scan.

The backup's own `index/COVERAGE_AND_GAPS.json` explicitly says `requested_full_thread_complete=false` and `full_chat_export_present=false`. It preserves inaccessible chat gaps, unknown attachments, unavailable workstation-only data, and an early archive receipt size mismatch. Therefore “all available outer files enumerated” is justified; “all original messages and all scientific sources recovered” is not.

### Original-thread chronological endpoint

`index/CONVERSATION_CONTEXT_AND_RESEARCH_SEQUENCE_KO.md` makes the continuation after September 16 explicit:

1. **R10 (September 19–20):** adds twelve optical nodes to R9, making a 36-node campaign; partial local execution and MAIN review were preserved.
2. **Fresh R1 (September 20):** the user explicitly restarts the original MES motivation independently of older negative judgments/native checkout blockage. The result is an exact positive shear operator, residual inverse-image formulation, a separate Bianchi-I endpoint optical/stress pilot, and signed morphology normalization.
3. **Generalized R2 V3 (September 20):** the user asks for all kinematical sectors and tilt, no named Bianchi class, Lie-algebra-compatible generality, no ODE/PDE/Boltzmann evolution, and no VIGILODE dependency. This is the **last recovered scientific result of the linked original thread**.

The old restriction to reading only MES-bound repository antecedents belongs to the scope of that fresh R1/R2 derivation. The present user explicitly requests integration with the accumulated repository work; the historical restriction is provenance, not a reason to refuse today's authorized integration.

## 11. Unique post-September-16 results missing from the history-only reconstruction

### R10 execution/review is real, scoped, and historical

The source-subset snapshot is at commit `52ab95f2ef5509a653df0a91761687898126c2ea`. The plan snapshot is `c8bd214a61088b684cad1d08873f05227cf5bfb0`, tree `d66ccc669492c2b6f233d58b818c86b69fc3aaa7`. The reviewed return is `48e77f8d05a01b9df78d37475e9fae48f65bad6d`, tree `05c577d096ce6640442d1cc6338879dd6e018eb1`; tested source `99b8e433e0fca4e1384cdc6991e14f15ccddd407`, tree `0b48298ecd80cec834cbf1199afe6a3b14412ec5`.

The full `continuation_execution/return/MAIN_REVIEW_AND_NEXT_PROMPT.md` was read. It accepts a partial diagnostic checkpoint with caution, not native/CAS/production admission. It records:

- An independently constructed flat-characteristic shear→energy→occupation→brightness/temperature→STF fixture. Its pointwise residual was about 8.9e-14, while the final forward and Richardson derivative relative errors were about 4.75e-4 and 1.79e-6. These are different diagnostics.
- Attempt 01 FAIL and attempt 02 exploratory PASS with an openly changed all-grid→finest-pair angular acceptance scope. This is not retroactive PASS of the first attempt.
- A standalone mixed 5×5 shear map of rank 1 versus the physical full-STF rank 5. No invertible normalization adapter can repair that rank deficit. This does not automatically diagnose the separate ver3 runtime builder.
- A saved R9 mean-response common-zero-point/free-shell-monopole null. In the stated response model, 35 mean combinations remain identifiable; a rank-27 depth contrast discards eight more combinations than removal of the single scalar nuisance alone.
- General-ell shear formulas require the ambient homogeneous-polynomial derivative convention; a spherical gradient with an unchanged `(m+4)` term is a different operator. An m=1/ell=3 discriminator was required.
- `CLIENT_WORKTREE_MISMATCH` and `REGISTERED_IDENTITY_CHANGED` were historical native review blockers. They are not evidence about current runtime availability, and they do not block the later fresh theory series.

### Fresh R1: exact shear block and finite residual set

The R1 final decision explicitly records an independent bounded **PROMOTE** to further analytic/statistical-method research only, superseding the history-only assumption that the latest work had no independent reviewer. It does not promote observed shear, a universal MES theorem, publication priority, repository/native admission, or full Einstein–matter realizability.

For nonnegative bolometric brightness B, moments `M_r=∫B e^⊗r dΩ` and STF shear S, the exact local block is

`L_B(S)=S M2+M2 S−M4:S−I(M2:S)/3`.

It is self-adjoint on STF2, depends only on brightness ell=0,2,4, and obeys the stated coercivity bound `S:L_B(S)≥lambda_min(M2)||S||²`. Nonzero nonnegative L1 brightness gives positive-definite M2; a singular angular measure is a separate extension. The exact conditional shear set is `L_B^-1 R`. A static sky supplies B and L_B, but not the spacetime/collision residual R. If R is unrestricted, shear remains unrestricted. The final revision also distinguishes arbitrary inverse images from the convex-hull information supplied by support functions.

The separate Bianchi-I endpoint branch reconstructs a normalized endpoint optical tensor; only fixed principal axes permit its identification with integrated shear. Finite stress budgets can bound current shear without evolving a full solver. That example is optional and not a premise for the general R2/R3/R5 theory.

### Generalized R2 V3: the sign convention and all-kinematics weak law are already fixed

R2 defines `U·U=−c²`, `omega_ab=D_[a U_b]`, `omega^a=epsilon^abc omega_bc/2`, with positive rigid rotation mapped to positive angular velocity. It explicitly states its sign adapter to the Ellis book. With rate acceleration `a=A/c`, the photon generator is

`R(e)=H+a·e+S:ee`, `V(e)=−P_e(a+Se)−omega×e`.

Thus the omega ambiguity identified in the September 16 history **is resolved for the adopted fresh R2 branch**. One must translate older formulas, not reopen R2's declared sign merely because the old packet used the opposite index convention. The ideal inverse and equal-L2 error constant √3 are already derived; neither equals actual detector covariance or endpoint proper-motion inference.

R2 also already contains the exact all-kinematics bolometric weak law with an ambient homogeneous derivative, its J0/J1/J2 blocks, the first-jet distinction between local boost and global tilt, Lie algebra plus metric/metric-jet requirements, and weak Raychaudhuri constraints. The rank-9 isotropic/rank-12 anisotropic test is explicitly conditional on a known residual, not a static-CMB reconstruction theorem.

Its tensor bundle contains expansion displacement, STF shear, axial vorticity, polar acceleration and polar tilt, with distinct labels/parity. For displacement `y=k−k_ref`, normalization uses the gauge of one common admissible/reference body B. A projected experiment must use `P_I B`, not `B∩I`. A product of sector bounds yields a max gauge; a sum-of-squares ellipsoid is an additional assumption. The signed normalized tensor T is preserved alongside `Q=T⊗T`, `F=||T||²`, `D=100(1−sqrt(F))`, tensor exceedance Pi and transported growth G. No probability law means no numerical Pi.

The R2 V1 likelihood-centering bug was independently caught and corrected in V2/V3: B constrains `k−k_ref`, so the physical set is `k_ref+B`. The historical witness had correct loss 0 versus erroneous loss 81. V3 decision is **PROMOTE_TO_NEXT_THEORY_OBSERVATIONAL_CONTRACT**. The full legacy signed x identity, useful empirical residual body, real-data likelihood, all-15-component identifiability, full polarization response, universal nonlinear MES theorem and novelty remain unresolved.

The recovered original-thread next ID is therefore exactly:

`MES_GENERALIZED_TENSOR_R3_OBSERVATIONAL_CONTRACT`.

Its requested next outcome is an actual response/source/frame/remainder contract for one experiment, a useful bounded joint residual class, nuisance-projected identified body, and a small same-law synthetic tensor-statistic calculation. The present remote integration has since progressed several of these theoretical links; blindly replaying this historical prompt would duplicate work.

## 12. Current remote R1–R5 integration supersedes the archive resume frontier

The parent task acquired current main `cc162c804eecb3c588efc6edadbe057a8a67301f`, tree `f14a536e7934d99bbe67489d1b81e5da0079cb09`. I read the acquired integration documents under `recovery/remote_sources/docs/research/mes_r1_r5_integration_20260927/`; I did not independently re-fetch the remote or rerun their science.

The integration's original source packet SHA-256 is `412bca18a18cded432764481f4d7f8bacee7844d148c82e2d9856481b50dd89d`. The remote work is **DOCUMENTATION_INTEGRATION_COMPLETE / NO_NEW_SCIENTIFIC_ADMISSION**. Its pre-integration working HEAD `549d8516...` is historical input, not a contradiction of the parent-acquired current main commit.

| Stage integrated on current main | New or reused substance | Evidence ceiling |
|---|---|---|
| R1, 2026-09-20 | Exact positive shear block/residual inverse; optional endpoint Bianchi-I pilot | Original scoped analytic decision retained |
| R2, 2026-09-20 | Exact all-kinematics optical and weak laws, corrected likelihood, common-body tensor normalization | Original V3 decision retained; not observed all-sector inference |
| R3, 2026-09-27 OBSERVABLE_JET | Nearby-source endpoint expansion and proper-motion response; finite-distance budgets; conditional joint inference | Report-supported; separate raw/independent verdict remains a provenance gap; source supplement exploratory |
| R4, 2026-09-27 ALGEBRAIC_CLOSURE | Lie+metric normal spatial closure, full tilted first jet, compensated distance shells | Conditional proof and corrected V2 CAS evidence; original V1 implementation failure preserved |
| R5, 2026-09-27 FINITE_TILT_JOINT | Exact fixed-tilt rank9 affine geometry, compatibility equations, b-free target combinations, retained timejet rank8, joint-body disk fixture | Conditional analytic/registered evidence; new finite-boost/source candidates remain HOLD |

The September 27 stages are identified by series/date/work-unit/hash and must not be confused with other same-number GENERALIZED R3/R4/R5 results from September 20.

### Concrete progress beyond the earlier proposed H,V gap

R3 already supplies a nearby-source observable bridge under its declared common-congruence and frame assumptions:

`Hcal(n)=H−a·n+sigma:nn`, `kappa0(n)=P_n sigma n+omega×n`.

The leading proper-motion acceleration contribution cancels for the same emitter/observer congruence. Ideal calibrated rank12, distance-only rank9 and free-frame-spin quotient rank9 are report-supported results. Local V is therefore not being equated to measured proper motion in the integrated theory. Actual selected sample/frame/source budgets remain absent.

R4's three-shell combination `−2y(D)+5y(2D)−2y(4D)` cancels the specified common `u/r` and linear-r terms. It carries sharp remainder `7MD²`, equal independent-noise variance `33s²`, and deterministic error coefficient 9. Finite shell widths require actual shell moments and a corresponding remainder kernel; common spin/calibration and arbitrary source motion do not disappear. Original and transformed data must not be multiplied as independent likelihoods.

R5 fixes the homogeneous tilt p and maps six symmetric metric-jet plus three tilt-timejet components into twelve kinematical components with rank9 and three affine compatibility equations. Free b changes `delta a=z`, `delta B=p z^T`; consequently `Theta−p·a`, `sigma−STF(pa^T)` and `omega−p×a/2` are b-free combinations. They are not renamed as individual physical shear/expansion/vorticity. For a nonempty compact-plus-free input class, a target is bounded exactly when its projection annihilates the free response directions. The retained radiation timejet map has rank8, so unrestricted radiation timejets can absorb all eight retained equations; exact finite-tilt geometry does not restore discarded radiation products or physical source constraints.

R5's positive-shear appendix is normalized reuse of R1/R2, not proof that all earlier exact radiation work was incomplete or withdrawn. Likewise an unresolved finite-electron/source candidate does not revoke the previously scoped Liouville theorem.

## 13. Correct current continuation and non-duplication decision

The integration explicitly advises selecting **one target**, such as the fixed homogeneous finite-tilt b-free `sigma−STF(beta a^T)` or a calibrated nearby-source shear, and matching the already-derived R1/R2 weak law to the actual source/frame/timejet/remainder namespace. Then determine the target's nuisance-projected response using one common selected distance/proper-motion sample and its frame-spin/calibration contract, and obtain one useful physical budget or measured input. If no narrower interval is justified, identify the dominant budget rather than invent a bound.

This is the current minimal frontier, superseding the history-only Section 9 suggestion to develop the entire endpoint mapping anew. The actual remaining gaps are useful source/timejet/remainder radii; selected-data joint law and shared calibration; applicable nongeodesic MES normalization; Einstein–matter compatibility; empirical D/Pi/G; production implementation of the adopted theory; and R3's separate raw/review provenance. The underlying exact identities and already-completed CAS fixtures should not be broadly rerun just to restate them.

No new scientific calculation, remote mutation, test replay, or vendor expansion was performed in this coverage follow-up. The original archive chronology, superseded formulas, first failures, scoped decisions and current imported evidence limits all remain distinct.
