"""R108 lane s4: receipted re-fetch of the two papers that S4 quotes (review finding S4-4).

Purpose: the S4 summary (literature_locators) and ``htt/bass/transport/bjs_bianchi_vii_h.py`` quote McEwen et al.
2006 (astro-ph/0510349) and Pontzen & Challinor 2007 (0706.2075).  The copies in ~/Downloads/htt_r108/s4/lit were
downloaded without a receipt.  This script fetches both PDFs again from arxiv.org into a NEW, EMPTY directory,
writes one RECEIPTS.jsonl line per file (url, final_url, http status, bytes, sha256, md5, fetched_at_utc and the
served file name, which carries the arXiv version), compares each with the earlier unreceipted copy, and checks
that the quoted phrases occur in the text of the fetched version (``pdftotext``, run as an external binary; the
PDFs are data, never executed or imported).
Inputs: network (arxiv.org).  Outputs: <dest>/*.pdf, <dest>/RECEIPTS.jsonl, <dest>/LIT_PHRASE_CHECK.json.
No randomness.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

DEST = Path.home() / "Downloads/htt_r108/s4/lit_receipted"
OLD = Path.home() / "Downloads/htt_r108/s4/lit"
UA = "htt-r108-lit-fetch/1 (python urllib)"
PAPERS = [
    {"id": "S4-LIT-1", "arxiv": "astro-ph/0510349", "name": "mcewen2006_astro-ph0510349.pdf",
     "citation": "McEwen, Hobson, Lasenby & Mortlock 2006, MNRAS 369, 1858",
     "phrases": ["specify the direction of the incoming photon",
                 "which is related to the observing angles by"],
     "not_checked": "eq. A2 (an equation; pdftotext does not render it as checkable text)"},
    {"id": "S4-LIT-2", "arxiv": "0706.2075", "name": "pontzen_challinor2007_0706.2075.pdf",
     "citation": "Pontzen & Challinor 2007, MNRAS 380, 1387",
     "phrases": ["σij = 0 except for σ12 , σ13",
                 "always choose σ12 = σ13 which we do for compatibility with previous studies",
                 "the ratio of the shear to Doppler contributions",
                 "If instead we assume the same tilt"],
     "not_checked": "eq. 67 (an equation)"},
]


def _norm(s: str) -> str:
    return re.sub(r"\s+", "", s)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dest", type=Path, default=DEST)
    ap.add_argument("--timeout", type=float, default=60.0)
    a = ap.parse_args(argv)
    if a.dest.exists() and any(a.dest.iterdir()):
        raise SystemExit(f"destination {a.dest} is not empty; receipts are written only into a new empty directory")
    a.dest.mkdir(parents=True, exist_ok=True)
    script = Path(__file__).resolve()
    checks = {"schema": "htt.r108.s4_lit_phrase_check/1", "command": [sys.executable, *sys.argv],
              "script": {"path": str(script), "sha256": hashlib.sha256(script.read_bytes()).hexdigest()},
              "pdftotext": subprocess.run(["pdftotext", "-v"], capture_output=True, text=True).stderr.strip()
              .splitlines()[0], "papers": []}
    for p in PAPERS:
        url = f"https://arxiv.org/pdf/{p['arxiv']}"
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        fetched_at = dt.datetime.now(dt.timezone.utc).isoformat()
        with urllib.request.urlopen(req, timeout=a.timeout) as resp:
            body = resp.read()
            final_url, status = resp.geturl(), resp.status
            ctype, cdisp = resp.headers.get("Content-Type"), resp.headers.get("Content-Disposition")
        if not body.startswith(b"%PDF"):
            raise SystemExit(f"{url}: response is not a PDF")
        out = a.dest / p["name"]
        out.write_bytes(body)
        sha = hashlib.sha256(body).hexdigest()
        old = OLD / p["name"]
        old_sha = hashlib.sha256(old.read_bytes()).hexdigest() if old.exists() else None
        rec = {"id": p["id"], "name": p["name"], "path": str(out), "url": url, "final_url": final_url,
               "http_status": status, "content_type": ctype, "content_disposition": cdisp, "bytes": len(body),
               "sha256": sha, "md5": hashlib.md5(body).hexdigest(), "fetched_at_utc": fetched_at,
               "status": "FETCHED", "route": "arxiv.org/pdf (HTTPS GET, urllib)", "citation": p["citation"],
               "earlier_unreceipted_copy": {"path": str(old), "sha256": old_sha,
                                            "identical_to_this_fetch": old_sha == sha}}
        with open(a.dest / "RECEIPTS.jsonl", "a") as fh:
            fh.write(json.dumps(rec) + "\n")
        txt = subprocess.run(["pdftotext", "-enc", "UTF-8", str(out), "-"], capture_output=True, check=True).stdout
        flat = _norm(txt.decode("utf-8", errors="replace"))
        checks["papers"].append({"id": p["id"], "name": p["name"], "sha256": sha, "citation": p["citation"],
                                 "phrases": {ph: _norm(ph) in flat for ph in p["phrases"]},
                                 "not_checked": p["not_checked"],
                                 "match_rule": "all whitespace removed from the phrase and from the pdftotext output"})
        print(json.dumps({"id": p["id"], "bytes": len(body), "sha256": sha, "same_as_earlier": old_sha == sha,
                          "phrases": checks["papers"][-1]["phrases"]}), flush=True)
    (a.dest / "LIT_PHRASE_CHECK.json").write_text(json.dumps(checks, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
