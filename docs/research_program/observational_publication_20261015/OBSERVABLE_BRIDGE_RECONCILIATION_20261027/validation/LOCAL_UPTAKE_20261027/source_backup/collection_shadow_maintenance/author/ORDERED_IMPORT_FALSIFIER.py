import sys, runpy, importlib, sysconfig
from pathlib import Path
assert "statistics" not in sys.modules, "statistics must not be preloaded"
for path in ["htt/htt/tests/test_bass_d2_transfer.py", "htt/htt/tests/test_peculiar_jeans.py"]:
    runpy.run_path(path)
    print("legacy imported:", path, "statistics loaded:", "statistics" in sys.modules)
for module in ["common.structured_inference", "common.statistical_foundations", "scripts.codex_harness.run_pr254_normalizer_benchmark"]:
    importlib.import_module(module)
    print("consumer imported:", module)
import statistics
expected = Path(sysconfig.get_path("stdlib")) / "statistics.py"
print("statistics origin:", statistics.__file__)
print("stdlib expected:", expected)
assert Path(statistics.__file__).resolve() == expected.resolve()
assert statistics.NormalDist().inv_cdf(.5) == 0.0
print("NormalDist.inv_cdf(0.5):", statistics.NormalDist().inv_cdf(.5))
