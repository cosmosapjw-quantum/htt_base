"""Verify all checkpoint payload SHA256 and reject unexpected missing files."""
from pathlib import Path
import json,hashlib,sys

def main(root):
    root=Path(root)
    obj=json.loads((root/'MANIFEST_SHA256.json').read_text())
    for item in obj['files']:
        target=root/item['path']
        if not target.is_file():raise RuntimeError('MISSING: '+str(target))
        b=target.read_bytes();h=hashlib.sha256(b).hexdigest()
        if len(b)!=item['bytes'] or h!=item['sha256']:
            raise RuntimeError('SHA_MISMATCH '+item['path'])
    print('VERIFIED',len(obj['files']),'source/coded/scientific payload SHA256')
if __name__=='__main__':main(sys.argv[1] if len(sys.argv)>1 else '.')
