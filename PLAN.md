# SpinTune: plan to start implementation

**Written:** Mon 2 Nov 2026. **Scope:** what has to be true before the first line of `spintune/` code, and the order to get there. The design itself is in [`architecture/`](architecture/README.md); task IDs (A0, A1, F1, …) refer to [§15.3](architecture/15-plan.md#153-tasks-needs--hard-dependencies-done--the-check-that-must-pass).

## Where things stand

- The repo holds the v5 design, its reviews and the `checks/` feasibility scripts. There is no `spintune/` package, `pyproject.toml` or test suite yet.
- [§15.4](architecture/15-plan.md#154-schedule) planned W1 (28 Oct – 3 Nov) to end with the first sensor-only, metered end-to-end comparison (A0–A3, B1, R1 minimal, B2). None of it has started, so we are about **one week behind**, with 25 days to the final.
- **Fixed dates ahead:**

| Date | What |
|---|---|
| Fri 13 Nov | Submit the IBM Open Plan run (F4) |
| Tue 17 Nov | Freeze tag ([§11.6](architecture/11-success-measurement.md#116-pre-registration)) |
| Wed 25 – Thu 26 Nov | Demo and dry run |
| Fri 27 Nov | Final |

---

## Phase 1: Blocking prerequisites (A0). Nothing runs without these

### 1.1 Python 3.12 on both laptops (Mac and Windows)

QArray's Rust core (`qarray-rust-core` 1.3.1) has wheels for Python 3.10–3.12 only, on every OS, so both machines need 3.12. The environment [§13](architecture/13-prerequisites.md) marks "verified 25 Oct" is on neither.

| | Mac | Windows (checked 2 Nov) |
|---|---|---|
| Python today | 3.14.2 (Homebrew), 3.9.6 (system) | 3.11.9 only |
| uv | none | 0.11.9, in `%USERPROFILE%\.local\bin` |
| Other | no conda or pyenv; no `qarray` or `qiskit` | Git 2.52, long paths on; 24 threads, 31 GB RAM |
| Install uv | `brew install uv` | installed, but 0.11.9 is too old for the lock: `uv self update` (otherwise `winget install --id=astral-sh.uv -e`) |
| Install 3.12 | `uv python install 3.12` | `uv python install 3.12` |

- [x] Mac: `brew install uv`, then `uv python install 3.12` (2 Nov: uv 0.13.6, CPython 3.12.16)
- [ ] Windows: `uv self update`, then `uv python install 3.12`. `pyproject.toml` requires uv ≥ 0.13.6, because `uv.lock` is lock revision 5. Never re-lock with an older uv.

Neither needs a system-wide 3.12: uv downloads its own, and the project pins it.

### 1.2 `pyproject.toml` and `uv.lock` for the `spintune` package

Pinned in the design ([§1.2](architecture/01-design-decisions-and-evidence.md#12-evidence-status-25-oct-2026), `checks/README.md`):

| Package | Version |
|---|---|
| `qarray` | 1.6.0 |
| `qiskit` | 2.6.1 |
| `qiskit-aer` | 0.18.0 |
| `qiskit-experiments` | 0.14.2 |
| `samplomatic` | 0.21.0 |
| `torch` | unpinned |
| `botorch` | unpinned; optional extra, only for T-BO and `bo_overhead.py` |

Needed by the plan but **missing from that list**:

| Package | Why |
|---|---|
| `qiskit-ibm-runtime` | `FakeTorino` (F3) and the IBM Open Plan run (F4) both come from it |
| `pytest` (dev) | A2's "Done" checks are unit tests: ledger, time model, latching partition test |
| `scipy` | Used throughout `checks/` |
| `matplotlib` | Figures (E1) |
| `scikit-image` | Hough line fitting for reader v1 (R1) and T2's fitter |
| `h5py` (optional extra) | Raw D-CSD files (R3, later) |

**Windows check (2 Nov):** the full list above, plus the QDarts pins, resolves for Python 3.12 on `win_amd64` (`uv pip compile --python-platform x86_64-pc-windows-msvc`, nothing installed). Every package has a Windows wheel or is pure Python. Things to know:

- `qarray==1.6.0` pins `numpy==2.2.4` exactly and pulls in `jax[cpu]` (0.12.0.1, which has Windows wheels). Numpy is fixed by QArray on both OSes.
- `torch` from PyPI is a CPU build on Windows (2.15.0). That's all the plan needs ([§12](architecture/12-compute-plan.md)), so don't add a CUDA index.
- The QDarts set resolves to `numpy` 1.26.4, `scipy` 1.12.0, `cvxpy` 1.5.2, all with `cp312-win_amd64` wheels.

- [x] Write `pyproject.toml` with the main dependencies, `pytest` as a dev dependency and `botorch` as an optional extra (`uv init --package --python 3.12`, then `uv add …`). No OS-specific markers or indexes. Done with `requires-python = ">=3.12,<3.13"`, a flat `spintune/` layout, and extras `bo` (botorch) and `data` (h5py).
- [x] `uv lock` and commit `uv.lock`. The lock is universal, so one lockfile serves both OSes. Locked on the Mac (2 Nov, 128 packages; numpy 2.2.4, jax 0.12.0.1, torch 2.15.0, as in the Windows check above).
- [ ] Windows: `uv sync --locked --all-extras` and confirm it installs without re-locking
- [x] Add `.gitattributes` with `* text=auto eol=lf`, so `uv.lock`, `.py` and `.md` files don't churn line endings between Mac and Windows
- [ ] If the teammate's laptop still has the 25 Oct environment, diff its `pip freeze` against the lockfile first, so the lock matches the environment that produced the §1.2 numbers

### 1.3 Reproduce the `checks/` numbers (A0's Done check)

A0 is done when every `checks/` script reruns from the repo on **both laptops (Mac and Windows)**, with outputs saved. That shows the new environment matches the one behind the design's numbers.

- [x] Run each script from `checks/` (some `exec` a sibling file by relative path) and save the output. One command on both OSes, from the repo root: `uv run python checks/run_checks.py` (~5 min on the Mac). It runs every script with its arguments from `checks/README.md`, plus the three `headroom_v4.py` flag runs behind §1.2, and writes `checks/outputs/<os>/<script>.txt` and `machine.txt` (machine, per-script wall time).
  - `qdarts_check.py` runs in the QDarts environment instead ([Phase 3](#phase-3-needed-soon-but-not-on-day-one))
  - Outputs must be UTF-8, or Windows's won't diff cleanly against the Mac's. `run_checks.py` writes UTF-8 with LF itself and sets `PYTHONUTF8=1` for each script, so no `Out-File` or shell redirection is needed. Not yet run on Windows. Quote the repo path there, because it has a space (`D:\QML JEV\…`).
  - `qarray_timing.py` runs with `RAYON_NUM_THREADS=1`, because §1.2's timings are single-threaded. Unpinned, QArray uses every core and its timing varies from run to run.
- [x] Compare against [§1.2](architecture/01-design-decisions-and-evidence.md#12-evidence-status-25-oct-2026). Mac, 2 Nov: every count, tally and ratio matches; only timings differ (see `checks/outputs/mac/`):

| Script | Expected |
|---|---|
| `headroom_v4.py`, in-distribution | T★ 357 px / 5.0 queries / 0.33 s; T3 527 / 8.3 / 0.50 s; T3-M 528 px / 0.50 s; chip history 451 / 5.8 / 0.36 s |
| `anchor_check.py` | Fixed 22.5 mV rule: 24/300 and 45/300 wrong; period-bounded rule: 0/300 at each spread |
| `qarray_timing.py` | 2 dots: ~97 ms per 100×100, ~9.9 ms per 32×32 (machine-dependent). Mac (M4 Pro), one thread: 85.9 / 9.4 ms; 4 dots 117 / 12.7 ms (§1.2: 116 / 12.4) |

- [ ] Same run on the second laptop (Windows), then commit `checks/outputs/windows/` and diff it against `checks/outputs/mac/`. Counts and wrong-anchor tallies should match exactly across OSes. Timings will differ (the Windows machine has 24 threads; the 30 s figure is from 14 cores), so record the machine next to each timing.

### 1.4 Package skeleton and ignore rules

- [x] Create `spintune/` per [Appendix A](architecture/appendix-a-interfaces-and-code-layout.md) (empty modules: `fleet.py`, `device.py`, `interface.py`, `evaluator.py`, `anchor.py`, `reader.py`, `prior.py`, `harness.py`, `tuners/`, `qiskit_cz/`) and `tests/`
- [x] Add the generated-output folders and a data folder to `.gitignore`: `fleets/ runs/ logs/ priors/ figs/ data/` (none are listed today). Anchored at the repo root.
- [ ] `uv run pytest` passes on both OSes. An empty suite makes pytest exit 5, so `tests/test_skeleton.py` imports each Appendix A module. Mac: 10 passed.
- [x] Commit

**Rules for `spintune/` code so it runs on both OSes:**

- Windows starts worker processes by `spawn`, not `fork`. The harness's parallel runs ([§12](architecture/12-compute-plan.md)) need an `if __name__ == "__main__":` guard and picklable worker functions. Keep workers long-lived, because each spawn re-imports jax, torch and qiskit.
- Pin threads per worker in code (`os.environ["OMP_NUM_THREADS"] = "1"`, and the same for `MKL_`, `OPENBLAS_` and `RAYON_NUM_THREADS`) before numpy, jax or torch is imported, not in the shell. Bash and PowerShell set environment variables differently.
- `open(..., encoding="utf-8")` for every text file (traces, logs, priors). Windows defaults to cp1252.
- `pathlib.Path` for every path; no hard-coded `/`.

---

## Phase 2: Decisions to settle before A1/A2 code

### 2.1 Where the sensor signal and noise come from (sensor-model spike, 1–2 h)

As used in `checks/qarray_timing.py`, QArray's `WhiteNoise`, `TelegraphNoise` and `LatchingModel` are set per pixel and applied within one call. [§4.3](architecture/04-measurement-interface.md#43-simulation-behind-the-interface-design-call) needs noise and latching that carry over between queries in simulated instrument time, with the same exogenous random numbers shared across tuners. So:

- QArray supplies only **noiseless occupancy** along arbitrary paths. `anchor_check.py` already does this with `ground_state_open`.
- `device.py` adds white noise, telegraph noise, 1/f drift and latching on top.

The open choice is the **noiseless sensor signal**:

| Option | For | Against |
|---|---|---|
| QArray's `ChargeSensedDotArray`, with virtual compensation on QT0 | Closer to the physical sensor | Dot A : dot B step ratio and the stress scenarios are indirect |
| Our own occupancy-to-step model: signal = s_A·n_A + s_B·n_B, ratio 3 ([§7.2](architecture/07-fleet.md#72-parameters-defaults-and-sweep-ranges)), optional Coulomb-peak lineshape for the detuning and sign-flip stress | The step ratio, detuning, sign flip and SEB background transitions ([§5.1](architecture/05-reading-the-device.md#51-the-anchor-certificate-design-call) b) are explicit parameters | Our own model to justify |

**Decision (2 Nov 2026): QArray's `ChargeSensedDotArray`**, with QArray's own noise turned off. The cost is that each stress knob has to be set indirectly:

- Dot A : dot B step ratio (default 3, swept 2–4) comes from the sensor–dot capacitances. They have to be calibrated per ratio, and the ratio drifts along the sensor peak.
- Compensation error (0–20%) comes from deliberately mis-setting the QT0 virtual gate.
- SEB background transitions aren't native to QArray, so `device.py` adds them on top.

- [x] Spike on one cell: ray and window queries, speed, and whether the step ratio can be held at 2, 3 and 4 (2 Nov, `checks/sensor_spike.py`, recipe in 2.2 step 6)

**Spike result (2 Nov).** Pass bar, fixed before the run: the per-state A:B step ratio stays within ±20% of target over states (0..2, 0..2), with no sign flip at nominal compensation. One cell; E_c 4.0/4.4 meV, r_m 0.07, SEB E_c 2 meV, γ = 0.2 meV [assumed]; 50 mV window at 0.25 mV pitch, T = 0.

| Dot-A step / γ | ε (compensation error) | r = 2 | r = 3 | r = 4 |
|---|---|---|---|---|
| **0.25** | **0** | **PASS** (0.94–1.14 × target) | **PASS** (0.92–1.15) | **PASS** (0.91–1.15) |
| 0.5 | 0 | fail: sign flip at (0,0) | fail: sign flip | fail: up to 11× at (0,0) |
| either | 0.2 | fail: the SEB drifts ±5γ across the window, through several peaks | fail | fail |

- **The QArray path holds at nominal settings.** The ratio is exact at linear order and drifts from about 1.15× target at (0,0) to about 0.92× at (2,1), because of the Lorentzian's curvature (as expected in the 2.1 caveat). Only 8 of the 9 states had both step types in the window; (2,2) was missing.
- **Design constraint: dot-A step ≤ 0.25 γ.** At 0.5 γ, the (0,0)→(2,2) detuning span (≈ 1.5 γ) is wider than the flank, so the first steps cross the peak.
- **The ε = 0–20% stress is extreme at γ = 0.2 meV.** The SEB's QT1 lever arm (0.15 [assumed]) × 20% × 50 mV ≈ 1.5 meV ≈ 7 γ of drift, so the sensor runs through Coulomb oscillations and a per-state ratio means nothing. That may be the right stress, but the metric should become "fraction of the window on a usable flank", and the range needs a real γ and SEB lever arm (on the Equal1 list).
- **Speed:** ~0.3 ms per 65-pixel ray, 0.8 ms per 32×32 window, 2.3 ms per 64×64 window (~0.6 µs/pixel), the same at T = 300 mK. Not a bottleneck.
- **Gotchas found** (all in 2.2 step 6): `ChargeSensedDotArray` ignores `charge_carrier` and loads electrons at **negative** voltages; it has **no lead capacitance for the sensor**; and some lever-arm targets are **infeasible** (dot B's QT0 lever arm of 0.005 came out as a negative capacitance through the sensor coupling; 0.02 works).

- [ ] Record the choice in `architecture/` as a design call, with the spike table above
- [ ] Decide the compensation-error stress: keep ε ∈ [0, 0.2] with a "usable flank fraction" metric, or narrow it once γ and the SEB lever arms are known

### 2.2 Units mapping

[§7.2](architecture/07-fleet.md#72-parameters-defaults-and-sweep-ranges) is in physical units (lever arm 0.27 eV/V, charging energy 4 meV, so P ≈ 15 mV). The check scripts use scale-free model units with an `mv` conversion factor.

- [x] Write down one mapping from the §7.2 hierarchy (wafer → chip → cell) to QArray's `Cdd` and `Cgd`, before A1 (2 Nov: the recipe below, evidence in `checks/qarray_units.py`, `checks/qarray_recipe.py`, `checks/sensor_spike.py`)

#### QArray's unit convention (read from the source, checked numerically on 2 Nov)

- QArray's free energy is F = (n − Cgd·V)ᵀ · cdd⁻¹ · (n − Cgd·V) (`python_implementations/helper_functions.py`). There is **no ½ and no e**. `cdd` is the Maxwell matrix that QArray builds from the `Cdd`/`Cgd` you pass in.
- k_B is in eV/K and multiplies `T` (`ground_state.py`). So **V is in mV, F is in meV and `T` is in mK**: the §7.2 setting `T=300` means 0.3 K.
- Capacitances are therefore in e/mV, and the missing ½ puts a factor 2 into every energy:

| Quantity | QArray expression | Single-dot check (E_c = 4 meV, P = 15 mV, T = 300) |
|---|---|---|
| Charging energy E_c,i [meV] | 2·(cdd⁻¹)_ii | `Cg = 1/P`, `C_Σ = 2/E_c` → period 15.00 mV ✓ |
| Mutual charging energy E_cm [meV] | 2·(cdd⁻¹)_AB | — |
| Lever-arm matrix α_ij [meV/mV = eV/V] | 2·(cdd⁻¹·Cgd)_ij | 10–90% thermal width 0.42 mV, predicted 2·ln9·k_BT/α = 0.43 mV ✓ |
| Period of dot i along its own gate [mV] | E_c,i / α_ii | — |
| Line shift r_m (fraction of P when the other dot gains an electron) | E_cm / E_c,i | — |

This is the standard constant-interaction model (lever arm α = C_g/C_Σ, E_c = e²/C_Σ; for double dots, E_c1 = (e²/C_1)/(1 − C_m²/(C_1C_2)), after van der Wiel et al., RMP 75, 1 (2003)), with QArray's factor 2 folded in. Thermal broadening is sub-pixel at 0.3 K (0.43 mV against the 2 mV pitch), so it only matters for the OOD-hot set.

#### The recipe (exact inverse, checked on 2 Nov)

1. **Sample the hierarchy** (§7.1, §7.2): wafer offset and Δ_edge → chip offset σ_die, radial term Δ_edge·(r/R)², α scale, x scale → cell α factors per dot, E_c, cross-coupling x, E_cm, first-electron offsets σ_cell.
2. **Build the target energies.** E_c,A, E_c,B, E_cm and the lever-arm matrix α (rows: dots A, B; columns: QT1, QA1; diagonal from the sampled α, off-diagonal x·α).
3. **Convert to QArray's matrices.**
   - K = ½·[[E_c,A, E_cm], [E_cm, E_c,B]] (this is cdd⁻¹)
   - cdd = K⁻¹, Cgd = K⁻¹·α/2
   - non-Maxwell inputs: Cm = −cdd_AB, C_lead,i = cdd_ii − Cm − Σ_g Cgd_ig, then `DotArray(Cdd=[[C_lead,A, Cm], [Cm, C_lead,B]], Cgd=Cgd, T=T_mK)`
   - Check run: E_c = (4.0, 4.4) meV, E_cm = 0.8 meV and α = [[0.27, 0.0675], [0.06, 0.25]] come back exactly, and the measured period is 14.82 mV against 14.81 predicted.
4. **Physicality check:** every input capacitance ≥ 0 (Cm, Cds, every Cgd entry), **and the physical lead capacitance ≥ 0: (cdd_ii − Σ_j≠i |cdd_ij|)/2 − Σ_g Cgd_ig ≥ 0.** QArray's own C_lead ≥ 0 is too weak by the factor 2: it allows lever arms summing to 2, against a physical limit of 1. Cgd can come out negative when a target lever arm is below what the dot already gets through its neighbours (seen in the spike). Resample failures, and log the rejection rate, because rejection reshapes the §7.2 distributions.
5. **Offsets** (σ_wafer, σ_die, radial term, σ_cell, Δ_nom) are shifts of the plane gates, applied in `device.py` before QArray is called: V → V − Δ, with Δ = α⁻¹·diag(α)·δ, where δ_i is dot i's first-electron shift in mV along its own gate (same idea as `checks/prior_check.py:19`).
6. **Sensor** (2.1, `ChargeSensedDotArray`; checked in the 2 Nov spike). Same inverse as step 3, one size up:
   - K_full = ½·[[E_c,A, E_cm, s_A], [E_cm, E_c,B, s_A/r], [s_A, s_A/r, E_c,s]], where s_i is the sensor detuning shift per electron on dot i (meV) and r the A:B ratio. This sets the ratio **exactly** at linear order: no calibration loop.
   - cdd_full = K_full⁻¹, Cgd_full = K_full⁻¹·α_full/2, with α_full 3 × 4 (rows A, B, sensor; columns QT0, QT1, QT2, QA1).
   - Non-Maxwell inputs: Cm = −cdd_AB, Cds = −cdd_{s,A/B}, dot C_lead = cdd_ii − Cm − Cds_i − Σ Cgd_i.
   - **The sensor has no lead-capacitance slot in QArray**, so add a 5th dummy gate held at 0 V with Cgs_dummy = cdd_ss − Σ Cds − Σ Cgs. Without it, E_c,s and the sensor lever arms can't be set independently.
   - **Sign:** `ChargeSensedDotArray` ignores `charge_carrier` and loads electrons at negative voltages. `device.py` passes −V.
   - Signal = Σ lorentzian(ΔF_s, 0, γ), with `coulomb_peak_width` γ in meV. Keep s_A ≤ 0.25 γ, and place the operating point so the (0,0)→(2,2) detuning span is centred on the max-slope flank at γ/√3.
   - Compensation: the sensor lever arms are α_s = 2·(cdd_full⁻¹·Cgd_full)_s, the QT0 coefficient for gate g is k_g = −α_s,g/α_s,QT0, and the stress uses k_g·(1 − ε).

#### Ask Equal1's physicists (feeds [§14](architecture/14-questions-for-equal1.md) Q1, Q6)

Everything has a §7.2 default, so none of this blocks A1. Answers replace defaults.

- [ ] Which two gates span the charge-tuning plane, and **which gate the 0.27 eV/V lever arm refers to**
- [ ] The lever-arm matrix of both dots on those gates, including cross-coupling (one cell is enough)
- [ ] E_c of each dot and the mutual E_cm, or equivalently how far one dot's lines jump when the other dot loads
- [ ] Cryogenic spread of first-electron voltage within a chip and between chips, and how much of it is shared within a chip
- [ ] Cell-to-cell spread of lever arm and E_c, and how correlated the two dots of the same cell are
- [ ] Electron temperature, as opposed to the 0.3 K fridge temperature
- [ ] Sensor: dot A : dot B step ratio from an existing stability diagram, SEB peak width, SEB lever arms on QT0 and QT1, how they compensate it and the residual, and how often SEB lines overlay the double-dot response

#### Still open (ours to decide)

- [x] **Nominal E_cm** (signed off 2 Nov). §7.2 says "±20% around nominal (r_m ≤ 0.3)" but gives no nominal. Decision: default **r_m ≈ 0.07** (E_cm = 0.07·E_c) [assumed], swept up to **0.23**.
  - 0.07 matches what `checks/anchor_check.py:13` already uses (Cm ≈ 0.1, C_Σ ≈ 1.35, so r_m ≈ 0.05–0.1), which keeps the default in the regime the checks have tested.
  - 0.23 ≈ 0.3/1.3 keeps the +30% end of the sweep inside the certificate's r_m,max = 0.3 ([§5.1](architecture/05-reading-the-device.md#51-the-anchor-certificate-design-call)).
  - Replace with Equal1's line-jump value if it arrives (see the list above).
- [x] **Dot B's E_c and α vs dot A's** (signed off 2 Nov). Both dots already share the chip scale, so the question is only whether there's an extra shared factor at cell level. §7.1 says "per-dot lever arms" (independent α); E_c is ambiguous. Decision: **independent at cell level by default**, plus a **ρ ∈ {0, 0.5} robustness sweep** (shared cell factor plus per-dot residual).
  - Independent is conservative for the headline: tuners can't predict dot B from dot A, so any history advantage comes from cells and chips, which is the claim we make.
  - ρ > 0 is probably closer to the fab (shared oxide, gate stack and strain), but it's unsourced. Setting it high risks building the advantage into the simulator.
  - Not covered either way: systematic A-vs-B mean differences (dot A sits under QT1/QT2 next to the SEB, dot B under QT2/QA1).
  - E_c and α of the *same* dot both depend on C_Σ. Sampling them independently can fail the step 4 physicality check, so a high rejection rate points here.
- [x] **Where the hierarchy multipliers act** (signed off 2 Nov). Decision: the **chip α scale acts on the whole α matrix, and the chip x scale on the ratio x only**:
  - diagonal: α_i = 0.27 × chip α scale × cell factor_i
  - off-diagonal: α_i,other gate = x_i × chip x scale × α_i
  - Why: every gate couples through the same stack, so a "strong" chip pulls harder on both gates. The alternative (α scale on the diagonal only, absolute off-diagonal) quietly makes strong chips have relatively weaker cross-talk, which no source supports.
  - Consequence: virtual-gate ratios change only with the x scale. Cross-talk learned on one cell transfers to the rest of its chip in proportion to how small the x spread is, so that spread is a history-advantage lever and needs a defensible number.
  - **Normalise x by row:** x_A = α_A,QA1 / α_A,QT1, relative to the dot's own gate, which is the virtual-gate convention. `checks/anchor_check.py:13` normalises by column instead (`x * a[::-1]`). That's a ~10% difference at ±10% spreads, so past results are fine, but the fleet generator uses row.
- [x] **Offsets with cross-coupling:** step 5 shifts each dot's line along its own gate with the other gate fixed. Confirmed 2 Nov: this is what σ_cell means (§7.2's source is a single-gate array)
- [x] **Sensor matrices** (Cds, Cgs, γ) that give ratio 2, 3 and 4 and stay near the peak: closed form in step 6, passes the 2.1 spike at s_A ≤ 0.25 γ. γ itself is still [assumed] (0.2 meV) until Equal1's SEB peak width arrives
- [x] **QArray's sensor noise is off by default:** `noise_model=None` becomes `BaseNoiseModel()`, which adds zero. Just never pass one
- [x] The existing `checks/` scripts stay scale-free at T = 0. They are unaffected and don't need porting

### 2.3 New schedule

W1's deliverable now lands in W2 at best.

| Option | What it means |
|---|---|
| **Compress** | Fit the old W1 and W2 into the next ~8 days, with G0 and the reader freeze around 10–12 Nov; keep the 17 Nov freeze |
| **Cut** | Apply the [§15.6](architecture/15-plan.md#156-cut-order-and-what-is-never-cut) cut order now, starting with drift, the full spread map, T6-NN/T-BO and the CNN reader; shrink the promises before spending contingency |

- [ ] Pick one and update [§15.4](architecture/15-plan.md#154-schedule). The 13 Nov and 17 Nov dates should not slip silently.

### 2.4 Who owns which track

Two people, tracks A, B, R, D, E and F ([§15.2](architecture/15-plan.md#152-tracks-and-hour-caps-design-call)). The critical path is A1 → A2 → B1 → B2 → B4 → reader freeze → D1 → D2 → D3 → E2 → E3 ([§15.5](architecture/15-plan.md#155-critical-path)). F1 (the CZ Hamiltonian) depends only on A0.

| Track | Owner |
|---|---|
| A: simulation, interface, evaluator (critical path) | _TBD_ |
| F: Qiskit, starting with F1 as soon as A0 is done | _TBD_ |
| B, R, D, E | _TBD_ |

---

## Phase 3: Needed soon, but not on day one

| Prerequisite | Needed by | Owner | Note |
|---|---|---|---|
| QDarts environment: Python 3.12, `qdarts==1.0.5`, `numpy<2`, `scipy<=1.12`, `cvxpy==1.5.2` | A4, W2 | _TBD_ | Kept separate from the main environment because of those pins. A second uv project, e.g. `workers/qdarts/`, with its own lockfile |
| IBM Quantum account, Open Plan instance (us-east) and saved API token | F4, submit by 13 Nov | _TBD_ | Course Lab 0 (`Unit_0_ Activation Workshop/`) walks through it. Do it this week |
| QDSD raw files (186 MB) and D-CSD (1.8 GB) | R3 | _TBD_ | Into the git-ignored `data/`. Raw files, never resized ([§7.6](architecture/07-fleet.md#76-external-real-device-data-sourced-none-is-22fdx)) |
| Equal1's answers to Q1 (which gates are swept) and Q2 (how dot B loads) ([§14](architecture/14-questions-for-equal1.md)) | A1 device template | _TBD_ | The design has fallbacks, so nothing waits on them |

---

## Phase 4: Stale docs to fix

- [ ] `README.md`, `architecture/README.md` and [§17](architecture/17-references.md) still point at `bobi_resources/PLAN.md` and `SPINTUNE-2.md`, which were deleted in `560d5d6`. [§15.3](architecture/15-plan.md#153-tasks-needs--hard-dependencies-done--the-check-that-must-pass) is now the only task list; point the links there and at this file.
- [ ] [§1.2](architecture/01-design-decisions-and-evidence.md#12-evidence-status-25-oct-2026) and [§13](architecture/13-prerequisites.md) rows 1 and 3 still say the repo and the `checks/` commit are to do. Both are done (remote: `github.com/nanuth/spintune`). Row 1's "verified 25 Oct" should say which machine.
- [ ] [§15.1](architecture/15-plan.md#151-before-the-pitch-tue-27-oct-idea-only), the pre-pitch checklist for 27 Oct, is past: mark it done or remove it.
- [ ] Once Phase 1 is done, change the README status from "design stage".

---

## Order of work

| # | Step | Phase | Estimate |
|---|---|---|---|
| 1 | Install uv and Python 3.12; write `pyproject.toml`; lock; rerun `checks/` | 1.1–1.3 | ~2 h |
| 2 | Skeleton, ignore rules, doc fixes; commit | 1.4, 4 | ~1 h |
| 3 | New schedule and track owners | 2.3, 2.4 | — |
| 4 | Sensor-model spike, units mapping, then start A1 | 2.1, 2.2 | 1–2 h before A1 |

**In parallel:** the IBM account (Phase 3), and F1 by whoever is not on the A1 → A2 path.

## Open questions

- [ ] Does the teammate's laptop still have the 25 Oct environment? If so, its `pip freeze` is the quickest way to a lockfile that reproduces §1.2.
- [ ] What came out of the 27 Oct pitch? Did Equal1 receive the structured data request ([§14](architecture/14-questions-for-equal1.md) Q3–Q5), or answer Q1 and Q2?

add to gitignore the files that are related only to the local 