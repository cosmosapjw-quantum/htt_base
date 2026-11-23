"""One-axis homogeneous photon-solver convergence with resumable per-case receipts."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass, replace
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import signal
import subprocess
import sys
import tempfile
import time

import numpy as np
import scipy

from bass.collision import moving_thomson
from bass.recombination import baryon_history, opacity_history, tilted_hyrec
from bass.transport import coupled_einstein_boltzmann, general_lie_stokes, moving_collision_stage
from scripts.r105 import native_optical_refinement


@dataclass(frozen=True)
class Case:
    family: str
    cells: int = 96
    ell: int = 4
    picard: int = 4
    depth: float | None = 1.
    rings: int = 16
    epsilon: float = 2e-4


def make_cases(families, grid, pilot=False):
    cases={}
    for family in families:
        base=Case(family, epsilon=0. if family=="FLRW" else 2e-4)
        if pilot:
            base=replace(base,cells=48)
        if base.rings<max(grid["ell"])+4:
            raise ValueError("requested ell_max exceeds the fixed angular grid; choose ell <=12 or revise rings")
        cases.setdefault(base,[]).append("baseline")
        for axis, values in grid.items():
            for value in values:
                case=replace(base,**{axis:value})
                if case!=base:
                    cases.setdefault(case,[]).append(axis)
    return cases


def case_key(case):
    return json.dumps(asdict(case),sort_keys=True,separators=(",",":"))


def execute(case, timeout):
    start=time.monotonic()
    cpu=time.process_time()
    def alarm(signum,frame):
        raise TimeoutError(f"case exceeded {timeout:g} s")
    prev=signal.signal(signal.SIGALRM,alarm)
    signal.setitimer(signal.ITIMER_REAL,timeout)
    try:
        answer=native_optical_refinement.solve_case(case.family,case.cells,case.depth,case.picard,None,
                    case.epsilon,ell=case.ell,rings=case.rings,detailed=True)
        return {"status":"executed","observables":answer,"cpu_s":time.process_time()-cpu,
                "wall_s":time.monotonic()-start,
                "worker_peak_RSS_KiB":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    except Exception as err:
        return {"status":"timeout" if isinstance(err,TimeoutError) else "failed",
                "error":f"{type(err).__name__}: {err}","wall_s":time.monotonic()-start}
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,prev)


def identity():
    modules=[coupled_einstein_boltzmann,general_lie_stokes,moving_collision_stage,moving_thomson,
             baryon_history,opacity_history,tilted_hyrec,native_optical_refinement]
    roots=[Path(m.__file__).resolve() for m in modules]+[Path(__file__).resolve()]
    data=Path(tilted_hyrec.DEFAULT_ATOMIC_DIR)
    roots.extend(data/x for x in ("Alpha_inf.dat","R_inf.dat","two_photon_tables.dat","fit_swift.dat"))
    roots.append(Path(coupled_einstein_boltzmann.HYREC_REF_CSV))
    # Include transitively loaded BASS physics (IC, algebra, geometry, angular basis).
    # Paths are module-qualified so two distinct modules may share a basename.
    files = {p.name: p for p in roots}
    for name, module in list(sys.modules.items()):
        if name.startswith("bass.") and getattr(module, "__file__", None):
            source = Path(module.__file__).resolve()
            if source.suffix == ".py":
                files[name] = source
    hashes = {key: hashlib.sha256(path.read_bytes()).hexdigest() for key, path in sorted(files.items())}
    return {"sha256":hashes,"python":platform.python_version(),"numpy":np.__version__,"scipy":scipy.__version__,
            "OMP_NUM_THREADS":os.getenv("OMP_NUM_THREADS"),"OPENBLAS_NUM_THREADS":os.getenv("OPENBLAS_NUM_THREADS")}


def save(path, data):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile("w",dir=path.parent,delete=False,encoding="utf-8") as stream:
        tmp=Path(stream.name)
        try:
            json.dump(data,stream,indent=2,allow_nan=False)
            stream.write("\n")
        except BaseException:
            tmp.unlink(missing_ok=True)
            raise
    tmp.replace(path)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preset",choices=("local","pilot"),default="local")
    parser.add_argument("--families",nargs="+",choices=("FLRW","VII_h","IX","VI_-1/9"))
    parser.add_argument("--cells",nargs="+",type=int)
    parser.add_argument("--ells",nargs="+",type=int)
    parser.add_argument("--picards",nargs="+",type=int)
    parser.add_argument("--depths",nargs="+",help="fixed or positive scalar optical depth caps")
    parser.add_argument("--workers",type=int,default=2)
    parser.add_argument("--timeout-seconds",type=float,default=1800.,help="per case; Linux worker interval timer")
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    pilot=args.preset=="pilot"
    fam=args.families or (["FLRW","VI_-1/9"] if pilot else ["FLRW","VII_h","IX","VI_-1/9"])
    grid={"cells":args.cells or ([48,96] if pilot else [96,192,384]),
          "ell":args.ells or ([4] if pilot else [4,6,8]),
          "picard":args.picards or ([4] if pilot else [4,6]),
          "depth":[None if x=="fixed" else float(x) for x in (args.depths or (["1"] if pilot else ["fixed","1","0.5"]))]}
    if (min(grid["cells"])<2 or min(grid["ell"])<2 or min(grid["picard"])<1
        or any(x is not None and (not np.isfinite(x) or x<=0) for x in grid["depth"])
        or args.workers<1 or not np.isfinite(args.timeout_seconds) or args.timeout_seconds<=0):
        parser.error("invalid numeric settings")
    cases=make_cases(fam,grid,pilot)
    request={case_key(c):a for c,a in cases.items()}
    signature=identity()
    if args.output.exists():
        packet=json.loads(args.output.read_text())
        if packet.get("physics_identity")!=signature or packet.get("requested_cases")!=request:
            raise ValueError("existing output describes other code, inputs, runtime or cases; choose a new output path")
    else:
        root=Path(__file__).resolve().parents[2]
        githead=subprocess.run(["git","-C",str(root),"rev-parse","HEAD"],capture_output=True,text=True)
        packet={"schema":"htt.r105.solver_axes.1","physics_identity":signature,
                "git_HEAD_if_known":githead.stdout.strip() or None,"requested_cases":request,"cases":{},
                "description":"one-factor changes from each named baseline; ell and time axes do not change GL rings",
                "neutrino_fraction":0.,"wall_timeout_per_case_seconds":args.timeout_seconds}
    todo=[c for c in cases if packet["cases"].get(case_key(c),{}).get("status")!="executed"]
    packet["status"]="running"
    packet["wall_timeout_per_case_seconds"]=args.timeout_seconds
    packet["worker_limit"]=args.workers
    save(args.output,packet)
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        jobs={pool.submit(execute,c,args.timeout_seconds):c for c in todo}
        for future in as_completed(jobs):
            c=jobs[future]
            packet["cases"][case_key(c)]={**future.result(),"inputs":asdict(c),"axes":cases[c]}
            save(args.output,packet)
    result=all(r["status"]=="executed" for r in packet["cases"].values()) and len(packet["cases"])==len(cases)
    packet["status"]="executed" if result else "incomplete"
    save(args.output,packet)
    print(f"{len(cases)} cases, {len(todo)} ran, {packet['status']}: {args.output}")
    return 0 if result else 1


if __name__=="__main__":
    raise SystemExit(main())
