# A22-08 — added QU windows and high-band leakage in a finite operator

Owner obsstat; C0 PROCESSED_OPERATOR_SENSITIVITY, transfer none; base9f0beb69.
New operator: secondary Galactic latitude windows on bandlimited processed Q/U.
[Specification](EXPERIMENT.json) was frozen before these new scores, after A22-07
scores had been seen. This is a declared follow-on diagnostic, not a blind test.
Next consumer L03/L04 operator qualification; matched physical-null gate remains HOLD.
Independent review pending.

For each of five PR3 full/HM/OE products and L32/64/128, synthesize Q/U from BOTH
cached E/B pseudoalms onto RING NSIDE64 using spin2,lmax=mmax=L. Multiply both by
the same pixel-centre W=1(|b|>20deg) or W=1(|b|>30deg), then analyze spin2 with
lmax=mmax4 and score E ell2..4 with the frozen J234/top-axis statistic. The original
common mask and delivered beam are already in the inputs. Neither is applied a
second time; there is no pixel-window correction/deconvolution. This finite
operator is not a physical new sky cut before the original processing.

Packing is explicit through Alm.getidx for each lmax, with complete m. Direct
prefix slicing of packed arrays would be incorrect. Both E/B arrays, m0 reality,
zero spin2 ell0/1, size/finiteness, source/metadata hashes and same-sky identities
are checked. No raw Planck map processing or old split-ratio campaign is repeated.

The symmetric windows are RING throughout; their exact support has32512/24320of
49152pixels. First narrow validation produced2FAIL: floating-point latitude
comparison misclassified antipodal pixel centres on the mathematical30deg boundary.
Astra approved a bounded repair preserving the strict original cut: hp.pix2ring
integer centres, with30deg predicate4*abs(2N-ring)>3N and20deg predicate
2*abs(2N-ring)>3N*sin20deg. Boundary rings80/176 are excluded. No tolerance or sky
cut was relaxed. Both affected tests then passed in13.41s before observed scores.

Controls use physical polarization parity E_lm→(-1)^ell E_lm and
B_lm→(-1)^(ell+1) B_lm. Scalar B parity is a negative control. Antipodal symmetry
makes parity a valid identity here; arbitrary input rotation alone is not invariant
under this fixed Galactic window. Further controls cover E/B decomposition,
linearity, exact repacking, added-band closure, and pure high-E/pure-B modes.

## Actual output and limits

All30primary cells and15unwindowed comparators produced finite features/defined
axes. J and alignment are emitted separately along with powers, axis gaps and
raw processed coefficients (Git outside). Joint descriptive maximum=.9944273827
at hm1/L32/20deg; the largest |J|=.0817159503 at hm2/L128/20deg, signed negative.
The combined max is alignment-determined and parity even. It is unscaled, not a
balanced invariant test and not a p-value. Thirty cells are one observed sky.

For the full product:

| cutoff | extra window | signed J234 | alignment23 |
|---|---|---:|---:|
|L32|none|-.01500822|.67953740|
|L32|20deg|-.00873799|.79643672|
|L32|30deg|-.00898740|.04127932|
|L128|none|-.01497157|.67946942|
|L128|20deg|-.00920142|.79473989|
|L128|30deg|-.00814971|.04692717|

The original A22-07 L32 alignment was .67950074; even the unwindowed finite-grid
roundtrip changes it slightly. These response differences qualify the explicit
finite operators. They do not bound the unknown foreground/noise or all physical
high modes. The strong latitude-window dependence is preserved.

Maximum normalized E/B-decomposition residual4.47e-17, physical-parity residual
3.94e-17 and repacked-band closure residual3.47e-17 are below the frozen1e-10
arithmetic tolerance. Norm denominators use sums of operands/inputs so cancellation
does not inflate an error. Unwindowed low-degree roundtrip defects are
2.49e-5..4.89e-5 relative to input coefficient norm, explicitly nonzero; they are
finite HEALPix quadrature errors, not failures of an exact inverse assertion.
Added-band responses have norms5.55e-9..1.07e-8K_CMB; the corresponding
(T_window−T_unwindowed)added response is also retained. This is the changed
operator's actual higher-band leakage, unlike identical low-ell prefix comparison.

[RESULT.json](RESULT.json) seals the new outside-Git25677-byte coefficient cache,
all45feature rows and controls. [Figure](OPERATOR.png) displays the two statistics
for declared operators. No calibrated null distribution, uncertainty band, MC
interval, cosmic E/B interpretation, Bianchi identification or physical L03/B02
completion follows. The existing matched total-field ensemble requirement is open.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q docs/research_program/observational_publication_20261015/ADVERSARIAL_AUDIT_20261022/continuation/cmb_pilot/test_operator.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python docs/research_program/observational_publication_20261015/ADVERSARIAL_AUDIT_20261022/continuation/cmb_pilot/operator.py
```

Requested parent Sol/high and framing/reviewer Astra/xhigh; observed UNKNOWN.
The finite-operator framing and repair approver is separate from final reviewer.
