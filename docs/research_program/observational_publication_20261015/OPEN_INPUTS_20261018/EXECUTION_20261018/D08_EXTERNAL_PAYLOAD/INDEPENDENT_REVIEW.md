# D08 independent review and targeted closeout — 2026-10-18

Fresh read-only `/root/open_d05_d08_review`, requested Astra/xhigh,
observed UNKNOWN. Final PASS_DIAGNOSTIC_ONLY after one concrete P2 correction.
No solver, upstream execution, new checkout, nested agents or numerical rerun.

Initial finding: report/result/generator wrongly called parameter/test binding
absent. Pinned official doc/index.html Testing lines86–94 explicitly declares
param.par/test-map agreement conditional on unit configuration. The one targeted
repair records upstream-declared binding separately from NOT_RUN execution
verification and cites that source. Absolute frame UNKNOWN, polarization absent,
physical atlas false, B02 HOLD remain unchanged. Four closeout tests PASS0.91s;
parent affected-suite4PASS2.93s. No remaining blocking finding.

Independent numerical evidence: actual FITS blob IDs equal official pinned tree;
associated-Legendre design reproduces169 coefficients within1.99e-20,
rank169, condition1.0006571686, residual fraction0.13433861449.
Unit scale2724.999989152853, fixed2725 residual5.6100806e-8. Both plots and
coefficient archive agree. Reversing only provenance edits reconstructs the
original code/result hashes; numerical fields unchanged. Inputs, coefficients,
plots, acquisition log/manifest retain prior identities.

Final SHA256:

```
legacy_intake.py c6f7215999babb141d1754fce60e46c6fee65730ffd39e8eb9cbd53738474ad7
RESULT.json 67f6a62891abbc437cc645eed2809267633db58cbc2cdaba52046be9e91ef613
REPORT_KO.md 53a159892f2fa2b4ed9a0b5b392fe34ffb38ad30fd2c8720c83a4c48837b476f
test_legacy_intake.py b481f8fb7e6b921a7f299948387c982eae50d2dddbff80ce58245334a27490f5
```

This is a source-bound external legacy T fixture diagnostic, not a polarized
atlas, native transfer, absolute-frame match, family identification or inference.
