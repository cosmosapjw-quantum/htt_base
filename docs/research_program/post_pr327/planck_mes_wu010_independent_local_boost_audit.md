# PMG-WU-010 independent local-boost audit

## Authority and scope

- inspected PR: `#442`
- inspected head: `491a343385e559910a243ab9a949dca7ba83732d`
- parent PR #441 head: `04680e99d56b9974fe1120854370af1fb94fb1d6`
- conventions: metric `(-,+,+,+)`, outward sky direction `n=-e`, dimensionless `beta=v/c`, thermodynamic blackbody temperature with Doppler weight `d=1`

This audit is independent formula reproduction plus exact-head repository-test readback. It is not observed-data execution, a Planck absolute-temperature admission, an empirical velocity fit, a global matter-frame tilt calculation, a Bianchi-family attribution, or a replay of the unavailable P01--P27 formal dossier.

## Independent exact checks

Wolfram exact algebra verified

1. the cancellation-safe identity
   `(gamma-1)/beta^2 = gamma^2/(gamma+1)` for `0<beta<1`;
2. `B_Q^T G_3 B_Q = 3 M_Q` for an exact rational generic STF2 probe;
3. the response-image projector has rank three, is idempotent, and is self-adjoint in the registered STF3 Frobenius metric.

## Independent numerical checks

A deterministic `80 x 160` Gauss--Legendre/uniform-azimuth sphere rule gave

- finite-to-linear correct-convention residual slope: `2.000002992637`;
- line-of-sight sign-mutation residual slope: `0.999998309811`;
- first-order harmonic-power fraction outside `ell=1,3`: `1.419666276311e-31`;
- maximum full-sky `L2` relative drift over `|beta|={1e-3,1e-2,0.1,0.5}`: `5.097042758756e-16`.

The exact-code companion test `htt/test_wu010_audit_closure.py` binds two load-bearing properties to the repository runtime:

1. full-sky `L2` preservation of the Doppler-weight-one pullback;
2. exact first-order `ell=1,3` support and agreement with the registered harmonic--STF maps.

## Literature cross-check

The implementation boundary agrees with the aberration-kernel literature: Doppler weight one has a unitary full-sky boost operator, while frequency-dependent observables and cut-sky processing require their own response treatment. Relevant primary sources include Dai & Chluba (2014), Yasini & Pierpaoli (2017), and the later boost-operator formulation of Chluba & Ravenni (2025).

## Audit disposition

`PASS_WITH_TYPED_LIMITATIONS_PENDING_FRESH_REVIEW`

No scientific claim is promoted. The remaining WU-010 gates are exact-head execution of the new characterization test, fresh independent read-only review, and synchronization of the PR/Confluence/research-dashboard authority records. The next physical bridge remains blocked by absolute-temperature, cut-sky transfer, nuisance, and matched-null requirements.
