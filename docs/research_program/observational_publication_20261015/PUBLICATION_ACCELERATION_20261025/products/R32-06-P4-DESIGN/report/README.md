# R32-06 finite response-design report candidate

Owner: HTT conditional response-design research. Task `R32-06-P4-DESIGN`, attempt 1, packet `2a504af3ea3221e2f1ecf03938a5b042296403afb7c07384eafef5847ec8c459`, input `sha256:263f8707d940df778ea5a6eeef1023cd7784fe5dac5ebe1be2795f0c6e4de450`. Builder `/root/r35_p4_prescribed_numeric_build`, requested `gpt-6-sol/high`, observed runtime `UNKNOWN`. Source author `/root/rc_2a504af3ea3221e2`. Transfer source `none`. Claim status: finite `DERIVED/CONDITIONAL`, candidate only. Independent review and original V03 physical history validation remain pending.

The deterministic consumer reads the literal contract and verifies all nine retained source hashes, plus the one-string inverse notation transition, before producing numerical arrays. It uses no native solver, survey catalogue or stochastic sampling law. `matrices.json` contains physical `J,N,W,P,L,A` and projected physical matrices for all four nominal designs; `spectra.json` contains both spectra, complete 18-coordinate right bases, projectors and identified-combination rows. Grids, witnesses, perturbation fixture, column scales and checks have separate compact JSON files. All JSON files use standard finite values or `null` with an explicit status for unbounded gains.

From the repository root:

```sh
python3 -B docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/products/R32-06-P4-DESIGN/report/reproduce.py
```

From any working directory, the absolute invocation below resolves its inputs and outputs from the script path. Substitute this checkout path if the checkout is relocated:

```sh
python3 -B /home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/products/R32-06-P4-DESIGN/report/reproduce.py
```

From this report directory, convert the complete released English manuscript and compile its RevTeX PDF:

```sh
python3 -B build_tex.py
latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error main.tex
python3 -B reproduce.py --finalize
```

`build_tex.py` calls local Pandoc with `markdown+tex_math_single_backslash+raw_tex`. The TeX has all 27 numbered equations, four propositions, complete nominal spectra, column-scale appendix and three vector figures. PDF compilation uses the local RevTeX 4.2 class. The original science manuscript is read-only. `RESULT.json` embeds a SHA-256 manifest of candidate files; the candidate identity is the SHA-256 of its canonical JSON serialization. `RESULT.json` does not hash itself. Raw first failures and final stdout/stderr are retained under `raw/`; the first two numerical/TeX build failures were mechanical and their corrections are present in the consumer and converter. The Matplotlib warning about unavailable Axes3D does not affect these 2D figures.

Physical `x_C`, `Q`, `F`, `Pi` and `G_F` are `NOT_EVALUABLE_WITH_THIS_RESPONSE`; matter vorticity is `NOT_MEASURED`. Hypothetical additions are explicitly calibrated conditional sensitivity functionals. They do not meet original V03 or original 42-node scientific acceptance.
