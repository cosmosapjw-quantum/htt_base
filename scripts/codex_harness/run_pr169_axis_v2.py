#!/usr/bin/env python3
"""Execute one fresh PR-169 CAS axis under repaired contract version 2."""
from pathlib import Path

import run_pr169_axis as base


base.CONTRACT_PATH = Path(
    "docs/generated/pr169_cas/CAS_CONTRACT_PR169_UNSIGNED_LEAKAGE_V2.json"
)
base.ASSIGNMENT_IDS = {
    "wolfram_xact": "A-PR169-CAS-V2-WOLFRAM",
    "sympy": "A-PR169-CAS-V2-SYMPY",
    "sage_singular": "A-PR169-CAS-V2-SAGE",
    "lean": "A-PR169-CAS-V2-LEAN",
}


if __name__ == "__main__":
    base.main()
