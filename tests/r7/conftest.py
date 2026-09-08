"""Use the composed checkout, including the nested installed-package layout."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT / "htt/src", ROOT / "htt", ROOT / "htt/htt"):
    sys.path.insert(0, str(path))

