
import json
from pathlib import Path
import subprocess, sys

HERE = Path(__file__).resolve().parent
sym = HERE / "symbolic_verify.py"
num = HERE / "numeric_verify.py"

def run(script):
    proc = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, check=True)
    return proc.stdout

def main():
    out = {"symbolic_stdout": run(sym), "numeric_stdout": run(num), "crosscheck_stdout": run(HERE / "crosscheck.py")}
    (HERE/"run_all_stdout.json").write_text(json.dumps(out, indent=2))
    print("verification bundle completed")
    print((HERE/"symbolic_results.json").read_text())
    print((HERE/"numeric_results.json").read_text())

if __name__ == "__main__":
    main()
