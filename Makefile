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
THREADS  := OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
PYPATH   := PYTHONPATH=$(REPO):$(REPO)/htt:$(REPO)/htt/htt

.PHONY: pr04-gates pr07-gates paper-a-gates paper-b-gates pr04-proofs \
        pr04-forbidden-deps pr07-wolfram pr07-cove

## All 23 external PR04 theorem/property gates + symbolic proofs + dep scan.
pr04-gates: pr04-forbidden-deps
	$(THREADS) $(PYPATH) $(PY) -m unittest discover -s $(GATEDIR) -p 'test_pr04_*.py' -v
	$(MAKE) pr04-proofs

## PR07 portable repair gates (unit-safe stress, independent dynamics, PAPER-A).
pr07-gates: pr04-forbidden-deps
	$(THREADS) $(PYPATH) $(PY) -m unittest discover -s $(GATEDIR7) -p 'test_pr07_*.py' -v

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
