# Decision packets — GR-CAS-04, GR-CAS-11, GR-CAS-18

Date: 2026-10-13. Repository snapshot: cosmosapjw-quantum/htt_base `main` @ f1007dd, read-only (git status
clean before and after). Status: NON-AUTHORITATIVE research. Nothing was adopted, sealed, registered, run
under cas_gate, committed or pushed. `GRS/` = `docs/research_program/gr_statistics_loops_20260930/`.

Process: one deep research cycle — evidence audit → hypotheses → exact checks on two engines (SymPy 1.13.3;
Wolfram Language 15.0.1 via MCP, no xAct) → three fresh adversarial reviewers → one fresh decision gate
(which re-ran every check and builder preview and re-derived the key identities by hand). Full record:
`state/` (ledger, hypotheses, negative results, reviews, decision log) and `checks/`.

| Node | What actually blocks it | Gate recommendation | Smallest owner decision |
|---|---|---|---|
| GR-CAS-04 | Wolfram/xAct axis does not machine-check C04 (F1) and its C01 step is constant-true; no rule-consistent cheap path to an eligible run; EF6 waits on CAS-06 | keep CAS_BLOCKED (no node depends on it); successor contract on hold | confirm "no CAS-04 successor now" |
| GR-CAS-11 | owner adoption of the C01 successor; sealing procedure; routing | adopt v4.1 via builder v3; register only after adoption | adopt v4.1 (or v4) and name the sealing procedure |
| GR-CAS-18 | missing physics/measurement inputs (by design); the recorded input list is incomplete | append a corrected 10-item missing-input list; HOLD unchanged | approve the append-only record |

---------------------------------------------------------------------------------------------------
## 1. GR-CAS-04 — energy-frame rate budget, Euler restrictions (C01–C04 finite; EF6 analytic)

### 1.1 Correction of the 2026-10-12 handoff text
The handoff said the conservation→Euler link "is not in the contract". That was wrong. The sealed contract
(`GRS/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-04/EXECUTION_CONTRACT.json`, sha256 058da4…) states C04 as
"Project perfect-fluid conservation to recover A=-c^2 Dp/(epsilon+p)" with the assumption "Conserved perfect
fluid for Euler"; Lean derives it (`completion_20261003/lean/attempts/017/Proof.lean`, theorem
`euler_from_actual_conservation`). The defect is in one axis source.

### 1.2 Audited blocker
- F1 (HIGH): `completion_20261003/wolfram_xact/axis.wl:96-117` checks only the product-rule expansion and then
  solves a separately supplied Euler equation; conservation is never imposed, so the block is unchanged by any
  source term J^b.
- Wolfram C01 (`axis.wl:29-30`) is constant-true (projector with a repeated contravariant index times an
  expression xAct reduces to 0) — stronger than review finding F2's wording.
- Rider: the retained SymPy (`sympy/run.py` ~l.84) and Sage (`sage_singular/engine.py` ~l.62) C04 sources insert
  the rest-frame normalization derivative ∂_a u^0 = 0 instead of deriving it; Sage's Euler line (~l.71-74) is
  constant-true. They do connect the projected divergence to the Euler form, which Wolfram does not.
- Eligibility: only `run-adjudicate` (one parent executing all four axes) can produce an eligible PASS
  (`.agent-harness/scripts/cas_gate.py`, docstring; contract `exceptions_adjudication.aggregate_status_rule`).

### 1.3 Why no cheap path exists (N-001, each item verified)
1. Owner prohibition: "Do not restart existing SymPy/Wolfram authors/engines"
   (`CAS-04/remaining_axes_20261003/EXECUTION_BOUNDARY.json`).
