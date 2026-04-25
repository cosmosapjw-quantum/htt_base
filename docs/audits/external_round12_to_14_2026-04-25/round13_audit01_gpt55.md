# V5-RUNTIME Round-13 External Audit Verdict

**Auditor**: GPT-5.5 Thinking
**Date**: 2026-04-25
**Bundle SHA**: 0536f0e (HEAD per COMMIT_LOG.md)

## Verdict (one-line)

**PARTIALLY-CONFIRMED** — Phase A는 super-horizon low-k artefact와 IMEX drift 비원인성을 꽤 잘 지지하지만, Option A를 “최종 물리 fix”로 확정하기에는 부족하다. k_min clipping은 diagnostic/safety guard로는 타당하나, low-k 모드를 버리는 fix가 아니라 analytic SW/low-k continuation 또는 split quadrature로 대체해야 한다. 잔여 32×는 Ψ=-0.34 대 +0.6만으로 설명되지 않고, LOS source/Doppler/acoustic projection convention 쪽이 더 강한 후보다.

## Summary

D5는 linear-probe path에 직접 쓰이지 않으므로 root-cause 증거로는 약하다. D1+D2는 Φ/Ψ가 1/k^2로 폭주하지 않는다는 점은 보여주지만, 스크립트가 실제 constraint residual을 계산하지 않고, BASS `psi`의 sign convention도 MB95와 직접 맞지 않을 가능성이 남아 있다. D3의 k_min sweep은 760→32 하락을 재현하지만, 각 run이 새 12-point log grid라 “동일 적분에서 low-k 95% 기여”를 증명하지는 않는다. D4는 monkey-patch가 effective라면 IMEX projection drift를 강하게 배제한다.

## Step 1 — Phase A 진단 방법론 검증

### Q1.1 — D5 seed amplitude trace

`projected_seed.amplitude = 1.39e-4` at k=1e-4 and `1.39e-2` at k=1e-3 does confirm that the seed projection trace contains a k^2-scaled quantity. But this is not evidence that the D2 linear probe is still being divided by a hidden k^2 amplitude.

Reason: D5 config sets `unit_amplitude_normalization=False` and `primordial_b_k_sq=1.0` in `investigation_code/v5_round12_phase_a_diagnostics.py:74-78`. The actual linear-probe wrapper also forcibly replaces the config with `unit_amplitude_normalization=False`, clears `primordial_b_k_sq_fn`, and uses explicit division by `probe_b_k_sq` in `code_under_audit/flrw_pipeline.py:1258-1287`. In `_los_and_wrap`, the seed amplitude is consumed only under `if cfg.unit_amplitude_normalization and seed_amp_for_norm is not None` at `flrw_pipeline.py:345-352`; otherwise it is bypassed. Therefore D5 is relevant as an archaeology trace but irrelevant to the active 760× path.

### Q1.2 — D1+D2 Φ/Ψ behavior

`sources.psi(eta)` is a real callable evaluation, not a mere array misuse. `extract_flrw_sources_from_tier_b` returns PCHIP callables with `extrapolate=False` in `tier_b_source_extraction.py:308-318`, and the diagnostic evaluates them on the solver’s own eta grid at `v5_round12_phase_a_diagnostics.py:211-220`. So there is no obvious interpolation-domain bug.

But two problems remain. First, the script’s docstring promises a comoving-density constraint residual R, but the implementation never computes or prints R; it only prints `psi`, `theta_0`, `v_b`, `pi`, and SW combo. Thus D1+D2 refutes “visible Ψ blow-up”, not the full “constraint residual is clean” claim. Second, the measurement at η_* is actually the first solver grid point in the transcript (`η_init=η_*=260.1 Mpc`), so this is a nearest-grid recombination/start-point sample, not an independently resolved visibility-peak diagnostic.

