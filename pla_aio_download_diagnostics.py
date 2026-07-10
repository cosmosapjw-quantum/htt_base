#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pla_aio_download_diagnostics.py

Bottleneck-OWNERSHIP diagnostic + benchmark for the ESA Planck Legacy Archive
(PLA) AIO servlet, tuned for a very-long-fat (Incheon KR -> ESAC Spain) path.

This is a *diagnosis*, not a menu benchmark. It runs experiments whose signature
patterns uniquely identify which party owns the throughput bottleneck (client TCP
dynamics, client uplink, ESAC server, or the network path), then emits a single
deterministic production-download command.

SAFETY (see module SAFETY section): never touches the final FITS files, never
downloads a whole file, all bytes go to /dev/null or a self-deleted temp dir,
no cookies/auth, per-socket congestion-control selection (never touches the
system default unless explicitly allowed + always restored), guaranteed cleanup
of temp dirs + subprocesses on normal exit AND on exception/SIGINT/SIGTERM.

Standard library only + subprocess calls to `curl`/`aria2c` + a small raw-socket
helper for the congestion-control experiment.

Usage:
    python3 pla_aio_download_diagnostics.py --duration 90
    python3 pla_aio_download_diagnostics.py --dry-run

Deliverable outputs (under .../downloads/pla/diagnostics/):
    pla_aio_diagnostics_report.json
    pla_aio_diagnostics_report.md
