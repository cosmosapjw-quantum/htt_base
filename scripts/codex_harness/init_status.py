#!/usr/bin/env python3
import sys, yaml
from pathlib import Path

def main():
    if len(sys.argv)!=3:
        print('usage: init_status.py <pr_backlog.yaml> <pr_status.yaml>', file=sys.stderr); return 2
    data=yaml.safe_load(Path(sys.argv[1]).read_text())
    status={'generated_from': sys.argv[1], 'completed': [], 'blocked': [], 'in_progress': None, 'notes': 'Update after each PR merge.'}
    Path(sys.argv[2]).write_text(yaml.safe_dump(status, sort_keys=False), encoding='utf-8')
    print(f"initialized {sys.argv[2]} with {len(data.get('prs',[]))} PRs")
if __name__=='__main__': raise SystemExit(main())
