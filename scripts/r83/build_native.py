"""R83 optional four-window C++ source-verified builder, /tmp only."""
import json
from pathlib import Path
from htt.obsstat import p2p3_fast as f

def main():
    lib=Path(f._certified_native())
    receipt=json.loads(lib.with_name("manifest.json").read_text())
    print(json.dumps({"binary":str(lib),"bytes":lib.stat().st_size,"build":receipt},indent=2))
if __name__=="__main__":
    main()
