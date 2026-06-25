# PR04 research-program gate targets (LR-06A/B/C).
#
# Deterministic: thread counts are pinned to 1 so the theorem/property gates are
# reproducible across machines and CI jobs. The external 23 gates are necessary
# but not sufficient; the canonical pytest suite remains the merge authority.

REPO    := $(CURDIR)
PY      ?= $(REPO)/venv/bin/python
PYTHON  ?= python
GATEDIR := $(REPO)/research_gates/pr04/tests
THREADS := OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
PYPATH  := PYTHONPATH=$(REPO):$(REPO)/htt

.PHONY: pr04-gates paper-a-gates paper-b-gates pr04-proofs pr04-forbidden-deps

## All 23 external PR04 theorem/property gates + symbolic proofs + dep scan.
pr04-gates: pr04-forbidden-deps
	$(THREADS) $(PYPATH) $(PY) -m unittest discover -s $(GATEDIR) -p 'test_pr04_*.py' -v
	$(MAKE) pr04-proofs

## PAPER-A: identifiability / congruence-kinematics gates + PAPER-A symbolic cores.
paper-a-gates:
	cd $(GATEDIR) && $(THREADS) $(PYPATH) $(PY) -m unittest -v \
	  test_pr04_schema test_pr04_congruence test_pr04_response test_pr04_integration
	$(THREADS) $(PY) $(REPO)/scripts/prove_pr04_paper_theorems.py

## PAPER-B: restricted Bianchi-I dynamics gates + PAPER-B symbolic cores.
paper-b-gates:
	cd $(GATEDIR) && $(THREADS) $(PYPATH) $(PY) -m unittest -v \
	  test_pr04_bianchi test_pr04_pushforward
	$(THREADS) $(PY) $(REPO)/scripts/prove_pr04_paper_theorems.py

## Symbolic (Wolfram) proofs of the PAPER-A/B analytic cores.
pr04-proofs:
	$(THREADS) $(PY) $(REPO)/scripts/prove_pr04_paper_theorems.py

## Forbidden old-Rust / raw-data dependency scan over the PR04 overlay.
pr04-forbidden-deps:
	$(THREADS) $(PYPATH) $(PY) $(REPO)/research_gates/pr04/tools/verify_forbidden_dependencies.py --repo $(REPO)
