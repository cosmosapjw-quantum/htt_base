# BASS_PY_INTEGRATION_v4 — AMENDMENT 01

**Date**: 2026-04-17
**Status**: PROPOSED, pending approval
**Scope**: Adds a 4-level precision-verification ladder (L0–L3) to the existing 10-week plan without altering the existing DAG.
**Baseline**: `BASS_PY_INTEGRATION_v4.md` (782L, approved 2026-04-15)

---

## §1 Motivation

The v4 baseline plan tracks *functionality milestones* (Paper I forward/inverse, tilt, Pastén, forward strata, likelihood, Phase 3 validation, manuscript). It does **not** track *cross-implementation precision* as a first-class deliverable. Two consequences:

1. Likelihood inference at W6 runs without an explicit admission criterion. A forward model with unknown ±X% systematic bias propagates into $\ln B$ with unknown sign and magnitude. VER06 production values ($\ln B = +26.4$, $\beta = 1.36 \times 10^{-3}$, $F_{\mathrm{Bayes}} = 0.093 \pm 0.025$) become unfalsifiable until the forward operator is calibrated.

2. At W8 (Phase 3 validation) the plan does not specify which *independent oracle* each bass-py output is compared against. Rust BASS Track A ($D_2 = 1038$, 101.5% CAMB at $\ell=2$, but $D_{100} = 478$% CAMB due to $\dot\sigma$ cancellation) and Track B ($D_2 = 1004$, 98.2% CAMB) already exist as validated reference points; they should be exploited for a three-way consistency check rather than ignored.

This amendment formalizes a staged **precision ladder** L0–L3, each with (a) an explicit oracle, (b) a measurable tolerance, and (c) a failure-handling procedure.

---

## §2 Structural change to the plan

The ladder is **layered onto** existing milestones. No delivery date slips. No modules are removed.

| Level | Inserted into | Blocks | Oracle | Tolerance |
|-------|---------------|--------|--------|-----------|
| L0 | W3D5 (as precision_dashboard.py) | W4 entry | Analytic Paper I values + ch05 cross-ref | $10^{-10}$ analytic, $10^{-8}$ roundtrip |
| L1 | W5 closing gate | W6 entry | CAMB source/transfer at $(k, \eta)$ grid | ±5% for $\ell \leq 30$ |
| L2 | W6.5 (new) | W7 (sampling runs) | CAMB $D_\ell$ end-to-end + $O(\Sigma^2)$ perturbative | **±2% for $\ell \in [2,30]$ — hard gate** |
| L3 | W8 Phase 3 validation | W9 (manuscript integration) | Rust BASS Track A + Track B + CAMB consensus | **±3% envelope** |

The **hard gate** semantics at L2: likelihood sampling runs cannot begin until L2 is green. This replaces the current W6 boundary (which has no gate).

---

## §3 L0 — Distribution-level precision (W3D5)

### 3.1 Oracle

Paper I closed-form moment values and ch05 cross-reference table. **No CAMB comparison at this level** — CAMB does not expose distribution-level moments cleanly.

### 3.2 Comparisons

