# PR07 Blocker Resolution Matrix

| Blocker | Why it blocks | Resolution | Local command / artifact | Exit gate | Status |
|---|---|---|---|---|---|
| B-shear unit mismatch | dimensionless Π used where physical π required | PR07-001 split `pi_physical`/`Pi_normalized` | `make pr07-gates`; Wolfram `b_shear_*` | RHS equivalence + derivative gates | ✅ |
| B-conservation review | single production fixture, not independent | PR07-003 chain-rule + constraint-transport campaign | `research_gates/pr07/test_pr07_conservation.py` | residuals <1e-11; cross-integrator | ✅ |
| A-Wigner overstatement | boost non-additivity ≠ Wigner-angle proof | PR07-002/004 split theorem | `pr07_paper_a.json`, Wolfram core | no Wigner angle claimed | ✅ |
| NT-A1 coefficient provenance | numeric closure coeff lacked source | PR07-002 keep κ symbolic (4/21 figure-only) | claim lint | no unregistered numeric coefficient | ✅ |
| NT-A3 CRLB claim | only estimator sampling variance shown | PR07-002 rename | Wolfram theorem JSON | no CRLB/universal-floor wording | ✅ |
| NT-B3 zero-branch/source leakage | ratio 0/0; depth variation not tilt-specific | PR07-002 `Δ_F=L F`, `L·1=0` | report + zero-branch note | finite contrast; rank gate for attribution | ✅ |
| K1 missing E2E | ideal synfast null omits pipeline systematics | PR08-001 NERSC E2E summary | ticket `PR08-001` | global rank p-value + matched manifest | ⛔ `BLOCKED_MISSING_PR4_E2E_ACCESS` |
| K5 conditional covariance | fixed σ\*/offsets + self-injection under-cover | PR08-002 hierarchical + PR08-003 mocks | `obsstat/bulkflow_mle.py`; `pr07_k5_*.json` | component/amplitude coverage + bias | ✅ mechanics; ⛔ mocks |
| K6 missing field realizations | cell bootstrap can't propagate reconstruction covariance | PR08-004 affine fit per realization | `obsstat/affine_flow.py`; ticket `PR08-004` | realization-conditioned posterior or no-go | ⛔ `BLOCKED_MISSING_FIELD_REALIZATIONS` |
| potential-flow curl suppression | vorticity structurally removed | PR07-006/PR08-004 structural non-identifiability | K6 curl-suppression gate | physical-vorticity claim stays blocked | ✅ (no-go demonstrated) |
| package import path | Makefile didn't import canonical modules | PR07-005 PYTHONPATH + interpreter fallback | `make pr04-gates pr07-gates` | clean checkout passes | ✅ |
| missing forbidden-dependency tool | old-Rust science could leak | PR07-005 required CI check | `make pr04-forbidden-deps` | zero forbidden imports/tokens | ✅ |
| low-ℓ solver absent | family transfer/source likelihood has no native owner | PR10 separate programme | solver gate ledger | exact FLRW + transfer comparator | 🧭 |
