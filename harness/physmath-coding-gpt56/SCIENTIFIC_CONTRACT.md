# SCIENTIFIC_CONTRACT.md — BASS/HTT (htt_base) instantiation

_Mounted 2026-07-14 onto the BASS/HTT Bianchi anisotropy program. SSoT authority:
`/CLAUDE.md` §1/§5 + `docs/SSOT_POLICY.md`; on conflict those win._

## Scientific objective

CMB T+E+B spectra for Bianchi types via the master departure identity
`x_C = Σ²_std − W²_std + Ω_tilt + Ω_{k,aniso}`, linked to the Maartens–Ellis–Stoeger
kinematic bound hierarchy; plus the obsstat data lanes (K1 CMB morphology, K5 CF4 peculiar
velocities, K6 vorticity, EXT-DESI/ACT/JWST) under the honest claim envelope.

## Governing definitions

- Comparator: graded `g = (Σ², W², Ω_tilt, Ω_k)`; `x_C = tr(C M)`, `M = diag(g) ⪰ 0`.
- Parent identity: `1 = Ω_m + Ω_Λ + Ω_k + Ω_tilt + Σ² − W²`, `c = (1, −1, 1, 1)`.
- Vorticity normalization: `W² = ω_ab ω^ab / (6H²)` (the ω_a ω^a/H² document convention is 3×).
- Thomson primitive: `Π_BASS ≡ Θ₂ + E₀ + E₂`; production polter `= 2Θ₂/5 + 3E₂/5`.

## Conventions

- formalism: 1+3 covariant PSTF (Ellis–van Elst) primary; CAMB-convention synchronous gauge
  on the MB-95 production path.
- unit system: Mpc / km/s / μK²; h-corrections explicit. **CF4 SGX/SGY/SGZ columns are km/s
  (cz), NOT Mpc — positions must come from Dist×n̂ (NSC-audit-confirmed bug class).**
- normalization: T_CMB = 2.72548 K (Fixsen 2009); known in-tree drift `2.7255` under guard test.
- fiducial P(k): EH98 no-wiggle, σ_v,1d = 308.09 km/s closed form. **CAMB linear σ_v = 309.0;
  370 km/s is the NONLINEAR (halofit) value — never label it linear (NSC audit P0-2).**
- stochastic convention: fixed seeds in-script (deterministic cards); GRF generators must
  Hermitianize kz=0/Nyquist planes (NSC audit P1, open defect in `pv_forward_mocks.py`).

## Valid regime

- Full-mode end-to-end LoS closed ONLY for FLRW, I, V, IX; the other 8 families are
  axis-aligned mode subsets (FB-2.2/FB-2.3 dispatch); off-axis raises `OutOfScopeError`.
- Tilted backgrounds: policy-fixed velocity closure default (`tilt_background_owner`).
- Claim tiers: kinematic/statistical measurements, consistency nulls, upper limits, exact
  theorems only. NO Bianchi family identification / geometry / anisotropy detection claims.

## Required invariants

- `D_2 = 1002.086744 μK²` bit-identical (Rust MB-95 anchor; PSTF target, PR-024c open).
- `D_2(Σ²=1e-8) = 0.174112 μK²` gallery anchor.
- `x_C` bit-identity across comparator representations (gate-guarded).
- `W2_max = 3.3789e-13` live geodesic anchor (frozen predecessors byte-identical).
- Frozen surfaces: v5/v6/v6.1/v7/v8 reports, rev-r195..r197 cards, K5 v7/v8/v9 cards,
  `cf4_groups.npz` — byte-stable under every `--check`.

## Known limits

| Limit | Expected result | Tolerance | Reference/test |
|---|---|---:|---|
| single-sky F_shear dispersion (ℓ=2) | sqrt(2/5)=0.632456 | exact | egs3-gates B1 / CAMB crosscheck |
| cell diagonal σ_v (CF4 MV) | 308.09 km/s closed form | 0.1% | test_cf4_mv_bulkflow |
| IMEX λ_max(A_right) | ~1e-16 (machine) | — | ver3_layout_protocol audits |
| uniform-flow MV injection | exact recovery | 1e-8 | cf4_mv_bulkflow validation |
| Gauss/momentum residuals (T3-lin) | < 1e-10 | — | run_egs3_v7_seals |

## Reference cases

- trusted numerical reference: `bass_rs dump_dl_spectrum_sparse` (MB-95 production).
- cross-engines: SymPy (gating) + SageMath/Singular + Lean 4 + Wolfram/xAct seals.
- published benchmarks: CAMB 1.6.6 visibility; Watkins+2023 / Whitford+2023 (comparison-only —
  the K5-MV headline was REFUTED by the 2026-07-13 NSC audit, monopole leakage; remediation
  pending owner sign-off).

## Numerical requirements

- target precision: bit-identity on anchors; `--check` byte-stability on all cards/figures.
- performance envelope: 10–15 s single-run target (CAMB ~5 s / CLASS ~7 s reference).
- ensemble policy: mock counts + seeds registered in-card; empirical p floors stated as
  resolution limits, never as evidence.

## Failure semantics

Fail-closed everywhere: `OutOfScopeError` / `AWAITING_NATIVE_LOWELL_SOLVER` / registered
`BLOCKED_*` codes — never fabricate, never substitute silently. NaN/Inf, non-convergence,
railed fit parameters at grid edges (σ* class), and validation-gate failure are failures, not
results. BANNED constructs: TCA pre-phase, FLRW UFA, photon RSA (approximation-free mandate).

## Change control

Approval required: any SSoT numerical value, convention, baseline, tolerance; anything touching
frozen surfaces; claim-tier promotions (CLAIM_LEDGER + gate bundle); NSC-audit P0 remediation
(REV-R199+ scope). Additive commits only on `research/pr04-multicomponent`; never stage
`project/` or `CLAUDE.md`.