The value Ψ≈−0.34 is k-independent enough to refute a raw 1/k^2 divergence. It does not refute sign/factor convention errors. In MB95, conformal Newtonian gauge uses `ds^2=a^2[-(1+2ψ)dτ^2+(1−2φ)dx_i dx_i]`, and anisotropic stress enters as `k^2(φ−ψ)=12πGa^2(ρ+P)σ`. BASS instead documents and implements a positive `psi_minus_phi` added as `psi=phi+psi_minus_phi` in `tier_b_source_extraction.py:147-150, 291-302`. Unless BASS’s internal `phi` or stress variable is already sign-flipped relative to MB, that is a sign-convention mismatch candidate.

The analytic comparison `Ψ_SW≈+0.6` is also not uniquely fixed unless the exact C/ζ normalization is nailed down. MB95 eq. 98 gives `ψ=20C/(15+4Rν)` and `φ=(1+2Rν/5)ψ`; for Rν≈0.409, this is `ψ≈1.20 C`, not automatically 0.6 unless C≈0.5. So the sign mismatch is serious; the magnitude mismatch alone is not enough to diagnose 32×.

### Q1.3 — D3 k_min sweep

D3 is good evidence that the sparse audit integral is hypersensitive to the low-k end. The transcript shows D2/Route-B = 3956, 3086, 756.5, 91.5, 32.2 as k_min is raised from 1e-5 to 1e-3. The canonical 756→32 change is a factor 23.5, which supports the “super-horizon spike plus sub-horizon baseline” decomposition as a useful empirical description.

But it is not a mathematically clean decomposition. The script builds a fresh `np.logspace(log10(k_min), -1, 12)` for every k_min at `v5_round12_phase_a_diagnostics.py:288-291`; it is not the same dense grid with low-k segments zeroed or replaced. Changing k_min changes all 12 abscissae and trapezoid weights. Therefore “super-horizon spike contributes 95%” should be weakened to: “the observed sparse-grid D2 estimate is low-k-end sensitive, and removing the low-k region by regridding collapses the ratio to about 32.”

### Q1.4 — D4 every_n_steps toggle

The monkey-patch is probably effective. D4 imports the module object `bass.spectrum.flrw_pipeline as _pipe`, replaces `_pipe._pipeline_runtime_controls`, and then calls `compute_flrw_d_ell_linear_probe` in the same module namespace. The pipeline code calls `_pipeline_runtime_controls(cfg)` when building the run controls in both the single-k and shared chunk paths (`flrw_pipeline.py:410-415, 474-475`).

Still, the diagnostic should log the actual RuntimeControlBlock handed to `execute_tier_b_solver` or the lower runtime request. Without that trace, the audit cannot exclude a hidden worker/import path bypass. If the patch is effective, the bit-identical result is strong evidence that every-4-step IMEX projection drift is not the observable’s root cause.

## Step 2 — 32× 잔여 root cause 분석

### Q2.1 — Ψ≈−0.34 sign

BASS’s `psi` is intended to be the Newtonian potential used inside the SW source: `theta_0 + psi + pi/4`. But the reconstruction is not manifestly MB95-compatible. MB95’s conformal Newtonian metric and stress equation imply a specific relation between ψ, φ, and anisotropic stress. BASS computes a constraint-like `phi` using `(delta_rho_tot - 3H*mom/k)`, then adds a positive stress correction as `psi = phi + psi_minus_phi`.

This is enough to keep “sign convention mismatch” alive. It is not enough to declare the exact fix, because the BASS variable named `phi` may already represent a sign-flipped Bardeen potential or a synchronous-to-Newtonian transformed variable. The required test is simple: run extractor with `anisotropic_stress=False`, compare against MB95 no-stress growing mode, then enable stress and check whether the sign follows `φ−ψ`, not `ψ−φ`.

### Q2.2 — magnitude 0.34 vs 0.6

The magnitude mismatch is a weak explanation for 32×. Numerically, `0.6/0.34≈1.76`, and squared this gives ≈3.1, not 32. The linear factor corresponding to 32 is sqrt(32)≈5.66. Therefore Ψ magnitude alone cannot be the residual factor.

