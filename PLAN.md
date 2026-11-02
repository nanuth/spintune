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
| Install uv | `brew install uv` | already done (otherwise `winget install --id=astral-sh.uv -e`) |
| Install 3.12 | `uv python install 3.12` | `uv python install 3.12` |

- [x] Mac: `brew install uv`, then `uv python install 3.12` (2 Nov: uv 0.13.6, CPython 3.12.16)
- [ ] Windows: `uv python install 3.12`

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
- [x] Windows: outputs must be UTF-8, or they won't diff cleanly against the Mac's. `run_checks.py` writes UTF-8 with LF itself and sets `PYTHONUTF8=1` for each script, so no `Out-File` or shell redirection is needed. Quote the repo path, because it has a space (`D:\QML JEV\…`).
- [x] Compare against [§1.2](architecture/01-design-decisions-and-evidence.md#12-evidence-status-25-oct-2026). Mac, 2 Nov: every count, tally and ratio matches; only timings differ (see `checks/outputs/mac/`):

| Script | Expected |
|---|---|
| `headroom_v4.py`, in-distribution | T★ 357 px / 5.0 queries / 0.33 s; T3 527 / 8.3 / 0.50 s; T3-M 528 px / 0.50 s; chip history 451 / 5.8 / 0.36 s |
| `anchor_check.py` | Fixed 22.5 mV rule: 24/300 and 45/300 wrong; period-bounded rule: 0/300 at each spread |
| `qarray_timing.py` | 2 dots: ~97 ms per 100×100, ~9.9 ms per 32×32 (machine-dependent). Mac (M4 Pro): 51 / 6.3 ms |

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

- [ ] Spike both on one cell: ray and window queries, speed, step ratio control. **Leaning: our own step model.**
- [ ] Record the choice in `architecture/` as a design call

### 2.2 Units mapping

[§7.2](architecture/07-fleet.md#72-parameters-defaults-and-sweep-ranges) is in physical units (lever arm 0.27 eV/V, charging energy 4 meV, so P ≈ 15 mV). The check scripts use scale-free model units with an `mv` conversion factor.

- [ ] Write down one mapping from the §7.2 hierarchy (wafer → chip → cell) to QArray's `Cdd` and `Cgd`, before A1

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
