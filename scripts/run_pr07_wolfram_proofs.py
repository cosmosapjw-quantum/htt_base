#!/usr/bin/env python3
"""PR07 local-only Wolfram/xAct symbolic gate.

A single persistent Wolfram session is used when wolframclient is available;
otherwise the tool falls back to ``wolframscript -code``. Missing Wolfram is a
*registered blocker* (exit 2), never silently replaced by a Python proof. The
abstract-index (xAct) script may individually report xAct as missing while the
base-engine checks still pass.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess

REPO = Path(__file__).resolve().parents[1]
WOLFRAM_DIR = REPO / "wolfram"


def _run_client(path: Path, kernel: str | None) -> dict:
    from wolframclient.evaluation import WolframLanguageSession
    from wolframclient.language import wlexpr
    session = WolframLanguageSession(kernel) if kernel else WolframLanguageSession()
    try:
        session.start()
        quoted = str(path.resolve()).replace('\\', '\\\\').replace('"', '\\"')
        raw = session.evaluate(wlexpr(f'ExportString[Get["{quoted}"], "RawJSON"]'))
        return json.loads(raw)
    finally:
        session.terminate()


def _run_script(path: Path) -> dict:
    exe = shutil.which('wolframscript')
    if not exe:
        raise FileNotFoundError('neither wolframclient nor wolframscript is available')
    code = f'Print[ExportString[Get["{path.resolve()}"], "RawJSON"]]'
    proc = subprocess.run([exe, '-code', code], text=True, capture_output=True, check=True)
    lines = [x.strip() for x in proc.stdout.splitlines() if x.strip().startswith('{')]
    if not lines:
        raise RuntimeError(f'no JSON emitted by {path}: {proc.stdout}\n{proc.stderr}')
    return json.loads(lines[-1])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--kernel', default=None)
    parser.add_argument('--out', type=Path, default=REPO / 'docs/generated/pr07_wolfram_proofs.json')
    parser.add_argument('scripts', nargs='*')
    args = parser.parse_args()
    scripts = [Path(x) for x in args.scripts] or [
        WOLFRAM_DIR / 'pr07_symbolic_core.wls',
        WOLFRAM_DIR / 'pr07_xact_abstract.wls',
        WOLFRAM_DIR / 'pr07_bianchi_i_coordinates.wls',
    ]
    try:
        import wolframclient  # noqa: F401
        runner = lambda p: _run_client(p, args.kernel)
        backend = 'wolframclient'
    except Exception:
        runner = _run_script
        backend = 'wolframscript'

    results = []
    try:
        for script in scripts:
            results.append({'script': script.name, 'result': runner(script)})
    except Exception as exc:
        payload = {'status': 'BLOCKED_WOLFRAM_UNAVAILABLE_OR_FAILED', 'backend': backend,
                   'error': repr(exc), 'results': results}
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(payload, indent=2) + '\n')
        print(json.dumps(payload, indent=2))
        return 2

    # Verify every boolean check across the base-engine scripts is true. The
    # xAct script's structural checks are advisory when xAct is unavailable.
    all_true = True
    for entry in results:
        res = entry['result']
        checks = res.get('checks', res)
        for key, value in checks.items():
            if isinstance(value, bool) and not value:
                all_true = False
    payload = {'status': 'PASS' if all_true else 'FAIL', 'backend': backend, 'results': results}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + '\n')
    print(json.dumps(payload, indent=2))
    return 0 if all_true else 1


if __name__ == '__main__':
    raise SystemExit(main())
