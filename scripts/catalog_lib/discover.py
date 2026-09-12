"""Discover finite project sources from supplied roots and prior asset inventory."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess

from .db import identity
from .scan import git


def discover(main, e2e, inventory, output_worktree, baseline):
    main,e2e,inventory=Path(main),Path(e2e),Path(inventory)
    git_sources=[{'id':'htt_base','path':str(main),'history':'all'}]
    backup=Path('/mnt/sn850x2t/htt_rewrite_20260717/git_dir_pre_rewrite')
    if backup.exists():git_sources.append({'id':'htt_pre_rewrite','path':str(backup),'history':'all'})
    worktrees=[]
    for block in git(main,'worktree','list','--porcelain',text=True).stdout.strip().split('\n\n'):
        item=dict(line.split(' ',1) if ' ' in line else (line,'') for line in block.splitlines())
        worktrees.append(item)
    roots=[{'id':'main_overlay','path':str(main),'description':'Main checkout with preserved uncommitted and ignored project materials'},
           {'id':'e2e_assets','path':str(e2e),'description':'Connected external code, data, archives and research runs'}]
    for item in worktrees:
        p=Path(item['worktree'])
        if p==main or str(p).startswith(str(e2e)+'/') or str(p)==str(output_worktree):continue
        roots.append({'id':'worktree_'+identity(str(p))[:12],'path':str(p),'description':'Registered worktree overlay; missing roots remain explicit'})
    origins=set();common_dirs=set()
    for config in git_sources:
        path=config['path']
        common=git(path,'rev-parse','--git-common-dir',text=True,check=False).stdout.strip()
        common_dirs.add(str((Path(path)/common).resolve()))
    source_rows=[]
    if inventory.exists():
        with (inventory/'git_repositories.csv').open() as f:source_rows=list(csv.DictReader(f))
    for row in source_rows:
        p=Path(row['path'])
        if not p.exists():continue
        common=git(p,'rev-parse','--git-common-dir',text=True,check=False).stdout.strip()
        if not common:continue
        resolved=str((p/common).resolve())
        if resolved in common_dirs:continue
        common_dirs.add(resolved)
        config={'id':'external_'+identity(resolved)[:12],'path':str(p),'history':'all'}
        if '/lean-shared/' in str(p):config['dependency_only']=True
        if row.get('origin','').rstrip('/').removesuffix('.git')=='https://github.com/cosmosapjw-quantum/htt_base':
            heads=git(p,'for-each-ref','--format=%(objectname)',text=True).stdout.splitlines()
            if all(git(main,'cat-file','-e',oid+'^{commit}',check=False).returncode==0 for oid in heads):config['replica_of']='htt_base'
        git_sources.append(config)
    scope={'schema_version':1,'owner':'COMMON','scope':'static project navigation; non-claim-bearing',
      'baseline_source':'htt_base','baseline_commit':baseline,
      'git_sources':git_sources,'filesystem_sources':roots,'worktrees':worktrees,
      'asset_inventory_source':str(inventory),
      'commit_maps':[str(main/'docs/git_history/commit_map_20260717.tsv')],
      'exclude_roots':[str(Path(output_worktree).parent),str(e2e/'lean-shared')],
      'follow_link_roots':[str(main),str(e2e)]+[r['path'] for r in roots],
      'metadata_only_directories':['.git','.remember','.venv','venv','venvs','env','envs','target','__pycache__','.cache','.lake','.pytest_cache','node_modules','.mypy_cache','.ruff_cache','site-packages','conda-meta','__MACOSX'],
      'text_limit_bytes':8*1024**2,'archive_limit_bytes':2*1024**3,'archive_depth':4,
      'limits_meaning':'Over-limit inputs remain inventoried with explicit processing status, not silently excluded.',
      'scientific_execution':'NOT_EXECUTED'}
    return scope
