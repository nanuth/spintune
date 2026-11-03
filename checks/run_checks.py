"""Rerun every checks/ script and save its output (PLAN.md 1.3, A0's Done check).

    uv run python checks/run_checks.py ["<SCRIPTS key>" ...]   # no keys = run all

Writes checks/outputs/<os>/<script>.txt as UTF-8 on every OS, plus, on a full
run, machine.txt with the machine and per-script wall time. Same command on Mac
and Windows; compare outputs/mac/ with outputs/windows/.
qdarts_check.py is skipped: it needs the separate QDarts environment.
"""

import os
import platform
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Output name -> [script, args...], as documented in checks/README.md. Run with cwd=checks/.
SCRIPTS = {
    "headroom_v4.py": ["anchor_check.py"],
    # The flagged runs behind §1.2's descent-direction, ray-size and shortcut rows.
    "headroom_v4.py --axis-descent": ["anchor_check.py", "--axis-descent"],
    "headroom_v4.py --need-sized": ["anchor_check.py", "--need-sized"],
    "headroom_v4.py --stop-length 22.5": ["anchor_check.py", "--stop-length", "22.5"],
    "anchor_check.py": [],
    "qarray_timing.py": [],
    "prior_check.py": [],
    "hier_check.py": [],
    "hier_check2.py": [],
    "cz_v3_check.py": [],
    "cz_v3_scan.py": ["."],
    "regime_check.py": [],
    "bo_overhead.py": [],
    # Kept only because the review documents cite them.
    "headroom_v3.py": ["anchor_check.py"],
    "headroom_rough.py": ["anchor_check.py"],
    "headroom_pitch.py": ["anchor_check.py"],
    "cz_check.py": [],
    "cz_pulse_check.py": [],
    "review_v2_checks.py": [],
}
SKIPPED = {"qdarts_check.py": "needs the QDarts environment (PLAN.md Phase 3)"}

# Extra environment per script. §1.2's QArray timings are single-threaded; unpinned,
# QArray's Rust core uses every core and the timing varies run to run.
ENV = {"qarray_timing.py": {"RAYON_NUM_THREADS": "1"}}


def os_name() -> str:
    return {"Darwin": "mac", "Windows": "windows"}.get(platform.system(), platform.system().lower())


def machine() -> str:
    cpu = platform.processor() or platform.machine()
    if platform.system() == "Darwin":
        cpu = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"],
                             capture_output=True, text=True).stdout.strip() or cpu
    return (f"{platform.system()} {platform.release()} {platform.machine()}, {cpu}, "
            f"{os.cpu_count()} logical CPUs, Python {platform.python_version()}")


def main(names: list[str]) -> int:
    unknown = [n for n in names if n not in SCRIPTS]
    if unknown:
        print(f"unknown script(s): {unknown}; known: {list(SCRIPTS)}", file=sys.stderr)
        return 2
    on_disk = {p.name for p in HERE.glob("*.py")} - {Path(__file__).name}
    missing = on_disk - {key.split()[0] for key in SCRIPTS} - SKIPPED.keys()
    if missing:
        print(f"scripts with no entry in SCRIPTS: {sorted(missing)}", file=sys.stderr)
        return 2

    out = HERE / "outputs" / os_name()
    out.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    rows, failed = [], []
    for key in names or SCRIPTS:
        script, args = key.split()[0], SCRIPTS[key]
        extra = ENV.get(key, {})
        cmd = " ".join([*(f"{k}={v}" for k, v in extra.items()), script, *args])
        print(f"{cmd} ...", end=" ", flush=True)
        t0 = time.perf_counter()
        r = subprocess.run([sys.executable, script, *args], cwd=HERE, env={**env, **extra},
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        dt = time.perf_counter() - t0
        text = r.stdout + (f"\n--- stderr ---\n{r.stderr}" if r.stderr.strip() else "")
        # headroom_v4.py --stop-length 22.5 -> headroom_v4_stop-length_22.5.txt
        stem = "_".join([Path(script).stem, *(a.lstrip("-") for a in key.split()[1:])])
        (out / f"{stem}.txt").write_text(text, encoding="utf-8", newline="\n")
        status = "ok" if r.returncode == 0 else f"exit {r.returncode}"
        print(f"{status} ({dt:.1f} s)")
        rows.append(f"| {cmd} | {status} | {dt:.1f} |")
        if r.returncode:
            failed.append(key)

    lines = [f"Machine: {machine()}", "",
             "| Script | Status | Wall time (s) |", "|---|---|---|", *rows, "",
             *(f"Skipped {k}: {v}" for k, v in SKIPPED.items())]
    if not names:  # only a full run rewrites the machine summary
        (out / "machine.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    if failed:
        print(f"FAILED: {failed}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