2. DAG repeat_policy: "No repeated same blocker, passed-component rerun, or assurance-only publication without new evidence."
3. The gate requires each axis payload to carry exactly all obligations C01–C04, so C02/C03 would re-run.
4. Runner incompatibility: `lean/run.py` prints a path, exit code and raw log, not the typed JSON payload;
   `sage_singular/run.py:66` calls the PATH `Singular` (the toolchain drift that voided CAS-05 v3's first PASS).

### 1.4 Research results (exact, two engines; `checks/chk04_projection_and_eigen.py`, `checks/WOLFRAM_CROSSCHECK.md`)
In any chart at a point (metric value fixed by a linear change; all 40 first metric derivatives generic;
reviewer re-ran with a random non-η metric value):

    h_db ∇_a T^ab − [(ε+p) a_d + D_d p] = u_d N0 Θ + ½(ε+p) u_d u^a N_a,
    N0 = u·u + 1,  N_a = ∂_a(u·u) = 2 u_b ∇_a u^b,  Θ = u^a ∂_a(ε+p) + (ε+p) ∇_a u^a.

So with normalization (N0 = N_a = 0) and ∇_a T^ab = 0: (ε+p) a_d = −D_d p, A = c² a. C01 analogue:

    h ∇_X(T u + ε u) − [(S_T + εI) ∇_X u + h(∇_X T) u]
      = (Xε) u N0 + ½ ε u N_X − ½ N_X h(Tu+εu) + ½ N_X ε u N0,

valid also for non-symmetric T with S_T := hTh. Analytic obligation note (H-04E, on hold): the bordered
Jacobian of (v, μ) ↦ (Tv − μv, g(v,v)+1) at (u, −ε) has det = −2 det(S_T + εI); det L ≠ 0 ⇔ −ε simple,
which is the IFT non-degeneracy already invoked in `GRS/gr/ENERGYFRAME_THEOREMS.md:91` (local uniqueness up
to ±u; future branch by continuity; C^k metric). The spectral bound ||L⁻¹||₂ = 1/min|ε+p_i| ≤ 1/δ needs S
self-adjoint in an orthonormal rest frame.

### 1.5 Gate decision
- PROMOTE H-04G: keep CAS-04 at CAS_BLOCKED. No node lists GR-CAS-04 in `depends_on` (PORT-CAS-10 and
  LOOP2-P2P3 only cross-reference it), so the downstream cost is zero.
- HOLD H-04B′ (successor contract, CAS-05 v3 pattern). If ever adopted, fix first: per-component negative
  controls encoded as obligations or review criteria; normalization derivative written u_b ∇_a u^b = 0 (never
  "u·∇u", which is the acceleration); every axis connects the actual projected divergence to the Euler form by
  an executed equality; gate-compatible runners (typed JSON; Lean theorem-map runner as in CAS-05 v3);
  Singular and Lean pinned in the run spec and re-bound to CAS_ENVIRONMENT 6d2253…; new run directory and
  RUN_SPEC; no reuse of the retained SymPy/Sage/Wolfram envelopes. Cost reference: CAS-05 v3 four authors
  44,275,998 tokens (43,538,560 cached); CAS-04's earlier Lean author alone 8,325,491.
- HOLD H-04D (scope EF1/EF4 without EF6): decide together with H-04B′; scoping must live in a closeout record.

### 1.6 The owner decision
Confirm the default "no CAS-04 successor now". Revisit when a node adds `depends_on: GR-CAS-04`, or when
CAS-06 leaves CAS_CONFLICT. Before deciding, look at: §1.3 (four reasons), the dependents scan in §1.5, the
cost reference, and the §1.2 rider.

---------------------------------------------------------------------------------------------------
## 2. GR-CAS-11 / C01 — Bregman three-point identity and moment cancellation

### 2.1 Audited blocker
- v3 (`GRS/cas_corr_followup_20260930/intake/contracts/CAS11-C01-BREGMAN.json`, 57202993…) never defines its
  cancellation premise. v4 proposal (`GRS/cas11_c01_resolution_20261001/C01_SUCCESSOR_PROPOSAL.json`) awaits
  explicit owner adoption. Body hash e586ee87… and all seven input hashes plus the v3 hash were recomputed at
  f1007dd: no drift.
- Routing (10-01): registration exit 2, REVIEW_HIERARCHY_UNSATISFIED; the tier table then lacked gpt-6.1-sol.
  Later registrations routed reviews to gpt-6-astra under newer authorities, but the failed C01 request also
  lacked `author_evidence_refs` (present in every successful request), so the cause is not isolated.

### 2.2 Research results
- v4 is true in full generality and faithful to the parent CAS-11 statement: after the scalar Φ terms cancel,
  each coordinate summand of LHS − RHS is identically zero (all n, n = 0 included); cancellation is
  ⟨M*λ, f−g⟩ = λ(M(f−g)) = 0. Checked on both engines; reviewer: 158 random exact instances, 0 failures.
- v3 is ill-posed; its natural literal readings are false. Counterexample: Φ = |x|²/2 on R², M = [1 0],
  g = (0,0), h = (0,1), f = (0,1): moment matching holds and the functional annihilates the gradient
  difference, but the cross term is 1 and D(f‖g) = 1/2 ≠ D(f‖h) − D(g‖h) = −1/2. Readings that make v3 true
  need the parent's span condition (not a permitted v3 input) or assume the conclusion.
- v4 omits the parent's "No constant-true checks" rule (`GRS/cas/contracts/CAS-11.json`) and the withdrawn
  brief's negative controls; the gate checks one boolean, and CAS-04 shows constant-true checks do pass it.
  Hence v4.1.
- Parent-level caveat (not a v4 defect): when the score difference carries a log-normalizer constant, the
  number/normalization functional must be a row of M; otherwise the cross term is (a′−a)(N_f − N_g).

### 2.3 v4.1 and the sealing artifact
v4.1 = v4 body + three `forbidden_shortcuts` lines + two abstract negative controls:
- "No constant-true checks or copied historical evidence."
- Each universal-target check must evaluate false on the declared negative controls.
- Reporting clause (gate requirement, because the gate accepts exactly one `checks` key and turns a non-null
  `counterexample` into FAIL): "Negative-control outcomes are reported in raw output and proof_coverage only;
  the payload `checks` keeps exactly the obligation key CAS11-C01-BREGMAN, and `counterexample` refers only to
  the contract targets, never to a negative control."
- Controls: span hypothesis removed (cancellation must not be certified); cross-term sign flipped (identity check must fail).

Builder `packets/build_cas11_c01_contract_v4_DRAFT.py` (v3 of the draft):
- verifies e586ee87…, the v3 hash, every input hash, and that the body's `identity.supersedes_contract`
  names the same v3 bytes;
- adds `identity.successor` (pattern of `CAS-05/neutral_admission_20261003/EXECUTION_CONTRACT_V3.json`);
- requires `--authorization` citing "session <id> … turn <id>" or "sha256:<64 hex>" of an adoption record
  (vague strings exit 2); has `--check` for byte equality; uses neutral author-facing text that cites no
  non-permitted input.

Preview hashes (placeholder authorization, not sealable): v4 `73620080ea6f5d51…`, v4.1 `ec60c0ee32962bbf…`.
A synthetic-authorization self-test sealed, re-checked byte-equal, and parsed under the frozen gate as R3,
four axes, obligation `CAS11-C01-BREGMAN`. The gate parser does not read status fields, so this proves
structure only. The decision gate marked the builder REOPEN_VALIDATION; the listed fixes are applied but
were not re-gated.

### 2.4 Gate decision
PROMOTE H-11A′ (v4.1 plus the clause); HOLD H-11A (v4 unchanged) as fallback; PROMOTE the wording
"v3 is ill-posed; its natural literal readings are false".

### 2.5 The owner decision
Adopt v4.1 (or v4) and name the sealing procedure. Before deciding, look at:
- the disclosed diff against e586ee87… (`packets/v4_preview_v4.1.json`);
- the three hand-checkable facts (three-point identity; λ(M(f−g)) = 0; the v3 counterexample);
- the gate's single-key and counterexample rule;
- the routing plan with its unisolated cause.

After adoption:
1. commit the builder under `scripts/codex_harness/` and cite its sha256;
2. seal with the real authorization;
3. pin Lean and Singular in the run spec (the CORR environment 885c53e4… records a Lean probe timeout and only
   Sage-internal Singular);
4. register under the current authority with `author_evidence_refs`, continuing task
   GRSTAT-CAS11-C01-20261001T031553Z;
5. run four fresh blind axes, then `run-adjudicate`, then review.

Do not probe registration before adoption: a successful registration reserves a launch, and the handoff bars
reviewer retries before adoption. Cost reference: R3 four-axis campaign (CAS-05 v3: 44M tokens, mostly cached)
for a statement provable in two lines. This unblocks GR-CAS-12 and GR-CAS-13.

---------------------------------------------------------------------------------------------------
## 3. GR-CAS-18 — TEFF-H2 HOLD (no executable contract, by design)

### 3.1 Finding
CAS-18's own target is "Retain HOLD and explicit missing input list". The recorded list
(`GRS/supplements/TEFF_CLAIMS.json`, TEFF-H2 `needed`, four items) is not sufficient for any identification
argument. The template contract (H-18A) and the negative-control contract (H-18B) were rejected: they conflict
with "Scope gate, not CAS identity", the no-solver rule and repeat_policy, and duplicate CAS-12's
COLL-NONLINEAR control.

### 3.2 Corrected missing-input list (append-only; TEFF-H2 stays HOLD)

| # | Input | Source / reason | Related node |
|---|---|---|---|
| 1 | Collision kernels, linear and nonlinear (stimulated / Compton–Kompaneets type), plus the regularity class of retained kernels for which nonlinear moment functionals are Lipschitz (top-hat bands excluded or bounded separately) | recorded item 1; `TEFF_POSITIVE_BRIDGE.md:141` "Nonlinear collisions … need their own kernels and bounds"; review18 spike construction (no finite ν for top-hat bands) | CAS-12 (COLL-NONLINEAR) |
| 2 | Polarization: matrix-valued (Stokes) transfer with its own divergence and envelope, or an explicit scalar-unpolarized restriction of the claim | bridge:141 "not a guarantee for polarized or frequency-redistributing CMB transfer" | none yet |
| 3 | Observation kernels incl. beam, line-of-sight/visibility integration and time accumulation | recorded item 1; bridge:222 (raywise estimator, beam weight, LOS mixing inside the declared model) | none yet |
| 4 | Electron/medium and transport inputs (T_e, n_e, τ(E)) with uncertainty entering as an operator-perturbation term | recorded item 2; bridge:141 (energy-dependent τ); CAS_TASKS control COLL-TAU | CAS-12 (τ) |
| 5 | Admissible-class/envelope prior for both states (b or T_max, non-positive log-fugacity, no condensate) and invariance of the class under the dynamics | bridge:102 ("T_max is additional prior information"); control BE-REF "both states required" | CAS-12 |
| 6 | An independently certified divergence budget ε (not inferred from retained moments or a fitted entropy) | bridge:104 "an independently certified ε"; CAS-11 takes ε as a premise | CAS-11 (premise) |
| 7 | Kinematic design matrix with column rank: s = inf_{\|v\|=1} \|Jv\| > 0 (m ≥ k) | recorded item 3; bridge:143 "supplies neither the design matrix nor its rank"; CAS-15 target "Stacked map injective iff intersection commutants 0" | CAS-15 |
| 8 | A bound on Jacobian variation over the region of interest (requires the nonlinear forward model, not J at one point) | review18 G4/G5 | none yet |
| 9 | A localization prior not fitted from the same data, plus either a global non-aliasing argument or an explicit "local identification only" scope | `reviews/POSITIVE_EXTENSION_DECISION.md:15,121` (no trial-parameter solution as evidence) | none yet |
| 10 | Measurement calibration as a noise model with a coverage level, in the same whitened norm as items 7–8, and joint (profiled) propagation of the collision residual set — not per-channel boxes | recorded item 4; bridge:143 ("profiling/projecting over e"; per-channel bars discard shared constraints) | statistics nodes (not verified) |

Illustrations only (not contracts): HOLD-NONLINEAR — moment-matched states whose nonlinear collision moments
differ (prefer the number-conserving flux-form variant from review18; K2 difference 10). HOLD-FORWARD — a
bounded rank-deficient linear map such as diag(1,0), which matches the linear source of that control better
than the circle example.

### 3.3 Gate decision and owner decision
The gate PROMOTEs H-18E, append-only, and REJECTs H-18A and H-18B. The owner decision is to approve appending
this list as a superseding record in a new file. Do not edit `TEFF_CLAIMS.json`: its sha256 9654e73e… is
recorded in `PACKAGE_MANIFEST.json`, `publication/CHANGESET.json`, `publication/SOURCE_TO_REPO.json` and
`reviews/POSITIVE_EXTENSION_DECISION.json`. HOLD is unchanged and no task is created. Before deciding,
check each row's source, keep the original four items, and have a physics read of items 2, 3 and 8.

---------------------------------------------------------------------------------------------------
## 4. Limits of this cycle
- No xAct was available; xAct feasibility of a connected Wolfram projection is unknown.
- The local `~/.codex` authority, tier table and current CAS-06 input plan were not visible.
- The three adversarial reviewers and the gate are Claude subagents sharing a model family with the producer.
  Their independence is fresh context and no producer preferences in the prompts; it is not a different lineage.
- The builder fixes after the gate were not re-gated.
- Physics completeness of the 10-item list needs the owner's or a domain reviewer's read.
