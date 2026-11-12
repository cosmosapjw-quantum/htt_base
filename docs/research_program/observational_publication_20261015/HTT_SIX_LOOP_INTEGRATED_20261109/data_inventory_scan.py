"""Machine-readable inventory of locally held vs in-progress data under the raw root. Stat-only: no file is opened or hashed.
States: HELD (no partial files, nothing modified in the last RECENT_S seconds), DOWNLOADING (an active process names the directory in its
command line, or a file changed within RECENT_S), PARTIAL_STALLED (partial-download files present, no activity). Symlinks are recorded, not followed.
Usage: python3 data_inventory_scan.py --raw /mnt/extdrive/workdir/raw --out DATA_INVENTORY.json
"""
import argparse, json, os, re, time
RECENT_S = 900; PART = (".part", ".lock", ".tmp", ".crdownload")
def scan(path):
    n = b = pn = pb = links = 0; newest = 0.0; stack = [path]
    while stack:
        d = stack.pop()
        try:
            with os.scandir(d) as it:
                for e in it:
                    if e.is_symlink(): links += 1; continue
                    if e.is_dir(follow_symlinks=False): stack.append(e.path); continue
                    st = e.stat(follow_symlinks=False); newest = max(newest, st.st_mtime)
                    if e.name.endswith(PART) or ".part." in e.name or e.name.endswith(".part.json"):
                        if e.name.endswith(".part"): pn += 1; pb += st.st_size
                    else: n += 1; b += st.st_size
        except OSError: pass
    return n, b, pn, pb, links, newest
def sanitize(cmd, raw):
    cmd = cmd.replace(raw, "<RAW>")
    cmd = re.sub(r"--cookies\s+\S+", "--cookies <omitted>", cmd)
    return re.sub(r"(/home|/tmp)/\S+/(\S+)", r"<LOCAL_PATH>/\2", cmd)
def active_dirs(raw):
    out = []
    for pid in os.listdir("/proc"):
        if not pid.isdigit(): continue
        try: cmd = open(f"/proc/{pid}/cmdline", "rb").read().replace(b"\0", b" ").decode(errors="replace")
        except OSError: continue
        if any(k in cmd for k in ("download", "curl ", "wget", "aria2", "rsync", "gdown")) and "data_inventory_scan" not in cmd: out.append((pid, cmd[:600]))
    return out
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--raw", required=True); ap.add_argument("--out", required=True); a = ap.parse_args(); now = time.time(); procs = active_dirs(a.raw)
    items = []
    for top in sorted(os.listdir(a.raw)):
        p = os.path.join(a.raw, top)
        if os.path.isfile(p) or os.path.islink(p):
            st = os.lstat(p); items.append({"path": top, "kind": "file" if os.path.isfile(p) else "symlink", "files": 1, "bytes": st.st_size, "partial_files": 0, "state": "DOWNLOADING" if now - st.st_mtime < RECENT_S else "HELD", "newest_mtime_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(st.st_mtime))}); continue
        subs = [top] if top not in ("new_acquisitions", "observational_bundles") else [os.path.join(top, s) for s in sorted(os.listdir(p)) if os.path.isdir(os.path.join(p, s))]
        for rel in subs:
            if os.path.islink(os.path.join(a.raw, rel)): items.append({"path": rel, "kind": "symlink", "state": "HELD_SYMLINK_NOT_FOLLOWED"}); continue
            n, b, pn, pb, links, newest = scan(os.path.join(a.raw, rel)); ap_ = [pid for pid, c in procs if os.path.join(a.raw, rel) in c or os.path.basename(rel) in c]
            recent = now - newest < RECENT_S if newest else False
            state = "DOWNLOADING" if (ap_ or recent) else ("PARTIAL_STALLED" if pn else "HELD")
            items.append({"path": rel, "kind": "dir", "files": n, "bytes": b, "partial_files": pn, "partial_bytes": pb, "symlinks": links, "state": state, "active_pids": ap_, "newest_mtime_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(newest)) if newest else None})
    summ = {s: sum(1 for i in items if i["state"].startswith(s)) for s in ("HELD", "DOWNLOADING", "PARTIAL_STALLED")}
    json.dump({"schema": "htt.data_inventory/1", "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)), "raw_root_convention": "workdir/raw on the local external drive; paths are relative; no raw bytes in Git", "method": "stat-only walk; no hashing", "recent_activity_window_s": RECENT_S,
               "summary": summ, "active_download_processes": [{"pid": p, "cmdline_head": sanitize(c, a.raw)[:200], "owner": "unverified; may belong to another session/project"} for p, c in procs], "items": items}, open(a.out, "w"), indent=1)
    print(summ, len(procs))
if __name__ == "__main__": main()
