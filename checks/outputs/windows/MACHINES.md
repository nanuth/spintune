# Machines behind these outputs

| Output | Machine | Wall time |
|---|---|---|
| `headroom_v4.txt` (`headroom_v4.py anchor_check.py`) | Windows 11, 24 threads, 31 GB, Python 3.12.13 (uv) | 34 s |
| `cz_v3_scan.txt` (`cz_v3_scan.py .`) | same | 9 s |
| `qarray_timing.txt` | same | 2 dots: 59.5 ms / 100×100, 6.9 ms / 32×32 |
| `anchor_check.txt` | same | — |

Counts and wrong-anchor tallies match §1.2 exactly. Mac run: `../mac/`. `headroom_v4` and `anchor_check` are byte-identical to it, and `cz_v3_scan` differs in one entry at 2×10⁻¹³.

`qarray_units.txt`, `qarray_recipe.txt` and `sensor_spike.txt` come from 47f1b55 (machine not recorded; same author). The Mac reproduces them; only sensor_spike's speed lines differ.

`qarray_timing.txt` here is unpinned. §1.2's numbers are single-threaded, and `run_checks.py` now runs it with `RAYON_NUM_THREADS=1`. Rerun with `uv run python checks/run_checks.py`, which writes `machine.txt` here; then delete this file.
