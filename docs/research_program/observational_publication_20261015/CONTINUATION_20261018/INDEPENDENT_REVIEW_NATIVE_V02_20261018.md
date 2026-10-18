# Fresh native review: V02 finite processing response

Requested reviewer `gpt-6-astra/xhigh`; independently observed runtime `UNKNOWN`.
Fresh bounded context, read-only, separate from implementation. This is one
review with one targeted repair closeout, not a sequence of new admission gates.

## Initial review and concrete repair

Verdict: **PASS_SCOPED_FINITE_CENTRE_COUNTERFACTUAL**; original V02 incomplete
pending a **locally executable** native-child processing extension. Initial
result SHA256 `8230c16f2a763d85dd7b26f50ead7a6adee863b5f01057ba61f5f44250e26fd8`;
receipt `6c1d41722d3728262da9ec6ef5215ca0b513343ca7dd859c16051d4eede572d9`.

P1 finding for original acceptance: `V02_EXECUTION_20261018/run_v02.py:77–81,96`
uses RING64-centre synthesis, whereas the original producer at Git object
`c2889730d2b5e5b778951f15e8f09afd55bed4e3`,
`scripts/run_htt_planck_multisplit_spin_20261015.py:79–81`, averages valid masked
NESTED2048 children before coarse OLS. Exact support and the centre-based leakage
matrix do not establish operator equality. The candidate discloses this; it is
NOT_RUN, not an external-input blocker. No correctness blocker was found for the
explicit centre counterfactual itself.

Independent checks: all fourteen receipt hashes; exact original retained vector;
actual FITS INT_BEAM ell0–16; independent SVD response maximum difference
`1.11e-15`; historical leakage delta `3.608e-16`; FWL residualized-SVD/Jacobian
delta `3.411e-13` microK/beta; closed-form z-generator relative error `9.013e-11`;
photon four-vector Lorentz direction error `2.22e-16` and exact Doppler agreement;
all saved experiment norms/residual algebra and singular values reproduced.
Figure labels match the diagnostic scope. Author and parent each ran eight
focused tests, PASS. Reviewer reused those executions and made the independent
checks above, without repeating the native source scan or completed experiment.
Author's authoritative runtime is `440.01840044592973` seconds.

Reviewer-authorized bounded repair, preserving every original centre-package byte:

1. Single writer only in `V02_EXECUTION_20261018/NATIVE_CHILD_EXTENSION/`.
   Same source SHA900e6c6f, actual INT_BEAM once, original support T26846/hash
   `98c90cbd186aceed02f6692ef83685b44d0f7f22569f218ea2936dcfafcedfbf`.
2. Reproduce the original TMASK intersection, native source-value validity and
   masked 1024-child means, with original coverage>=.995. Inspect actual source
   validity once or reuse an exact validity cache; do not refit the source.
3. Use `d_native(beta)=A_native B_INT [P16 U_beta s-s]` and apply the increment to
   `a_fit`. Report `A_native B_INT s-a_fit` separately, never force it to zero.
4. Six projected fields: baseline, three analytic local columns, generic
   beta=.00123*(1,2,3)/sqrt14 and half-beta finite increments. Retain source ell2..5,
   output ell16, quadrature/cutoff diagnostics, geometric rank and unknown sectors.
5. Direct-real-harmonic/native-synthesis sample controls, explicit masked-child
   sums, fixed support, zero increment<=1e-9 microK, FWL/joint<=1e-8 microK/beta.
   One native map at a time or bounded chunks, two threads, no dense native design.
6. Pointwise residual/error vectors and finite-comparison envelopes only; no
   physical covariance or certified infinite Lorentz-tail claim. Preserve failures.

If this repair passes, the reviewer permits original finite V02 completion as
`PASS_SCOPED_V02_SOURCE_DEFINED_FINITE_NATIVE_PROCESSING`. Do not add the later
physical-null qualification as a new V02 gate. Unknown physical source sectors,
frequency/bandpass and component-separation/calibration responses remain limits
on later physical interpretation, not automatic blockers to this finite task.
Primary reference: [Planck XXVII, sections 2 and 6](https://arxiv.org/html/1303.5087v3).

Targeted implementation dispatched to a separate requested `gpt-6.1-sol/high`
worker, observed runtime `UNKNOWN`. At this initial review the repair closeout was
pending and V02 was not closed. The following final closeout supersedes that state.

## Single targeted repair closeout

**PASS_SCOPED_V02_SOURCE_DEFINED_FINITE_NATIVE_PROCESSING**. No blocking finding
remains. The same independent reviewer permits original V02 `completed_scoped`
under its unchanged acceptance, for the declared finite source perturbation
through the actual native-child operator. No broader scientific admission.

- Native result SHA256 `a5c0fca1e7f979bba8e17f30caece0d98dd7c253a812906d61f05f9dddad1a5b`.
- Native receipt SHA256 `03f46eff8a841b2d6a87ad4e3e3a8a2a5ef2731e8fade075306cc12d2b9f012c`.
- All twelve extension receipt files, fourteen original receipt files and the
  preserved-centre identity snapshot match. Original centre bytes are unchanged.
- Packed actual source validity, counts and T26846 support match exactly;
  minimum selected actual coverage is .9951171875.
- Independent direct-real-harmonic averages over every child of four control
  parents, including one with 1020 valid children, agree with six saved fields
  within `1.421e-13` microK. Independent SVD/Jacobian delta `1.279e-13` and
  FWL delta `2.096e-13` microK/beta. Independent analytic z-generator mode delta
  `9.948e-14` microK/beta.
- Native baseline mismatch `0.02549089788694` microK is explicitly retained.
  Both finite increments/residuals, centre differences, singular values and
  finite-comparison envelopes reproduce from saved arrays. PNG/PDF agree.
- Author and parent each ran four focused extension tests, PASS. Reviewer reused
  the execution and independently checked arrays/identities/child means without
  rerunning the six-field native experiment (62.05635194503702s).

The original valid-source averaging rule and once-only beam are correct. Spin0
and additional-smoothing arguments agree with the [official healpy API](https://healpy.readthedocs.io/en/latest/generated/healpy.sphtfunc.alm2map.html).
The addition-theorem finite-comparison envelope is mathematically consistent,
not an infinite-tail certificate. Physical upstream response, physical covariance,
identifiable physical rank and global-history response remain UNKNOWN. They do
not add a new physical-null gate to finite V02. No further repair required.
