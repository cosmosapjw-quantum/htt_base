# R2-03 independent review

Verdict: **SCOPED PASS** for the finite-ansatz F4 implementation and C0 same-sky diagnostic. The complete empirical R2-03 card, actual full-field F4 and joint posterior remain **HOLD**.

Reviewer was a fresh read-only native agent, requested `gpt-6-astra/ultra`. Independently observed model and effort: `UNKNOWN`. Upstream proofs were assumed valid under owner direction; no proof campaign was rerun. Base commit `c5a683eba0ef1a7d10cc5a7bd6cb6b853bc69eb1`; all five final source SHA-256 values match `RETURN.json`.

One P2 wording finding in `htt/obsstat/r2_cmb_product_bridge.py` was repaired: monopole/dipole removal now follows each product's supplied processing convention. The reviewed bridge hash is `acbbb1185dd62474f42ccc0f460b7505a0f301dcd39e8e657a410d0443e2b4ba`. Reversing only that docstring recovers the preceding hash. The original diagnostic's generating hashes remain historical. No numerical behavior changed.

Independent checks: 15 affected tests passed; final wording repair 10 focused tests passed. Full-sphere direct quadrature F4 absolute error was `2.22e-16`; eight-coordinate Jacobian maximum absolute error was `1.45e-15`. Independent refit of four stored reduced maps had rank 36 and maximum retained coefficient difference `4.40e-20 K`; all six same-sky contrasts replayed. The common mask has 36,433 of 49,152 pixels. These contrasts are descriptive, not independent constraints or calibrated bias estimates.

The omission envelope `4(M+r)^3 r` applies only when a full-sphere sup-norm bound `r` is supplied. Missing release-specific beam/pixel/removal processing, joint shared-sky measurement law, physical dipole and angular-mean temperature joint uncertainty, and omitted-mode control prevent empirical full-field F4 and posterior claims. [Planck 2018 IV](https://www.aanda.org/articles/aa/full_html/2020/09/aa33881-18/aa33881-18.html) supports product-specific processing qualification.
