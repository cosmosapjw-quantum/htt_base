# Next-method contracts: fresh blind review and targeted correction

**HOST-ASSEMBLED SUMMARY**, transcribed from the actual findings of independent reviewer `/root/r25_blind_next_contracts`. The reviewer did not write this file. Requested/transport-selected `gpt-6-astra/xhigh`; observed runtime `UNKNOWN`. The reviewer read no author summaries or other reviews. Scope: prospective contracts and limited source/header checks, not executed science, physical acceptance or final plan admission. Repository skills were not used as audit authority.

The frequency-tensor draft required correction before task append. A singular ratio greater than1e-8 alone cannot justify rejecting an exact relation. With `a=1e-5 K_CMB`, orthonormal u/v and p/q, `AE=[a*u,a*(u+1e-7*v)]`, `AB=[a*p,a*q]`, exact target anchor2, an E error `5e-13*v` shifts fitted coefficients `(0,1)` to `(-.5,1.5)` and creates approximately `7.07e-6 K_CMB` B residual. Ordinary fixed-tolerance controls can pass this case.

The corrected draft requires certified spectral/Euclidean error bounds `eps_AE,eps_yE,eps_AB,eps_yB` and a certified lower bound `s<=sigma_min(AE)`. If `s<=eps_AE`, the relation is unresolved. Otherwise the frozen coefficient/error bounds are

```text
C=(||yE||+eps_yE)/(s-eps_AE)
Delta_c=(eps_yE+eps_AE*C+upperbound||yE-AE*ctilde||)/s
tau_B=eps_yB+eps_AB*C+upperbound||AB||*Delta_c
      + residual-evaluation roundoff upper bound.
```

A certified B residual lower bound must exceed this necessary bound before rejecting the exact delivered-tensor relation. C/Delta_c are dimensionless; matrix, vector and singular-value error quantities have K_CMB units. Implementation agreement does not certify either error. Without deterministic certification the required output is descriptive full residuals and **NUMERICALLY_UNRESOLVED**, with no exact-relation rejection or physical component-count inference.

A second correction freezes canonical-to-raw STF input conversion: `Re=c_re/sqrt2`, `Im=-c_im/sqrt2`, with m0 unchanged. The independent raw `a21=i` fixture must give `Qyz=+sqrt(15/(8*pi))`. Passing canonical coordinates directly to the raw decoder instead gives `-sqrt(15/(4*pi))`. A round-trip-only control cannot expose a shared convention error.

The reviewer actually obtained HTTP206 first28800bytes for all seven frequency products. Reviewed totals, Q/U columns, Galactic/NESTED and NSIDE metadata matched the contract. LFI headers use `K_CMB` and `POLCONV=COSMO`; HFI uses `Kcmb` and `POLCCONV=COSMO`. These are the same thermodynamic units: normalize spelling while preserving raw headers and keywords. Full products were neither downloaded nor qualified by these partial-header checks.

The other three reviewed contract identities—distance prefix `77439c5`, SMICA prefix `69ad48`, auxiliary full identity `2dfa96e815659ef53f03290f88afb3a2bd213b505856cbacd7adeeb127b2520f`—had no blocking mathematical defect found in this contract review. Under the fixed working law, the Schur conditional construction, composite-null maximum, sigma/RSS treatment and arithmetic mixture/average were sound. The SMICA archive/member identities matched; the four nonzero-weight rows had rank24 and nullity144, with application restricted to matched preprocessed inputs. The auxiliary reviewer verified the actual628/274cells, PGCs, quality scope and integer gap2547. These observations do not qualify survey selection, physical foreground/noise laws, or original scientific acceptance. Those three contracts were not modified by this correction.

Primary references used by the reviewer: [Universal Inference](https://arxiv.org/abs/1912.11436), [Planck IV §3.1](https://arxiv.org/html/1807.06208#S3.SS1), [Planck III §3.1.4](https://arxiv.org/html/1807.06207#S3.SS1.SSS4), and the [IRSA bandpass-corrected product matrix](https://irsa.ipac.caltech.edu/data/Planck/release_3/all-sky-maps/matrix_bpasscorr.html).

Exact predecessor frequency contracts and identities were preserved under `.agent-harness/runtime/r23-continuous/r25/next_contracts_first_candidate/` before edits. Acquisition predecessor SHA256: `4421ca3aba2ef4b307c974a496bea653dd3ef365ccdc402fceaa11969eb7405c`; tensor predecessor: `7c7716779a75dafb649179729512fd92b5583bbf035924c639e339794130947b`; frontier predecessor: `3525cd6a27ce0c4672e5be2c79940449dcd1248b4fe32aff61f59d0a3cbb8701`.

This host assembly performed JSON parsing, frontier hash-binding and targeted contract-diff checks only. No scientific execution, full-product acquisition, controller append/state change, or plan/final scientific PASS is asserted. Original17/42, alternate18/42, physical HOLD, historical48, one-use/ultra accounting and R9 UNKNOWN remain unchanged. Actual acquisition and any numerical product still require dispatch, raw evidence and separate independent review.
