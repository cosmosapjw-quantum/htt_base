"""R81 optional exact-source portable Fortran/C++ builds; binary in /tmp only."""
import json
from pathlib import Path
from htt.obsstat import phy_fast

def main():
    output={}
    for kind in ("mask","gram"):
        path=Path(phy_fast._certified_native(kind))
        manifest=json.loads(path.with_name("manifest.json").read_text())
        output[kind]={"path":str(path),"manifest":manifest,"bytes":path.stat().st_size}
    print(json.dumps(output,ensure_ascii=False,indent=2))
if __name__=="__main__":
    main()
