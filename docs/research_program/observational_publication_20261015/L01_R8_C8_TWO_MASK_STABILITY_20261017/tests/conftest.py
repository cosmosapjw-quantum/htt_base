"""Pytest import roots for the real GitHub stacked-version directory layout."""
from pathlib import Path
import sys

PROGRAMME = Path(__file__).resolve().parents[2]
LOCATIONS = (
    PROGRAMME / "R8_SPIN2_S02_COHERENT_20261017" / "src",
    PROGRAMME / "R8_SPIN2_S02_COHERENT_20261017" / "tests",
    PROGRAMME / "L01_R8_C8_TWO_MASK_STABILITY_20261017" / "src",
)
for loc in LOCATIONS:
    if not loc.is_dir():
        raise RuntimeError(f"HTT_REPO_DEPENDENCY_MISSING: {loc}")
    if str(loc) not in sys.path:
        sys.path.insert(0, str(loc))
