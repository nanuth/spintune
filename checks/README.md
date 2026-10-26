# Evidence scripts

These are the scripts behind every **[measured]** claim in `SpinTune_Design_v4.md` (§1.2). They are quick feasibility checks, not product code. Every tuning-cost number is an idealized estimate for one specified policy: noiseless cells and a perfect line reader.

## Environments
- **Main:** Python 3.12 with `qarray==1.6.0`, `qiskit==2.6.1`, `qiskit-aer==0.18.0`, `qiskit-experiments==0.14.2`, `torch` and `botorch` (BoTorch is used only by `bo_overhead.py`). QArray's Rust core has no wheel for Python ≥ 3.13.
- **QDarts:** a separate Python 3.12 environment with `qdarts==1.0.5`. It pins `numpy<2`, `scipy<=1.12` and `cvxpy==1.5.2`.
- Lockfiles are still to do (design §15.1).

## Scripts

| Script | Shows | Design section |
|---|---|---|
| `headroom_v4.py` | Cost of the §6.1 policy with every ray and window metered: rays rounded up to 16/32/64 samples and shrunk to fit the ±300 mV domain, integer pixels, §5.2 confirmation with billed retries, query count and RF time (§4.2). History tuners run as 10-cell chip sequences, with beliefs drawn around the truth from the §7.2 spreads. In-distribution: T★ 357 px / 0.33 s, T3 cold 527 / 0.50 s, chip history 451 / 0.36 s; history/cold 0.86 in pixels, 0.73 in time; pixels ≈ 1% of RF time. Flags: `--need-sized` (8–64-sample rays sized exactly: −4% pixels, T3 6–12% slower), `--axis-descent` (one axis at a time: T3 abstains on 19–22% of cells), `--stop-length 22.5` (the 1.5-period shortcut: 4/300 wrong anchors for T3 in the wide fleet). Run as `python headroom_v4.py anchor_check.py [flags]` (~30 s on 14 cores) | §0, §1.2, §4, §5.1, §6.1, §11.4 |
| `anchor_check.py` | In a descent along one axis at a time, a fixed 22.5 mV stopping rule declares an occupied point empty on 24/300 and 45/300 devices (start spreads 22 and 77 mV), all with P ≥ 25 mV. The period-bounded descent: 0/300 at each spread. Noiseless descent with perfect occupancy readout only; it also provides `device()`, `occ()` and `period_and_cell()` to `headroom_v4.py` | §1.2, §5.1 |
| `qarray_timing.py` | QArray time per 100×100 and 32×32 charge-sensed map, 2 and 4 dots, with noise and latching | §1.2, §12 |
| `prior_check.py` | Charge cells are congruent (a window can't tell (1,1) from (2,2)); zero-measurement success under narrow spreads (82–100%) | §1.2 |
| `hier_check.py`, `hier_check2.py` | Zero-measurement success with sourced spreads in mV: fleet mean 1–6%, earlier-cells mean 6–12% | §0, §1.2 |
| `cz_v3_check.py` | Standard convention `(dEz/4)(ZI − IZ)`: nominal Hann-pulse error, full Hamiltonian vs the pure-ZZ formula with fixed corrections, and the exact 2×2 odd-block propagator with its speed | §1.2, §8.2, §12 |
| `cz_v3_scan.py` | Hann-pulse error envelope vs J_max/ΔE_z. Run as `python cz_v3_scan.py <this folder>` | §8.2 |
| `qdarts_check.py` | QDarts installs and runs; tunnel coupling changes a charge-sensed scan; time per window | §1.2, §3.3 |
| `regime_check.py` | A "double-dot regime" label is met by 73–91% of random windows | §1.1, §1.2 |
| `bo_overhead.py` | BoTorch per-step overhead of 0.05–0.17 s in 3D | §1.2, §6.2 |

**Kept only because the review documents cite them, not used by the design:** `headroom_v3.py` (unmetered estimate: fractional pixels, a fixed 256-px confirmation, true-period history), `headroom_rough.py` and `headroom_pitch.py` (earlier estimates that skipped the crossing requirement), `cz_check.py` and `cz_pulse_check.py` (a Zeeman convention that doubles the gradient), and `review_v2_checks.py` (a reviewer's own check).

## Caveats
- All tuning-cost numbers use a **perfect line reader on noiseless cells**, and history beliefs drawn from the assumed fleet structure. They are planning estimates for one policy, not results and not a floor.
- `anchor_check.py` and `headroom_v4.py` read occupancy directly from QArray. They do not test sensor visibility, step signs, the 2D confirmation window, noise or latching.
