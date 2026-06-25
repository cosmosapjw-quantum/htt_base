# PR07 Web CRAG Source Ledger (retrieved 2026-06-25)

Primary sources, each tied to a design decision / novelty boundary — not copied
as authority for a repository result. URLs in `web_sources.json`.

| Topic | Primary source | Used for | Contradiction / limit tracked |
|---|---|---|---|
| Wolfram–Python bridge | Wolfram Client Library for Python docs | persistent local session, explicit kernel, termination | local engine still required |
| xAct roles | xAct/xTensor/xCoba docs | abstract vs component proof ownership | xTensor alone is not a component calculator |
| ODE cross-check | SciPy `solve_ivp` docs | DOP853 explicit + Radau implicit cross-check | agreement ≠ model correctness |
| PR4 calibration | *Exploring Statistical Isotropy in Planck DR4* (2504.05597) | 600 E2E benchmark, full pipeline matching | not a substitute for our exact scan-family execution |
| CF4 estimators | Whitford, Howlett & Davis, *Evaluating bulk-flow estimators for CF4* (2306.11269) | Kaiser MLE vs MVE terminology; realistic-mock requirement | their survey/model is not our covariance |
| CF4 reconstruction | Hoffman et al., *Large-scale velocity field from CF4* (2311.01340) | WF/CR ownership; reconstruction-conditioned errors | potential-flow prior suppresses curl |
| independent reconstruction | Nusser, *Bayesian Reconstruction … 2MRS … CF4* (2606.08593) | external field comparison (PR08-005) | cross-covariance must be owned |
| tilted Bianchi-I prior art | Sandin & Uggla, *Bianchi I with two tilted fluids* (0806.0759) | flux-cancellation / Codazzi prior art | two-fluid solutions are not our novelty |
| stability prior art | Fournodavlos, Marshall & Oliynyk (2508.15155) | future-stability novelty boundary | restricted parameter/matter branch differs |
| Bianchi CMB transfer | Pontzen & Challinor (0706.2075) | solver novelty boundary; T/E/B requirements | old templates do not validate our future solver |
| Planck Bianchi tests | Saadeh et al. (1605.07178) | avoid generic "first Bianchi test" claim | our novelty is source-owned multicomponent inference |

**Novelty boundary (PAPER-B):** do not claim discovery of tilted Bianchi-I
solutions (Sandin–Uggla) or new nonlinear stability (Fournodavlos et al.). The
contribution is the source-owned multicomponent identifiability framework and
the dimensionally consistent restricted-branch dynamics.