| Quantity | Oracle | Target |
|----------|--------|--------|
| $I_3$(BE), $I_4$(BE) at $\eta=0$ | $\Gamma(n+1)\zeta(n+1)$ | $< 10^{-10}$ rel err |
| $I_4/I_3$ for BE/MB/FD | 3.8322 / 4.0000 / 4.1060 | $< 10^{-10}$ rel err |
| $\Sigma_2 = (8/15) I_4/I_3$ | ch05 Eq. (shear-source) | $< 10^{-10}$ rel err |
| $F^{-1} \circ F$ closure (W3D1 roundtrip) | identity | $< 10^{-8}$ at amp $\leq 0.2$ |
| MB Laguerre Gram orthogonality | $(s+2)(s+1)\delta_{ss'}$ | $< 10^{-13}$ (W2D1 result stands) |
| MB TWO_FIELD Gram conditioning | $\kappa = 54.3$ at $\eta=0$ | reproducibility only |

### 3.3 Deliverable

`precision_dashboard.py` (~200 LoC estimated):
- Batched cross-ref of all analytic moments
- Table output: `(quantity, oracle_value, bass_py_value, rel_err, PASS/FAIL)`
- JSON export for L1/L2 historical tracking

### 3.4 Exit criterion

All L0 rows green → L0 GATE PASSED, W4 can begin.

---

## §4 L1 — Transfer/source-level precision (W5 closing)

### 4.1 Oracle

CAMB source terms at $(k, \eta)$ grid points, extracted via CAMB's `get_source_function` or equivalent. This is the **lowest layer where CAMB and bass-py are both meaningfully comparable**.

### 4.2 Rationale

Without L1 bisection, an L2 failure at W6.5 would be opaque — the ±2% could be in any of {Boltzmann ODE, source function, LoS integration, visibility}. L1 isolates the ODE→source layer from the subsequent integral kernels.

Rust Track A precedent: $D_{100} = 478$% CAMB was localized to $\dot\sigma$ ODE precision via source-level inspection. bass-py must have the same diagnostic capability.

### 4.3 Comparisons

| Quantity | Oracle | Target |
|----------|--------|--------|
| Temperature source $S_T(k, \eta)$ | CAMB `get_source_function` | ±5% point-by-point at $\ell \leq 30$ |
| Polarization source $S_E(k, \eta)$ | CAMB | ±5% at $\ell \leq 30$ |
| Visibility $g(\eta)$ peak position | CAMB | $< 0.5$% on $z_*$ |
| Recombination $x_e(z)$ | HyRec-2 | $< 1$% (reference is HyRec-2, not CAMB's internal RECFAST) |

### 4.4 Exit criterion

All L1 rows green → L1 GATE PASSED. If L1 fails but L0 is green, the regression is in the W4–W5 stack; diagnose there before proceeding.

---

## §5 L2 — Observed $D_\ell$ gate (W6.5) — hard gate

### 5.1 Oracle

CAMB $D_\ell$ end-to-end, TT/EE/TE at minimum, BB optional for this gate.

### 5.2 Gate criteria (all must pass)

| Criterion | Target | Status if failed |
|-----------|--------|------------------|
| **C1** $D_\ell$ TT agreement with CAMB | ±2% for $\ell \in [2, 30]$ | HALT |
| **C2** $O(\Sigma^2)$ perturbative consistency | $D_\ell(\Sigma^2 = 10^{-8}) - D_\ell(\Sigma^2 = 0)$ matches Fisher-linear to ±10% | HALT |
| **C3** FLRW baseline $D_2$ | within ±2% of CAMB $D_2$ (TT) | HALT |
| **C4** Precision report documented | `WEEK6_PRECISION_REPORT.md` filed | HALT (documentation blocker) |

### 5.3 Failure-handling protocol (binding)

```
IF any of C1–C4 fails:
  1. HALT all W6+ activity (no nested sampling)
  2. Run L1 bisection to localize the offending layer
  3. PATCH & re-run L0 → L1 → L2 in sequence
  4. LOG every failed attempt in WEEK6_PRECISION_REPORT.md
     (RCA: what broke, why it was missed, what check catches it next time)
  5. NO sampling runs until L2 green
  6. Gate re-review must pass PHYS-MATH + PHYS-MATH-CODE audit
```

This protocol is binding. Bypassing it — e.g., running sampling with "known" 5% bias because "it probably cancels" — is treated as a P0 finding retroactively.

### 5.4 Why ±2% and not tighter

- Rust Track B is at 1.8% CAMB ($D_2 = 1004$ vs CAMB baseline ~1022).
- Rust Track A is at 1.5% CAMB at $\ell=2$.
- Both existing implementations cluster around 2%; demanding tighter than their floor forces bass-py to out-perform Rust, which has no physical justification at this phase.
- **CONDITIONAL**: if bass-py reaches ±1% reliably during W6, the gate can be tightened retroactively.

### 5.5 Why $O(\Sigma^2)$ perturbative consistency matters

The VER06 production value $\beta = 1.36 \times 10^{-3}$ is a derivative, not a level. A forward operator that reproduces the isotropic level within 2% but fails perturbative consistency would produce a well-converged but *biased* posterior. C2 protects against this.

---

## §6 L3 — Three-way independent-implementation consensus (W8)

### 6.1 Oracle

Agreement across three substantively independent forward pipelines:

| Implementation | Method | Current $D_2$ CAMB-ratio |
|----------------|--------|--------------------------|
| bass-py FLRW limit | Paper I Teff + forward strata | TBD (target: 97–103%) |
| Rust BASS Track B | Transfer-scaling Route B (Michaelis-Menten lookup) | 98.2% |
| Rust BASS Track A | Full sync_gauge_camb.rs ODE (σ-based Φ̇) | 101.5% |

CAMB serves as the common anchor but is not counted as an "independent implementation" — it's the baseline.

### 6.2 Consensus definition

All three ratios inside a **±3% envelope** around a common center. Equivalently, $\max - \min < 3$%.

Current Rust-only envelope: 98.2%–101.5% = 3.3% → just outside ±3%. bass-py must land inside the [98.2%, 101.5%] interval *or* its inclusion should tighten the envelope.

### 6.3 Outcomes

| Scenario | Interpretation | Action |
|----------|----------------|--------|
| All three within ±3% | Precision ESTABLISHED at ±3% | Manuscript claims this envelope |
| bass-py inside Rust range | bass-py validates Rust | Report consensus, tighten if possible |
| bass-py outside but consistent with one Rust track | Localizes disagreement | Identify systematic: which two agree, which disagrees, why |
| All three disagree | No consensus | Systematic cause required before any $\ln B$ quotation |

### 6.4 Independence check

bass-py implements Paper I's Teff framework (species-resolved $(\Theta, \eta)$ + Laguerre spectral basis). Rust BASS implements covariant Boltzmann in sync-gauge CAMB convention with PSTF + $T_{\mathrm{eff}}$ parallel solvers. The methods are independent at the ansatz level, not just at the implementation level. This is the minimum bar for the three-way check to mean anything; if bass-py were a Python port of Rust BASS the consensus would be circular.

---

## §7 Integration into the existing plan

### 7.1 Week 3 insertion

Add to W3D5 scope alongside the existing `spherical_quadrature.py` (Lebedev): `precision_dashboard.py`. If D5 is overrun, `precision_dashboard.py` can slip to a W3 epilogue (W3D5.5) — **Lebedev quadrature keeps priority** since it unlocks 3D PSTF for the rest of the plan.

### 7.2 Week 5 closing

Add one-day L1 GATE CHECK at end of W5 (existing last day). No new module; uses existing forward stratum plus a `l1_source_comparison.py` utility.

### 7.3 Week 6.5 insertion (new day-block)

Insert **W6.5 PRECISION GATE** between existing W6 (Likelihood) and W7 (Phase 3 full 10-type). Deliverables:
- `WEEK6_PRECISION_REPORT.md` (required)
- All C1–C4 criteria green
- Gate review sign-off (equivalent to W2 gate review protocol)

**32 nested sampling runs scheduled for W6 shift to W6.5→W7 boundary** (runs begin only after gate is green).

### 7.4 Week 8 addition

Extend existing Phase 3 validation day to include the L3 three-way run. This does not require new infrastructure beyond what W6–W7 already builds.

### 7.5 Schedule impact

Net delivery delay: **0 days**. L0 fits inside W3D5 budget (~200 LoC), L1 fits inside W5 closing day, L2 is a new half-day-to-one-day block inserted as a gate, L3 is an extension of existing W8.

If any gate fails, the delay is finite (1–3 days per iteration) and required.

---

## §8 Binding principles added by this amendment

1. **No sampling runs before L2 is green.** This is binding.
2. **Every precision claim in the manuscript must trace to an L-level** and explicit oracle. "bass-py agrees with CAMB" without L-level attribution is a rejected phrasing.
3. **The three-way envelope is a reported number**, not a rhetorical claim. Manuscript states the actual envelope (e.g., "±2.8% across bass-py, Rust Track A, Rust Track B"), not "agrees with established codes".
4. **Gate failure logging is mandatory**, not optional. `WEEK6_PRECISION_REPORT.md` contains every failed attempt with RCA.

---

## §9 Open questions for approval

| Q | Options | Default |
|---|---------|---------|
| L0 deadline flexibility | W3D5 strict, or W3D5.5 epilogue | **W3D5.5 epilogue** (preserves Lebedev priority) |
| L1 oracle implementation | Call CAMB via subprocess, or pre-computed table | subprocess (fresh each run) |
| L2 $\ell$ range | [2, 30], or [2, 50]? | **[2, 30]** for gate, with [31, 100] as WATCH |
| L2 tolerance tightening trigger | Automatic if C1 ≤ 1% for 3 runs, or manual review | Manual review at W7 |
| L3 CAMB anchor | CAMB v1.6.6 pinned, or float? | Pinned (reproducibility) |

---

## §10 Claim taxonomy (three-tier)

| Claim | Tier |
|-------|------|
| "Likelihood sampling requires a calibrated forward operator" | ESTABLISHED (general Bayesian argument) |
| "±2% at $\ell \in [2, 30]$ is the appropriate gate" | CONDITIONAL on existing Rust Track A/B precision floor |
| "Three-way envelope establishes precision" | CONDITIONAL on implementation independence — verified in §6.4 |
| "L0 is fully CAMB-independent" | ESTABLISHED (analytical oracle only) |
| "L2 failure protocol prevents systematic $\ln B$ bias" | CONDITIONAL on C2 being tight enough — reviewable at W7 |

---

**End of amendment. Awaiting approval. On approval, master plan `BASS_PY_INTEGRATION_v4.md` is superseded by v4 + this amendment; the combined document becomes the v4.1 baseline.**
