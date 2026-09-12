#!/usr/bin/env python3
"""Static whole-history catalog CLI. Targets are parsed, never imported/run."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from catalog_lib.db import connect, get_meta
from catalog_lib.query import query, show, history, check, render, write_rows
from catalog_lib.package import pack, restore

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_DB=ROOT/'.cache/project_catalog/catalog.sqlite'
DEFAULT_PACK=ROOT/'docs/project_catalog/database'


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db',type=Path,default=DEFAULT_DB)
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('scan',help='parse declared sources without importing or executing them')
    p.add_argument('--scope',type=Path,default=ROOT/'docs/project_catalog/sources.json')
    p.add_argument('--full',action='store_true',help='require a new empty database; preserve existing snapshots')
    p=sub.add_parser('query',help='filter records; default comparison version is R8')
    add_filters(p)
    p=sub.add_parser('export',help='export filtered records or package a complete SQLite snapshot')
    add_filters(p)
    p.add_argument('--output',type=Path)
    p.add_argument('--package',type=Path,help='write compressed database parts to this directory')
    p.add_argument('--docs',type=Path,help='generate Korean navigation/list/coverage documents')
    p.add_argument('--curation',type=Path,default=ROOT/'docs/project_catalog/curation.json')
    p=sub.add_parser('show');p.add_argument('id')
    p=sub.add_parser('history');p.add_argument('id_or_path');p.add_argument('--limit',type=int,default=100);p.add_argument('--format',choices=['table','json','csv'],default='table')
    sub.add_parser('check')
    p=sub.add_parser('restore',help='restore the shipped database without any external source checkout')
    p.add_argument('--package',type=Path,default=DEFAULT_PACK)
    args=parser.parse_args(argv)
    if args.command=='restore':
        if args.db.exists():raise ValueError('destination database already exists; choose a new --db path')
        print(restore(args.package,args.db));return 0
    if args.command=='scan':
        from catalog_lib.scan import Scanner
        scope=json.loads(args.scope.read_text())
        if args.full and args.db.exists():raise ValueError('--full requires an absent database; choose a new --db path')
        with connect(args.db) as c:report=Scanner(c,scope).run()
        print(json.dumps(report,ensure_ascii=False,indent=2));return 0
    if not args.db.exists():
        if not (DEFAULT_PACK/'manifest.json').exists():raise ValueError('No database: run scan or restore first')
        restore(DEFAULT_PACK,args.db)
    if args.command=='export' and args.docs:
        from catalog_lib.reports import add_curation, write_reports
        with connect(args.db) as c:
            add_curation(c,args.curation)
            summary=write_reports(c,args.docs,args.curation)
        print(json.dumps(summary,ensure_ascii=False,indent=2));return 0
    with connect(args.db,readonly=True) as c:
        if args.command=='show':print(json.dumps(show(c,args.id),ensure_ascii=False,indent=2));return 0
        if args.command=='history':print(render(history(c,args.id_or_path,args.limit),args.format),end='');return 0
        if args.command=='check':
            report=check(c);print(json.dumps(report,ensure_ascii=False,indent=2));return 0 if report['status']=='PASS' else 1
        if args.command=='export' and args.package:
            print(json.dumps(pack(args.db,args.package),indent=2));return 0
        rows=query(c,kind=args.kind,text=args.q,owner=args.owner,status=args.status,language=args.language,
                   evidence=args.evidence,source=args.source,ref=args.ref,not_in_ref=args.not_in_ref,
                   needs_update=args.needs_update,port_status=args.port_status,limit=args.limit,offset=args.offset,
                   stream=args.command=='export' and args.output is not None)
        if args.command=='export' and args.output:
            write_rows(rows,args.output,args.format);return 0
        output=render(rows,args.format)
        print(output,end='')
    return 0


def add_filters(p):
    p.add_argument('--kind',choices=['code','feature','port','analysis','proposition','plan','update','annotation','evidence','document','file','asset','gap','source','ref'])
    p.add_argument('--q',help='literal text search (name, description, provenance and source path)')
    for name in ['owner','status','language','evidence','source']:p.add_argument('--'+name)
    p.add_argument('--ref',default='baseline',help='baseline, all, working, branch name or stored commit')
    p.add_argument('--not-in-ref',help='exclude the same path/content version present at this ref')
    p.add_argument('--needs-update',action='store_true')
    p.add_argument('--port-status',choices=['byte-identical','no-identical-match'],help='byte comparison to baseline; not proof of historical porting')
    p.add_argument('--limit',type=int,default=50,help='-1 exports all matches')
    p.add_argument('--offset',type=int,default=0)
    p.add_argument('--format',choices=['table','json','csv'],default='table')


if __name__=='__main__':
    try:sys.exit(main())
    except (ValueError,OSError) as exc:print(f'catalog: {exc}',file=sys.stderr);sys.exit(2)