The suggested baryon or neutrino fractions do not match cleanly either. `Rν/(1+Rν)` for Planck-like Rν≈0.409 is ≈0.290; its inverse is ≈3.45, not 1.76 or 5.66. `1−Rb/(1+Rb)` is not stable enough without a clearly defined Rb at η_* and also does not naturally produce 5.66. The MB95 denominator `15+4Rν` gives `(15+4Rν)/3≈5.55`, close to sqrt(32), but no audited code path squares exactly this factor downstream. Treat this as numerology until isolated by a transfer-function normalization test.

### Q2.3 — Doppler/acoustic regime

The high-k `α_meas/α_SW` blow-up is not by itself pathological, because an SW-only prediction is not valid in the acoustic/Doppler regime. But the transcript values are too structured to ignore: at k=0.1, odd multipoles reach |ratio|≈8e4, while even multipoles are ≈3.4e3. That is a strong footprint of LOS projection/source-term convention issues, not a mere global normalization.

The highest-priority suspect is the Doppler source implementation. BASS constructs `doppler = np.gradient(g*v_b, eta_grid)` and then projects the total source directly against `j_l[k(η0−η)]` (`flrw_bessel_projector.py:447-455, 539-546`). Standard LOS formulae can be written either with a velocity term multiplying `j_l'` or, after integration by parts, with a derivative source multiplying `j_l` and a specific k-factor/sign. BASS must prove that its `v_b` convention and derivative-source form are exactly equivalent. Right now this is not proven in the bundle.

### Q2.4 — sqrt(32) convention factor

I do not find a credible exact 5.66 convention factor in the audited files.

`4√2=5.657` matches numerically but has no obvious code anchor. `(15+4Rν)/3≈5.55` is close and appears in the seed formulas (`regular_adiabatic_ic.py:136-176`), but the seed-side B_K fixes are already applied and this denominator does not naturally appear as a downstream squared transfer normalization. `16/3=5.33` is not close enough and also lacks a direct line-level origin.

The C_l assembly is probably not the 32× source. It implements `C_l=4π∫dlnk P_R(k)|Δ_l|²` and `D_l=l(l+1)C_l T_CMB²/(2π)` in `cl_assembly.py:255-291, 492-518`, which is the standard convention. A global C_l conversion bug would also not naturally explain the strong k/ell dependence seen in the per-k diagnostic.

## Step 3 — Option A 검증

### Q3.1 — legitimate physics or numerical patch?

Clipping low k is legitimate only as a guarded diagnostic or as one half of a split analytic/numerical method. It is not legitimate as “remove k<k_min and call the result physical.” Low-l CMB power, especially D2, is physically supported by near-horizon and super-horizon modes. Discarding them biases the quadrupole.

CAMB and CLASS do not solve this by simply throwing away low-k modes. CAMB’s public documentation says it computes CMB spectra from primordial curvature perturbations with standard output scaling, and its source code explicitly treats large scales as a special regime (`EV%q<0.05`) by reducing/evolving the relevant equation set, not by clipping them out. CLASS documentation similarly describes storing and interpolating source functions and using approximation switches over k and τ, not deleting the low-k sector.

Therefore Option A is acceptable only if “k_min clipping” means: below k_split, replace the unreliable numerical source with a controlled analytic SW/low-k continuation and integrate that contribution separately. If it means “exclude k<1e-3,” it is a numerical patch.

### Q3.2 — dense Nk convergence

The bundle does not prove dense-Nk convergence. D3 uses five independent 12-point grids, not nested quadrature. The older Nk dependence noted by Round-12 auditors is consistent with unresolved quadrature and/or a low-k source pathology. The decisive diagnostic should dump the integrand `P_R(k)|Δ_2(k)|²` on a single dense grid, report per-log-k bin contributions, and then compare:

1. full numerical low-k;
2. low-k zeroed;
3. low-k replaced by analytic SW continuation;
4. dense adaptive or segmented quadrature.

If (3) converges to Route-B while (1) does not, Option A-with-continuation is valid. If only (2) “fixes” the number, it is just hiding the low-k problem.

