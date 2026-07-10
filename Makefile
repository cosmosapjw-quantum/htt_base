# PR04/PR07 research-program gate targets.
#
# Deterministic: thread counts are pinned to 1 so the theorem/property gates are
# reproducible across machines and CI jobs. The external gates are necessary but
# not sufficient; the canonical pytest suite remains the merge authority.
#
# PR07-005 (reproducible gate surface): PYTHONPATH spans repo root, repo/htt and
# repo/htt/htt so canonical modules import in a clean checkout; the interpreter
# falls back venv -> python3 -> python; the portable numerical gates are kept
# separate from the local-only Wolfram symbolic gate.

REPO     := $(CURDIR)
# Interpreter fallback: repo venv, then python3, then python.
PY       ?= $(shell [ -x "$(REPO)/venv/bin/python" ] && echo "$(REPO)/venv/bin/python" || command -v python3 || command -v python)
PYTHON   ?= python
GATEDIR  := $(REPO)/research_gates/pr04/tests
GATEDIR7 := $(REPO)/research_gates/pr07/tests
GATEDIRE := $(REPO)/research_gates/egs2/tests
GATEDIR3 := $(REPO)/research_gates/egs3/tests
THREADS  := OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
PYPATH   := PYTHONPATH=$(REPO):$(REPO)/htt:$(REPO)/htt/htt

.PHONY: pr04-gates pr07-gates egs2-gates egs3-gates paper-a-gates paper-b-gates \
        pr04-proofs pr04-forbidden-deps pr07-wolfram pr07-cove egs2-experiments \
        egs3-experiments egs3-wolfram egs3-seals egs3-sage egs3-lean v7-wolfram \
        v7-seals

## All 23 external PR04 theorem/property gates + symbolic proofs + dep scan.
pr04-gates: pr04-forbidden-deps
	$(THREADS) $(PYPATH) $(PY) -m unittest discover -s $(GATEDIR) -p 'test_pr04_*.py' -v
	$(MAKE) pr04-proofs

## PR07 portable repair gates (unit-safe stress, independent dynamics, PAPER-A).
pr07-gates: pr04-forbidden-deps
	$(THREADS) $(PYPATH) $(PY) -m unittest discover -s $(GATEDIR7) -p 'test_pr07_*.py' -v

## EGS2 extension gates (NT2-A1/A2 Fisher floor, NT2-B1 bracket, NT2-B2/B3, K1/K6 discharges).
egs2-gates:
	$(THREADS) $(PYPATH) $(PY) -m unittest discover -s $(GATEDIRE) -p 'test_egs2_*.py' -v

## EGS2 experiment evidence -> docs/generated/egs2_experiments.json.
egs2-experiments:
	$(THREADS) $(PYPATH) $(PY) $(REPO)/scripts/run_egs2_experiments.py

## EGS2 B1 closure: real-CAMB visibility cross-check seal (exit-2 registered blocker if camb absent).
egs2-camb-crosscheck:
	$(THREADS) $(PYPATH) $(PY) $(REPO)/scripts/run_egs2_camb_crosscheck_seal.py

## EGS3 extension gates (A1-A4 graded comparator/floor/e-value/RB; B1-B3 transfer/Volterra/vorticity).
egs3-gates:
	$(THREADS) $(PYPATH) $(PY) -m unittest discover -s $(GATEDIR3) -p 'test_egs3_*.py' -v

## EGS3 experiment evidence -> docs/generated/egs3_experiments.json.
egs3-experiments:
	$(THREADS) $(PYPATH) $(PY) $(REPO)/scripts/run_egs3_experiments.py

## EGS3 SymPy seals (parent identity/W^2 convention + Bianchi V constraint) -> docs/generated/*_seal.json.
egs3-seals:
	$(THREADS) $(PYPATH) $(PY) $(REPO)/scripts/run_egs3_symbolic_seals.py

## EGS3 local-only Wolfram cores (B4 two-sided bracket constants + PSD-cone redesign).
egs3-wolfram:
	$(THREADS) $(PY) $(REPO)/scripts/run_pr07_wolfram_proofs.py $(REPO)/wolfram/egs3_bracket_constants.wls --out $(REPO)/docs/generated/egs3_bracket_constants_proof.json
	$(THREADS) $(PY) $(REPO)/scripts/run_pr07_wolfram_proofs.py $(REPO)/wolfram/egs3_psd_cone.wls --out $(REPO)/docs/generated/egs3_psd_cone_proof.json
	$(THREADS) $(PY) $(REPO)/scripts/run_pr07_wolfram_proofs.py $(REPO)/wolfram/egs3_boost_tilt_separation.wls --out $(REPO)/docs/generated/egs3_boost_tilt_separation_proof.json

## EGS3 v7 SageMath exact-rational seals (T1'/DL1 signed-box endpoints + Bianchi V ideal membership).
egs3-sage:
	$(THREADS) $(PYPATH) $(PY) $(REPO)/scripts/run_egs3_sage_seals.py

## EGS3 v7 Lean-core machine-checked seals (gate-promotion lattice + endpoint certificates).
egs3-lean:
	$(THREADS) $(PYPATH) $(PY) $(REPO)/scripts/run_egs3_lean_seals.py

