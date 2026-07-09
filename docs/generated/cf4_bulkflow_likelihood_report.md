# CF4 Bulk-Flow Likelihood on the Full Group Release (LR-06D)

owner: OBSSTAT · claim_tier: diagnostic_only · ticket: LR-06D
release: Cosmicflows-4 (Tully+ 2023) VizieR J/ApJ/944/94 table4 · 38053 usable groups

| depth [Mpc] | N | sky frac | sigma_star | |B| [km/s] | apex (l,b) | mock coverage |
| --- | ---: | ---: | ---: | --- | --- | ---: |
| 60 | 3916 | 0.97 | 90 | 320 +/- 7 | (296, 20) | 0.68 |
| 100 | 8540 | 0.98 | 50 | 351 +/- 5 | (293, 22) | 0.72 |
| 150 | 13844 | 0.99 | 50 | 347 +/- 5 | (293, 21) | 0.65 |
| 200 | 18191 | 0.99 | 50 | 346 +/- 5 | (293, 21) | 0.67 |
| 300 | 26363 | 0.99 | 50 | 345 +/- 5 | (293, 21) | 0.67 |

Observer-frame note: peculiar velocities use the catalog ramp Vpec (V3k cosmological frame for the error scaling); a full Vh/Vls/V3k frame ablation is a follow-up.

## Caveats

- Weighted-GLS bulk flow on the CF4 group peculiar velocities; diagnostic-only.
- sigma_star is fitted to reduced chi^2 ~ 1; covariance is the inverse Fisher matrix.
- Forward-mock coverage uses the real geometry + errors with the recovered B as the injected truth.
- No global-tilt or Bianchi-geometry claim is made from CF4 distances alone.
- Selection and Malmquist/inhomogeneous-sampling biases are not fully forward-modelled here.
