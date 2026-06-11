#!/usr/bin/env python3
from __future__ import annotations
import re, sys, json
from pathlib import Path
if len(sys.argv)<2:
    print('Usage: check_latex_log.py build.log'); raise SystemExit(2)
p=Path(sys.argv[1]); txt=p.read_text(errors='ignore')
checks={
 'undefined_refs': r'Reference `[^\']+\' .* undefined|There were undefined references',
 'undefined_cites': r'Citation `[^\']+\' .* undefined|There were undefined citations',
 'missing_files': r'LaTeX Error: File `[^\']+\' not found',
 'overfull_hbox': r'Overfull \\hbox',
 'duplicate_labels': r'Label `[^\']+\' multiply defined',
}
summary={k:len(re.findall(v,txt)) for k,v in checks.items()}
print(json.dumps(summary,indent=2))
raise SystemExit(1 if any(v for v in summary.values()) else 0)
