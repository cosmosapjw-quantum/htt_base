"""Acquire selected public research inputs; never execute or extract downloads.

Default is a plan. --fetch uses create-only destinations outside the Git tree.
Byte caps and aggregate budgets are optional; null/omitted means uncapped. Existing large Planck streams keep
using their dedicated validated range-resume implementation.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from urllib.parse import urlsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener

DEFAULT_MANIFEST = Path(__file__).resolve().parents[1] / 'docs/research_program/observational_publication_20261015/FRONTIER_20261020/ACQUISITION_MANIFEST.json'
CHUNK = 1024 * 1024


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(CHUNK), b''):
            h.update(block)
    return h.hexdigest()


def check_url(url, hosts):
    p = urlsplit(url)
    if p.scheme != 'https' or p.hostname not in hosts or p.username or p.password or p.port not in (None, 443):
        raise ValueError('Only manifest-listed public HTTPS hosts without credentials are allowed')


class PublicRedirect(HTTPRedirectHandler):
    def __init__(self, hosts):
        super().__init__()
        self.hosts = hosts

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        check_url(newurl, self.hosts)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def destination(root, relative):
    root = Path(root).resolve()
    p = Path(relative)
    if p.is_absolute() or '..' in p.parts or not p.parts:
        raise ValueError('Destination must be a relative path inside data root')
    dest = root / p
    if not dest.resolve().is_relative_to(root) or dest.is_symlink():
        raise ValueError('Destination escapes data root')
    return dest


def validate_payload(path, spec):
    """Transport/format checks, not scientific admission."""
    path = Path(path)
    size = path.stat().st_size
    if size < spec.get('min_bytes', 1) or (spec.get('max_bytes') is not None and size > spec['max_bytes']):
        raise ValueError('Payload size outside declared bounds')
    if spec.get('expected_bytes') is not None and size != spec['expected_bytes']:
        raise ValueError('Payload length differs from source metadata')
    with path.open('rb') as f:
        prefix = f.read(4096)
    if prefix.lstrip().lower().startswith((b'<!doctype html', b'<html')):
        raise ValueError('HTML login/error page is not a data product')
    fmt = spec['format']
    if fmt in ('gzip', 'tar.gz'):
        if prefix[:2] != b'\x1f\x8b':
            raise ValueError('Missing gzip magic')
        # CRC and truncation are checked with a bounded expanded stream; no extraction.
        expanded = 0
        with gzip.open(path, 'rb') as f:
            for block in iter(lambda: f.read(CHUNK), b''):
                expanded += len(block)
                expanded_cap = spec.get('max_expanded_bytes', spec['max_bytes'] * 20 if spec.get('max_bytes') is not None else None)
                if expanded_cap is not None and expanded > expanded_cap:
                    raise ValueError('Expanded payload exceeds bound')
    elif fmt == 'fits':
        if prefix[:9] != b'SIMPLE  =' or size % 2880:
            raise ValueError('Invalid FITS transport header/block length')
    elif fmt == 'json':
        with path.open() as f:
            json.load(f)
    elif fmt in ('text', 'csv'):
        prefix.decode('utf-8')
        for token in spec.get('required_prefix_tokens', []):
            if token.encode() not in prefix:
                raise ValueError('Missing expected table/header marker: ' + token)
    else:
        raise ValueError('Unrecognized format')
    digest = sha256(path)
    if spec.get('sha256') and digest != spec['sha256']:
        raise ValueError('Upstream expected SHA256 mismatch')
    return {'bytes': size, 'sha256': digest}


def acquire(spec, root, hosts, reserve_bytes=2*1024**3, opener=None):
    """Reuse only a payload bound to an existing receipt or upstream expected hash.

    A failed download retains its unique .part file; it is never mistaken for a
    complete product. No partial resume for these small products. Large Planck
    inputs are explicitly delegated to the existing checked range-resume fetcher.
    """
    check_url(spec['url'], hosts)
    dest = destination(root, spec['path'])
    receipt_path = dest.with_name(dest.name + '.receipt.json')
    if receipt_path.is_symlink():
        raise ValueError('Receipt may not be a symlink')
    if dest.exists():
        identity = validate_payload(dest, spec)
        if receipt_path.exists():
            old = json.loads(receipt_path.read_text())
            if old.get('url') != spec['url'] or old.get('sha256') != identity['sha256'] or old.get('bytes') != identity['bytes']:
                raise ValueError('Existing payload/receipt identity mismatch; preserve and inspect')
        elif not spec.get('sha256'):
            raise FileExistsError('Existing unreceipted product: inspect/adopt with known hash, do not overwrite')
        return {'id': spec['id'], 'status': 'REUSED', 'path': str(dest), **identity}
    if receipt_path.exists():
        raise FileExistsError('Orphan receipt preserved; payload missing')
    dest.parent.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(dest.parent).free < reserve_bytes + (spec.get('expected_bytes') or spec.get('max_bytes') or CHUNK):
        raise OSError('Insufficient free space for expected product or next chunk plus reserve')
    opener = opener or build_opener(PublicRedirect(hosts))
    req = Request(spec['url'], headers={'User-Agent': 'HTT-open-inputs/1.0', 'Accept-Encoding': 'identity'})
    part = None
    try:
        with opener.open(req, timeout=45) as response:
            check_url(response.geturl(), hosts)
            if response.status != 200:
                raise ValueError('Fresh download requires HTTP 200')
            if response.headers.get('Content-Encoding', 'identity') != 'identity':
                raise ValueError('Unexpected transfer content encoding')
            length = response.headers.get('Content-Length')
            expected_length = int(length) if length else None
            if expected_length is not None and (expected_length <= 0 or (spec.get('max_bytes') is not None and expected_length > spec['max_bytes'])):
                raise ValueError('Content-Length exceeds product bound or is empty')
            if expected_length is not None and shutil.disk_usage(dest.parent).free < reserve_bytes + expected_length:
                raise OSError('Insufficient free space for Content-Length plus reserve')
            fd, name = tempfile.mkstemp(prefix=dest.name + '.', suffix='.part', dir=dest.parent)
            part = Path(name)
            received = 0
            with os.fdopen(fd, 'wb') as out:
                while True:
                    cap = spec.get('max_bytes')
                    block = response.read(min(CHUNK, cap - received + 1) if cap is not None else CHUNK)
                    if not block:
                        break
                    received += len(block)
                    if cap is not None and received > cap:
                        raise ValueError('Stream exceeds product bound')
                    if shutil.disk_usage(dest.parent).free < reserve_bytes + len(block):
                        raise OSError('Insufficient free space while streaming; partial retained')
                    out.write(block)
                out.flush()
                os.fsync(out.fileno())
            if expected_length is not None and received != expected_length:
                raise ValueError('Truncated HTTP payload')
            identity = validate_payload(part, spec)
            record = {'id': spec['id'], 'status': 'DOWNLOADED', 'url': spec['url'],
                      'final_url': response.geturl(), 'time_utc': datetime.now(timezone.utc).isoformat(),
                      'etag': response.headers.get('ETag'), 'last_modified': response.headers.get('Last-Modified'),
                      'content_type': response.headers.get('Content-Type'), 'path': str(dest),
                      'qualification': 'TRANSPORT_FORMAT_ONLY', **identity}
        # hard-link is atomic and create-only: never replace an existing destination.
        os.link(part, dest)
        part.unlink()
        with receipt_path.open('x') as out:
            json.dump(record, out, indent=2)
            out.write('\n')
        return record
    except Exception as exc:
        raise RuntimeError(f'{spec["id"]}: {exc}; partial={part}') from exc


def load_manifest(path):
    manifest = json.loads(Path(path).read_text())
    seen, paths = set(), set()
    hosts = manifest['allowed_hosts']
    for spec in manifest['resources']:
        if spec['id'] in seen or spec['path'] in paths:
            raise ValueError('Duplicate resource ID or path')
        seen.add(spec['id']); paths.add(spec['path'])
        check_url(spec['url'], hosts)
        if spec.get('max_bytes') is not None and (type(spec['max_bytes']) is not int or spec['max_bytes'] <= 0):
            raise ValueError('Invalid byte cap')
        destination(Path('/manifest_validation'), spec['path'])
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument('--data-root', type=Path, default=Path('/mnt/extdrive/workdir/htt_open_data'))
    parser.add_argument('--ids', nargs='+', help='Explicit resource IDs; otherwise only auto_fetch entries')
    parser.add_argument('--fetch', action='store_true')
    parser.add_argument('--budget-gib', type=float, default=None, help='Optional aggregate cap; omitted means no budget cap')
    parser.add_argument('--reserve-gib', type=float, default=2.0)
    args = parser.parse_args()
    manifest = load_manifest(args.manifest)
    if (args.budget_gib is not None and args.budget_gib <= 0) or args.reserve_gib < 0:
        parser.error('Budget must be positive and reserve nonnegative')
    resources = manifest['resources']
    if args.ids:
        unknown = set(args.ids) - {r['id'] for r in resources}
        if unknown:
            parser.error('Unknown IDs: ' + ', '.join(sorted(unknown)))
    chosen = [r for r in resources if r['id'] in args.ids] if args.ids else [r for r in resources if r.get('auto_fetch')]
    root = args.data_root.resolve()
    repo = Path(__file__).resolve().parents[1]
    if root.is_relative_to(repo):
        parser.error('Raw inputs must stay outside the repository')
    bound = sum(r['max_bytes'] for r in chosen) if all(r.get('max_bytes') is not None for r in chosen) else None
    if args.budget_gib is not None and (bound is None or bound > args.budget_gib * 1024**3):
        parser.error('Selected maximum-byte sum exceeds download budget; choose smaller batches')
    print(json.dumps({'resources': [r['id'] for r in chosen], 'max_bytes': bound,
                      'fetch': args.fetch, 'data_root': str(root)}), flush=True)
    if not args.fetch:
        return 0
    failures = 0
    for spec in chosen:
        try:
            result = acquire(spec, root, manifest['allowed_hosts'], int(args.reserve_gib*1024**3))
        except Exception as exc:
            failures += 1
            result = {'id': spec['id'], 'status': 'FAILED', 'error': str(exc)}
        print(json.dumps(result), flush=True)
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())

