PY ?= python3
REPO ?=

.PHONY: test demos clean-caches validate plugin-probe install-overlay freeze verify-release

test:
	PYTHONPATH=src $(PY) -m pytest -q

demos:
	PYTHONPATH=src $(PY) experiments/run_all.py

plugin-probe:
	PYTHONPATH=src $(PY) experiments/plugin_probe.py

clean-caches:
	find . -type d \( -name '__pycache__' -o -name '.pytest_cache' \) -prune -exec rm -rf {} +
	find . -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete

validate: test demos clean-caches
	$(PY) tools/verify_bundle.py

freeze: clean-caches
	$(PY) tools/build_manifest.py
	$(PY) tools/verify_bundle.py

verify-release: clean-caches
	$(PY) tools/verify_bundle.py

install-overlay:
	@test -n "$(REPO)" || (echo 'set REPO=/path/to/htt_base' && exit 2)
	$(PY) tools/install_into_repo.py --repo $(REPO) --dry-run
