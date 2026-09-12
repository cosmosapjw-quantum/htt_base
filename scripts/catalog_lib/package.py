"""Compressed SQLite transport; checksums concern packaging, not science."""
from __future__ import annotations

import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile


def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024**2),b''):h.update(b)
    return h.hexdigest()


def pack(db, directory, chunk_bytes=40*1024**2):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    # Read the consistent committed SQLite database, independent of any WAL.
    with tempfile.TemporaryDirectory(dir=directory) as temp:
        snapshot=Path(temp)/'catalog.sqlite'; compressed=Path(temp)/'catalog.sqlite.gz'
        # Copy only live logical pages; obsolete cache text/free pages do not
        # belong to the portable inventory. VACUUM INTO leaves the source intact.
        with sqlite3.connect(Path(db).resolve().as_uri()+'?mode=ro',uri=True) as src:
            src.execute('VACUUM INTO ?', (str(snapshot),))
        with open(snapshot,'rb') as inp,open(compressed,'wb') as raw,gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0,compresslevel=6) as out:shutil.copyfileobj(inp,out)
        parts=[]
        with compressed.open('rb') as f:
            for n,data in enumerate(iter(lambda:f.read(chunk_bytes),b'')):
                name=f'catalog.sqlite.gz.part{n:03d}'
                p=directory/name;p.write_bytes(data)
                parts.append({'name':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
        manifest={'format':'gzip_split_sqlite_v1','database_bytes':snapshot.stat().st_size,'database_sha256':sha(snapshot),'parts':parts,'checksum_scope':'transport_byte_identity_only'}
        # Remove only superseded parts belonging to this exact output format.
        keep={x['name'] for x in parts}
        for p in directory.glob('catalog.sqlite.gz.part[0-9][0-9][0-9]'):
            if p.name not in keep:p.unlink()
        (directory/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest


def restore(directory, db):
    directory=Path(directory);db=Path(db)
    manifest=json.loads((directory/'manifest.json').read_text())
    if manifest.get('format')!='gzip_split_sqlite_v1':raise ValueError('unsupported catalog transport format')
    db.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=db.parent) as temp:
        archive=Path(temp)/'combined.gz'; output=Path(temp)/'catalog.sqlite'
        with archive.open('wb') as out:
            for part in manifest['parts']:
                name=part['name']
                if Path(name).name!=name:raise ValueError('invalid part basename')
                p=directory/name
                if p.stat().st_size!=part['bytes'] or sha(p)!=part['sha256']:raise ValueError(f'catalog part does not match transport manifest: {name}')
                with p.open('rb') as f:shutil.copyfileobj(f,out)
        with gzip.open(archive,'rb') as f,output.open('wb') as out:shutil.copyfileobj(f,out)
        if output.stat().st_size!=manifest['database_bytes'] or sha(output)!=manifest['database_sha256']:raise ValueError('restored database transport mismatch')
        os.replace(output,db)
    return db
