# P6 finite optical inverse candidate

Open `main.pdf` (12 pages). The source is `main.tex`, generated literally from the scientific author's `../science/MANUSCRIPT.md` by `build_source.py`; references are in `references.tex`. Equation (26) is wrapped for width. The approved prose clarification distinguishes the dimensionless comparator vorticity contribution W² from the Section 3 whitening matrix W.

From the repository root, regenerate the retained-statistic illustration with:

```sh
.venv/bin/python docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/products/R32-05-P6-OPTICAL/report/reproduce.py
```

From this directory, build and audit:

```sh
python build_source.py
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
pdftotext -layout main.pdf raw/main.txt
pdfinfo main.pdf > raw/pdfinfo.txt
python validate_candidate.py
```

The recorded execution consumed retained small files once and passed 61 focused checks. `generated/retained_tensor_region.json` retains the complete dimensionless five-vector, 3×3 STF tensor, 5×5 adopted working matrix, basis, set parameters, and all diagnostic statuses. `generated/figure_data.json` retains all 301 frontier grid values (including the exact crossing), all 721 projection angles, and the deterministic supports. Tables have both CSV and TeX sources. All radii are assumed: the zero-radius case is an exact-response limit. In the frontier, solid curves are upper endpoints and dashed curves are lower endpoints. No physical Hubble rate is inserted.

The working matrix is an illustrative deterministic shape with no assigned confidence level. A same-event, same-congruence, same-frame response qualification and joint error region remain absent; physical shear detection, coverage and significance are not asserted. x has an apparent tensor component and a conditional physical image; x_C is incomplete, Q needs a positive policy denominator, and F/Pi/G_F lack their required measure/law/depth functional. No raw catalogue, quadrature, native solver or ODE is executed. No historical acceptance is changed.

`RESULT.json` seals source/output identities for independent review. It is candidate-only: both acceptance fields are false, qualified products are empty, and `optical_inverse_note` is proposed. `raw/` preserves actual stdout/stderr and the first read-only inventory failure (the output directory did not yet exist). Independent review and publication remain pending.
