# K5/CF4 identified-interval card -- v8-update extension

Frozen v7 base: `docs/generated/k5_cf4_identified_interval_card.json` (sha256 `5fa4d8456182454a...`)

## Teff fingerprint row (deterministic, one boost -> two channels)

| quantity | value |
| --- | --- |
| beta_CF4 (rapidity) | 1.136540933e-03 |
| s = tanh(beta) | 1.136540444e-03 |
| (3/2) s^2 (R3 deviation) | 1.937586e-06 |
| (5/2) s^2 (R5 deviation) | 3.229310e-06 |
| MES dipole ceiling R3 | 2.282653e-06 (= 1783323/781250000000) |
| MES dipole ceiling R5 | 3.804422e-06 (= 594441/156250000000) |
| fingerprint below ceiling | True |

NOT a measurement; derived from the unification seal. Statistical coverage/calibration ran at display mixings only (egs3.teff_statistical).

## Omega_k status

- PLUGIN/BLOCKED (unchanged); certified (measured_response_seal); leading-EGS-order no-channel
- external-prior branch: DOCUMENTED NULL -- no published direct Omega_k^aniso upper limit exists; Bianchi VII_h analyses marginalize Omega_K as a prior; fabricating a ceiling is forbidden
- survey: `docs/research_program/egs3/external_anisotropic_curvature_prior_survey.md`

## Registered-external model-conditional cross-checks

(omega/H)_0 < 5.2e-11 (Saadeh 2016) / < 7.6e-10 (Planck 2015 XVIII); (sigma_T,reg/H)_0 < 1.0e-6 (Saadeh 2016). Bianchi-VII_h-conditional; cross-checks only; no observational claim enabled.

`observational_claim_allowed = False`
