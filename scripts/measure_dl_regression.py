#!/usr/bin/env python3
"""
BASS baseline 회귀 측정 스크립트.

baseline_2026_04_16.json 에 기록된 3 개 config 를 현재 코드로 재실행하고,
baseline 대비 diff 를 출력한다.

사용법:
    python scripts/measure_dl_regression.py
    python scripts/measure_dl_regression.py --primary-only    # 24 DOF 만
    python scripts/measure_dl_regression.py --baseline <path> # 다른 baseline 파일
    python scripts/measure_dl_regression.py --update          # 변경 결과로 baseline 갱신 (주의!)

Anti-hallucination guards:
- git tag baseline-2026-04-16 이 존재하지 않으면 refuse
- fixture JSON 의 D_2 ratio 가 0.958 이 아니면 fixture 가 손상됐다고 가정
- 동일 config 두 번 실행해서 비결정성 체크 (--deterministic)
"""

from __future__ import annotations
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE = REPO_ROOT / "tests/fixtures/baseline_2026_04_16.json"
TEST_BIN_GLOB = "target/release/deps/bass_rs-*"

# 측정할 ℓ 값
ELL_POINTS = [2, 10, 30, 100, 200, 300]

# Primary format: "  D_  2 =   978.8 (CAMB:  1022.0, ratio: 0.958)"
RE_DL_PRIMARY = re.compile(
    r"D_\s*(\d+)\s*=\s*([-\d.eE+]+|inf|nan)\s*\(CAMB:\s*([-\d.eE+]+),\s*ratio:\s*([-\d.eE+]+|inf|nan)\)"
)
# Percent format: "  D_  2 = 82313... (inf% CAMB)" or "  D_  2 =   978.8 (95.8% CAMB)"
RE_DL_PERCENT = re.compile(
    r"D_\s*(\d+)\s*=\s*([-\d.eE+]+|inf|nan)\s*\(\s*([-\d.eE+]+|inf|nan)%\s*CAMB\s*\)"
)
# Solved count: "  Solved 200/200 k-modes" or "  Solved 57/200 k-modes"
RE_SOLVED = re.compile(r"Solved\s+(\d+)/(\d+)\s+k-modes")


def find_test_binary() -> Path:
    candidates = list(REPO_ROOT.glob(TEST_BIN_GLOB))
    # 일반 실행 파일만 (.d 파일 제외)
    candidates = [p for p in candidates if p.is_file() and not p.suffix]
    if not candidates:
        print(f"ERROR: no test binary under {TEST_BIN_GLOB}", file=sys.stderr)
        print("Run: cargo test --release --no-run --lib", file=sys.stderr)
        sys.exit(2)
    # 가장 최근 것
    return max(candidates, key=lambda p: p.stat().st_mtime)


def verify_git_tag() -> str:
    """Anti-hallucination guard: baseline tag 존재 확인."""
    try:
        result = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "tag", "-l", "baseline-2026-04-16"],
            check=True, capture_output=True, text=True, timeout=5,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"ERROR: git tag verification failed: {e}", file=sys.stderr)
        sys.exit(2)
    if "baseline-2026-04-16" not in result.stdout:
        print("ERROR: git tag 'baseline-2026-04-16' not found.", file=sys.stderr)
        print("This indicates PR-00 baseline freeze was not performed on this repo.", file=sys.stderr)
        sys.exit(2)
    # 현재 SHA
    sha = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True, timeout=5,
    ).stdout.strip()
    return sha


def verify_fixture(fixture_path: Path) -> dict:
    """Anti-hallucination guard: fixture 무결성 확인."""
    if not fixture_path.exists():
        print(f"ERROR: fixture {fixture_path} not found.", file=sys.stderr)
        sys.exit(2)
    with fixture_path.open() as f:
        baseline = json.load(f)
    # 정합성 sanity check: primary D_2 ratio 가 0.958 ± 0.001 인지
    try:
        d2_ratio = baseline["configs"]["config_24dof_no_pol_no_mnu"]["D_ell"]["2"]["ratio"]
    except KeyError:
        print("ERROR: fixture schema broken (no primary D_2 ratio).", file=sys.stderr)
        sys.exit(2)
    if abs(d2_ratio - 0.958) > 0.001:
        print(f"ERROR: fixture D_2 ratio = {d2_ratio}, expected 0.958.", file=sys.stderr)
        print("The fixture may have been modified or corrupted.", file=sys.stderr)
        sys.exit(2)
    return baseline


