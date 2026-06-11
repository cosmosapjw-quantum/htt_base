#!/usr/bin/env python3
import argparse, subprocess, sys
SUBSETS={
  'collect': ['python','-m','pytest','--collect-only','-q'],
  'smoke': ['python','-m','pytest','-m','smoke','-q'],
  'contracts': ['python','-m','pytest','tests/contracts','-q'],
  'mio': ['python','-m','pytest','tests/mio','htt/mio/tests','-q'],
  'htt': ['python','-m','pytest','tests/htt','htt/htt/tests','-q'],
  'obsstat': ['python','-m','pytest','tests/obsstat','-q'],
}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('subset', nargs='?')
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--dry-run', action='store_true')
    args=ap.parse_args()
    if args.list or not args.subset:
        print('\n'.join(sorted(SUBSETS))); return 0
    if args.subset not in SUBSETS:
        print(f"unknown subset {args.subset}", file=sys.stderr); return 2
    cmd=SUBSETS[args.subset]
    print(' '.join(cmd))
    if args.dry_run: return 0
    return subprocess.call(cmd)
if __name__=='__main__': raise SystemExit(main())