## EGS3 v7 local-only Wolfram seals (T4' estimated-covariance Hotelling/F; T3-lin xAct covariant momentum residual).
v7-wolfram:
	$(THREADS) $(PY) $(REPO)/scripts/run_pr07_wolfram_proofs.py $(REPO)/wolfram/egs3_v7_two_stage_coverage.wls --out $(REPO)/docs/generated/egs3_v7_wolfram_proofs.json
	$(THREADS) $(PY) $(REPO)/scripts/run_pr07_wolfram_proofs.py $(REPO)/wolfram/v7_t3lin_covariant_residual.wls --out $(REPO)/docs/generated/egs3_v7_t3lin_proof.json

## TEFF v8 active max-entropy effective-temperature representative gates (Thm 3 / Def 13 / Thm 18-22).
teff-gates:
	$(THREADS) $(PYPATH) $(PY) -m unittest discover -s $(REPO)/research_gates/teff/tests -p 'test_teff_*.py' -v

## EGS3/TEFF v8 local-only Wolfram seals (T3-full King-Ellis; TEFF representative constants; xAct;
## v8-update: T3-int interior family).
v8-wolfram:
	$(THREADS) $(PY) $(REPO)/scripts/run_pr07_wolfram_proofs.py $(REPO)/wolfram/v8_t3_king_ellis.wls --out $(REPO)/docs/generated/egs3_v8_t3_king_ellis_proof.json
	$(THREADS) $(PY) $(REPO)/scripts/run_pr07_wolfram_proofs.py $(REPO)/wolfram/v8_teff_representative.wls --out $(REPO)/docs/generated/egs3_v8_teff_representative_proof.json
	$(THREADS) $(PY) $(REPO)/scripts/run_pr07_wolfram_proofs.py $(REPO)/wolfram/v8_interior_family.wls --out $(REPO)/docs/generated/egs3_v8_interior_family_proof.json

## EGS3 v8 mathlib-backed Lean lane (forall-parameter T1'/DL1/T2' generalizations; separate package).
v8-mathlib:
	$(THREADS) $(PYPATH) $(PY) $(REPO)/scripts/run_egs3_v8_mathlib_seals.py

## EGS3/TEFF v8 aggregate lane: SymPy report-gating seals + TEFF gates + Wolfram cross-checks.
v8-seals: v7-sympy-seals teff-gates v8-wolfram

## EGS3 v7 strengthened-theorem SymPy seals (T1'/T2'/T4'/T5'/T8'/T9'/T3-lin/T3-full) -> docs/generated/*_seal.json.
v7-sympy-seals:
	$(THREADS) $(PYPATH) $(PY) $(REPO)/scripts/run_egs3_v7_seals.py

## EGS3 v7 aggregate symbolic-seal lane: SymPy (report-gating) + Sage + Lean + Wolfram.
v7-seals: egs3-seals v7-sympy-seals egs3-sage egs3-lean v7-wolfram

## PAPER-A: identifiability / congruence-kinematics gates + PAPER-A symbolic cores.
paper-a-gates:
	cd $(GATEDIR) && $(THREADS) $(PYPATH) $(PY) -m unittest -v \
	  test_pr04_schema test_pr04_congruence test_pr04_response test_pr04_integration
	cd $(GATEDIR7) && $(THREADS) $(PYPATH) $(PY) -m unittest -v test_pr07_paper_a
	$(THREADS) $(PY) $(REPO)/scripts/prove_pr04_paper_theorems.py

## PAPER-B: restricted Bianchi-I dynamics gates + PAPER-B symbolic cores.
paper-b-gates:
	cd $(GATEDIR) && $(THREADS) $(PYPATH) $(PY) -m unittest -v \
	  test_pr04_bianchi test_pr04_pushforward
	cd $(GATEDIR7) && $(THREADS) $(PYPATH) $(PY) -m unittest -v \
	  test_pr07_units test_pr07_conservation test_pr07_integrators
	$(THREADS) $(PY) $(REPO)/scripts/prove_pr04_paper_theorems.py

## Symbolic (Wolfram) proofs of the PAPER-A/B analytic cores.
pr04-proofs:
	$(THREADS) $(PY) $(REPO)/scripts/prove_pr04_paper_theorems.py

## Forbidden old-Rust / raw-data dependency scan over the PR04 overlay.
pr04-forbidden-deps:
	$(THREADS) $(PYPATH) $(PY) $(REPO)/research_gates/pr04/tools/verify_forbidden_dependencies.py --repo $(REPO)

## PR07 local-only Wolfram/xAct symbolic gate (NOT a portable check). Missing
## engine -> explicit blocker exit; never silently substituted by Python.
pr07-wolfram:
	$(THREADS) $(PY) $(REPO)/scripts/run_pr07_wolfram_proofs.py --out $(REPO)/docs/generated/pr07_wolfram_proofs.json

## PR07 concise-chain-of-checks CoVe report aggregation.
pr07-cove:
	$(THREADS) $(PYPATH) $(PY) $(REPO)/scripts/cove_verify_pr07.py --out $(REPO)/docs/generated/pr07_cove_report.json