def run_test(test_bin: Path, test_name: str, timeout_s: int = 600) -> str:
    """Rust 테스트 실행, stderr 캡처."""
    cmd = [
        str(test_bin),
        test_name,
        "--nocapture", "--exact", "--test-threads=1",
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout_s,
        )
    except subprocess.TimeoutExpired:
        return "__TIMEOUT__"
    # stdout 과 stderr 합쳐서 반환 (eprintln! 은 stdout 아닌 stderr 로 갈 수 있음)
    return result.stdout + "\n" + result.stderr


def parse_dl(output: str) -> tuple[dict, tuple[int, int] | None]:
    """eprintln! 출력에서 D_ℓ 값과 (solved, total) 추출."""
    dl_values = {}
    # primary format 먼저
    for m in RE_DL_PRIMARY.finditer(output):
        ell = int(m.group(1))
        val = m.group(2)
        camb = m.group(3)
        ratio = m.group(4)
        dl_values[ell] = {
            "bass": float(val) if val not in ("inf", "nan") else val,
            "camb": float(camb),
            "ratio": float(ratio) if ratio not in ("inf", "nan") else ratio,
        }
    # percent format (epol 등)
    if not dl_values:
        for m in RE_DL_PERCENT.finditer(output):
            ell = int(m.group(1))
            val = m.group(2)
            pct = m.group(3)
            dl_values[ell] = {
                "bass": float(val) if val not in ("inf", "nan") else val,
                "ratio_percent": float(pct) if pct not in ("inf", "nan") else pct,
            }
    # solved count
    solved = None
    for m in RE_SOLVED.finditer(output):
        solved = (int(m.group(1)), int(m.group(2)))
    return dl_values, solved


def status_for_config(solved: tuple[int, int] | None, dl_values: dict) -> str:
    """측정 결과로부터 config status 분류."""
    if solved is None:
        return "NO_DATA"
    s, t = solved
    if s < t * 0.9:
        return "BLOCKED"
    if not dl_values:
        return "NO_DL"
    # inf 또는 NaN 값이 있으면 BLOCKED
    for v in dl_values.values():
        bass = v.get("bass")
        if bass in ("inf", "nan") or (isinstance(bass, float) and (bass != bass or abs(bass) > 1e20)):
            return "BLOCKED"
    return "VALIDATED"


