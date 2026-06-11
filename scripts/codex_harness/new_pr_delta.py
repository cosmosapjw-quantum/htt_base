#!/usr/bin/env python3
import argparse, yaml
from pathlib import Path
TEMPLATE="""# {pr_id} PR delta

## Goal

## Evidence read

## Web/doc checks

- WEB_CHECK_STATUS: pending|done|skipped

## Subagent divergence

- code_cartographer:
- harness_engineer:
- physics_stat_auditor:
- claim_gate_reviewer:
- regression_tester:

## Chosen plan

## Files changed

## Tests run

## Review findings and fixes

## Claim-tier impact

## Residual risks

## Commit

"""

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('pr_id'); ap.add_argument('--dir', default='docs/PR_DELTAS'); ap.add_argument('--dry-run', action='store_true')
    args=ap.parse_args(); path=Path(args.dir)/f'{args.pr_id}.md'
    content=TEMPLATE.format(pr_id=args.pr_id)
    if args.dry_run: print(path); print(content); return 0
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(content, encoding='utf-8'); print(path); return 0
if __name__=='__main__': raise SystemExit(main())
