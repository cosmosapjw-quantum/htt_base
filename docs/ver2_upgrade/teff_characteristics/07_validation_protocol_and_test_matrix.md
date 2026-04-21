# Validation Protocol and Test Matrix

문서 목적: validation을 `코드가 돌아간다`가 아니라 `어떤 theorem/claim의 어떤 제어량이 실제 수치 파이프라인에서 대응되는가`로 설계한다.

---

## 1. Validation philosophy

Validation은 세 층과 하나의 robustness 층으로 나눈다.

- Layer A: exact/full characteristic transport correctness.
- Layer B: reduced-block Teff adequacy.
- Layer C: observable/spectrum adequacy.
- Layer R: realizability and switching robustness.

이 분리는 필수다. Layer A가 실패하면 Teff adequacy를 평가할 reference가 없다. Layer B가 성공해도 Layer C가 자동으로 성공하지 않는다.

---

## 2. Mandatory outputs

Every test should produce:

1. `config_<test-id>.yaml`,
2. `metrics_<test-id>.json`,
3. `summary_<test-id>.md`,
4. `log_<test-id>.txt`,
5. figures if relevant,
6. `passfail_<test-id>.json`.

Standard metric keys:

- `runtime_sec`,
- `max_memory_mb`,
- `state_l2_error`,
- `observable_error`,
- `spectrum_error`,
- `trace_residual`,
- `spin2_residual`,
- `high_residual`,
- `theta_min`,
- `eta_max`,
- `switch_count`,
- `min_dwell_time`,
- `status`.

---

## 3. Layer A - characteristic transport correctness

### A1. Minkowski straight-line test

Claim: characteristic integrator reproduces analytic null transport in flat spacetime.

Primary metric:

\[
\epsilon_{x,p}(t)=\|X_{\rm num}(t)-X_{\rm exact}(t)\|.
\]

Acceptance: convergence order matches integrator order; conserved quantities remain within tolerance.

### A2. FLRW redshift test

Claim: isotropic FLRW limit recovers standard redshift and intensity scaling.

Acceptance: numerical redshift and energy-density scaling converge to analytic values.

### A3. Anisotropic/Bianchi background test

Claim: 1+3 covariant characteristic formulation handles anisotropic expansion without pretending to be FLRW.

Acceptance: stress/anisotropy observables match semi-analytic or high-resolution reference.

### A4. Screen-basis transport test

Claim: polarisation basis transport is stable and gauge/basis-consistent.

Acceptance: basis orthonormality drift and spurious E/B mixing remain below tolerance.

---

## 4. Layer B - reduced-block Teff adequacy

### B1. One-field vs two-field false-trigger test

Claim: eta extension removes residual falsely attributed to spectral distortion in one-field Teff.

Primary metric:

\[
D^{(1)}_{\ge2}-D^{(2)}_{\ge2}.
\]

Acceptance: known eta-tangent configurations show reduced residual in the two-field chart.

### B2. Trace source adequacy test

Claim: when trace block is on Teff manifold, nonlinear Thomson source from Teff equals source computed from the full trace distribution.

Primary metric:

\[
\epsilon_{I_2}=\left|I_{2,\rm full}-I_{2,\rm Teff}\right|.
\]

Acceptance: machine/tolerance-level agreement for on-manifold cases.

### B3. Spin-2 invisibility test

Claim: Teff trace diagnostics do not falsely certify spin-2 adequacy.

Setup: construct states with identical trace but different spin-2 content.

Acceptance: trace diagnostics unchanged while spin-2 residual reports difference.

### B4. Q-normalization regression test

Claim: Paper V Table II convention is internally consistent.

Setup:

\[
\Theta(\mu)=1+A\mu+Q(\mu^2-1/3).
\]

Required outputs:

- exact `I2/(c_xi T0^4)`,
- linear `8Q/3`,
- quadratic `8Q/3 + 4A^2 + 16Q^2/21`,
- percent underestimate.

Acceptance: `(A,Q)=(0.30,0.15)` gives exact about `0.84214` and linear `0.400`.

---

## 5. Layer C - observable/spectrum adequacy

### C1. TT adequacy

Claim: trace reconstruction controls TT-relevant observable error in well-conditioned regimes.

Metrics:

- `Delta_TT`,
- `D_state`,
- `sigma_min(J)`.

Acceptance: empirical scaling follows the conditional local bound in Paper IV.

### C2. EE source plus propagation

Claim: nonlinear trace source improves source term, but EE accuracy also requires spin-2 propagation correctness.

Metrics:

- source error,
- E propagation error,
- final EE error.

Acceptance: source improvement translates into EE improvement only when spin-2 propagation is controlled.

### C3. BB full-spin-2 necessity

Claim: trace Teff cannot control BB by itself.

Setup: states with identical trace but different B-generating spin-2 content.

Acceptance: BB changes while trace Teff variables remain identical. This is a deliberate confirmation of scope boundary.

### C4. TE mixed adequacy

Claim: TE requires both trace and spin-2 correctness.

Acceptance: error decomposition separates trace-source error from spin-2 propagation/correlation error.

---

## 6. Layer R - realizability and switching

### R1. Theta positivity boundary

Monitor

\[
\theta_{\min}=\min_{\hat e}\Theta(\hat e).
\]

Acceptance: switching/refinement triggers before `Theta <= 0`.

### R2. Eta domain stress

Monitor eta bounds and degeneracy-related conditioning.

Acceptance: solver does not silently continue outside admissible statistical domain.

### R3. No-chattering switch test

Acceptance: switching obeys minimum dwell time and does not introduce conservation drift.

---

## 7. Pass/Warn/Fail policy

- PASS: primary acceptance criterion satisfied.
- WARN: primary criterion satisfied but conditioning, secondary metrics, or interpretation is marginal.
- FAIL: criterion missed, admissibility violated, or source/reference mismatch invalidates the test.

Do not count a run as PASS merely because it completed.

---

## 8. Minimal campaign order

Phase 1: A1, A2, A4.  
Phase 2: B2, B3, B4.  
Phase 3: C1, C2, C3.  
Phase 4: R1, R2, R3.  
Phase 5: stress tests and production-like regimes.

---

## 9. Interpretation rules

1. A successful Teff source test does not validate full polarisation transport.
2. A successful characteristic transport test does not validate reduced Teff adequacy.
3. A small collision-side diagnostic does not automatically imply small state residual.
4. TT success does not imply EE/BB success.
5. BB tests should deliberately demonstrate that trace Teff is insufficient.

---

## 10. Validation conclusion

The validation campaign should make the scope boundary visible. The best outcome is not `Teff works everywhere`; the best outcome is a calibrated map of where the trace-sector reduced chart is reliable, where it must switch off, and how its source bridge interacts with independently transported spin-2 modes.
