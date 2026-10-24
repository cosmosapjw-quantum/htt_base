"""One saved-carrier consumer. Requires controller's final INPUT.json."""

import json
from pathlib import Path
import sys

from factor import produce, sha256


HERE = Path(__file__).resolve().parent


def main():
    inp = json.loads((HERE / "INPUT.json").read_text())
    carrier = Path(inp["source"]["carrier"]["path"])
    result = Path(inp["source"]["result"]["path"])
    if sha256(carrier) != inp["source"]["carrier"]["sha256"]:
        raise RuntimeError("CARRIER_SHA_MISMATCH")
    if sha256(result) != inp["source"]["result"]["sha256"]:
        raise RuntimeError("RESULT_SHA_MISMATCH")
    output = HERE / "actual_run" / "products"
    output.mkdir(exist_ok=False)
    payload = produce(carrier, result, output)
    print(json.dumps({"status": payload["status"], "product_dir": str(output),
                      "factor_sha256": sha256(output / "FACTOR.npz"),
                      "result_sha256": sha256(output / "RESULT.json")}), flush=True)


if __name__ == "__main__":
    sys.exit(main())
