# Final advocate report — divergent 4-axis rescue of the Bianchi-anisotropy program

_Dev-tier research artifact. NEVER rendered into any report/manuscript (no-meta-dev rule). This is
the ADVOCATE/steelman counterpart to the 2026-07-14 external JCAP/PRD adversarial audit
(`docs/audits/jcap_prd_adversarial_audit_20260714/`), complementary to and NON-OVERLAPPING with the
LONG_HORIZON rescue roadmap. Produced by the mandated loop: initial web-CRAG → NO-WEB divergent
brainstorm + multi-persona debate → short final CRAG → steelman. Gates were disabled for IDEATION
ONLY; every family-ID/geometry route stays `hypothesis_only`, `public_use=false`, never promoted._

## Executive summary

The audit's verdict stands: **as shipped, there is no positive anisotropy / global-tilt / family /
geometry result.** This exploration does not overturn that. What it establishes is the opposite
of what the roadmap alone implies — the program is not just a set of defects to patch, it is a
**stranded but scientifically substantial** anisotropy programme, and the strongest advocate move is
to convert it into a **battery of solver-free, cross-dataset, sign/handedness/ceiling FALSIFIERS**
that would each kill the tilt hypothesis if it is spurious. Populated with net-new observables the
roadmap does not contain, this is a genuine (if modest, mostly INCREMENTAL) upgrade to the
"falsifiable research programme" the audit itself said was the only defensible posture.

**Honest calibration (final CRAG reduced novelty; completeness critic reduced non-overlap):**
of 70 brainstormed candidates → 25 debate survivors → 21 ranked, **16 are genuinely net-new**;
final-CRAG novelty is 0 NEW / 11 INCREMENTAL / 9 CONFIRMATORY / 3 ALREADY_KNOWN. The steelman
answers all 102 criticisms but **mostly by concede-and-rebuild (76), not refutation (1)**; 3 are
terminal concessions. No P0 is refuted — both imported CF4 P0s remain open; the advocate rescue is
to build the net-new work *around* them, not to deny them.

## Per-axis rescue thesis

### Theory (audit 2/5 → advocate target: honest 3/5 methods)