### Q3.3 — where should k_min_cutoff enter?

The correct implementation is option (c): split the integral. Below k_split, use analytic SW/low-k continuation; above k_split, use the numerical transfer. The assembly layer should know which domain is numerical and which is analytic, and the returned bundle should include metadata recording `k_split`, low-k analytic contribution, high-k numerical contribution, and the handoff error.

Option (a), wrapper-level removal from `k_grid`, is acceptable only as a diagnostic kwarg with default `None`. Option (b), assembly-level zero weights, is more explicit for an ablation but still not a physical fix. The physically honest fix is not clipping; it is replacing an invalid source model in the low-k domain.

### Q3.4 — correct cutoff value

`1e-3 Mpc^-1` is empirical, not physically principled. From the transcript, `η_*≈260.1 Mpc`, so `1/η_*≈3.84e-3 Mpc^-1`. Thus k=1e-3 has `kη_*≈0.26`, still super-horizon-ish at recombination. More importantly, for D2 the Bessel support scale is roughly `k(η0−η_*)≈ell`, with `η0−η_*≈13887 Mpc`, so ell=2 corresponds to k≈1.4e-4 Mpc^-1, and even the first broad j2 maximum is only a few times that. A hard cutoff at 1e-3 removes the physically central quadrupole support.

A principled split should be based on dimensionless conditions such as `kη_* < ε` for low-k analytic handling and convergence of the handoff, not a fixed empirical `1e-3`.

## Step 4 — Final 판정 + Round-12 closure 권장

Do not close Round-12 with clip-only Option A.

Recommended closure policy:

1. Accept Phase A’s main negative results: no visible 1/k^2 Φ/Ψ blow-up in the printed `psi`; IMEX every_n_steps drift is not the dominant D2 cause if the monkey patch is confirmed effective.
2. Accept D3 as a low-k sensitivity diagnostic, not as a causal 95% decomposition proof.
3. Permit a default-off `k_min_cutoff` diagnostic kwarg only if it is labelled inference-forbidden.
4. For production, implement split low-k analytic continuation plus numerical high-k integration, not low-k deletion.
5. Treat the 32× residual as a live blocker for any claim that the FLRW linear-probe normalization is solved. The most likely class is LOS/source convention, especially Doppler/acoustic projection and stress-potential sign mapping.

## Step 5 — Cross checks

### Q5.1 Route-B Rust D2 anchor

Expected impact is 0% if Option A remains inside `compute_flrw_d_ell_linear_probe` and the Route-B Rust binary path is truly independent. The README claims the golden anchor comes from `bass_rs dump_dl_spectrum_sparse`, but the actual `_d2_anchor_golden.json` file is not included in the bundle, so this cannot be independently verified here.

### Q5.2 CAMB cross-check tests

If `k_min_cutoff=None` is the default and no seed formulas are changed, the 43 CAMB cross-checks at `b_k_sq=1.0` should be bit-identical. If the tests exercise the new cutoff path, they should change by design and must be separately baselined.

### Q5.3 `_d2_anchor_golden.json`

Not fully verifiable from this bundle. README lines 145-148 state that the file says the anchor is from the Rust binary, but the JSON itself is absent. For the next audit bundle, include `_d2_anchor_golden.json`, the Rust command line, and the exact generated stdout artifact.

## Confidence and caveats

High confidence:
- D5 is irrelevant to the active linear-probe normalization path.
- D3 proves low-k-end sensitivity but not a clean 95% causal decomposition.
- C_l and D_l assembly formulas are not the obvious 32× bug.
- Clip-only k_min removal is not physically legitimate for D2.

Medium confidence:
- D4 likely refutes IMEX projection drift, pending a runtime-control trace.
- BASS `psi` has a live sign-convention risk relative to MB95.
- Doppler/source projection convention is the strongest 32× class of suspects.

Low confidence:
- Exact scalar factor responsible for 32×. The bundle lacks the isolation tests needed to pin it to one line.
