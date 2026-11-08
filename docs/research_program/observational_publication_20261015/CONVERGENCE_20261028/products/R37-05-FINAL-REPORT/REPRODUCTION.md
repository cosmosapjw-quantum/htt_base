# Reproduction Guide: R37 Final Scientific Convergence Release

This document specifies the exact instructions, environment requirements, commands, and expected outputs to reproduce the findings of the **Finite Scientific Convergence Release (`R37-05-FINAL-REPORT`)** and its constituent research units.

---

## 1. Environment & Prerequisites

### Hardware & Operating System
- OS: Linux x86_64 (tested on Ubuntu 24.04 LTS / Linux 6.8.0)
- Python: 3.12.3 in virtual environment `.venv`
- Disk Mount: `/mnt/extdrive` mounted with read access to open data and cached simulation files.
- LaTeX Toolchain: `latexmk`, `pdflatex`, `xelatex`, `bibtex`

### Environment Activation
```bash
cd /home/cosmosapjw/Dropbox/bianchi/htt_base
source .venv/bin/activate
export PYTHONPATH=.
```

---

## 2. Step-by-Step Reproduction by Research Unit

### Unit R36-06: Planck PR4 Commander Low-Ell Polarization Morphology
- **Input Data**: Observed map and 100 MC processed simulations in `/mnt/extdrive/workdir/htt_open_data/r36_pr4_actual/analysis/`
- **Execution**:
  ```bash
  .venv/bin/python docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-06-PR4-MORPHOLOGY/aggregate_mc_morphology.py
  ```
- **Verification Tests**:
  ```bash
  .venv/bin/python -m pytest docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-06-PR4-MORPHOLOGY/test_pr4_commander_morphology.py -v
  .venv/bin/python -m pytest docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-06-PR4-MORPHOLOGY/test_pr4_observed_pilot.py -v
  ```
- **Outputs**:
  - `COMMANDER_MC100_AGGREGATE.json`
  - `null_distribution_histograms.pdf`
  - `null_distribution_histograms.png`
  - `RESULT.json` ($p(J_{234} \ge \mathrm{obs}) = 0.4356$, $p(\mathrm{align}_{23}^2 \ge \mathrm{obs}) = 0.2277$)

### Unit R37-01: Radiation Morphology & STF5 Shear Sensitivity
- **Directory**: `docs/research_program/observational_publication_20261015/CONVERGENCE_20261028/products/R37-01-RADIATION/`
- **Verification Tests**:
  ```bash
  .venv/bin/python -m pytest docs/research_program/observational_publication_20261015/CONVERGENCE_20261028/products/R37-01-RADIATION/test_radiation_response.py -v
  ```
- **Outputs**:
  - `radiation_response_spectrum.pdf`
  - `shear_support_vs_transport_budget.pdf`
  - `polarization_omission_bias.pdf` (bias norm $0.0085038 \le 0.0087824$)

### Unit R37-02: Kinematic Image & Gaia Astrometry
- **Directory**: `docs/research_program/observational_publication_20261015/CONVERGENCE_20261028/products/R37-02-KINEMATICS/`
- **Verification Tests**:
  ```bash
  .venv/bin/python -m pytest docs/research_program/observational_publication_20261015/CONVERGENCE_20261028/products/R37-02-KINEMATICS/test_kinematic_image.py -v
  ```
- **Outputs**:
  - `GLS_tensor_scalar_comparison.pdf`
  - `chirality_radius.pdf` (fixed-Q sign radius $\rho_{\mathrm{sign}} = 1/\sqrt{3} \approx 0.57735$)

### Unit R37-03: Directional Hubble & Opacity Cosmology
- **Directory**: `docs/research_program/observational_publication_20261015/CONVERGENCE_20261028/products/R37-03-HUBBLE/`
- **Verification Tests**:
  ```bash
  .venv/bin/python -m pytest docs/research_program/observational_publication_20261015/CONVERGENCE_20261028/products/R37-03-HUBBLE/test_hubble.py -v
  ```
- **Outputs**:
  - `local_H_region_vs_opacity.pdf` (apparent ratio $[0.9222, 1.1074]$)
  - `distance_transmission_identified_interval.pdf` ($D_L \in [1.58114, 3.0]$)

### Unit R37-04: Finite Geometry Compatibility
- **Directory**: `docs/research_program/observational_publication_20261015/CONVERGENCE_20261028/products/R37-04-CLASSIFICATION/`
- **Verification Tests**:
  ```bash
  .venv/bin/python -m pytest docs/research_program/observational_publication_20261015/CONVERGENCE_20261028/products/R37-04-CLASSIFICATION/test_classification.py -v
  ```
- **Outputs**:
  - `family_compatibility_vs_amplitude.pdf`
  - `adequacy_residual.pdf` (exclusive margin $M_{\mathrm{excl}} = +0.36258$)

### Unit R37-05: Final Convergence Report Compilation
- **Directory**: `docs/research_program/observational_publication_20261015/CONVERGENCE_20261028/products/R37-05-FINAL-REPORT/`
- **PDF Compilation**:
  ```bash
  cd docs/research_program/observational_publication_20261015/CONVERGENCE_20261028/products/R37-05-FINAL-REPORT/
  pdflatex -interaction=nonstopmode REPORT_FINAL.tex
  pdflatex -interaction=nonstopmode REPORT_FINAL.tex
  ```
- **Verification**:
  Confirm `REPORT_FINAL.pdf` is generated without errors and contains all embedded vector figures and tables.

---

## 3. DAG Validation & Progress Harness

```bash
python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml
python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml
```

Expected result: 208/273 completed (76.19%), unblocked executable next = 0, residual held obligations = 65 (fully cataloged in `RESIDUAL_OBLIGATIONS.json`).