Defensible core: (1) **MES four-acceleration honesty theorem + `bounds.py` defect fix** — geodesic
`A²=0` (rev-r190) kills the in-house non-geodesic `B_accel=(3/4)ε₁+ε₂+(3/14)ε₃` STILL shipping in
`bounds.py`, and the O(β) four-acceleration T-dipole is spectrally degenerate with the kinematic
dipole (a live code-integrity win, rank #1, lowest risk in the set). (2) **Unsigned isotropy-leakage
ceiling `M_max`** — because `x_C = Σ²−W²+Ω_tilt+Ω_k` carries a MINUS on `W²`, `x_C≈0` does NOT
certify FLRW/EGS; `M_max` with Nilsson-class saturating witnesses formalizes exactly what `x_C≈0`
fails to guarantee (INCREMENTAL: this is the generalized-EGS acceleration loophole of
Clarkson–Coley 1999 applied to the project's own identity — an application, not a new theorem).
(3) **Buchert covariant home + two-patch cancellation obstruction** — re-expresses the shear sector
of `x_C` as the Buchert kinematical backreaction `Q_D` (a PROVENANCE move answering
"x_C is an in-house construct"; downclaimed — the Q_D content is standard Buchert/Wiegand and
Barrow–Tsagas already averaged Bianchi models). Gates-off ambitious tier: the **low-ell T–E
recombination-shear coherence ratio** (shear → coherent low-ell E with fixed TE sign vs boost →
T-quadrupole with no coherent E) is the single best empirical go/no-go, but the specific ratio
needs the native solver (Pontzen–Challinor 2007 computed the qualitative split).

### Statistics (audit 1/5 inferential → 3/5 formal)

Defensible core: (1) **occupancy-exceedance pushforward `x→Q→Π` + F⊥–lnB obstruction theorem** —
a computable, refutable primary object (**caveat from the completeness critic: `F_Bayes=E[Q|D]`
overlaps the frozen MIO functional ST-06/PR-142; the genuinely net-new sliver is the F⊥–lnB
obstruction theorem ONLY**). (2) **Exact zero-parameter boost-BipoSH residual-excitation vector** —
the real net-new statistics representative (the critic promoted it): analytically pre-whiten the
one exactly-known contaminant (observer boost), restoring statistical independence to the residual
survey-direction tests — turning the audit's "correlated self-oracle" wound into a method.
(3) **Partial-identification SBC** (structural-null `{W²,Ω_k}` no-update invariance) + a
**coverage toolkit** — both honestly reclassified as recombinations of the frozen PR-136/137/138 +
Imbens–Manski, contributing coverage-proofs, not primacy.

### Code / reproducibility (audit 2/5 → 4/5 achievable)

Defensible core: (1) **manufactured-universe end-to-end MMS** — Oberkampf–Roy grid-refinement
order-convergence toward an exact injected anisotropic ground truth (`B₀/θ₀/ω₀`) + a `β_true=0`
false-positive specificity bracket (net-new delta vs the frozen CO-04 numerical-oracle: the
anisotropy-specific ground truth and specificity bracket — the critic required this delta be
stated). (2) **physics-invariant symmetry-transform metamorphic battery** (rotation covariance,
axis permutation, quadratic amplitude scaling, monopole projection + the discrete B-mode-parity
metamorphic relation). (3) **MC finite-ensemble error-budget certifier** (fail-closed infra) — the
honesty substrate that quotes empirical p-floors as resolution limits, never as evidence. Gates-off:
**exact real-space Sachs-Wolfe ray tracer** + **11-type tetrad geometry oracle from structure
constants** — pre-native sub-components that shorten the native-solver gap.

### Data-analysis (audit 1/5 → 2-3/5 methods)

Defensible core: (1) **Tsagas `div(v)→q-dipole` cross-falsifier** — read `θ=div(v)` directly from
CF4/PV (`divergence()` already ships, computed then discarded), replacing the ad-hoc closure in
`tilted_flrw.py`, and force a SINGLE-AXIS coherence across the CF4 `div v` apex, the SNe `q`-dipole
apex, and the CMB low-ℓ. This is the flagship net-new observable: it uses a DIFFERENT moment of the
field (immune to the monopole-leakage P0 that killed the dipole headline) and a NEW dataset
combination (independent SNe), with a depth-tomography law discriminating local boost from global
tilt. (2) **validated-band ACT DR6 κ anisotropic-modulation transfer** (repairing the shipped
out-of-band `ℓ∈{2,10}` hardcode by measuring the quadrupolar off-diagonal within the validated
`40<L<763`). (3) **DESI number-count dipole redshift tomography** (reconstruction-free, mock-free)
and a **sign-locked one-sided `Ω_tilt` ceiling** (honestly reclassified as ST-04/PR-147 territory).

## The gates-off ambitious tier (hypothesis_only — the ambition the roadmap freezes)

The archaeology surfaced an entire stranded physics programme (`legacy/bianchi-defect-framework`:
DR-07…14 + paper2…9 + a full directional/family-discrimination inference stack). With gates off for
ideation, the boldest coherent route is the **VII_h family single-bit discriminants**: the
polarization **B-mode parity** (axisymmetric ⇒ B=0; helical VII_h ⇒ B~E + parity-odd TB/EB) and the
**handedness veto** `sign(EB/TB)=sign(x_h)`. **Completeness-critic correction (enforced): these must
NOT adjudicate a Bianchi family on shipped data** — they stay registered reference signals for the
future native atlas. The final CRAG confirmed the parity split is Pontzen–Challinor 2007
(CONFIRMATORY), so the only plausibly-new sliver is tying the CMB parity sign to the local PV-curl
handedness — hypothesis_only, modest. This is the honest ceiling of the gates-off exploration:
**a registered, falsifiable family-discrimination programme, not a family claim.**

## What is genuinely dead (terminal concessions)

Three criticisms received CONCEDE_TERMINAL (see `08_steelman_response_matrix.md`); the corpus's
positive anisotropy/global-tilt/family/geometry headlines are not rescuable at present data + no
native solver. The advocate does not dispute this — the rescue is the falsifier battery, not a
detection.

## Bottom line for the owner

The roadmap fixes the defects; this exploration says the program is worth more than its defects —
it is a stranded, externally-homeable (Buchert/MES/Tsagas/Pontzen–Challinor lineage), falsifiable
anisotropy programme whose strongest form is a solver-free cross-dataset falsifier battery. The
16 net-new candidates (`07_ranked_candidate_ledger.md`) are the concrete, non-overlapping,
mostly-runnable-now content to build it — honestly INCREMENTAL, honestly hypothesis_only where they
touch geometry, and each carrying a decisive falsifier.
