# D03 independent decision — 2026-10-18

Fresh bounded read-only task on `/root/open_d02_review`, requested Astra/xhigh,
observed runtime UNKNOWN. Scoped PASS for host associations and conditional
covariance diagnostics; no concrete repair required. Original
H02/S02/H04/S04/K04 remain HOLD. No previous large CF4 fit rerun or nested agents.

All 16 manifest entries and input seals match. Independently reconstructed every
one of 1701 associations using Astropy, including all654 matched rows and all
unresolved reasons/PGC/groups. Counterpart moduli/errors match the raw fields.
All nine GLS fits reproduce using the full combined nuisance/response design:
maximum response difference2.32e-16 mag, weighted normal-equation residual4.44e-12.
Ranks16/18,16/18,17/19 and response rank4 reproduce. Covariance contraction,
shared latent counterpart errors, raw symmetric-part handling are consistent.
11 focused tests PASS in1.944s, no skips. PNG inspected and scope consistent.

Unknown crosscovariance, cross-key calibration, exact individual SN ancestry and
directional selection stay unknown. The chosen Cholesky-order sensitivity family
does not establish bounds on all missing covariance or calibrated significance.

Checked identities (aggregate and manifest-file SHA identify different objects):

```
candidate aggregate c326fc79b4cfd255d4655cb47b27a4b399403179c3342ac30ae7113c80dcc388
CANDIDATE.json 67a4103dbf2ea5c4828d7c3c3409058b13e034d4cae87f9599188efa0bc15cc5
d03.py efafc801d31329441804094b00d63f688c6060ce0a6e3a425ac0f7074af41e54
D03_RESULT.json c711a82bf5dbe95fd7bd847fea2d7b7d8f30e18463d9113de406ae16dbbf7296
```

Review at descendant HEAD4a6b26bff0eadae8243054c2eb99add2b6bdc34f; frozen
candidate unchanged. Parent may publish this diagnostic increment and advance
its consumers; this decision is not physical admission.
