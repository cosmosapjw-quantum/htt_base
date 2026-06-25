# 08 — Prior-Art Map (Web CRAG) and Novelty

Grounding for the NT2-\* theorems and the blocker discharges (web-checked June 2026). Each entry: what exists, and the delta this program adds.

## Fisher / Cramér–Rao for low-ℓ CMB power (NT2-A1)

- **Knox 1995** (PRD 52, 4307); **Tegmark 1997**; **Scott, Srednicki & White**: the Gaussian power-spectrum Fisher information `I(C_ℓ)=(2ℓ+1)f_sky/(2C_ℓ²)`, hence `Var(C_ℓ)/C_ℓ²=2/((2ℓ+1)f_sky)` — the textbook cosmic-variance + sky-cut result. This is the engine of NT2-A1.
- **Delta:** no prior work propagates this to a *filling-fraction / occupancy diagnostic* `F_shear` through the EGS shear→multipole response and sums over `ℓ` to give a floor on the diagnostic. NT2-A1 is that floor — and it *corrects* the report's mislabelled single-ℓ "Cramér–Rao floor".

## EGS / almost-EGS chain (NT2-A2, NT2-B1, NT2-B3)

- **Ehlers–Geren–Sachs 1968**; **Stoeger–Maartens–Ellis 1995** (ApJ 443, 1); **Maartens–Ellis–Stoeger 1995** (PRD 51, 1525): almost-EGS bounds; hypotheses H1 (Copernican), H2 (multipoles never larger than now), **H3** (multipole derivatives bounded by the multipoles).
- **Ellis–Treciokas–Matravers** / **Treciokas–Ellis 1971** (CMP 23, 1): the ℓ=2 free-streaming closure, `κ=4/21` — the shear↔quadrupole coefficient.
- **Nilsson–Uggla–Wainwright–Lim 1999** (ApJ 522, L1): if H3 fails, an almost-isotropic CMB bounds neither shear nor Weyl (shear→0 but Weyl↛0) — the loophole behind NT2-B3(i) and the H3 condition in NT2-B1.
- **Delta:** NT2-B1 adds a *two-sided* bracket (lower bound excluding zero shear-filling), not the usual one-sided MES limit; NT2-A2 states octupole sufficiency for the diagnostic; NT2-B3 unions the Weyl loophole with the radial no-go.

## Velocity-field blockers (K5, K6)

- **Hoffman & Ribak 1991**; **Zaroubi, Hoffman & Dekel 1999**: Wiener filter + constrained realizations; the CR ensemble samples the posterior around the WF mean.
- **Hoffman et al. 2024** (MNRAS 527, 3788; arXiv 2311.01340): CF4 WF/CR reconstruction with Bias-Gaussianization; random/constrained CF3-like mocks; `V_bulk(R)` and `Δ_L(R)` profiles to 300 `h⁻¹`Mpc. **CORAS** (arXiv 2102.07291): CR error estimation for any inferred quantity.
- **Delta:** applying the CR ensemble specifically to the **curl/vorticity posterior** (K6) and to **release-matched forward-mock coverage** (K5) discharges the report's two velocity blocks.

## CMB E2E sims (K1)

- **Planck FFP10** (PR3): 999 CMB + 300 noise/systematic MC per method, public on the PLA (`dx12_v3_{method}_{cmb,noise}_mc_*`). **PR4/NPIPE:** ~300 SEVEM/Commander E2E sims. Used routinely for low-ℓ isotropy/anomaly null calibration (e.g. PR4 isotropy analyses 2024–2025).
- **Delta:** running the report's K1 max-scan on the public E2E ensemble discharges `BLOCKED_MISSING_PR4_E2E_ACCESS` — the "access" was never actually required.

## Novelty statement (one paragraph)

The Fisher formula for `C_ℓ`, the EGS/almost-EGS chain, the H3/Weyl loophole, Hoffman–Ribak CRs, and the public Planck E2E sims are all established. What is new here is (1) the **genuine multi-multipole Fisher–Cramér–Rao floor on the shear-filling diagnostic** `F_shear`, which both corrects the report's mislabelled single-estimator "floor" and is strictly stronger (a bound no unbiased estimator beats, below `0.632`, `f_sky`-aware); (2) the **two-sided quadrupole+octupole bracket** that excludes a vanishing shear-filling at nonzero quadrupole; (3) the **GR shear-memory sourcing** of the depth gap by the tilt anisotropic stress; (4) the **joint vorticity blind-sector no-go** for the CMB-temperature + radial-velocity channels; and (5) concrete, public-data **discharges of three of the four standing blocks** plus a tractable interim path for the fourth. No prior work connects a filling-fraction/occupancy diagnostic to a Fisher floor or to a two-sided EGS bracket, nor packages the CF4 WF/CR and Planck E2E machinery as discharges of these specific blocks.