"""

from __future__ import annotations

import argparse
import atexit
import glob
import json
import os
import re
import shutil
import signal
import socket
import ssl
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone

# --------------------------------------------------------------------------- #
# Paths (as given in the environment spec)
# --------------------------------------------------------------------------- #
E2E_ROOT = "/mnt/sn850x2t/htt_base_e2e"
PLA_ROOT = os.path.join(E2E_ROOT, "downloads", "pla")
DIAG_DIR = os.path.join(PLA_ROOT, "diagnostics")
LOGS_DIR = os.path.join(PLA_ROOT, "logs")
URLS_DIR = os.path.join(PLA_ROOT, "urls")
CMB_DIR = os.path.join(E2E_ROOT, "workdir", "raw", "planck_ffp10", "smica", "cmb_mc")
NOISE_DIR = os.path.join(E2E_ROOT, "workdir", "raw", "planck_ffp10", "smica", "noise_mc")

REPORT_JSON = os.path.join(DIAG_DIR, "pla_aio_diagnostics_report.json")
REPORT_MD = os.path.join(DIAG_DIR, "pla_aio_diagnostics_report.md")

# AIO servlet endpoint (public, no cookies, no Authorization).
HOST = "pla.esac.esa.int"
AIO_PATH = "/pla/aio/product-action?SIMULATED_MAP.FILE_ID="

# Dataset facts (given): 999 CMB (00970 corrupt/missing) + 300 noise, ~576 MiB each.
FILE_SIZE_MIB = 576.0
N_CMB = 999
N_NOISE = 300
N_FILES_TOTAL = N_CMB + N_NOISE  # 1299
MISSING_CMB_ID = 970

# Good-citizen production ceiling.
PROD_MAX_CONCURRENCY = 6

# Browser-like headers (no auth, no cookies).
BROWSER_UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
REFERER = "https://pla.esac.esa.int/"

# curl -w machine-readable format (raw backslash-n -> curl converts to newline).
CURL_W = (r"code=%{http_code}\nsize=%{size_download}\nspeed=%{speed_download}"
          r"\ntime=%{time_total}\nttfb=%{time_starttransfer}"
          r"\nredir=%{num_redirects}\neffurl=%{url_effective}\n")

# Default reference hosts for T6 (polite: 2 large static Range-capable files).
# IRSA US contrast is available via --reference-hosts but not enabled by default.
DEFAULT_REFERENCE_HOSTS = [
    "https://speed.hetzner.de/100MB.bin",
    "https://speed.cloudflare.com/__down?bytes=104857600",
]

# --------------------------------------------------------------------------- #
# Global cleanup registry — guarantees no orphaned procs / temp dirs / CC state.
# --------------------------------------------------------------------------- #
_LOCK = threading.Lock()
_TEMP_DIRS: set[str] = set()
_PROCS: set[subprocess.Popen] = set()
_GLOBAL_CC_RESTORE: str | None = None  # original global CC to restore, or None
_CLEANED = False


def _register_temp(d: str) -> None:
    with _LOCK:
        _TEMP_DIRS.add(d)


def _register_proc(p: subprocess.Popen) -> None:
    with _LOCK:
        _PROCS.add(p)


def _unregister_proc(p: subprocess.Popen) -> None:
    with _LOCK:
        _PROCS.discard(p)


def cleanup() -> None:
    """Idempotent: kill tracked procs, remove temp dirs, restore global CC."""
    global _CLEANED, _GLOBAL_CC_RESTORE
    with _LOCK:
        if _CLEANED:
            return
        _CLEANED = True
        procs = list(_PROCS)
        temps = list(_TEMP_DIRS)
        cc_restore = _GLOBAL_CC_RESTORE

    for p in procs:
        try:
            if p.poll() is None:
                p.terminate()
        except Exception:
            pass
    deadline = time.monotonic() + 5.0
    for p in procs:
        try:
            remaining = max(0.0, deadline - time.monotonic())
            p.wait(timeout=remaining)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass

    for d in temps:
        try:
            shutil.rmtree(d, ignore_errors=True)
        except Exception:
            pass

    if cc_restore is not None:
        try:
            subprocess.run(
                ["sysctl", "-w", "net.ipv4.tcp_congestion_control=%s" % cc_restore],
                capture_output=True, text=True, timeout=10,
            )
            sys.stderr.write("[cleanup] restored global tcp_congestion_control=%s\n"
                             % cc_restore)
        except Exception:
            sys.stderr.write("[cleanup] WARNING: failed to restore global CC=%s; "
                             "please run: sudo sysctl -w "
                             "net.ipv4.tcp_congestion_control=%s\n"
                             % (cc_restore, cc_restore))


def _signal_handler(signum, _frame):
    sys.stderr.write("\n[signal] caught %s -> cleaning up and exiting\n"
                     % signal.Signals(signum).name)
    cleanup()
    # Re-raise default behaviour so exit code reflects the signal.
    sys.exit(128 + signum)


# --------------------------------------------------------------------------- #
# Small utilities
# --------------------------------------------------------------------------- #
def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def human_bytes(n: float) -> str:
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(n) < 1024.0:
            return "%.2f %s" % (n, unit)
        n /= 1024.0
    return "%.2f PiB" % n


def mbit(bytes_per_s: float) -> float:
    return bytes_per_s * 8.0 / 1e6


def parse_curl_w(text: str) -> dict:
    out: dict = {}
    for line in text.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    # numeric coercion where sensible
    for k in ("code", "redir"):
        if k in out:
            try:
                out[k] = int(out[k])
            except ValueError:
                pass
    for k in ("size", "speed", "time", "ttfb"):
        if k in out:
            try:
                out[k] = float(out[k])
            except ValueError:
                pass
    return out


def run_cmd(cmd: list[str], timeout: float, dry: bool, label: str = "") -> dict:
    """Run a subprocess, tracked for cleanup. Returns dict with rc/stdout/stderr.

    In dry-run: prints the command and returns a stub (nothing executed)."""
    printable = " ".join(cmd)
    if dry:
        print("  [DRY] %s%s" % ((label + ": ") if label else "", printable))
        return {"cmd": printable, "dry": True}
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         text=True)
    _register_proc(p)
    try:
        out, err = p.communicate(timeout=timeout)
        rc = p.returncode
    except subprocess.TimeoutExpired:
        p.kill()
        try:
            out, err = p.communicate(timeout=5)
        except Exception:
            out, err = "", ""
        rc = -9
    finally:
        _unregister_proc(p)
    return {"cmd": printable, "rc": rc, "stdout": out, "stderr": err}


def sysctl_get(key: str) -> str | None:
    try:
        r = subprocess.run(["sysctl", "-n", key], capture_output=True,
                           text=True, timeout=10)
        if r.returncode == 0:
            return r.stdout.strip()
    except Exception:
        pass
    # fallback: read the proc file directly
    proc_path = "/proc/sys/" + key.replace(".", "/")
    try:
        with open(proc_path) as fh:
            return fh.read().strip()
    except Exception:
        return None


def read_nic_counters(iface: str) -> dict:
    res = {}
    base = "/sys/class/net/%s/statistics" % iface
    for k in ("rx_bytes", "tx_bytes"):
        try:
            with open(os.path.join(base, k)) as fh:
                res[k] = int(fh.read().strip())
        except Exception:
            res[k] = None
    return res


def detect_egress_iface() -> str | None:
    try:
        r = subprocess.run(["ip", "route", "get", "1.1.1.1"],
                           capture_output=True, text=True, timeout=10)
        m = re.search(r"\bdev\s+(\S+)", r.stdout)
        if m:
            return m.group(1)
    except Exception:
        pass
    return None


def aria2_running() -> list[str]:
    """Return command lines of running aria2c processes (empty if none)."""
    try:
        r = subprocess.run(["pgrep", "-a", "aria2c"], capture_output=True,
                           text=True, timeout=10)
        if r.returncode == 0:
            return [ln for ln in r.stdout.splitlines() if ln.strip()]
    except Exception:
        pass
    return []


# --------------------------------------------------------------------------- #
# Canary URLs
# --------------------------------------------------------------------------- #
def cmb_name(i: int) -> str:
    return "dx12_v3_smica_cmb_mc_%05d_raw.fits" % i


def noise_name(i: int) -> str:
    return "dx12_v3_smica_noise_mc_%05d_raw.fits" % i


def url_for(filename: str, https: bool = False) -> str:
    scheme = "https" if https else "http"
    return "%s://%s%s%s" % (scheme, HOST, AIO_PATH, filename)


def build_canaries() -> dict:
    """Confirmed-present canaries + a cycle list for multi-file tests."""
    single = [cmb_name(0), cmb_name(969), cmb_name(971), noise_name(0)]
    # Cycle for concurrency tests: cmb ids 0..29 excluding the missing 970.
    cycle = [cmb_name(i) for i in range(0, 30) if i != MISSING_CMB_ID]
    missing = cmb_name(MISSING_CMB_ID)
    return {
        "single_files": single,
        "cycle_files": cycle,
        "missing_probe": missing,
        "http": {f: url_for(f, False) for f in single},
        "https": {f: url_for(f, True) for f in single},
    }


# --------------------------------------------------------------------------- #
# Header-dump parsing (for T3 / Experiment D)
# --------------------------------------------------------------------------- #
def parse_header_dump(text: str) -> list[dict]:
    """Split a curl -D dump into per-response blocks (handles redirect chains)."""
    blocks: list[dict] = []
    cur: dict | None = None
    for raw in text.splitlines():
        line = raw.rstrip("\r")
        if line.startswith("HTTP/"):
            if cur is not None:
                blocks.append(cur)
            code = None
            m = re.match(r"HTTP/[\d.]+\s+(\d+)", line)
            if m:
                code = int(m.group(1))
            cur = {"status": code, "status_line": line, "headers": {}}
        elif cur is not None and ":" in line:
            k, v = line.split(":", 1)
            cur["headers"][k.strip().lower()] = v.strip()
        # blank lines separate header block from body; ignored here
    if cur is not None:
        blocks.append(cur)
    return blocks


def classify_range(block: dict) -> str:
    if not block or block.get("status") is None:
        return "UNKNOWN"
    code = block["status"]
    hdr = block.get("headers", {})
    cr = hdr.get("content-range")
    if code == 206 and cr:
        return "RANGE_OK"
    if code == 200:
        return "RANGE_IGNORED"
    if 300 <= code < 400:
        return "REDIRECT"
    if code >= 400:
        return "ERROR_%d" % code
    return "UNKNOWN_%d" % code


# --------------------------------------------------------------------------- #
# Raw-socket congestion-control downloader (T5)
# --------------------------------------------------------------------------- #
TCP_CONGESTION = getattr(socket, "TCP_CONGESTION", 13)


def _parse_url(url: str) -> tuple[str, str, int, str]:
    m = re.match(r"^(https?)://([^/:]+)(?::(\d+))?(/.*)?$", url)
    if not m:
        raise ValueError("cannot parse URL: %s" % url)
    scheme = m.group(1)
    host = m.group(2)
    port = int(m.group(3)) if m.group(3) else (443 if scheme == "https" else 80)
    path = m.group(4) or "/"
    return scheme, host, port, path


def raw_socket_download(url: str, cc: str | None, duration: float,
                        allow_global: bool) -> dict:
    """Open a socket (optionally selecting per-socket CC), GET the URL following
    redirects manually, and discard body bytes for `duration` seconds.

    Returns {ok, bytes, seconds, mibps, cc_method, cc, error}.
    Never writes to disk. The requested body is streamed to nowhere (counted)."""
    global _GLOBAL_CC_RESTORE
    result = {"url": url, "cc": cc, "ok": False, "bytes": 0, "seconds": 0.0,
              "mibps": 0.0, "cc_method": "default", "error": None}

    scheme, host, port, path = _parse_url(url)
    redirects_left = 5
    sock = None
    try:
        while True:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(20.0)
            # Per-socket CC selection (surgical: touches only this socket).
            if cc:
                try:
                    sock.setsockopt(socket.IPPROTO_TCP, TCP_CONGESTION, cc.encode())
                    result["cc_method"] = "per-socket"
                except OSError as e:
                    if allow_global:
                        # Global fallback (opt-in). Capture + restore in cleanup.
                        cur = sysctl_get("net.ipv4.tcp_congestion_control")
                        if _GLOBAL_CC_RESTORE is None and cur and cur != cc:
                            _GLOBAL_CC_RESTORE = cur
                        gr = subprocess.run(
                            ["sysctl", "-w",
                             "net.ipv4.tcp_congestion_control=%s" % cc],
                            capture_output=True, text=True, timeout=10)
                        if gr.returncode != 0:
                            raise RuntimeError(
                                "per-socket CC failed (%s) and global set failed"
                                % e)
                        result["cc_method"] = "global"
                    else:
                        raise RuntimeError(
                            "per-socket CC selection failed: %s "
                            "(re-run with --allow-global-cc-change to force)" % e)

            sock.connect((host, port))
            stream = sock
            if scheme == "https":
                ctx = ssl.create_default_context()
                try:
                    stream = ctx.wrap_socket(sock, server_hostname=host)
                except ssl.SSLError as se:
                    # Benchmark bytes are discarded; fall back to unverified TLS
                    # so a cert quirk on a data node does not abort the test.
                    # Record the failure so an operator is never silently served
                    # an unverified connection (matters for honest H4 diagnosis).
                    result["tls_unverified_fallback"] = "%s: %s" % (type(se).__name__, se)
                    sys.stderr.write("[T5] TLS verify failed for %s (%s); retrying "
                                     "UNVERIFIED for the throughput probe only\n"
                                     % (host, se))
                    try:
                        sock.close()
                    except Exception:
                        pass
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(20.0)
                    if cc and result["cc_method"] == "per-socket":
                        try:
                            sock.setsockopt(socket.IPPROTO_TCP, TCP_CONGESTION, cc.encode())
                        except OSError:
                            pass
                    sock.connect((host, port))
                    ctx = ssl._create_unverified_context()
                    stream = ctx.wrap_socket(sock, server_hostname=host)

            req = ("GET %s HTTP/1.1\r\nHost: %s\r\nUser-Agent: %s\r\n"
                   "Referer: %s\r\nAccept: */*\r\nConnection: close\r\n\r\n"
                   % (path, host, BROWSER_UA, REFERER))
            stream.sendall(req.encode("ascii", "ignore"))

            # Read headers.
            buf = b""
            while b"\r\n\r\n" not in buf:
                chunk = stream.recv(4096)
                if not chunk:
                    break
                buf += chunk
                if len(buf) > 65536:
                    break
            header_bytes, _, body_start = buf.partition(b"\r\n\r\n")
            header_txt = header_bytes.decode("iso-8859-1", "replace")
            first_line = header_txt.split("\r\n", 1)[0]
            m = re.match(r"HTTP/[\d.]+\s+(\d+)", first_line)
            status = int(m.group(1)) if m else 0

            if 300 <= status < 400:
                loc = None
                for hl in header_txt.split("\r\n")[1:]:
                    if hl.lower().startswith("location:"):
                        loc = hl.split(":", 1)[1].strip()
                        break
                try:
                    stream.close()
                except Exception:
                    pass
                if not loc or redirects_left <= 0:
                    result["error"] = "redirect without Location / too many hops"
                    return result
                redirects_left -= 1
                if loc.startswith("/"):
                    loc = "%s://%s%s" % (scheme, host, loc)
                scheme, host, port, path = _parse_url(loc)
                continue

            if status != 200:
                result["error"] = "unexpected status %d" % status
                try:
                    stream.close()
                except Exception:
                    pass
                return result

            # 200 OK: measure body throughput. Count only body bytes.
            total = len(body_start)
            start = time.monotonic()
            while True:
                elapsed = time.monotonic() - start
                remaining = duration - elapsed
                if remaining <= 0.05:
                    break
                # Cap recv block at the remaining window (min 0.05s) so we never
                # overshoot `duration` by more than a rounding sliver. Throughput
                # is computed from measured elapsed regardless, so this only
                # tightens wall-time, not the reported rate.
                stream.settimeout(min(5.0, remaining))
                try:
                    chunk = stream.recv(65536)
                except socket.timeout:
                    break
                except OSError:
                    break
                if not chunk:
                    break
                total += len(chunk)
            elapsed = max(1e-6, time.monotonic() - start)
            result["ok"] = True
            result["bytes"] = total
            result["seconds"] = elapsed
            result["mibps"] = (total / elapsed) / (1024.0 * 1024.0)
            try:
                stream.close()
            except Exception:
                pass
            return result
    except Exception as e:  # noqa: BLE001 - report any socket/tls error
        result["error"] = "%s: %s" % (type(e).__name__, e)
        return result
    finally:
        try:
            if sock is not None:
                sock.close()
        except Exception:
            pass


# --------------------------------------------------------------------------- #
# Report accumulator
# --------------------------------------------------------------------------- #
class Report:
    def __init__(self):
        self.data = {"meta": {"tool": "pla_aio_download_diagnostics.py",
                              "started": now_iso()},
                     "tasks": {}}

    def set(self, key: str, value) -> None:
        self.data["tasks"][key] = value

    def write(self, dry: bool) -> None:
        if dry:
            return
        os.makedirs(DIAG_DIR, exist_ok=True)
        tmp = REPORT_JSON + ".tmp"
        with open(tmp, "w") as fh:
            json.dump(self.data, fh, indent=2, default=str)
        os.replace(tmp, REPORT_JSON)
        md = render_markdown(self.data)
        tmp_md = REPORT_MD + ".tmp"
        with open(tmp_md, "w") as fh:
            fh.write(md)
        os.replace(tmp_md, REPORT_MD)


# --------------------------------------------------------------------------- #
# TASKS
# --------------------------------------------------------------------------- #
def t1_environment(rep: Report, dry: bool) -> dict:
    print("\n== T1: environment discovery ==")
    iface = detect_egress_iface()
    running = aria2_running()
    env = {
        "timestamp": now_iso(),
        "hostname": socket.gethostname(),
        "kernel": " ".join(os.uname()),
        "user": os.environ.get("USER") or os.environ.get("LOGNAME") or str(os.getuid()),
        "e2e_root_exists": os.path.isdir(E2E_ROOT),
        "egress_iface": iface,
        "aria2c_running": running,
        "aria2c_is_running": bool(running),
    }
    # File counts (dir listing only; never reads final file contents).
    if not dry:
        env["cmb_present"] = len(glob.glob(os.path.join(CMB_DIR, "dx12_v3_smica_cmb_mc_*_raw.fits")))
        env["noise_present"] = len(glob.glob(os.path.join(NOISE_DIR, "dx12_v3_smica_noise_mc_*_raw.fits")))
        env["aria2_control_files"] = (
            len(glob.glob(os.path.join(CMB_DIR, "*.aria2")))
            + len(glob.glob(os.path.join(NOISE_DIR, "*.aria2"))))
    # df -h for scratch
    dfr = run_cmd(["df", "-h", "/mnt/sn850x2t"], timeout=15, dry=dry)
    env["df"] = dfr.get("stdout", "").strip() if not dry else "(dry)"
    # NIC counters
    env["nic_iface"] = iface
    env["nic_start"] = read_nic_counters(iface) if (iface and not dry) else {}
    # Congestion-control + buffers (for H1/H6 interpretation)
    env["tcp_congestion_control"] = sysctl_get("net.ipv4.tcp_congestion_control")
    env["tcp_available_congestion_control"] = sysctl_get(
        "net.ipv4.tcp_available_congestion_control")
    env["core_rmem_max"] = sysctl_get("net.core.rmem_max")
    env["tcp_rmem"] = sysctl_get("net.ipv4.tcp_rmem")
    avail = (env["tcp_available_congestion_control"] or "").split()
    env["bbr_available"] = "bbr" in avail

    print("  host=%s iface=%s cc=%s bbr_available=%s aria2c_running=%s"
          % (env["hostname"], iface, env["tcp_congestion_control"],
             env["bbr_available"], env["aria2c_is_running"]))
    if not dry:
        print("  final files: cmb=%s noise=%s aria2ctrl=%s"
              % (env.get("cmb_present"), env.get("noise_present"),
                 env.get("aria2_control_files")))
    if env["aria2c_is_running"]:
        print("  ! aria2c RUNNING -> final dirs treated read-only; heavy "
              "bandwidth tests skipped unless --allow-bench-during-download")
    rep.set("T1_environment", env)
    rep.write(dry)
    return env


def t2_canaries(rep: Report, dry: bool) -> dict:
    print("\n== T2: canary URL generation ==")
    can = build_canaries()
    print("  single canaries: %d  cycle list: %d  missing probe: %s"
          % (len(can["single_files"]), len(can["cycle_files"]),
             can["missing_probe"]))
    rep.set("T2_canaries", can)
    rep.write(dry)
    return can


def t3_headers_range(rep: Report, canaries: dict, dry: bool) -> dict:
    print("\n== T3: header / Range diagnostics (+ Experiment D backend re-test) ==")
    results = []
    # Test the first CMB canary over http and https, plus a noise canary.
    targets = [
        ("http", canaries["single_files"][0]),
        ("https", canaries["single_files"][0]),
        ("http", canaries["single_files"][3]),  # noise
    ]
    servlet_range_seen = set()
    backend_range_seen = set()
    backend_urls = set()
    for scheme, fname in targets:
        url = url_for(fname, https=(scheme == "https"))
        dump_fd, dump_path = (None, None)
        if not dry:
            dump_fd, dump_path = tempfile.mkstemp(prefix="pla_hdr_", suffix=".txt")
            os.close(dump_fd)
        cmd = ["curl", "-sS", "-L", "-r", "0-0",
               "-D", (dump_path if dump_path else "/dev/stderr"),
               "-o", "/dev/null", "--max-time", "20",
               "-A", BROWSER_UA, "-H", "Referer: %s" % REFERER,
               "-w", CURL_W, url]
        r = run_cmd(cmd, timeout=40, dry=dry, label="T3 %s" % scheme)
        entry = {"scheme": scheme, "file": fname, "url": url, "cmd": " ".join(cmd)}
        if dry:
            results.append(entry)
            continue
        w = parse_curl_w(r.get("stdout", ""))
        entry.update(w)
        dump_txt = ""
        try:
            with open(dump_path) as fh:
                dump_txt = fh.read()
        finally:
            try:
                os.unlink(dump_path)
            except Exception:
                pass
        blocks = parse_header_dump(dump_txt)
        servlet_block = blocks[0] if blocks else {}
        final_block = blocks[-1] if blocks else {}
        entry["num_response_blocks"] = len(blocks)
        entry["servlet_status"] = servlet_block.get("status")
        entry["servlet_range"] = classify_range(servlet_block)
        entry["backend_status"] = final_block.get("status")
        entry["backend_range"] = classify_range(final_block)
        entry["accept_ranges_servlet"] = servlet_block.get("headers", {}).get("accept-ranges")
        entry["accept_ranges_backend"] = final_block.get("headers", {}).get("accept-ranges")
        entry["content_type"] = final_block.get("headers", {}).get("content-type")
        entry["content_length"] = final_block.get("headers", {}).get("content-length")
        entry["content_range"] = final_block.get("headers", {}).get("content-range")
        entry["url_effective"] = w.get("effurl")
        entry["num_redirects"] = w.get("redir")
        entry["bytes_downloaded"] = w.get("size")
        entry["redirected"] = bool(w.get("redir"))
        if entry["redirected"] and entry.get("url_effective"):
            backend_urls.add(entry["url_effective"])
        servlet_range_seen.add(entry["servlet_range"])
        backend_range_seen.add(entry["backend_range"])
        print("  %-5s %s: servlet=%s(%s) backend=%s(%s) redirects=%s eff=%s"
              % (scheme, fname[:34], entry["servlet_status"], entry["servlet_range"],
                 entry["backend_status"], entry["backend_range"],
                 entry["num_redirects"], (entry.get("url_effective") or "")[:60]))
        results.append(entry)

    summary = {
        "servlet_range_verdicts": sorted(servlet_range_seen),
        "backend_range_verdicts": sorted(backend_range_seen),
        "backend_urls": sorted(backend_urls),
        "servlet_supports_range": "RANGE_OK" in servlet_range_seen,
        "backend_supports_range": "RANGE_OK" in backend_range_seen,
        "any_range_supported": ("RANGE_OK" in servlet_range_seen
                                or "RANGE_OK" in backend_range_seen),
    }
    out = {"results": results, "summary": summary}
    if not dry:
        print("  => servlet Range=%s  backend Range=%s"
              % (summary["servlet_supports_range"],
                 summary["backend_supports_range"]))
        if summary["backend_supports_range"] and not summary["servlet_supports_range"]:
            print("  *** EXPERIMENT D HIT: backend node supports Range though the "
                  "servlet does not -> aria2 split>1 against backend URL unlocks. ***")
    rep.set("T3_headers_range", out)
    rep.write(dry)
    return out


def _single_stream_run(url, extra_headers, duration, dry, label):
    cmd = ["curl", "-sS", "-L", "-o", "/dev/null",
           "--max-time", str(int(duration))]
    for h in extra_headers:
        cmd += ["-H", h]
    cmd += ["-w", CURL_W, url]
    r = run_cmd(cmd, timeout=duration + 25, dry=dry, label=label)
    if dry:
        return {"cmd": " ".join(cmd), "dry": True}
    w = parse_curl_w(r.get("stdout", ""))
    w["cmd"] = " ".join(cmd)
    w["mbit"] = mbit(w.get("speed", 0.0))
    w["mibps"] = w.get("speed", 0.0) / (1024.0 * 1024.0)
    return w


def t4_single_stream(rep: Report, canaries: dict, duration: float, dry: bool) -> dict:
    print("\n== T4: single-stream benchmark (+ Experiment C TTFB) ==")
    # >=2 canary files to reduce single-file noise.
    files = [canaries["single_files"][0], canaries["single_files"][1]]
    variants = [
        ("A_http_default", "http", []),
        ("B_http_ua", "http", ["User-Agent: %s" % BROWSER_UA]),
        ("C_http_ua_referer", "http",
         ["User-Agent: %s" % BROWSER_UA, "Referer: %s" % REFERER]),
        ("D_https_ua_referer", "https",
         ["User-Agent: %s" % BROWSER_UA, "Referer: %s" % REFERER]),
    ]
    runs = []
    for fname in files:
        for name, scheme, headers in variants:
            url = url_for(fname, https=(scheme == "https"))
            w = _single_stream_run(url, headers, duration, dry, "T4 %s" % name)
            entry = {"variant": name, "file": fname, "scheme": scheme, "url": url}
            entry.update(w if isinstance(w, dict) else {})
            if not dry:
                print("  %-20s %s: %.3f MiB/s (%.2f Mbit/s) code=%s ttfb=%.3fs"
                      % (name, fname[-14:], entry.get("mibps", 0.0),
                         entry.get("mbit", 0.0), entry.get("code"),
                         entry.get("ttfb", 0.0)))
            runs.append(entry)
    valid = [r for r in runs if not dry and r.get("code") == 200 and r.get("size", 0) > 0]
    ttfbs = [r["ttfb"] for r in valid if "ttfb" in r]
    speeds = [r["mibps"] for r in valid]
    summ = {}
    if valid:
        summ = {
            "best_mibps": max(speeds),
            "median_mibps": sorted(speeds)[len(speeds) // 2],
            "ttfb_min": min(ttfbs) if ttfbs else None,
            "ttfb_max": max(ttfbs) if ttfbs else None,
            "ttfb_mean": (sum(ttfbs) / len(ttfbs)) if ttfbs else None,
            "ttfb_variable": (bool(ttfbs) and (max(ttfbs) - min(ttfbs) > 2.0)),
        }
        if summ["ttfb_variable"] or (ttfbs and max(ttfbs) > 5.0):
            print("  ! high/variable TTFB (min=%.2fs max=%.2fs) -> possible H4 "
                  "(backend retrieval-bound)" % (min(ttfbs), max(ttfbs)))
    out = {"runs": runs, "summary": summ}
    rep.set("T4_single_stream", out)
    rep.write(dry)
    return out


def t5_congestion_control(rep: Report, canaries: dict, env: dict,
                          duration: float, test_bbr: bool,
                          allow_global: bool, dry: bool) -> dict:
    print("\n== T5: congestion control CUBIC vs BBR (raw socket, per-socket) ==")
    url = url_for(canaries["single_files"][0], https=False)
    current_cc = env.get("tcp_congestion_control") or "cubic"
    bbr_available = env.get("bbr_available", False)
    out = {"url": url, "current_cc": current_cc, "bbr_available": bbr_available,
           "test_bbr": test_bbr, "runs": {}, "ratio": None, "notes": []}

    if dry:
        print("  [DRY] would raw-socket GET %s under cc=%s%s"
              % (url, current_cc, " and cc=bbr" if (test_bbr and bbr_available) else ""))
        rep.set("T5_congestion_control", out)
        return out

    # Baseline under current CC.
    base = raw_socket_download(url, current_cc, duration, allow_global)
    out["runs"][current_cc] = base
    if base["ok"]:
        print("  cc=%-6s %.3f MiB/s (%s, %s)"
              % (current_cc, base["mibps"], human_bytes(base["bytes"]),
                 base["cc_method"]))
    else:
        print("  cc=%-6s FAILED: %s" % (current_cc, base["error"]))

    if test_bbr and bbr_available:
        bbr = raw_socket_download(url, "bbr", duration, allow_global)
        out["runs"]["bbr"] = bbr
        if bbr["ok"]:
            print("  cc=%-6s %.3f MiB/s (%s, %s)"
                  % ("bbr", bbr["mibps"], human_bytes(bbr["bytes"]), bbr["cc_method"]))
            if base["ok"] and base["mibps"] > 0:
                out["ratio"] = bbr["mibps"] / base["mibps"]
                print("  => BBR/%s throughput ratio = %.2fx" % (current_cc, out["ratio"]))
        else:
            print("  cc=bbr FAILED: %s" % bbr["error"])
            out["notes"].append("BBR run failed: %s" % bbr["error"])
    elif test_bbr and not bbr_available:
        note = ("BBR test skipped -- this is the HIGHEST-VALUE experiment; "
                "re-run after `sudo modprobe tcp_bbr` (then set --test-bbr).")
        out["notes"].append(note)
        print("  ! " + note)
    else:
        out["notes"].append("BBR test disabled via --no-test-bbr.")

    rep.set("T5_congestion_control", out)
    rep.write(dry)
    return out


def _parallel_curl(urls, duration, dry, iface, label):
    """Launch len(urls) concurrent curls to /dev/null; return aggregate stats."""
    if dry:
        for u in urls:
            print("  [DRY] curl -sS -L -o /dev/null --max-time %d ... %s"
                  % (int(duration), u))
        return {"dry": True, "n": len(urls)}
    nic_before = read_nic_counters(iface) if iface else {}
    procs = []
    handles = []
    tmp_outs = []
    t0 = time.monotonic()
    try:
        for u in urls:
            fd, path = tempfile.mkstemp(prefix="pla_w_", suffix=".txt")
            os.close(fd)
            tmp_outs.append(path)
            cmd = ["curl", "-sS", "-L", "-o", "/dev/null",
                   "--max-time", str(int(duration)),
                   "-A", BROWSER_UA, "-H", "Referer: %s" % REFERER,
                   "-w", CURL_W, u]
            fh = open(path, "w")
            handles.append(fh)
            p = subprocess.Popen(cmd, stdout=fh, stderr=subprocess.DEVNULL, text=True)
            _register_proc(p)
            procs.append(p)
        for p in procs:
            try:
                p.wait(timeout=duration + 30)
            except subprocess.TimeoutExpired:
                p.kill()
            _unregister_proc(p)
    finally:
        # Guaranteed: reap + close every parent-side fd even if a spawn/wait
        # raises mid-loop (child keeps its own dup of stdout).
        for p in procs:
            if p.poll() is None:
                try:
                    p.kill()
                    p.wait(timeout=5)
                except Exception:
                    pass
            _unregister_proc(p)
        for fh in handles:
            try:
                fh.close()
            except Exception:
                pass
    wall = max(1e-6, time.monotonic() - t0)
    nic_after = read_nic_counters(iface) if iface else {}
    total_size = 0.0
    per_conn = []
    for path in tmp_outs:
        try:
            with open(path) as fh:
                w = parse_curl_w(fh.read())
            sz = w.get("size", 0.0) or 0.0
            total_size += sz
            per_conn.append({"code": w.get("code"), "size": sz,
                             "mibps": (w.get("speed", 0.0) or 0.0) / (1024.0 * 1024.0)})
        except Exception:
            pass
        finally:
            try:
                os.unlink(path)
            except Exception:
                pass
    nic_delta = None
    if nic_before.get("rx_bytes") is not None and nic_after.get("rx_bytes") is not None:
        nic_delta = nic_after["rx_bytes"] - nic_before["rx_bytes"]
    agg_mibps_curl = (total_size / wall) / (1024.0 * 1024.0)
    agg_mibps_nic = ((nic_delta / wall) / (1024.0 * 1024.0)) if nic_delta else None
    return {
        "n": len(urls), "wall_s": wall,
        "curl_total_bytes": total_size,
        "nic_rx_delta_bytes": nic_delta,
        "agg_mibps_curl": agg_mibps_curl,
        "agg_mbit_curl": mbit(total_size / wall),
        "agg_mibps_nic": agg_mibps_nic,
        "per_conn_avg_mibps": agg_mibps_curl / len(urls) if urls else 0.0,
        "per_conn": per_conn,
    }


def t6_reference_hosts(rep: Report, hosts: list[str], duration: float,
                       iface: str | None, dry: bool) -> dict:
    print("\n== T6: reference-host control group (isolates client vs ESAC) ==")
    out = {"hosts": hosts, "single": [], "parallel4": []}
    for h in hosts:
        print("  reference single-stream: %s" % h)
        s = _parallel_curl([h], duration, dry, iface, "T6 single")
        if not dry:
            s["host"] = h
            out["single"].append(s)
            print("    single: %.3f MiB/s (%.2f Mbit/s)"
                  % (s.get("agg_mibps_curl", 0.0), s.get("agg_mbit_curl", 0.0)))
        print("  reference parallel N=4: %s" % h)
        pth = _parallel_curl([h] * 4, duration, dry, iface, "T6 parallel4")
        if not dry:
            pth["host"] = h
            out["parallel4"].append(pth)
            print("    N=4:    %.3f MiB/s (%.2f Mbit/s)  per-conn %.3f MiB/s"
                  % (pth.get("agg_mibps_curl", 0.0), pth.get("agg_mbit_curl", 0.0),
                     pth.get("per_conn_avg_mibps", 0.0)))
    if not dry and out["single"]:
        out["best_single_mibps"] = max(s.get("agg_mibps_curl", 0.0) for s in out["single"])
        out["best_parallel4_mibps"] = (max(p.get("agg_mibps_curl", 0.0)
                                       for p in out["parallel4"]) if out["parallel4"] else 0.0)
    rep.set("T6_reference_hosts", out)
    rep.write(dry)
    return out


def t7_concurrency_sweep(rep: Report, canaries: dict, duration: float,
                         iface: str | None, dry: bool) -> dict:
    print("\n== T7: concurrency sweep (+ per-connection average) ==")
    levels = [1, 2, 3, 4, 6, 8, 10]
    cycle = canaries["cycle_files"]
    results = []
    for n in levels:
        urls = [url_for(cycle[i % len(cycle)], https=False) for i in range(n)]
        print("  N=%d ..." % n)
        r = _parallel_curl(urls, duration, dry, iface, "T7 N=%d" % n)
        if not dry:
            r["level"] = n
            results.append(r)
            print("    N=%2d: agg %.3f MiB/s (%.2f Mbit/s) | per-conn %.3f MiB/s | "
                  "nic %s"
                  % (n, r.get("agg_mibps_curl", 0.0), r.get("agg_mbit_curl", 0.0),
                     r.get("per_conn_avg_mibps", 0.0),
                     (human_bytes(r["nic_rx_delta_bytes"]) + "/win")
                     if r.get("nic_rx_delta_bytes") else "n/a"))
    summary = {}
    if not dry and results:
        aggs = [(r["level"], r["agg_mibps_curl"]) for r in results]
        per_conns = [(r["level"], r["per_conn_avg_mibps"]) for r in results]
        best_level, best_agg = max(aggs, key=lambda x: x[1])
        summary["best_level"] = best_level
        summary["best_agg_mibps"] = best_agg
        summary["aggregate_by_level"] = dict(aggs)
        summary["per_conn_by_level"] = dict(per_conns)
        # classification signatures
        agg1 = dict(aggs).get(1, 0.0) or 1e-9
        agg_max = best_agg
        pc1 = dict(per_conns).get(1, 0.0) or 1e-9
        pc_high = dict(per_conns).get(max(l for l, _ in aggs), 0.0)
        summary["aggregate_scaling_factor"] = agg_max / agg1
        summary["per_conn_retention_high_N"] = pc_high / pc1
        # trend judgement
        if agg_max <= agg1 * 1.15:
            summary["trend"] = "flat_aggregate"      # H2 candidate (per-IP cap)
        elif summary["per_conn_retention_high_N"] > 0.75 and summary["aggregate_scaling_factor"] > 1.8:
            summary["trend"] = "linear_scale_out"     # H3 candidate (per-stream cap)
        else:
            summary["trend"] = "per_conn_decays"      # H1 / self-congestion
        print("  => best N=%d (%.3f MiB/s); trend=%s; agg-scale=%.2fx; "
              "per-conn retention@maxN=%.2f"
              % (best_level, best_agg, summary["trend"],
                 summary["aggregate_scaling_factor"],
                 summary["per_conn_retention_high_N"]))
    out = {"results": results, "summary": summary}
    rep.set("T7_concurrency_sweep", out)
    rep.write(dry)
    return out


def t8_aria2_microbench(rep: Report, canaries: dict, t3: dict,
                        env: dict, allow_bench: bool, dry: bool) -> dict:
    print("\n== T8: aria2 micro-benchmark (gated, temp dir only) ==")
    out = {"skipped": False, "reason": None, "runs": []}
    if not shutil.which("aria2c"):
        out["skipped"] = True
        out["reason"] = "aria2c not installed"
        print("  skipped: aria2c not installed")
        rep.set("T8_aria2_microbench", out)
        rep.write(dry)
        return out
    if env.get("aria2c_is_running") and not allow_bench:
        out["skipped"] = True
        out["reason"] = ("aria2c already running -- skipped to avoid confounding "
                         "the production download + doubling load on ESAC "
                         "(override: --allow-bench-during-download)")
        print("  skipped: " + out["reason"])
        rep.set("T8_aria2_microbench", out)
        rep.write(dry)
        return out

    tmp_dir = os.path.join(DIAG_DIR, "tmp_aria2")
    if not dry:
        os.makedirs(tmp_dir, exist_ok=True)
        # Register BEFORE any loop work so that even if a config below raises,
        # atexit/signal cleanup() removes this dir (guaranteed net; the explicit
        # rmtree at the end is only the prompt happy-path cleanup).
        _register_temp(tmp_dir)

    range_ok = t3.get("summary", {}).get("any_range_supported", False)
    backend_range = t3.get("summary", {}).get("backend_supports_range", False)
    backend_urls = t3.get("summary", {}).get("backend_urls", [])
    # Base configs (single connection per file).
    configs = [(1, 1), (2, 1), (4, 1), (6, 1)]
    if range_ok:
        configs += [(2, 2), (4, 2)]

    # If only the backend supports Range, point split jobs at the backend URL.
    for (j, s) in configs:
        use_backend = (s > 1 and backend_range and not
                       t3.get("summary", {}).get("servlet_supports_range", False)
                       and backend_urls)
        # Build a small input list (j distinct files).
        if not dry:
            for f in glob.glob(os.path.join(tmp_dir, "*")):
                try:
                    os.remove(f)
                except Exception:
                    pass
        # aria2 input-file format: URI line + indented `out=` so concurrent
        # jobs write distinct filenames (the servlet path has no basename).
        inputs = []
        for i in range(j):
            fname = canaries["cycle_files"][i % len(canaries["cycle_files"])]
            if use_backend:
                uri = backend_urls[i % len(backend_urls)]
            else:
                uri = url_for(fname, https=False)
            inputs.append("%s\n  out=bench_%02d_%s" % (uri, i, fname))
        input_file = os.path.join(tmp_dir, "in.txt")
        if not dry:
            with open(input_file, "w") as fh:
                fh.write("\n".join(inputs) + "\n")
        cmd = ["aria2c", "--no-conf=true", "--input-file", input_file,
               "--dir", tmp_dir,
               "--max-concurrent-downloads=%d" % j,
               "--split=%d" % s,
               "--max-connection-per-server=%d" % s,
               "--max-overall-download-limit=0", "--max-download-limit=0",
               "--auto-file-renaming=false", "--allow-overwrite=true",
               "--file-allocation=none",
               "--user-agent=%s" % BROWSER_UA,
               "--header=Referer: %s" % REFERER,
               "--stop=120", "--summary-interval=0", "--console-log-level=warn"]
        print("  aria2 j=%d s=%d%s ..." % (j, s, " (backend URL)" if use_backend else ""))
        nic_before = read_nic_counters(env.get("nic_iface")) if (env.get("nic_iface") and not dry) else {}
        t0 = time.monotonic()
        r = run_cmd(cmd, timeout=140, dry=dry, label="T8 j%d s%d" % (j, s))
        wall = time.monotonic() - t0
        entry = {"jobs": j, "split": s, "backend": use_backend, "cmd": " ".join(cmd)}
        if not dry:
            nic_after = read_nic_counters(env.get("nic_iface")) if env.get("nic_iface") else {}
            downloaded = 0
            for f in glob.glob(os.path.join(tmp_dir, "*")):
                if f.endswith(".txt"):
                    continue
                try:
                    downloaded += os.path.getsize(f)
                except Exception:
                    pass
            entry["wall_s"] = wall
            entry["bytes_on_disk"] = downloaded
            entry["mibps"] = (downloaded / max(1e-6, wall)) / (1024.0 * 1024.0)
            entry["mbit"] = mbit(downloaded / max(1e-6, wall))
            if nic_before.get("rx_bytes") and nic_after.get("rx_bytes"):
                entry["nic_rx_delta"] = nic_after["rx_bytes"] - nic_before["rx_bytes"]
            print("    j=%d s=%d: %.3f MiB/s (%.2f Mbit/s)"
                  % (j, s, entry["mibps"], entry["mbit"]))
            # clean the downloaded blobs immediately (temp dir)
            for f in glob.glob(os.path.join(tmp_dir, "*")):
                if f.endswith(".txt"):
                    continue
                try:
                    os.remove(f)
                except Exception:
                    pass
        out["runs"].append(entry)

    if not dry:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        with _LOCK:
            _TEMP_DIRS.discard(tmp_dir)
        if out["runs"]:
            best = max(out["runs"], key=lambda e: e.get("mibps", 0.0))
            out["best"] = {"jobs": best["jobs"], "split": best["split"],
                           "mibps": best.get("mibps", 0.0)}
    rep.set("T8_aria2_microbench", out)
    rep.write(dry)
    return out


ERR_MARKERS = [r"\[ERROR\]", r"\[WARN\]", r"errorCode=", r"Exception:",
               r"Download aborted", r"\b403\b", r"\b404\b", r"\b429\b",
               r"\b503\b", r"timeout", r"reset"]


def t9_log_analysis(rep: Report, dry: bool) -> dict:
    print("\n== T9: aria2 log analysis ==")
    out = {"logs": [], "counts": {}, "samples": []}
    if dry:
        print("  [DRY] would grep %s/*.log for error markers" % LOGS_DIR)
        rep.set("T9_log_analysis", out)
        return out
    log_files = sorted(glob.glob(os.path.join(LOGS_DIR, "*.log")))
    counts: dict = {m: 0 for m in ERR_MARKERS}
    have_grep = shutil.which("grep") is not None
    for lf in log_files:
        size = os.path.getsize(lf)
        out["logs"].append({"file": os.path.basename(lf), "bytes": size})
        for m in ERR_MARKERS:
            n = 0
            if have_grep:
                # -a: treat binary as text; -c: count; -E: extended regex.
                # Exclude the DEBUG false-positive "err:0".
                r = subprocess.run(["grep", "-aEc", m, lf],
                                   capture_output=True, text=True, timeout=180)
                try:
                    n = int((r.stdout or "0").strip() or "0")
                except ValueError:
                    n = 0
            counts[m] += n
        # Collect a few real error samples (bounded), excluding err:0.
        if have_grep and len(out["samples"]) < 20:
            r = subprocess.run(
                ["grep", "-aE", r"\[ERROR\]|errorCode=|Download aborted", lf],
                capture_output=True, text=True, timeout=180)
            for ln in (r.stdout or "").splitlines():
                if "err:0" in ln:
                    continue
                if len(out["samples"]) >= 20:
                    break
                out["samples"].append("%s: %s" % (os.path.basename(lf), ln.strip()[:200]))
    out["counts"] = {k: v for k, v in counts.items() if v}
    print("  scanned %d logs; error-marker counts: %s"
          % (len(log_files), out["counts"] or "none"))
    rep.set("T9_log_analysis", out)
    rep.write(dry)
    return out


# --------------------------------------------------------------------------- #
# T10 recommendation engine (ownership-driven)
# --------------------------------------------------------------------------- #
def t10_recommend(rep: Report, env, t3, t4, t5, t6, t7, t8, dry: bool) -> dict:
    print("\n== T10: recommendation engine (ownership-driven) ==")
    signals = {}
    hypotheses = []  # (id, name, confidence, evidence)

    # --- gather signals -----------------------------------------------------
    bbr_ratio = (t5 or {}).get("ratio")
    signals["bbr_ratio"] = bbr_ratio
    signals["bbr_available"] = env.get("bbr_available")

    t4s = (t4 or {}).get("summary", {})
    signals["single_best_mibps"] = t4s.get("best_mibps")
    signals["ttfb_max"] = t4s.get("ttfb_max")
    signals["ttfb_variable"] = t4s.get("ttfb_variable")

    t7s = (t7 or {}).get("summary", {})
    signals["conc_trend"] = t7s.get("trend")
    signals["conc_best_level"] = t7s.get("best_level")
    signals["conc_best_agg_mibps"] = t7s.get("best_agg_mibps")
    signals["agg_scale"] = t7s.get("aggregate_scaling_factor")
    signals["per_conn_retention"] = t7s.get("per_conn_retention_high_N")

    ref_single = (t6 or {}).get("best_single_mibps")
    ref_par = (t6 or {}).get("best_parallel4_mibps")
    signals["ref_single_mibps"] = ref_single
    signals["ref_parallel4_mibps"] = ref_par

    backend_range = t3.get("summary", {}).get("backend_supports_range", False)
    servlet_range = t3.get("summary", {}).get("servlet_supports_range", False)
    any_range = t3.get("summary", {}).get("any_range_supported", False)
    signals["servlet_range"] = servlet_range
    signals["backend_range"] = backend_range

    pla_single = signals["single_best_mibps"] or 0.0

    # --- score hypotheses ---------------------------------------------------
    # Experiment D (dominant if it hits): static Range-capable backend.
    if backend_range and not servlet_range:
        hypotheses.append(("ExpD", "Backend node supports Range (servlet does not)",
                           0.95,
                           "T3 backend classified RANGE_OK on url_effective; "
                           "aria2 split>1 against the backend URL is a distinct "
                           "acceleration path."))

    # H1 loss-limited CUBIC: BBR raises single-stream ~2-3x.
    if bbr_ratio is not None:
        if bbr_ratio >= 1.8:
            hypotheses.append(("H1", "Loss-limited TCP (CUBIC collapses on LFN)",
                               0.9,
                               "T5 BBR/%s single-stream ratio = %.2fx (>=1.8)."
                               % (env.get("tcp_congestion_control"), bbr_ratio)))
        elif bbr_ratio <= 1.2:
            signals["bbr_no_effect"] = True

    # H6 client receive buffer.
    try:
        rmem_max = int((env.get("core_rmem_max") or "0"))
    except ValueError:
        rmem_max = 0
    tcp_rmem_fields = (env.get("tcp_rmem") or "").split()
    tcp_rmem_max = int(tcp_rmem_fields[-1]) if tcp_rmem_fields and tcp_rmem_fields[-1].isdigit() else 0
    signals["core_rmem_max"] = rmem_max
    signals["tcp_rmem_max"] = tcp_rmem_max
    # BDP for ~300ms RTT at 100 Mbit/s ~ 3.75 MB. If autotune ceiling < that, H6.
    if tcp_rmem_max and tcp_rmem_max < 4 * 1024 * 1024:
        hypotheses.append(("H6", "Client receive buffer too small",
                           0.6,
                           "tcp_rmem max=%s (< ~3.75 MB BDP for 300ms/100Mbit); "
                           "raising net.ipv4.tcp_rmem may lift single-stream."
                           % human_bytes(tcp_rmem_max)))
    else:
        signals["tcp_rmem_ample"] = True

    # H3 server per-stream throttle: single capped, BBR no effect, aggregate ~linear.
    if signals.get("conc_trend") == "linear_scale_out":
        conf = 0.85 if signals.get("bbr_no_effect") else 0.7
        hypotheses.append(("H3", "Server per-stream throttle",
                           conf,
                           "T7 aggregate scales %.2fx with per-conn retention %.2f "
                           "at high N -> per-stream cap; scale-out works."
                           % (signals.get("agg_scale") or 0.0,
                              signals.get("per_conn_retention") or 0.0)))

    # H2 server per-IP aggregate cap: aggregate fixed regardless of N (and CC).
    if signals.get("conc_trend") == "flat_aggregate":
        hypotheses.append(("H2", "Server per-IP aggregate cap",
                           0.8,
                           "T7 aggregate flat across N (scale=%.2fx); a fixed per-IP "
                           "ceiling. Use minimum N that reaches it."
                           % (signals.get("agg_scale") or 0.0)))

    # H4 backend retrieval-bound: high/variable TTFB, weak concurrency effect.
    if signals.get("ttfb_variable") or (signals.get("ttfb_max") or 0) > 5.0:
        weak_conc = (signals.get("agg_scale") or 0.0) < 1.5
        conf = 0.75 if weak_conc else 0.5
        hypotheses.append(("H4", "Server backend I/O / retrieval-bound",
                           conf,
                           "T4 TTFB max=%.2fs (variable=%s); concurrency effect %s."
                           % (signals.get("ttfb_max") or 0.0,
                              signals.get("ttfb_variable"),
                              "weak" if weak_conc else "present")))

    # Client-vs-server discriminator via reference hosts (T6).
    if ref_single is not None and pla_single > 0:
        if ref_single > pla_single * 2.0:
            hypotheses.append(("SERVER", "ESAC-specific slowness (reference host fast)",
                               0.7,
                               "T6 reference single-stream %.2f MiB/s >> PLA %.2f MiB/s "
                               "-> bottleneck is ESAC server/path, not the client link."
                               % (ref_single, pla_single)))
        elif ref_single < pla_single * 1.3:
            hypotheses.append(("CLIENT", "Client uplink/path limited (reference also slow)",
                               0.7,
                               "T6 reference single-stream %.2f MiB/s ~ PLA %.2f MiB/s "
                               "-> your link/path is the limit (BBR + rmem are levers)."
                               % (ref_single, pla_single)))

    # H5 path/peering: only assessable with time-of-day sampling.
    signals["h5_note"] = ("Time-of-day variance (H5) not sampled in a single run; "
                          "re-run at different hours to test for peering congestion.")

    # --- pick the leading hypothesis ---------------------------------------
    hypotheses.sort(key=lambda h: h[2], reverse=True)
    leading = hypotheses[0] if hypotheses else (
        "INCONCLUSIVE", "Insufficient signal", 0.0,
        "Not enough successful measurements to attribute ownership.")

    # --- informational ETA --------------------------------------------------
    best_sustained = 0.0
    for cand in (signals.get("conc_best_agg_mibps"), (t8 or {}).get("best", {}).get("mibps"),
                 signals.get("single_best_mibps")):
        if cand and cand > best_sustained:
            best_sustained = cand
    total_bytes = N_FILES_TOTAL * FILE_SIZE_MIB * 1024 * 1024
    remaining_files = N_FILES_TOTAL - (env.get("cmb_present", 0) + env.get("noise_present", 0))
    remaining_files = max(0, remaining_files)
    remaining_bytes = remaining_files * FILE_SIZE_MIB * 1024 * 1024
    eta = {}
    if best_sustained > 0:
        rate = best_sustained * 1024 * 1024  # bytes/s
        eta = {
            "best_sustained_mibps": best_sustained,
            "full_set_hours": total_bytes / rate / 3600.0,
            "remaining_files": remaining_files,
            "remaining_hours": remaining_bytes / rate / 3600.0,
        }

    # --- build the production command ---------------------------------------
    prod = build_production_command(t3, t7, signals)

    # --- warnings -----------------------------------------------------------
    warnings = []
    if best_sustained and best_sustained < 3.0:
        warnings.append("Best sustained throughput %.2f MiB/s < 3 MiB/s -> the "
                        "bottleneck is REMOTE server/path throttling, NOT the "
                        "NVMe scratch disk (local writes far exceed this)."
                        % best_sustained)
    if not any_range:
        warnings.append("Range unsupported on BOTH servlet and backend -> do NOT "
                        "use aria2 `split > 1` (it cannot help and may hurt). "
                        "Parallelism must come from concurrent whole-file jobs.")
    warnings.append("Good-citizen: keep sustained concurrency <= %d against this "
                    "public ESA archive; avoid retry storms." % PROD_MAX_CONCURRENCY)
    if not env.get("bbr_available"):
        warnings.append("BBR unavailable in this kernel (%s). The single highest-"
                        "value lever is untested: `sudo modprobe tcp_bbr` then "
                        "re-run with --test-bbr." % (env.get("tcp_available_congestion_control")))

    out = {
        "signals": signals,
        "ranked_hypotheses": [
            {"id": h[0], "name": h[1], "confidence": h[2], "evidence": h[3]}
            for h in hypotheses],
        "leading_hypothesis": {"id": leading[0], "name": leading[1],
                               "confidence": leading[2], "evidence": leading[3]},
        "eta": eta,
        "warnings": warnings,
        "production_command": prod,
    }
    print("  LEADING HYPOTHESIS: [%s] %s (conf %.2f)"
          % (leading[0], leading[1], leading[2]))
    print("  evidence: %s" % leading[3])
    if eta:
        print("  informational ETA @ %.2f MiB/s: full set ~%.1f h, remaining ~%.1f h"
              % (eta["best_sustained_mibps"], eta["full_set_hours"], eta["remaining_hours"]))
    for w in warnings:
        print("  ! %s" % w)
    rep.set("T10_recommendation", out)
    rep.write(dry)
    return out


def build_production_command(t3, t7, signals) -> dict:
    """Emit a single concrete, restart-robust aria2 production command."""
    servlet_range = t3.get("summary", {}).get("servlet_supports_range", False)
    backend_range = t3.get("summary", {}).get("backend_supports_range", False)
    any_range = servlet_range or backend_range

    # Concurrency: prefer measured sweet spot, capped at the good-citizen ceiling.
    best_level = signals.get("conc_best_level") or 4
    jobs = min(PROD_MAX_CONCURRENCY, max(2, int(best_level)))
    # split only if Range is actually supported somewhere.
    split = 2 if any_range else 1
    conn_per_server = split

    staging = os.path.join(PLA_ROOT, "stage")
    input_file = os.path.join(URLS_DIR, "k1_ffp10_smica_pending.aria2.txt")
    session = os.path.join(URLS_DIR, "aria2_session_prod.txt")

    cmd = [
        "aria2c",
        "--no-conf=true",
        "--input-file=%s" % input_file,
        "--dir=%s" % staging,
        "--continue=true",
        "--max-concurrent-downloads=%d" % jobs,
        "--split=%d" % split,
        "--max-connection-per-server=%d" % conn_per_server,
        "--min-split-size=100M" if any_range else "--min-split-size=1G",
        "--file-allocation=none",
        "--auto-file-renaming=false",
        "--allow-overwrite=false",
        "--conditional-get=true",
        "--save-session=%s" % session,
        "--save-session-interval=60",
        "--auto-save-interval=30",
        "--max-tries=0",
        "--retry-wait=30",
        "--connect-timeout=60",
        "--timeout=120",
        "--user-agent=%s" % BROWSER_UA,
        "--header=Referer: %s" % REFERER,
    ]
    cmd_str = " \\\n    ".join(cmd)

    # Atomic move: aria2 writes to staging; move only *completed* files (no .aria2
    # control sibling) into the final dirs so partials never appear there.
    move_snippet = (
        "# After (or alongside) aria2, atomically publish only COMPLETE files:\n"
        "for f in %s/dx12_v3_smica_cmb_mc_*_raw.fits; do\n"
        "    [ -e \"$f\" ] || continue\n"
        "    [ -e \"$f.aria2\" ] && continue          # still downloading -> skip\n"
        "    mv -n \"$f\" %s/                          # atomic within same fs\n"
        "done\n"
        "for f in %s/dx12_v3_smica_noise_mc_*_raw.fits; do\n"
        "    [ -e \"$f\" ] || continue\n"
        "    [ -e \"$f.aria2\" ] && continue\n"
        "    mv -n \"$f\" %s/\n"
        "done"
        % (staging, CMB_DIR, staging, NOISE_DIR))

    note = ("Downloads land in the staging dir; the move loop publishes only files "
            "with no sibling .aria2 control file, so partials never appear in the "
            "final cmb_mc/noise_mc dirs. Run the move loop periodically (e.g. cron/"
            "watch) during the multi-day run, and once more at the end.")
    if not any_range:
        note += (" Range is unsupported: split=1 (whole-file jobs only); do NOT "
                 "raise split.")

    return {"aria2_command": cmd_str, "aria2_argv": cmd,
            "jobs": jobs, "split": split, "staging_dir": staging,
            "atomic_move_snippet": move_snippet, "note": note}


# --------------------------------------------------------------------------- #
# Markdown rendering
# --------------------------------------------------------------------------- #
def render_markdown(data: dict) -> str:
    t = data.get("tasks", {})
    L = []
    L.append("# PLA AIO Download — Bottleneck-Ownership Diagnostic\n")
    L.append("_Generated: %s_\n" % data.get("meta", {}).get("started", ""))

    rec = t.get("T10_recommendation", {})
    lead = rec.get("leading_hypothesis", {})
    if lead:
        L.append("## VERDICT\n")
        L.append("**Owner / leading hypothesis: [%s] %s** (confidence %.2f)\n"
                 % (lead.get("id"), lead.get("name"), lead.get("confidence", 0.0)))
        L.append("> %s\n" % lead.get("evidence", ""))

    # Prominent surfacing: Experiment D + BBR gain (per §7 of the spec).
    t3 = t.get("T3_headers_range", {}).get("summary", {})
    if t3.get("backend_supports_range") and not t3.get("servlet_supports_range"):
        L.append("### ⭐ Experiment D HIT — backend node supports Range\n")
        L.append("The servlet does not support Range but the redirected backend URL "
                 "does. This unlocks aria2 `split>1` against the backend — potentially "
                 "the largest single win. Backend URL(s):\n")
        for u in t.get("T3_headers_range", {}).get("summary", {}).get("backend_urls", []):
            L.append("- `%s`" % u)
        L.append("")
    t5 = t.get("T5_congestion_control", {})
    if t5.get("ratio") and t5["ratio"] >= 1.8:
        L.append("### ⭐ BBR gain — %.2fx over %s\n"
                 % (t5["ratio"], t5.get("current_cc")))
        L.append("Congestion control is the dominant lever: apply BBR for the real run.\n")

    if rec.get("production_command"):
        pc = rec["production_command"]
        L.append("## Recommended production command\n")
        L.append("Concurrency **N=%d**, split **%d**. Restart-robust, staging + "
                 "atomic move (partials never touch final dirs).\n"
                 % (pc.get("jobs"), pc.get("split")))
        L.append("```bash\n%s\n```\n" % pc.get("aria2_command", ""))
        L.append("```bash\n%s\n```\n" % pc.get("atomic_move_snippet", ""))
        L.append("_%s_\n" % pc.get("note", ""))

    if rec.get("warnings"):
        L.append("## Warnings\n")
        for w in rec["warnings"]:
            L.append("- %s" % w)
        L.append("")

    if rec.get("eta"):
        e = rec["eta"]
        L.append("## Informational ETA\n")
        L.append("- best sustained: **%.2f MiB/s** (%.2f Mbit/s)"
                 % (e["best_sustained_mibps"], mbit(e["best_sustained_mibps"] * 1024 * 1024)))
        L.append("- full set (1299 files): ~%.1f h (~%.1f days)"
                 % (e["full_set_hours"], e["full_set_hours"] / 24.0))
        L.append("- remaining (%d files): ~%.1f h (~%.1f days)\n"
                 % (e["remaining_files"], e["remaining_hours"], e["remaining_hours"] / 24.0))

    if rec.get("ranked_hypotheses"):
        L.append("## Ranked hypotheses\n")
        L.append("| id | hypothesis | conf | evidence |")
        L.append("|----|-----------|------|----------|")
        for h in rec["ranked_hypotheses"]:
            L.append("| %s | %s | %.2f | %s |"
                     % (h["id"], h["name"], h["confidence"], h["evidence"]))
        L.append("")

    # Evidence tables
    env = t.get("T1_environment", {})
    if env:
        L.append("## T1 — environment\n")
        for k in ("hostname", "kernel", "egress_iface", "tcp_congestion_control",
                  "tcp_available_congestion_control", "bbr_available",
                  "core_rmem_max", "tcp_rmem", "aria2c_is_running",
                  "cmb_present", "noise_present", "aria2_control_files"):
            if k in env:
                L.append("- **%s**: %s" % (k, env[k]))
        L.append("")

    t3f = t.get("T3_headers_range", {})
    if t3f.get("results"):
        L.append("## T3 — header / Range (+ Experiment D)\n")
        L.append("| scheme | servlet | servlet_range | backend | backend_range | redirects | url_effective |")
        L.append("|--------|---------|---------------|---------|---------------|-----------|---------------|")
        for r in t3f["results"]:
            if r.get("dry"):
                continue
            L.append("| %s | %s | %s | %s | %s | %s | %s |"
                     % (r.get("scheme"), r.get("servlet_status"), r.get("servlet_range"),
                        r.get("backend_status"), r.get("backend_range"),
                        r.get("num_redirects"), (r.get("url_effective") or "")[:70]))
        L.append("")

    t4f = t.get("T4_single_stream", {})
    if t4f.get("runs"):
        L.append("## T4 — single-stream (+ TTFB)\n")
        L.append("| variant | file | MiB/s | Mbit/s | code | TTFB s | redirects |")
        L.append("|---------|------|-------|--------|------|--------|-----------|")
        for r in t4f["runs"]:
            if r.get("dry"):
                continue
            L.append("| %s | %s | %.3f | %.2f | %s | %.3f | %s |"
                     % (r.get("variant"), (r.get("file") or "")[-14:],
                        r.get("mibps", 0.0), r.get("mbit", 0.0), r.get("code"),
                        r.get("ttfb", 0.0), r.get("redir")))
        L.append("")

    t5f = t.get("T5_congestion_control", {})
    if t5f.get("runs"):
        L.append("## T5 — congestion control (raw socket)\n")
        for cc, r in t5f["runs"].items():
            if r.get("ok"):
                L.append("- **cc=%s**: %.3f MiB/s (%s, method=%s)"
                         % (cc, r["mibps"], human_bytes(r["bytes"]), r["cc_method"]))
            else:
                L.append("- **cc=%s**: FAILED (%s)" % (cc, r.get("error")))
        if t5f.get("ratio"):
            L.append("- **BBR/%s ratio = %.2fx**" % (t5f.get("current_cc"), t5f["ratio"]))
        for n in t5f.get("notes", []):
            L.append("- _%s_" % n)
        L.append("")

    t6f = t.get("T6_reference_hosts", {})
    if t6f.get("single"):
        L.append("## T6 — reference hosts (client vs server control)\n")
        L.append("| host | single MiB/s | N=4 MiB/s | N=4 per-conn MiB/s |")
        L.append("|------|--------------|-----------|--------------------|")
        par_by_host = {p.get("host"): p for p in t6f.get("parallel4", [])}
        for s in t6f["single"]:
            p = par_by_host.get(s.get("host"), {})
            L.append("| %s | %.3f | %.3f | %.3f |"
                     % ((s.get("host") or "")[:48], s.get("agg_mibps_curl", 0.0),
                        p.get("agg_mibps_curl", 0.0), p.get("per_conn_avg_mibps", 0.0)))
        L.append("")

    t7f = t.get("T7_concurrency_sweep", {})
    if t7f.get("results"):
        L.append("## T7 — concurrency sweep\n")
        L.append("| N | agg MiB/s | agg Mbit/s | per-conn MiB/s | NIC rx delta |")
        L.append("|---|-----------|------------|----------------|--------------|")
        for r in t7f["results"]:
            L.append("| %d | %.3f | %.2f | %.3f | %s |"
                     % (r.get("level"), r.get("agg_mibps_curl", 0.0),
                        r.get("agg_mbit_curl", 0.0), r.get("per_conn_avg_mibps", 0.0),
                        human_bytes(r["nic_rx_delta_bytes"]) if r.get("nic_rx_delta_bytes") else "n/a"))
        s = t7f.get("summary", {})
        if s:
            L.append("\n_best N=%s (%.3f MiB/s); trend=%s; agg-scale=%.2fx; "
                     "per-conn retention@maxN=%.2f_\n"
                     % (s.get("best_level"), s.get("best_agg_mibps", 0.0),
                        s.get("trend"), s.get("aggregate_scaling_factor", 0.0),
                        s.get("per_conn_retention_high_N", 0.0)))

    t8f = t.get("T8_aria2_microbench", {})
    if t8f.get("runs"):
        L.append("## T8 — aria2 micro-benchmark\n")
        L.append("| jobs | split | backend | MiB/s | Mbit/s |")
        L.append("|------|-------|---------|-------|--------|")
        for r in t8f["runs"]:
            if r.get("dry"):
                continue
            L.append("| %s | %s | %s | %.3f | %.2f |"
                     % (r.get("jobs"), r.get("split"), r.get("backend"),
                        r.get("mibps", 0.0), r.get("mbit", 0.0)))
        L.append("")
    elif t8f.get("skipped"):
        L.append("## T8 — aria2 micro-benchmark\n\n_skipped: %s_\n" % t8f.get("reason"))

    t9f = t.get("T9_log_analysis", {})
    if t9f.get("counts") is not None:
        L.append("## T9 — log analysis\n")
        if t9f.get("counts"):
            for k, v in t9f["counts"].items():
                L.append("- `%s`: %d" % (k, v))
        else:
            L.append("- no error markers found")
        if t9f.get("samples"):
            L.append("\nSamples:\n")
            for s in t9f["samples"][:10]:
                L.append("- `%s`" % s)
        L.append("")

    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def parse_args(argv):
    ap = argparse.ArgumentParser(
        description="PLA AIO download bottleneck-ownership diagnostic + benchmark.")
    ap.add_argument("--duration", type=float, default=90.0,
                    help="per-test duration in seconds (default 90).")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the plan + every command that would run; touch "
                         "nothing, download nothing.")
    grp = ap.add_mutually_exclusive_group()
    grp.add_argument("--test-bbr", dest="test_bbr", action="store_true", default=None,
                     help="force the BBR experiment (default: on if bbr available).")
    grp.add_argument("--no-test-bbr", dest="test_bbr", action="store_false",
                     help="disable the BBR experiment.")
    ap.add_argument("--reference-hosts", type=str, default=None,
                    help="comma-separated override for T6 reference hosts.")
    ap.add_argument("--allow-global-cc-change", action="store_true",
                    help="opt-in: allow changing the GLOBAL congestion control if "
                         "per-socket selection is impossible (always restored).")
    ap.add_argument("--allow-bench-during-download", action="store_true",
                    help="run heavy bandwidth tests even if aria2c is already "
                         "running (default: skip them to avoid confounding).")
    return ap.parse_args(argv)


def print_preamble(args, dry):
    print("=" * 74)
    print("PLA AIO DOWNLOAD DIAGNOSTIC — bottleneck OWNERSHIP, not menu-picking")
    print("=" * 74)
    print("Plan: T1 env -> T2 canaries -> T3 headers/Range(+ExpD) -> T4 single(+TTFB)")
    print("      -> T5 CUBIC vs BBR (raw socket) -> T6 reference hosts -> T7 concurrency")
    print("      -> T8 aria2 microbench -> T9 logs -> T10 recommendation")
    print("SAFETY: bytes -> /dev/null or self-deleted temp; final FITS never touched;")
    print("        no cookies/auth; per-socket CC only; guaranteed cleanup on exit/signal.")
    print("per-test duration: %.0fs   dry-run: %s" % (args.duration, dry))
    print("outputs: %s , %s" % (REPORT_JSON, REPORT_MD))
    print("=" * 74)


def main(argv=None):
    args = parse_args(argv if argv is not None else sys.argv[1:])
    dry = args.dry_run

    # Signal + exit cleanup guarantees.
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)
    atexit.register(cleanup)

    print_preamble(args, dry)

    if not dry:
        os.makedirs(DIAG_DIR, exist_ok=True)

    rep = Report()
    rep.data["meta"]["args"] = vars(args)

    ref_hosts = (DEFAULT_REFERENCE_HOSTS if not args.reference_hosts
                 else [h.strip() for h in args.reference_hosts.split(",") if h.strip()])

    try:
        env = t1_environment(rep, dry)
        canaries = t2_canaries(rep, dry)

        # Heavy bandwidth tests gated when aria2c is running (confound + load).
        bench_allowed = (not env.get("aria2c_is_running")) or args.allow_bench_during_download
        if not bench_allowed:
            print("\n! aria2c running and --allow-bench-during-download not set:")
            print("  running only passive probes (T3 1-byte, T9 logs). Stop/pause")
            print("  the production download and re-run for full bandwidth diagnosis.")

        # T3 header probes are 1-byte range requests (max-time 20s) -> always safe.
        t3 = t3_headers_range(rep, canaries, dry)

        # Decide BBR test: default on if available (unless --no-test-bbr).
        if args.test_bbr is None:
            test_bbr = bool(env.get("bbr_available"))
        else:
            test_bbr = args.test_bbr

        t4 = t5 = t6 = t7 = t8 = None
        if bench_allowed:
            t4 = t4_single_stream(rep, canaries, args.duration, dry)
            t5 = t5_congestion_control(rep, canaries, env, args.duration, test_bbr,
                                       args.allow_global_cc_change, dry)
            t6 = t6_reference_hosts(rep, ref_hosts, args.duration,
                                    env.get("nic_iface"), dry)
            t7 = t7_concurrency_sweep(rep, canaries, args.duration,
                                      env.get("nic_iface"), dry)
            t8 = t8_aria2_microbench(rep, canaries, t3, env,
                                     args.allow_bench_during_download, dry)
        else:
            for key in ("T4_single_stream", "T5_congestion_control",
                        "T6_reference_hosts", "T7_concurrency_sweep",
                        "T8_aria2_microbench"):
                rep.set(key, {"skipped": True,
                              "reason": "aria2c running; use --allow-bench-during-download"})

        t9 = t9_log_analysis(rep, dry)

        # Record NIC end counter.
        if env.get("nic_iface") and not dry:
            env["nic_end"] = read_nic_counters(env["nic_iface"])
            rep.set("T1_environment", env)

        t10_recommend(rep, env, t3, t4 or {}, t5 or {}, t6 or {}, t7 or {},
                      t8 or {}, dry)

        rep.data["meta"]["finished"] = now_iso()
        rep.write(dry)

        if not dry:
            print("\nReports written:\n  %s\n  %s" % (REPORT_JSON, REPORT_MD))
        else:
            print("\nDRY RUN complete — nothing executed, nothing written.")
    finally:
        cleanup()
    return 0


if __name__ == "__main__":
    sys.exit(main())