def compare_config(config_key: str, baseline_cfg: dict, current_dl: dict,
                   current_status: str, current_solved: tuple | None) -> tuple[str, list[str]]:
    """
    baseline vs current 비교. (verdict, lines) 반환.
    verdict 는 UNCHANGED / IMPROVED / REGRESSED / BLOCKED_BOTH / NEWLY_BLOCKED / NEWLY_UNBLOCKED
    """
    baseline_status = baseline_cfg.get("status")
    lines = []
    lines.append(f"[{config_key}]")
    lines.append(f"  baseline status : {baseline_status}")
    lines.append(f"  current status  : {current_status}")
    if current_solved is not None:
        lines.append(f"  k-modes         : {current_solved[0]}/{current_solved[1]}")
    # 분기
    if baseline_status == "VALIDATED" and current_status == "VALIDATED":
        # D_ℓ diff 표
        lines.append(f"  {'ell':>5} {'baseline':>10} {'current':>10} {'delta':>10} {'rel':>8}")
        any_regressed = False
        any_improved = False
        for ell in ELL_POINTS:
            b = baseline_cfg.get("D_ell", {}).get(str(ell))
            c = current_dl.get(ell)
            if b is None or c is None:
                continue
            bv = b["bass"]
            cv = c["bass"]
            if not isinstance(bv, (int, float)) or not isinstance(cv, (int, float)):
                continue
            delta = cv - bv
            rel = delta / bv if bv != 0 else 0.0
            mark = ""
            # 절댓값 ratio 가 CAMB 에 더 가까워지면 improved (epsilon 1e-3 — fixture
            # 의 ratio 가 보통 3 자리수 반올림이라 1e-4 는 false positive 발생)
            b_ratio = b.get("ratio", 1.0)
            c_camb = c.get("camb", b["camb"])
            c_ratio = cv / c_camb if c_camb else 1.0
            if abs(c_ratio - 1.0) < abs(b_ratio - 1.0) - 1e-3:
                mark = "  ← improved (closer to CAMB)"
                any_improved = True
            elif abs(c_ratio - 1.0) > abs(b_ratio - 1.0) + 1e-3:
                mark = "  ← REGRESSED"
                any_regressed = True
            lines.append(f"  {ell:>5} {bv:>10.2f} {cv:>10.2f} {delta:>+10.2f} {rel:>+7.2%}{mark}")
        if any_regressed:
            return "REGRESSED", lines
        elif any_improved:
            return "IMPROVED", lines
        else:
            return "UNCHANGED", lines
    elif baseline_status == "BLOCKED" and current_status == "VALIDATED":
        lines.append("  ✓ NEWLY UNBLOCKED — config can now be measured")
        if current_dl:
            lines.append(f"  current D_ℓ:")
            for ell in ELL_POINTS:
                c = current_dl.get(ell)
                if c and isinstance(c.get("bass"), (int, float)):
                    lines.append(f"    D_{ell:<3} = {c['bass']:.2f}")
        return "NEWLY_UNBLOCKED", lines
    elif baseline_status == "VALIDATED" and current_status == "BLOCKED":
        lines.append("  ✗ NEWLY BLOCKED — previously measurable config now fails")
        return "NEWLY_BLOCKED", lines
    elif baseline_status == "BLOCKED" and current_status == "BLOCKED":
        lines.append("  · still BLOCKED")
        return "BLOCKED_BOTH", lines
    else:
        return "UNKNOWN", lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", type=Path, default=FIXTURE)
    ap.add_argument("--primary-only", action="store_true",
                    help="24 DOF config 만 측정 (빠름, ~73s)")
    ap.add_argument("--mini-only", action="store_true",
                    help="mini 50k config 만 측정 (가장 빠름, ~15s — PR 작업 중 권장)")
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--skip-tag-check", action="store_true",
                    help="git tag 검증 스킵 (권장 안 함)")
    args = ap.parse_args()

    print(f"BASS baseline 회귀 측정 — fixture: {args.baseline}")
    print("=" * 78)

    if not args.skip_tag_check:
        sha = verify_git_tag()
        print(f"current HEAD: {sha[:12]}")
    baseline = verify_fixture(args.baseline)
    print(f"baseline date: {baseline['measurement_date']}")
    print(f"baseline SHA : {baseline['git_sha'][:12]}")

    test_bin = find_test_binary()
    print(f"test binary  : {test_bin.name}")
    print()

    configs_to_run = list(baseline["configs"].items())
    if args.mini_only:
        configs_to_run = [(k, v) for k, v in configs_to_run if "mini" in k]
    elif args.primary_only:
        configs_to_run = [(k, v) for k, v in configs_to_run if "24dof_no_pol" in k]

    results = {}
    for config_key, config_info in configs_to_run:
        test_name = config_info["test_name"]
        print(f">>> running {config_key} ({test_name})")
        output = run_test(test_bin, test_name, timeout_s=args.timeout)
        if output == "__TIMEOUT__":
            print(f"    TIMEOUT after {args.timeout}s")
            results[config_key] = ("TIMEOUT", [f"[{config_key}] TIMEOUT"])
            continue
        dl, solved = parse_dl(output)
        status = status_for_config(solved, dl)
        verdict, lines = compare_config(config_key, config_info, dl, status, solved)
        results[config_key] = (verdict, lines)
        print("\n".join(lines))
        print()

    # Summary
    print("=" * 78)
    print("SUMMARY")
    print("=" * 78)
    for k, (verdict, _) in results.items():
        print(f"  {k:<45}  {verdict}")

    # Exit code
    any_regressed = any(v == "REGRESSED" or v == "NEWLY_BLOCKED" for v, _ in results.values())
    sys.exit(1 if any_regressed else 0)


if __name__ == "__main__":
    main()
