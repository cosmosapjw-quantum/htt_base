import importlib
import importlib.util
import json
import sys
import sysconfig
from pathlib import Path

root = Path.cwd()
assert "statistics" not in sys.modules, "No cached statistics allowed at entry"
legacy_paths = ["htt/htt/tests/test_bass_d2_transfer.py", "htt/htt/tests/test_peculiar_jeans.py"]
for index, relative in enumerate(legacy_paths):
    spec = importlib.util.spec_from_file_location(f"review_legacy_{index}", root / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert "statistics" not in sys.modules, "Legacy import unexpectedly preloaded statistics"
    assert str(root / "htt" / "bass") not in sys.path, "Package interior remains import search root"
    print(json.dumps({"legacy_import": relative, "statistics_preloaded": False}))
expected = (Path(sysconfig.get_path("stdlib")) / "statistics.py").resolve()
assert Path(importlib.util.find_spec("statistics").origin).resolve() == expected
for name in ["common.structured_inference", "common.statistical_foundations", "scripts.codex_harness.run_pr254_normalizer_benchmark"]:
    module = importlib.import_module(name)
    print(json.dumps({"consumer_import": name, "origin": module.__file__}))
statistics = importlib.import_module("statistics")
assert Path(statistics.__file__).resolve() == expected
assert statistics.NormalDist().inv_cdf(0.5) == 0.0
legacy_statistics = importlib.import_module("bass.statistics")
assert Path(legacy_statistics.__file__).resolve() == (root / "htt" / "bass" / "statistics.py").resolve()
assert legacy_statistics is not statistics
assert callable(legacy_statistics.chi_squared)
print(json.dumps({"stdlib_statistics_origin": statistics.__file__, "NormalDist_inv_cdf_half": statistics.NormalDist().inv_cdf(0.5), "public_legacy_statistics_origin": legacy_statistics.__file__, "PASS": True}))
