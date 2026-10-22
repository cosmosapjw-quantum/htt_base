# A22-06 — selected distance-cohort likelihood and completion sets

Owner HTT, C0 DERIVED_CONDITIONAL/DIAGNOSTIC_ONLY, transfer none. New inputs/model:
the628observed-target outcome×distance-availability law, actual274released moduli,
and a separately selected6dFGSv release. Next consumers H02/S02/S04/K04.
Independent review found two issues; targeted closeout pending. All original physical acceptances remain open.

At fixed shared nuisance nu, the target-conditioned marked likelihood is
p(o,r,y|W,T=1)=integral K_or(y|X,W,nu)s(X,W,nu)f(X|W,nu)dX / A_T(W),
where A_T=integral s*f. After marginalizing shared nuisance/correlated velocities,
use the joint ratio integral p(X,nu)S(X,nu)K(data|X,nu) / integral p(X,nu)S(X,nu).
A product of individual denominators needs an additional factorization assumption.
The full5460parent targeting history and its normalizer are not known.

The defined extension q_T(o,r,dy)=pi_or F_or(dy), sum pi=1, would contribute
pi_o0 for missing distances and pi_o1 f_o1(y) for observed distances. Its distance
factors are not implemented or evaluated here. The executed likelihood is the
mark-only multinomial sum n_or log(pi_or), with working MLE pi=n/628. It retains
every nondetection/confusion row. The separate completion calculation pools
released DMbest values across observed marks; it does not evaluate F_or.
No independence-based standard error, distance likelihood or p-value is attached.

| Outcome | DM present | DM missing |
|---|---:|---:|
| accepted |269|116|
| other quality |1|21|
| confused |3|26|
| nondetection |1|191|

The354missing distances have mass.5636942675 in this fixed628-target cohort.
PGC1095542's invalid Vhel affects an existing prediction-domain mass1/628; it is
still a retained nondetection. Physical Q unknown mass remains1, outer[0,1].

For the strict released-value event DMbest−delta>tau, with k observed events,
the sharp uniform finite-cohort completion interval is[k/628,(k+354)/628].
It is attained by completing all missing events to0or1. Integer centimagnitudes
preserve exact strict ties. Full calibration-shift staircases are emitted; a finite
physical delta bound is UNKNOWN. At delta0, tau32/34/36/38mag give k271/228/9/0.
For tau34 the interval is[.3630573248,.9267515924]. This is a released-value
completion set, without a physical-Pi or true-distance coverage interpretation.

[Dupuy §3.3](https://arxiv.org/html/2101.01515) describes changing proposal pools,
cuts, visual screening and adaptive observations. Current table2 has22retained
inclinations<=45deg and2missing, despite the intended final>45deg language.
All628rows are preserved with DESIGN_VINTAGE_OR_MEASUREMENT_UNRESOLVED. Current
inclinations cannot reconstruct the exact historical cut variables. Outcome
codes e_W50=100/500 are confusion/nondetection, not Gaussian error bars.

## New separately selected 6dFGSv source

The official [PV catalogue](https://cdsarc.cds.unistra.fr/ftp/J/MNRAS/445/2677/ReadMe)
and [FP catalogue](https://cdsarc.cds.unistra.fr/ftp/J/MNRAS/443/1231/ReadMe) were
downloaded anonymously as gzip tables plus ReadMes,983630bytes total. CRC, hash,
schema, width, units/frame and exact names were checked. All8885PV rows join the
11102-row FP release. Js=1 has8896rows;12PV rows haveJs=0 and23Js=1 rows are absent
from PV. The actual PV release membership is preserved. Group-unassigned6219
versus group-assigned2666 rows and all seven Jcode patterns remain visible.
The .dat404path was replaced with the official .dat.gz path after source inspection.

For a raw Gaussian FP model x=(r,s,i), selection on u=2r+i and s has a bivariate
Gaussian tail normalizer. [Dam Eq55–59](https://arxiv.org/html/2002.05898)
motivates the denominator; the deterministic quadrature helper verifies independent
zero cuts f=1/4, unbounded cuts f=1 and one zero cut f=1/2. It rejects non-PD and
numerically unresolved tails without a probability floor. This helper was not
multiplied into already corrected released eta. No CF4/TF/6dF duplicate source was
counted as an independent distance measurement; no latent PV covariance was added.

The first independent review reproduced an inaccurate small-tail value:
independent cuts [10,-30] returned2.618362323602611e-23 instead of
7.61985302416047e-24 (factor3.436237307); absolute quadrature tolerances were
insufficient. The repair uses exact independent/one-cut tails, mode-scaled
relative quadrature for correlated tails and a swapped-cut agreement check.
Underflow/unresolved relative accuracy remains an explicit failure. No tolerance
was relaxed. The report was narrowed to the executed mark likelihood.

Five narrow tests passed; actual-data command exit0, exact8cell counts and12/23
membership discrepancies reproduced. No97LP,2048draw or D02 regression rerun.
Source hashes and exact threshold results: [RESULT.json](RESULT.json).
[Figure](SELECTION.png) shows mark counts, completion curves and membership gaps.

```bash
OPENBLAS_NUM_THREADS=1 .venv/bin/python -m pytest -q docs/research_program/observational_publication_20261015/ADVERSARIAL_AUDIT_20261022/continuation/selection_model/test_cohort.py
OPENBLAS_NUM_THREADS=1 .venv/bin/python docs/research_program/observational_publication_20261015/ADVERSARIAL_AUDIT_20261022/continuation/selection_model/cohort.py
```

Needed for physical inference: parent selection variables/vintages, observation
history/RFI/confusion kernel, joint measurement/calibration/PV law, missing-distance
assumptions or data, and contributor overlap. Requested theory Astra/xhigh and
parent Sol/high; observed UNKNOWN. None of these missing inputs is replaced by
628/5460, e_DMbest hard bounds or transferred6dF zero-point errors.
