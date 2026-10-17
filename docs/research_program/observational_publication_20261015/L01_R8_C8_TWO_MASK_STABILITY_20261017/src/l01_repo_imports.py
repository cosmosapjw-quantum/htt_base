"""Import bridge for HTT's intentionally separate, versioned L01 source directories.

No code is copied: resolve the original predecessor modules in the same
checked-out Git tree. Fail closed on a partial checkout.
"""
from pathlib import Path
import sys

PREDECESSOR = "R8_SPIN2_S02_COHERENT_20261017"


def activate() -> Path:
    programme = Path(__file__).resolve().parents[2]
    directory = programme / PREDECESSOR / "src"
    required = ("l01_k_spectral_certificate.py", "spin2_finite.py", "healpix_ring_coords.py")
    missing = [name for name in required if not (directory / name).is_file()]
    if missing:
        raise RuntimeError(f"HTT_PREDECESSOR_SOURCE_MISSING {directory}: {missing}")
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))
    return directory
