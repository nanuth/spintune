# SpinTune v3: Design Document

**Certified, fleet-aware charge tuning for CMOS spin-qubit cells, with an open benchmark that scores any tuner on cost and on how often it is wrong**

| | |
|---|---|
| **Event** | Equal1 × Fsas "Compute the Future", Timișoara HPC Hackathon (InnoWeek 2026). Idea-only pitch Tue 27 Oct 2026; final Fri 27 Nov 2026 at Qiskit Fall Fest |
| **Team** | Duo, 20+ h/week each through November (~180 focused hours). Laptops (Apple M4 Pro, 14 cores) |
| **Judging constraints** | Visible Qiskit use is required. HPC use is optional |
| **Version** | v3, 25 Oct 2026. Supersedes `SpinTune_Design_v2.md` for all technical content |
| **Inputs** | v2 design; `FEASIBILITY_REVIEW_V2.md` (findings R1–R8); Bobi's `bobi_resources/SPINTUNE-2.md` and `bobi_resources/PLAN.md`; `CROSS_REVIEW.md`; new checks run 25 Oct (§1.4) |
| **Source of truth** | This document: *what and why*. `PLAN.md`: the task checklist, to be rebuilt from §15.3. `SPINTUNE-2.md`: pitch notes, to be updated per §15.1 |
| **Status** | Design. Feasibility checks only (scripts in `checks/`). No tuner has been built. Every target is a hypothesis, frozen before the test fleet is generated (§11.6) |

Tags used throughout:
- **[measured]**: we ran it; the script is in `checks/`.
- **[sourced]**: published, with a link.
- **[inferred]**: our reading of a source that doesn't state it outright.
- **[assumed]**: our assumption, always swept.
- **[design call]**: a choice made in this document, which the team can override.

---

## 0. Pitch

> Equal1 builds qubits the way the chip industry builds chips: 29–35 quantum-dot cells per chip, many chips per wafer, one commercial 22 nm FD-SOI process. Every cell still has to be tuned before it can hold a qubit, and nobody can watch thousands of cells. An unattended tuner has two jobs: be cheap, and never say a cell is ready when it isn't.
>
> **SpinTune is a charge tuner that proves its answer and learns from the fleet.**
> - **It proves its answer.** Before it declares a cell ready, it certifies the electron count against the empty region of the device. The rule holds across the whole range of devices a fab produces.
> - **It learns from the fleet.** The bring-up logs of earlier chips, plus the cells already tuned on the same chip, tell it where to look and how coarsely it can scan. That is data Equal1 already has.
>
> It ships with an open benchmark. The benchmark has frozen virtual fleets modelled on published 22FDX statistics, metered measurements, and one success definition. Any tuner (ours, a commercial one, or a lab script) is scored on cost *and* on how often it falsely claims success, on-premises, without calibration data leaving the site.

**What we have already measured** (25 Oct, simulated cells; §1.4):
- **Shortcuts miscount silently.** We tested v2's own rule: "no transition for 1.5 typical charge periods means the device is empty". It declared the wrong electron count on **8–15% of cells**, every one with a charge period ≥ 25 mV. The v3 certificate made **0 errors in 600** noiseless trials across the full 5–40 mV range.
- **We know roughly how much a fleet can save.** We simulated a perfect line reader on noiseless cells.
  - Certified tuning that starts at the right answer, the irreducible floor, costs **380 pixels** on average.
  - Starting from the chip's earlier cells costs **442**. A cold start costs **563**.
  - So in the ideal case, chip history saves about a fifth of the measurement, and nothing can save more than about a third.
  - Most of the saving comes from knowing the charge period, which lets the tuner scan more coarsely.
  - The benchmark measures how much of that survives sensor noise, latching, a real reader and unfamiliar chips.
- **Guessing without measuring rarely works.** Setting a cell to the fleet-average voltage lands in the target charge state only **1–6%** of the time under sourced spreads. Using the chip's earlier cells raises that to 6–12%. Some measurement is always needed; the question is how little.

### If it works: what changes

1. **No silent failures.**
   - Every declared cell carries a certificate. False successes are measured against a pre-registered ceiling of 1%.
   - Across 29 cells × many chips, a tuner that never lies is worth more than a fast one.
2. **Bring-up logs become an asset.** Each chip's tuning makes the next chip cheaper.
   - **Pre-registered targets:**
     - ≥ 90% reliability;
     - ≤ 1% false successes;
     - a cost confidence interval entirely below the cold start;
     - never worse than the cold start on chips unlike the fleet.
   - In the ideal case, chip history saves about a fifth and nothing saves more than about a third. So we pitch "certified and cheaper", not "2× fewer measurements".
3. **The field gets a common yardstick.**
   - The community's data-needs review notes that there is **no standard success metric** for autotuning, so published results can't be compared ([arXiv 2312.14322](https://arxiv.org/abs/2312.14322)).
   - The benchmark (fixed fleets, metered measurements, one success definition, a false-success count) lets Equal1 score any vendor's tuner against its own device statistics.
4. **The fab gets a number to design to:** how tuning cost grows with fabrication spread, and at what spread learning from the fleet starts to pay (§12).
5. **It runs anywhere**, on a laptop or an on-premises cluster. That's the sovereign, offline angle for Fsas.
6. **A quantitative answer to "where should the exchange gate operate, and does charge noise matter there?"**
   - A Qiskit model of the CZ gate, built from the device Hamiltonian, splits the two-qubit error budget into charge noise, dephasing, pulse error and the residual floor (§8).

**What it does not claim:**
- It covers charge-state tuning of already-formed dots. At rf-readout rates that's well under a second of integration per cell. The value is trust and automation at scale, not hours saved.
- It makes no physical gate-fidelity claim, no quantum-advantage claim, and no claim about any commercial tuner.
- The fleet is *modelled on* published 22FDX statistics. It is not calibrated to Equal1's cells (§3.1, §7.2).
- Everything is simulated until real scans are available (§7.6).

**If it doesn't work, we report it straight.** The headline is chosen by a pre-registered rule once headroom is measured (gate G0, §11.4).
- If there is little avoidable cost left, the headline becomes the certified tuner plus the benchmark, with the measured headroom as a finding.
- The Qiskit error budget is a result either way.

---

## 1. What changed in v3, and why

### 1.1 Review of v2 (`FEASIBILITY_REVIEW_V2.md`) → resolutions

| Finding | Resolution | Where |
|---|---|---|
| **R1** The empty-anchor rule can silently miscount | Replaced by a **certificate**. Transition-free lengths are set from the fleet's *maximum* charge period, not the prior's typical one. Rays run along both axes plus the diagonal. Each line crossing must be visible and have the right sign. The tuner abstains if the domain can't fit the certificate. Tested: the v2 rule failed on 8–15% of cells, the certificate on 0/600 [measured]. Noisy and missed-line tests added to G1/G2. Floor re-estimated | §5.1, §1.4 |
| **R2** The lattice tracker assumes line indices before anchoring | Lattice tracker dropped. **Anchor-first ray descent**: there is no inference about absolute charge numbers before the certificate, and the prior only chooses where to start and how coarsely to scan. An ambiguity unit test is required. Ray and mosaic schedules are explicit; T2 is a billed 3×3 mosaic | §5, §6.1 |
| **R3** Two test wafers can't support claims about new wafers | Test fleet is **20 wafers × 5 chips × 10 cells**. Bootstrap resamples whole wafers. OOD fleets reuse the same underlying cells with one parameter changed | §7.4, §11.5 |
| **R4** Information access is confounded with algorithm quality | Added **T3-H**, classical search seeded by the same chip history, and **T3-M**, Bobi's fleet-mean start. Two explicit comparisons: history vs none in the same policy, and learned vs conventional with equal information. The primary classical comparator is chosen on validation. Histories hold only the tuner's own declarations, including its mistakes. All-10-cell totals are reported | §6.2–6.4, §11 |
| **R5** The template mixes the transport and SEB-sensing configurations | Template rebuilt on the paper's **SEB + double-dot configuration (Fig. 4c)**, verified 25 Oct: SEB between QT0 and QT1, dots between QT1/QT2 and QT2/QA1. Tuning plane is (QT1, QA1). Wording changed to "modelled on"; pitch qualified | §3.1, §0 |
| **R6** The quantum acceptance tests rely on equivalences that don't hold | Zeeman convention fixed to (ΔE_z/4)(ZI − IZ) and checks rerun [measured]. Hann limit is now J_max ≤ ΔE_z/5. The pure-ZZ formula holds to 1% only for J_max/ΔE_z ≤ 0.09. The map uses full propagation through an exact 2×2 reduction (0.3 core-hours). RB is validated on known Markovian channels; quasi-static results are descriptive. The IBM run is a scheduled demo with a fallback; the free allowance is 10 min per **rolling 28 days** | §8, §10, §11.4 |
| **R7** Time-correlated noise and QDarts success need explicit semantics | **Persistent simulator state** across queries; per-query reset is a labelled ablation. QDarts success means the dominant charge state has probability ≥ 0.9. The time model is spelled out. A time budget B_t is pre-specified, and time is reported separately from pixels | §4.3, §11.2–11.3 |
| **R8** The protected scope is too large for 180 h | Smaller protected core. The learned probe estimator and set encoder are optional, after G0. The **sensor-only G0 is a week-2 milestone**. C2 compute benchmarked (2×2 block method) | §2, §12, §15 |

### 1.2 What we took from Bobi's plan, and what we didn't

**Adopted**

| Bobi's idea | How v3 uses it | Where |
|---|---|---|
| Learn the prior from **simulated tuning logs**, "the data Equal1 would already have" | The fleet prior and the hierarchy are fitted only from training-fleet tuning logs, never from simulator parameters | §6.4, §7.5 |
| **Never worse** on chips unlike the fleet | Pre-registered robustness bar in G3(e) | §11.4 |
| **Fleet-mean init** as a named curve: "if the full prior ≈ fleet-mean init, the claim becomes 'fleet statistics give X'" | Tuner **T3-M** and comparison (c) | §6.2, §6.3 |
| Plain numpy/json **interfaces**, trace and prior files, the `spintune/` module map | Adapted: rays, sessions, judging after the run | Appendix A |
| Task list with **Needs / Done**, tracks, a written **critical path**, off-path work given to whoever is blocked | Rebuilt for v3 | §15.3–15.5 |
| **Tuesday is an idea-only pitch** | Evidence slides are backup only | §15.1 |
| 32×32 windows; drift by **2D cross-correlation**, with no ML | 32×32 is the drift window; window sizes {16, 32, 64} | §4.1, §9 |
| Cross-correlation check reused as a **multi-dot convergence test** | Kept for the multi-dot stretch goal | §3.4, §9 |
| Regime label **"bad"** (low SNR, latching) | A reader output that triggers abstention | §5.3 |
| **Oracle-label ablation** (PLAN T11) | Oracle-assisted mode | §5.4 |
| 6-dot run with **iterative sweeps, a 5-pass cap**, and cold vs per-position prior | Stretch, conditional on Equal1 confirming the layout | §3.4 |
| Q&A table and "don't say" list | Kept in the pitch notes, with corrected answers | §15.1 |

**Not adopted, and why:**
- **The "double-dot regime" target.** In QArray, 73–91% of random 32×32 windows already qualify [measured, `regime_check.py`].
- **The 10% lognormal fleet with a single shared back-gate offset.** The fleet-mean start hits (1,1) on 100% of such devices [measured]. Sourced spreads are used instead (§7).
- **BoTorch BO as the search policy.**
  - A scalar window score can't count electrons.
  - BoTorch's overhead is 0.05–0.17 s per step [measured, `bo_overhead.py`], more than the simulation itself.
  - It's kept only as an optional comparator, T-BO.
- **A budget of 300 windows (307,200 px).** Nothing fails at that budget, so reliability tells you nothing. The free `span` argument is also gone; pitches are fixed instead.
- **The compute table's basis**, "every step is a fresh simulation", and the **median** as the headline statistic.
- **QFlow as training data.** It's used only as an external test.
- **The 72 ns trade-press CZ figure for physics.** The v3 paper gives 200 ns.
- **The 6-dot run on the main path.** Equal1's 22FDX cells are linear arrays of ≤ 3 dots [sourced].

### 1.3 Decisions this document makes [design calls; confirm or override]

These settle the four questions in `CROSS_REVIEW.md` §7, plus four new ones.

1. **Target:** the (1,1) charge state, established by certificate and count.
2. **6-dot run:** a stretch goal, conditional on Equal1 confirming such a layout.
3. **Search policy:** anchor-first ray descent, shared by every search tuner. This is neither v2's lattice tracker (R2 shows it can't resolve whole-electron offsets before anchoring) nor BoTorch.
4. **Source of truth:** this document for *what and why*, `PLAN.md` for the checklist, `SPINTUNE-2.md` for pitch notes.
5. **Headline branches are pre-registered** on the measured headroom (G0).
6. **Device template:** the paper's SEB + double-dot configuration, tuning plane (QT1, QA1).
7. **Budget B = 40,000 px.** That's one full-domain coarse mosaic plus a confirmation, i.e. the manual fallback a failed autotune triggers.
8. **Confirmation** is one 16×16 window; certificate lengths are as in §5.1.
9. **Primary cost metric (changed after the builder review):**
   - The headline cost is the **paired cost among cells where both tuners succeed**. Reliability is tested separately.
   - The restricted mean with B = 40,000 px is secondary.
   - **Why:** a certified run costs ~400 px, so charging 40,000 px per failure would make every cost gate a count of a few dozen failures.
10. **Charge period in the in-distribution fleets:**
    - P ≈ 15 mV ± 17% per cell.
    - The design tolerance of 7.5–30 mV sets **P_max = 30 mV**.
    - The 5–40 mV range is a separate "wide-period" scenario.
11. **C2 runs two labelled scenarios:** Equal1's measured Si/SiGe device, and a 22FDX projection (§8.5).
12. **RF is simulated; DC is only a re-costing.** Each run is simulated once in the RF scenario; DC time is computed from the same query log.

### 1.4 Evidence status (25 Oct 2026)

| Item | Status | Result |
|---|---|---|
| Main environment: QArray 1.6.0, Qiskit 2.6.1, Aer 0.18.0, qiskit-experiments 0.14.2, Samplomatic 0.21.0, Python 3.12 | **[measured]** installs | `StandardRB`, `InterleavedRB`, `LayerFidelity`, `PauliEvolutionGate`, `InjectNoise`, `Twirl`, `optimal_Vg` present |
| QDarts 1.0.5, own environment (numpy 1.26) | **[measured]** runs | 2 dots + sensor: 0.2 s at 32×32, 0.3 s at 64×64. t_c of 5 vs 80 µeV changes the scan by ~15% of the signal range |
| QArray timing (one thread, noise and latching, T = 300 mK) | **[measured]** | 2 dots: 97 ms per 100×100, 9.9 ms per 32×32. 4 dots: 116 / 12.4 ms |
| Charge cells are congruent in constant capacitance | **[measured]** | (1,1), (2,2), (3,3): 3,011–3,023 px each, so a window alone can't give the count |
| Zero-measurement success | **[measured]** | v1 spreads: 82–100%. Sourced spreads (σ_cell 22 mV, die 74 mV): fleet mean **1–6%**, earlier-cells mean **6–12%**, for P = 15–25 mV |
| **v2 anchor rule** | **[measured]** `anchor_check.py` | Declared "empty" on occupied cells in **24/300** (start spread 22 mV) and **45/300** (77 mV) cells, all with P ≥ 25 mV. The **v3 certificate: 0/600** (noiseless, perfect reader, P ~ U[5, 40] mV) |
| Certificate fits inside a ±300 mV domain | **[measured]** Monte Carlo of the §7.2 hierarchy | **99.70%** of cells (99.93% if the low side is −350 mV) |
| **Cost floor and headroom, ideal case** | **[measured]** perfect reader, noiseless, the §6.1 policy (locate, then certify with crossings; period measured first when unknown). Diagonal ray and confirmation added analytically. `headroom_v3.py` | **In-distribution fleet** (P ≈ 15 mV ± 17%, P_max 30 mV): oracle start **380 px** mean, chip-history start (26 mV spread, P known to ±20%) **442**, fleet-mean start **573**, cold start (design spec only) **563**. **h ≈ 32%**; history/cold = **0.79**. **Wide-period scenario** (P 5–40 mV): 445 / 492 / 794 / 765 px; h ≈ 42%; history/cold 0.64. An earlier estimate (342/354/436 px, `headroom_pitch.py`) skipped the crossing requirement and is **superseded** |
| Bobi's "double" target | **[measured]** `regime_check.py` | 73–91% of random 32×32 windows already qualify |
| BoTorch overhead (3D, GP refit + qLogEI) | **[measured]** `bo_overhead.py` | 0.05–0.17 s per step at 50–300 observations |
| **v2 Zeeman convention** | **[measured]** confirms review R6 | v2 used (ΔE_z/2)(ZI − IZ), which doubles the gradient. v2's "Hann 1−F ≤ 1.2×10⁻⁶ for J ≤ ΔE_z/3" is **superseded** |
| **Hann CZ pulse, standard convention** | **[measured]** `cz_v3_check.py`, `cz_v3_scan.py` | The nominal error oscillates with J_max/ΔE_z (e.g. 4×10⁻⁵ at 0.32, 2×10⁻⁶ at 0.33). Worst case up to a given ratio: ≤ 1×10⁻⁶ up to 0.15; ≤ 3.4×10⁻⁶ up to 0.21; ≤ 1×10⁻⁴ up to 0.35. **Design limit: J_max ≤ ΔE_z/5** |
| **Pure-ZZ formula vs full Hamiltonian** (local corrections fixed at nominal) | **[measured]** | Excess infidelity over 0.8 sin²(πδJ/4J) ≈ **1.15·(J_max/ΔE_z)²**: 0.03% at 0.017, 0.5–0.7% at 0.07–0.08, 2.9% at 0.16, 12–19% at 0.32. Agreement within 1% needs J_max/ΔE_z ≤ 0.09. Reproduces the review's 5.2031×10⁻⁵ point (its J = 20 MHz in the old convention equals J = 10 MHz here) |
| C2 propagation cost | **[measured]** | The exact 2×2 odd-block propagator matches 4×4 `expm` to 7×10⁻¹⁵. 1,000 draws × 2,000 slices take 0.12 s per map point, so **10⁴ points ≈ 0.3 core-hours**, vs ≈ 27 with a 4×4 `expm` per draw |
| CZ quasi-static error is pure ZZ; v1's `CPhase` model is 3× too pessimistic | **[measured]** | Holds within the validity range above |
| Equal1 22FDX cell configurations | **[sourced]**, verified 25 Oct against [2412.08422v2](https://arxiv.org/html/2412.08422v2) | Transport: dots QT0/QT1 and QT1/QT2, QT1 the barrier. **SEB + double dot (Fig. 4c,f): SEB between QT0 and QT1, double dot between QT1, QT2 and QA1**; barriers under QT2 and QA1; data at 700 mK; rf reflectometry at 75.5 MHz |
| IBM Quantum Open Plan | **[sourced]** 25 Oct ([plans](https://quantum.cloud.ibm.com/docs/en/guides/plans-overview)) | Up to **10 min per rolling 28-day window**, us-east only. A promotion offers +180 min over 12 months (as of 16 Mar 2026) |
| Tuners, reader, benchmark | Not started | — |

All scripts are in `checks/` (copied 25 Oct, see `checks/README.md`). They still need to be committed (§15.1).

---

## 2. Goals, non-goals, anti-goals

**Goals**
1. **C1 (primary question):**
   - On unseen simulated cells, does a fleet- and chip-history-informed warm start reduce *certified* charge-tuning cost at equal reliability?
   - It is compared with the same policy started cold, and with the best classical tuner given the same information.
   - Whether it is the headline is set by G0 (§11.4).
2. **C4 (deliverable either way):** the open benchmark. It contains:
   - the device generator and frozen fleets;
   - the metered measurement interface with persistent device state;
   - the certificate and the one success definition;
   - the baselines, including the oracle-start floor T★;
   - scripts that regenerate every figure from logs.
3. **Trust:** the false-success rate is a primary metric for every tuner, and the certificate is a deliverable in its own right.
4. **C2 (protected, because Qiskit is required):**
   - a model-based CZ error budget built from the device Hamiltonian;
   - an Aer RB pipeline validated on known channels;
   - an IBM hardware run, as a scheduled demonstration with a fallback.
5. **C3 (stretch, first to cut):** drift detection and local re-tune.

**Non-goals**
- Dot formation, barrier pinch-off, spin readout, and qubit-level calibration on spins.
- Estimating tunnel coupling, lever arms or spin parameters from charge data. This is infeasible in this regime (§8.4).
- Joint tuning of a multi-cell chip or a 6-dot array (§3.4).
- BO-based search (optional comparator only).
- Replacing or integrating with any commercial tuner.
- Real Equal1 hardware. We use it if offered; nothing depends on it.

**Anti-goals (a failure even if it technically works)**
- A headline that comes from an easy fleet, a weak baseline, a generous cold-start box, or a cost metric or budget picked after seeing results.
- A tuner that looks cheap because it stops early and wrongly. False successes are failures.
- Evaluator ground truth leaking into anything a tuner can see, including its history.
- Quantum for show (§10.3), or calling a model-based Aer result "verification" of a physical qubit.
- Unsourced or outdated numbers on slides.

---

## 3. Scope and device template

### 3.1 Primary device: a 22FDX SEB-sensed double dot, modelled on Equal1's cells

```text
 source ── QA0 ── QT0 ── QT1 ── QT2 ── QA1 ── drain        (+ global back gate BG under the buried oxide)
 (QR0)   spacer   └─ SEB ─┘└ dot A ┘└ dot B ┘    spacer (QR1)
          rf reflectometry on the source, 75.5 MHz
```

| | Value | Status |
|---|---|---|
| Gates | QA0, QT0, QT1, QT2, QA1 in series between doped source and drain. QA0 and QA1 are spacers. A back gate reaches the substrate through a via. There are no plunger gates; barrier gates and back gate act as plungers | [sourced] 2412.08422v2, Fig. 1, Table 1 |
| Configuration | SEB + double dot: "a SEB forming between QT0 and QT1, with a double quantum dot forming between QT1, QT2, and QA1". Barriers are formed under QT2 and QA1 | [sourced] Fig. 4c,f |
| Inter-dot barrier | QT2 (the gate shared by the two sensed dots). Held fixed during charge tuning | [inferred] |
| Charge-tuning plane | (QT1, QA1) at fixed QT2 and BG. Each swept gate is next to one dot; the other dot sees it through next-nearest coupling | [design call]. The paper does not name the swept axes; question 1 for Equal1 (§14) |
| Sensor | The SEB, next to QT1. Sweeping QT1 detunes the sensor strongly, so the interface models a **compensated** sensor by default (virtual compensation on QT0). An uncompensated sensor is a stress scenario | Compensation [assumed] |
| Sensor sensitivity | Dot A, adjacent to the SEB, gives larger steps than dot B. Ratio 2–4 [assumed], swept. This matters for the certificate's visibility test | [assumed] |
| Reservoirs | The SEB is tunnel-coupled to the source; dot A loads through the QT1 barrier [inferred]. How dot B loads (from the drain through QA1, or only via dot A) isn't stated. Its lead transitions are modelled as prone to latching | [assumed]; question 2 (§14) |
| Carrier | Electrons | [sourced] 2412.08422v2, [2412.08302v1](https://arxiv.org/html/2412.08302v1), [equal1.com/technology](https://www.equal1.com/technology) |
| Published operating data | V_QT1 = 350 / 390 / 420 mV for decoupled / separating / merged dots (transport configuration, where QT1 is the barrier). Data at 700 mK (Figs. 2, 4) and 70 mK (Fig. 3). Lever arm 0.27 eV/V | [sourced]; which gate the lever arm refers to in this configuration is [assumed] |

**Why not the transport configuration?**
- v2 combined it with the SEB. In transport, the dots sit between QT0/QT1 and QT1/QT2 with QT1 as the barrier.
- A series double dot in transport conducts only near triple points, so a charge-sensing reader doesn't apply.

**Status of this template:** our reading of the published papers, not a confirmed Bell-1 specification. The generator is described as *modelled on* the published devices.

**Hidden coupling structure in the generator:**
- Each dot couples to its swept gate with lever arm α. Next-nearest couplings are x_A·α (QA1 → dot A) and x_B·α (QT1 → dot B), with x ~ 0.1–0.4 [assumed].
- QT2 and BG couple to both dots. Their fixed voltages enter as offsets.
- Inter-dot capacitance is ±20%.
- The SEB couples to QT1 and to both dots, with dot A coupled more strongly.

**Secondary template:** a generic double dot with plungers P1 and P2, an inter-dot barrier, and a sensor dot. It's for comparison with the autotuning literature and public datasets.

### 3.2 What "a chip" means here

- Equal1 reports 29 NMOS + PMOS cells per chip (its technology page says 35), each a linear array of at most 3 dots [sourced].
- **The unit of tuning is one cell.**
- A fleet "chip" is 10 cells sharing die-level parameters. A "wafer" groups chips sharing wafer-level parameters (§7.1).

### 3.3 Simulators

- **QArray 1.6.0** (constant capacitance, Rust backend) [measured].
  - **Use:** all in-distribution and most OOD fleets.
  - **Strengths:** fast, with analytic ground truth (`optimal_Vg`).
  - **Limits:** identical charge cells, no tunnel coupling, no dot formation.
- **QDarts 1.0.5** ([repo](https://github.com/qplai/QDarts), [arXiv 2404.02064](https://arxiv.org/abs/2404.02064), MIT licence) [measured].
  - **Physics:** finite tunnel coupling, an exact thermal state, voltage-dependent tunnel couplings, and non-constant charging energy (which breaks the identical-cell symmetry).
  - **Use:** the OOD-simulator fleet.
  - **How it runs:** in its own environment, as a worker process behind the same interface. Latching and 1/f noise are added in our wrapper (§4.3).
- **Fallback if QDarts misbehaves:** QArray plus our own rounded inter-dot lineshape layer.
- **Not adopted:**
  - SimCATS: no t_c parameter, and a non-commercial licence.
  - QDFlow: no tunnel coupling, and much slower.

### 3.4 Deferred and stretch

Listed so nobody builds them early:
- **6-dot / multi-cell run** (Bobi's T12). Build it only if Equal1 confirms a linear multi-dot layout to tune pair by pair. If so, use Bobi's design: iterative sweeps, a 5-pass cap, convergence by cross-correlation (§9), and cold vs per-position prior on ~20 chips. `LayerFidelity`/EPLG would then be the natural chain metric.
- **Stages where per-device search may cost more than charge-state tuning:** sensor operating-point search; barrier and tunnel-coupling setting with QDarts' voltage-dependent couplings; virtual-gate calibration. These are candidates for a follow-up C1 if G0 shows little headroom. They are not designed here.
- t_c and lever-arm estimation in the charge-qubit regime; noise learning; valley physics; real-Equal1 replay.

---

## 4. The measurement interface (the only view of a device)

**Rule:**
- Tuners never see device parameters, noiseless maps or labels. They act only through a **session**, which bills every query.
- Only the evaluator sees ground truth, and it judges *after* the run.
- **The only exception is public metadata:** chip ID, wafer ID, cell index and die position (x, y), which a fab always knows.

### 4.1 Queries [design call]

| Query | Shape | Pixels | Use |
|---|---|---:|---|
| `window(center, pitch, size)` | 2D, size ∈ {16, 32, 64} | 256 / 1,024 / 4,096 | Confirmation, mosaic tiles, drift reference (32×32) |
| `ray(start, direction, pitch, n)` | 1D, n ∈ {16, 32, 64} | 16 / 32 / 64 | Descent, certificate, measuring the period |

- **Pitch:** one of {0.5, 1, 2, 4} mV per query.
  - The largest window spans 256 mV.
  - A ray at 2 mV spans 128 mV.
- **Domain:** [−300, +300] mV per axis around the design-nominal target.
  - Queries that would leave it are refused (logged, not billed).
  - The certificate fits inside for 99.7% of cells [measured]. The rest must abstain.
- **Mosaic:** larger regions are covered by tiling 64×64 windows, each billed.
  - The full domain at 4 mV is a 3×3 mosaic: **36,864 px**.
- **Budget:** **B = 40,000 px** per cell.
  - That's a full-domain coarse mosaic plus a certificate and a confirmation: the manual fallback a failed autotune triggers [design call].
  - A run that exceeds B is a failure.
  - B is also the failure charge in the *secondary* restricted-mean metric (§11.3).
  - The success-versus-budget curve is reported from 300 px up to B.
- **Compute cap:** 120 s of tuner computation per cell [assumed].

### 4.2 Cost model (pixels are not time)

```text
t_query = n_px · t_int + t_setup + n_lines · t_settle + |ΔV_jump| / slew
```

- **Within a query**, the sweep runs at the pixel rate (fast gate lines).
- **ΔV_jump** is the DC move from where the previous query ended to where this one starts, at the DC slew rate.
- **Instrument time** is cumulative per cell, and the persistent noise processes evolve in it (§4.3).

| Term | RF scenario (Equal1-relevant) | DC scenario | Status |
|---|---|---|---|
| t_int per pixel | 10 µs | 1 ms | [assumed], swept |
| t_setup per query | 20 ms | 20 ms | [assumed], swept |
| t_settle per line | 1 ms | 5 ms | [assumed] |
| DC slew | 1 V/s | 1 V/s | [assumed] |

- **One simulation, two costings:**
  - Every run is simulated once, in the RF scenario. Per-pixel SNR, telegraph switching and latching are all defined at the RF pixel rate and in RF instrument time.
  - DC time is a re-costing of the same query log, not a separate run.
- **Time budget B_t (RF):** 1.25 × the RF time of a full-domain mosaic plus a certificate and a confirmation, i.e. T2's whole protocol.
  - The harness computes it once from the frozen constants and freezes it. That's ≈ 5 s with the defaults.
  - A run that exceeds B_t is a failure.
  - The DC equivalent (≈ 54 s) is used only for the DC re-costing.
- **Reported:** pixels (primary), RF and DC time, query count, and tuner compute time.

### 4.3 Simulation behind the interface [design call; review R7]

- **Deterministic part:** a lazy tile cache. Noiseless occupancy and sensor maps are computed on demand per pitch and stored per cell.
- **Persistent stochastic state:** for each cell session, telegraph fluctuators, 1/f drift and latched occupancy carry over between queries. They are drawn along the actual acquisition path (raster or ray order) in simulated instrument time. Queries are simulated in the order they are issued.
- **Noise parameters (defaults [assumed], swept):**
  - **White noise:** SNR = (dot-A step height) / (per-pixel noise σ) = 10 at the RF pixel time. Dot-B steps are smaller by the SEB sensitivity ratio (§7.2).
  - **Telegraph noise:** 2 fluctuators per dot. Each shifts that dot's lines by 0.05–0.2·P, with switching rates log-uniform over 1–100 Hz in instrument time.
  - **Latching:** applied per pixel step, at the probabilities in §7.2.
- **Common random numbers:** each cell's noise trajectories are pre-drawn as a function of instrument time, from a seed. Every tuner sees the same noise process, so comparisons are paired.
- **Ablation:** "per-query reset", labelled as a simplified scenario. The persistent run is the reference.
- **QDarts** runs as a worker that returns noiseless tiles; the wrapper adds the stochastic parts.

Code-level interfaces: Appendix A.

---

## 5. Reading the device: certificate, count, confirm

### 5.1 The anchor certificate [design call; review R1]

A window alone can't tell (1,1) from (2,2) [measured]. Every tuner must therefore certify an **empty (0,0) region** before it may declare a charge state.

**Constants (frozen with the fleet spec):**
- **P_max:** the upper end of the design tolerance for the addition voltage along a swept-gate axis. It is part of each scenario's spec.
  - **30 mV** for the in-distribution and OOD QArray fleets (design nominal 15 mV, tolerance ×/÷ 2).
  - **40 mV** for the wide-period scenario.
  - For QDarts, computed from its generator, including the larger first addition energy.
  - The OOD-spec fleet (§7.4) tests what happens when real devices exceed P_max.
- **r_m,max = 0.3:** the largest shift of one dot's lines when the other dot gains an electron, as a fraction of P.
- **L = 1.25 · (1 + r_m,max) · P_max:** the required transition-free length. That's **49 mV** at P_max = 30 mV and 65 mV at 40 mV.

**Certificate for a candidate empty point v0 (every ray billed; all must hold):**
1. **Axis rays.** For each axis (−QT1 and −QA1), there is a ray through v0 that:
   - crosses a visible transition above v0;
   - has no transition for at least L below that crossing.

   One ray, cast upward from v0 − L·e until it crosses a transition, satisfies this. So does the last descent ray, if it ended at v0 after crossing a line.
2. **Diagonal ray.** From v0 along −(1, 1)/√2, at least √2·L, transition-free. This is redundancy against one missed line.
3. **Sign and noise floor on rays.**
   - Each crossing's step sign must match electron addition, with the polarity calibrated from the session's first crossings.
   - The noise floor is measured on the transition-free stretch.
   - Rays do **not** decide which dot a line belongs to.
4. **Visibility per dot, in 2D.**
   - The confirmation window (§5.2) must show the two first lines that bound the certified empty region, with the two distinct orientations: dot-A lines steep in the (QT1, QA1) plane, dot-B lines shallow.
   - Each must reach step SNR ≥ s_min (tuned on validation).
   - **Step SNR** = (step height / per-pixel σ) × √(n/2), for a matched filter averaging n pixels on each side.
   - A tuner may repeat a ray or window to average; repeats are billed.
   - If either dot's first line isn't visible, the tuner abstains; it does not conclude "empty".
5. **Domain.** If any required ray would leave the domain, the tuner abstains.
6. **Validity at v0.** Every ray in the certificate must pass through v0. A ray cast before a later move along the other axis no longer counts.

**Count:**
- The target (1,1) cell is the region reached from v0 by crossing dot A's first line once and dot B's once, in the addition direction, and no other line.
- Dot identity comes from orientation in the 2D confirmation window.
- Inter-dot lines on a ray count as transitions: they reset the transition-free stretch.
- No hypothesis tracking is needed, because nothing about absolute charge numbers is inferred before the certificate.

**Why it holds in a constant-capacitance cell:**
- If dot A holds an electron at v0, a ray along −QT1 must cross a dot-A transition within (1 + r_m)·P. The same holds for dot B along −QA1.
- Measured: 0 errors in 600 noiseless trials across P = 5–40 mV with L = 65 mV, compared with 8–15% for the v2 rule [measured]. The pilot repeats this at L = 49 mV on the in-distribution fleet.
- Under noise, a missed line can only produce a silent error if it is invisible on both an axis ray and the diagonal ray. The noisy tests measure how often that happens.

**Pre-registered contingency:** if the ray-only certificate's false-count rate on noisy validation cells exceeds 0.5%, a 16×16 depletion window below v0 (pitch ≤ L/16, 256 px) is added. This is decided before the freeze.

**Required tests (part of G1 and G2):**
- **(a) Noiseless:** across the scenario's full P range up to P_max, and the full cross-coupling range, every cell is either counted correctly or abstains.
- **(b) Noisy:**
  - sensor SNR 3–30, telegraph noise, latching p = 0.8–1.0, injected missed lines;
  - the false-count rate among certified anchors must be ≤ 0.5% on validation.
- **(c) Ambiguity test (R2):**
  - Take two cells whose local scans around the start point are identical, but whose targets lie several periods apart.
  - The policy must not declare before certification, and must declare correctly after it.

### 5.2 Confirmation and declaration

- **Window:** one 16×16 window at the predicted (1,1) centre.
  - **Pitch:** the largest allowed value ≤ P_est/4 (≥ 4 px per period).
  - Allowed pitches are a factor 2 apart, so the span is always 2–4·P_est for P_est from 2 to 32 mV.
  - Above 32 mV (wide-period scenario only), a 32×32 window at 4 mV is used instead.
- **What it must show:** the (0,0) corner, both certified first lines, and the (1,1) cell. The count is then visible in 2D within one billed query.
- **Period check:** if the period fitted in the window differs from P_est by more than 20%, the tuner retries with the corrected value (billed).
- **Declared point V\*:** the point inside (1,1) with the largest margin from the fitted bounding lines.
- **Margin:** **≥ 0.15·P_est** along each bounding line's normal, **and** ≥ 3σ of quasi-static gate noise projected onto that normal (§7.3).
- **Retries** are allowed and billed.
- **Outcome:** the tuner either declares V\* or abstains with a reason.

### 5.3 Reader contract

The **reader** is a small CNN (U-Net-lite) with a 1D variant for rays, shared by all tuners.

- **Input:** a normalised window or ray, plus its pitch.
- **Output per pixel, windows (multi-label):** dot-A line, dot-B line, inter-dot line. Pixels where two families meet, such as triple points, carry both labels.
- **Output per sample, rays:** transition or none, plus step amplitude and sign.
  - Ray transitions are given a dot only provisionally, by step height and spacing, and only to estimate P (§6.1).
  - The 2D window is the authority on which dot a line belongs to.
- **Window-level head:** {no transitions, lines present, bad}. Bobi's "bad" class (low SNR, latching artefact) feeds abstention.
- **Abstention:** a confidence map, plus an abstain flag when confidence along the detected lines falls below a threshold tuned on validation.
- **Labels from the evaluator:**
  - **QArray:** a pixel is a dot-A line if dot A's occupancy changes between it and a neighbour, and so on.
  - **QDarts:** a pixel is labelled where the *dominant* charge configuration changes. Pixels where no configuration reaches probability 0.9 are marked as a transition zone. Line positions are the 0.5-probability contours.
- **Not the reader's job:** the charge count. That comes from the certificate and count, which are algorithmic and tested separately.
- **Training data:** windows and rays from the training fleet only, mixed across pitches and noise levels.

### 5.4 Oracle-assisted development mode

- During development, each tuner also runs with a perfect reader (masks supplied by the evaluator). This tests the search geometry and the budget before reader errors are added. It is Bobi's T11 ablation.
- These results are labelled "oracle-assisted" and are never mixed with sensor-only results.

---

## 6. Tuners and baselines

### 6.1 The shared policy: anchor-first ray descent [design call; review R2]

Every search tuner except T2 runs this policy. They differ only in what they know before the first query:
- a start point s and its uncertainty Σ;
- a belief about the charge period P.

1. **Period first, if unknown.**
   - If the tuner's P belief is wider than ±25% (90% interval), it first casts one 64-px ray centred on s along +QT1.
   - The pitch is the finest that spans ≥ 2·P_max: 1 mV when P_max ≤ 32 mV, otherwise 2 mV.
   - If that ray shows ≥ 2 same-dot crossings, P is known.
2. **Pitch.**
   - Use the largest allowed pitch ≤ P_lo/3, where P_lo is the 5th percentile of the tuner's current belief about P. That gives ≥ 3 px per period.
3. **Locate.**
   - Alternate rays along −QT1 and −QA1, each continuing from where the last one ended.
   - Stop when both axes end in a transition-free stretch ≥ L. No crossing is needed in this phase.
   - The first ray's length is chosen to reach the prior's 2σ point below s.
   - If P is still unknown, estimate it from ≥ 2 same-dot crossings seen while locating.
4. **Certify** at the end point v0 (§5.1).
   - Reuse the last locate ray if it crossed a line. Otherwise cast one ray per axis from v0 − L·e upward to the first crossing.
   - Then cast the diagonal ray.
   - If P is still unknown, cast one 64-px ray above the first line to measure it.
5. **Confirm.** Place the confirmation window at the certified corner plus the estimated half-periods (§5.2).
6. **Declare V\* or abstain.**

This is the policy simulated in `checks/headroom_v3.py` with a perfect reader (§1.4).

The prior **never** sets absolute charge numbers. It only chooses s, the ray lengths and the pitch.

**Left to the builder:** ray lengths, ordering and retry logic, within these rules.

### 6.2 Tuners

| ID | Tuner | Starting knowledge | What it isolates |
|---|---|---|---|
| T★ | **Oracle start:** the shared policy from the true (1,1) centre, with the true P | Truth (evaluator) | The floor: the cost of the mandatory evidence |
| T0 | **Random start:** the shared policy from a uniformly random point in the domain, P unknown | None, not even the design nominal | What a search costs with no knowledge |
| T2 | **Scan-and-fit:** 3×3 mosaic at 4 mV (36,864 px); fit lines (Hough + least squares) to a capacitance model; compute the target analytically; then certificate and confirmation | Design spec only | The physics baseline an Equal1 engineer would propose. Expensive in pixels, strong on reliability |
| T3 | **Ray navigation, cold:** the shared policy with only the **design spec**: s = design-nominal target (the domain centre), Σ = diag(100 mV)², P_nom = 15 mV with tolerance 7.5–30 mV. Its period belief is wider than ±25%, so it measures P first | Design spec | Competitive classical method, in the spirit of ray-based state identification ([Zwolak et al., PRX Quantum 2, 020335 (2021)](https://arxiv.org/abs/2102.11784)) |
| T3-M | **Fleet-mean start (Bobi):** T3 with s = the fleet-mean target, Σ = the fleet covariance, and P from the fleet distribution (all from training logs) | Fleet mean and spread | "What do fleet statistics alone give?" With the default Δ_nom = 0 it differs from T3 only through Σ and the P belief (still wider than ±25%), so it is expected to be about equal [measured, ideal case: 1.02×]. It differs more in the Δ_nom sweep |
| T3-H | **Conventional history:** T3 with s = the running mean of its *own earlier declared* V\* on this chip. For a chip's first cell, s = the running mean over this wafer's earlier chips; with no history at all, the design spec. P = the median of its own earlier measured periods. Σ = the sample spread, or the T3-M values while fewer than 3 points exist | Own chip and wafer history | The strongest classical use of the same information as T6 (R4) |
| T5 | **SpinTune-F:** the shared policy with s, Σ and P from the fleet prior (hierarchical empirical Bayes, fitted from training logs, with a radial term from die position) | Fleet | Value of a learned fleet prior |
| T6 | **SpinTune-H:** T5 plus this chip's and this wafer's own earlier traces, combined by hierarchical shrinkage into a posterior over the chip's offset, scales and P | Fleet + own history | **Headline candidate** |

**Optional, first to cut:**
- **T6-NN:** a learned set encoder or probe CNN in place of shrinkage. Kept only if it beats T6 on validation by ≥ 10% cost.
- **T-BO:** BoTorch with a prior from tuning logs (Bobi's design), as a literature-style comparator.

**Ablations:**
- T6 with the prior fitted on unfiltered logs (§6.4).
- T5 without the radial term.
- Per-query-reset noise (§4.3).

### 6.3 Comparisons (each one answers a different question; review R4)

| | Comparison | Question |
|---|---|---|
| (a) | T6 vs T5, and T3-H vs T3 | Does history help, within the same policy? |
| (b) | **T6 vs T3-H** | With equal information, does learned inference beat a conventional running mean? |
| (c) | T5 vs T3, and T3-M vs T3 (Bobi) | What does the fleet prior give, and what does the fleet mean alone give? |
| (d) | T6 vs the **primary classical comparator** | Is it better than the best classical option? The comparator is chosen on validation among {T2, T3, T3-M, T3-H}, as the one with the lowest paired cost among those meeting T6's reliability minus 2 points. It is frozen at the tag. It is never chosen as the minimum on test |
| (e) | Everything vs T★ | How much avoidable cost is left? |

### 6.4 Histories and tuning logs

- **Test-time history:** only *that tuner's own* earlier traces on this chip and wafer. That includes its declarations (right or wrong), the lines and periods it measured, and its abstentions. Never evaluator truth.
- **Tuning order:** fixed and random, set by seed.
  - Chips are tuned in order on their wafer; chip j sees chips 1…j−1.
  - Cells are tuned in order on their chip; cell k sees cells 1…k−1.
  - Every tuner uses the same order.
- **Reported:**
  - totals over all 10 cells per chip, including the cold first cell and any failures;
  - the gain as a function of k.
- **Training logs (Bobi's T7):** T3 runs with the real reader over the training fleet.
  - Each log entry has a downstream-verification flag (the evaluator's judgement). This mirrors how a fab learns which bring-ups worked.
  - The prior is fitted on **verified** logs [design call]. An ablation fits it on unfiltered logs.
- **Prior file (Bobi's format, extended):**
  - the fleet mean of the target;
  - covariances at wafer, chip and cell level;
  - the radial coefficient;
  - the P model.

---

## 7. The fleet

### 7.1 Structure [design call]

The fleet is hierarchical: **wafer → chip (die) → cell**.

| Level | Shared by | Varies |
|---|---|---|
| Wafer | All cells on the wafer | Common voltage offset (σ_wafer); radial edge-shift amplitude Δ_edge |
| Chip (die) | All cells on the chip | Common-mode offset σ_die; lever-arm scale (±5%); cross-coupling scale (±10%); radial term Δ_edge·(r/R)² from die position |
| Cell | — | Per-dot first-electron offset σ_cell; per-dot lever arms (±10% about the chip scale); cross-coupling; inter-dot capacitance; E_c |

- **Splits are by whole wafer.** Train, validation and test never share a wafer.
- **Hierarchy strength**, the fraction of variance at chip level, is swept (§12).

### 7.2 Parameters (defaults and sweep ranges)

| Parameter | Default | Sweep | Source / status |
|---|---|---|---|
| Lever arm α | 0.27 eV/V × chip scale (lognormal 5%) × cell factor (lognormal 10%) | Centre 0.2–0.4 | [sourced] centre: Equal1 22FDX ([2412.08302v1](https://arxiv.org/html/2412.08302v1)); Quobly/CEA 22FDX 0.2–0.4 ([2501.10146](https://arxiv.org/abs/2501.10146)). Spreads and the gate it refers to in our plane are [assumed] |
| Charging energy E_c | 4 meV × chip scale (lognormal 10%) × cell factor (lognormal 8%) | Centre 2–8 meV | [sourced] centre: 2.0–4.5 meV in multi-gate 22FDX dots (2501.10146). Spreads [assumed] |
| Charge period P = E_c/α, per cell | ≈ 15 mV × lognormal(≈ 17%); chip-level part ≈ 11%, cell-level ≈ 13% | **Wide-period scenario:** P ~ U[5, 40] mV, P_max 40 mV | Derived. The **design spec** gives T3 a nominal 15 mV with a tolerance of 7.5–30 mV; **P_max = 30 mV** sets the certificate length (§5.1) |
| σ_cell, per-dot first-electron spread within a chip | 22 mV | 10–40 mV | [sourced] σ = 22 mV, measured in a **different group's 22FDX transistor-dot array** ([2310.20434](https://arxiv.org/html/2310.20434)), not an Equal1 multi-gate cell. Intel Si/SiGe: 61–63 mV ([2307.04812v2](https://arxiv.org/html/2307.04812v2)) |
| σ_die, chip-to-chip offset (residual after the radial term) | 60 mV | 0–150 mV | [sourced, low–medium confidence] room-temperature threshold-voltage IQR ≈ 100 mV over ~40 dies (2501.10146) |
| Δ_edge, radial edge shift | 0–60 mV (uniform per wafer) | 0–120 mV | [assumed] |
| σ_wafer | 30 mV | 0–80 mV | [assumed] |
| **Δ_nom**, gap between the design-nominal prediction and the true fleet mean | 0 mV | 0–100 mV | [assumed]. Default 0 is conservative (cold = fleet-mean start) |
| Cross-coupling x (next-nearest gate) | 0.25 (cell 0.1–0.4) | 0.1–0.6 | [assumed] |
| Inter-dot capacitance | ±20% around nominal (r_m ≤ 0.3) | ±10–30% | [assumed] |
| SEB sensitivity, dot A : dot B | 3 | 2–4 | [assumed] |
| Temperature | 0.3 K (QArray `T=300`) | 0.35 / 0.5 / 0.75 K | Bell-1 runs at 0.3 K; Equal1 measured at 350/500/750 mK ([2412.01920 v3](https://arxiv.org/html/2412.01920v3)) |
| Sensor white noise | SNR 10 per pixel at the RF t_int, defined on **dot-A** steps (dot B: 10/3) | SNR 5–30 | [assumed]. Definition in §4.3 |
| Telegraph noise | 2 fluctuators per dot, line shift 0.05–0.2·P, rates 1–100 Hz | Amplitude ×0.5–2 | [assumed] |
| Charge noise √S_E at 1 Hz | 4 µeV/√Hz | 1.7–6.5 µeV/√Hz | [sourced] SOI 1.7–6.3 ([2209.01853](https://arxiv.org/abs/2209.01853)); 22FDX p-type median 6.5 ([2507.21306v1](https://arxiv.org/html/2507.21306v1)) |
| Latching | Lead p = 0.95 (dot B 0.85), inter-dot p = 0.99 | 0.8–1.0 | [assumed] |

### 7.3 Charge noise as seen by the gates

- Energy noise converts to gate-voltage noise as √S_V = √S_E/α.
- For 1/f noise, the quasi-static variance is S(1 Hz)·ln(f_high/f_low).
- **Defaults:**
  - f_low = 1/(1000 s) and f_high = 1/t_gate, so the log factor ≈ 20.7 at t_gate = 200 ns;
  - σ_E ≈ 18 µeV and σ_V ≈ 68 µV;
  - dot-to-dot correlation of 0 and 0.5 are both run [assumed].

### 7.4 Fleets [review R3]

| Fleet | Size | Purpose |
|---|---|---|
| Pilot | 5 wafers × 4 chips × 10 cells (200) | Building, debugging, G0, and sizing the test fleet |
| Train | 50 wafers × 20 chips × 10 cells (10,000) | Reader, tuning logs, priors |
| Validation | 10 wafers × 5 chips × 10 cells (500) | Thresholds, hyperparameters and comparator selection for **all** tuners |
| **Test (in-distribution)** | **20 wafers × 5 chips × 10 cells (1,000)**. The pilot may raise this to at most 40 wafers if the wafer-bootstrap CI half-width on the paired cost ratio R_T6/T3 would exceed 0.05 | **Headline**, run once after the freeze |
| OOD-hot / OOD-noisy / OOD-crosstalk | The **same underlying cells** as test wafers 1–10 (500 cells), changing only: 0.75 K / √S_E = 6.5 with SNR 5 / cross-coupling 0.4–0.6. SNR 5 rather than 3: with the 3:1 sensitivity ratio, SNR 3 would put dot B near 1 per pixel | Paired robustness tests |
| OOD-spec (reported, no gate) | The same 500 cells, with E_c scaled so that ~10% of cells exceed P_max | What the certificate does when devices fall outside the design tolerance it relies on |
| OOD-wafer | 10 new wafers × 5 × 10, with σ_wafer and Δ_edge ×2 | Fab-level shift |
| OOD-simulator | QDarts, 10 wafers × 2 chips × 10 cells (200); underlying parameters mapped where defined | Finite t_c, non-constant charging energy |

Bobi's "shifted fleet" (offset back gate, wider spread, more telegraph noise) maps onto OOD-wafer, OOD-crosstalk and OOD-noisy.

### 7.5 Tuning logs (Bobi)

- Training-fleet logs come from T3 with the real reader (§6.4).
- The prior and hierarchy (T5, T6) are fitted only from these logs.
- The generator's parameters are never used for fitting.

### 7.6 External real-device test sets [sourced; none is FD-SOI; none has ground-truth t_c]

| Dataset | What it is | Labels | Tests |
|---|---|---|---|
| **QDSD** ([Zenodo 11402792](https://doi.org/10.5281/zenodo.11402792)), CC-BY-4.0 | Si-MOS and GaAs stability diagrams | 38 single-dot diagrams with transition polylines and electron counts 0–4+ | Certificate and count on real data |
| **Delft D-CSD** ([Zenodo 16363472](https://doi.org/10.5281/zenodo.16363472)), CC-BY-4.0 | 9,849 charge-sensed Si/SiGe and Ge/SiGe scans | None; **we hand-label 50** (~4 h) | Reader F1 on real charge-sensed data |
| **QFlow 2.0 `exp_small`** ([NIST](https://data.nist.gov/od/id/66492819760D3FF6E05324570681BA721894)), registration required | 756 measured scans | No dot / single / double | Optional; first to cut. Test only |

---

## 8. Physics layer: the Qiskit CZ error-budget study (C2)

### 8.1 Conventions [design call]

- Energies are in µeV; frequencies (J/h, ΔE_z/h) in MHz.
- **Exchange:** J = 4·U·t_c² / (U² − ε²) ([QTCAD](https://docs.nanoacademic.com/qtcad/theory_spin_fem/exchange/)). ε is measured from the (1,1) centre along the detuning axis.
- **Validity:**
  - t_c ≤ 0.1·(U − |ε|) [assumed];
  - gate voltages inside the domain;
  - **J_max ≤ ΔE_z/5**, the pulse limit (§8.2).
- **Barrier control:** t_c = t₀·10^((V_QT2 − V₀)/V_dec), with V_dec swept over 33–110 mV per decade ([2410.15590v2](https://arxiv.org/html/2410.15590v2), [2411.13882](https://arxiv.org/abs/2411.13882)) [sourced].
  - In this configuration the inter-dot barrier is QT2 (§3.1). The paper's 350–420 mV values refer to QT1 in the transport configuration.

### 8.2 CZ gate model [measured checks]

```text
H(t) = (J(t)/4)(XX + YY + ZZ) + (ΔE_z/4)(ZI − IZ)     ΔE_z = difference of the two qubit frequencies
       odd-subspace splitting = √(J² + ΔE_z²)
Hann pulse: J(t) = J_max · sin²(π t / T),  T = 1/J_max  (∫J dt = 1/2)
local Z corrections calibrated once at nominal, in the ΔE_z rotating frame
```

**Propagation:**
- |00⟩ and |11⟩ only pick up a phase, so the exact propagator reduces to a 2×2 problem in the odd subspace.
- It is computed in closed form per time slice and vectorised over noise draws.
- It matches the 4×4 matrix exponential to 7×10⁻¹⁵ [measured].

**Checks** (`cz_v3_check.py`, `cz_v3_scan.py`):
- **Nominal Hann error** oscillates with J_max/ΔE_z. The worst case up to a given ratio is:
  - ≤ 1×10⁻⁶ up to 0.15;
  - ≤ 3.4×10⁻⁶ up to 0.21;
  - ≤ 1×10⁻⁴ up to 0.35.

  **The design limit is J_max ≤ ΔE_z/5.**
- **Quasi-static δJ with fixed corrections:**
  - The error is close to the pure-ZZ form 1 − F = 0.8·sin²(δφ/4), with δφ = π·δJ/J.
  - The full Hamiltonian adds ≈ 1.15·(J_max/ΔE_z)² relative excess.
  - So the formula is a **large-gradient approximation**, valid to 1% for J_max/ΔE_z ≤ 0.09. At J_max = ΔE_z/5, the full result is ≈ 5% higher.
- **Square pulses** need synchronisation with the Zeeman splitting. They are not used.
- **Equal1's CZ** is 200 ns, with F_CZ = 99.30% at 350 mK and 98.41% at 750 mK (Si/SiGe, [2412.01920 v3](https://arxiv.org/html/2412.01920v3)) [sourced].
  - A 200 ns Hann pulse means J_max = 5 MHz.
  - That's within J_max ≤ ΔE_z/5 for ΔE_z ≥ 25 MHz.

### 8.3 Noise and error-budget components

| Component | Model | Inputs |
|---|---|---|
| Charge noise through J | Per shot or RB sequence, draw one quasi-static (δε_A, δε_B, δV_QT2) from §7.3 and hold it for the whole circuit. Evaluate J exactly, so second order at ε = 0 is kept | §7.3; ε, U, V_dec |
| Single-qubit dephasing during the gate | δf = (∂f/∂ε)·δε, quasi-static, calibrated to T2* = 5.9–11.1 µs [sourced, 2412.01920 v3] | ∂f/∂ε [assumed, micromagnet scenario] |
| Residual coherent pulse error | From the Hann-pulse Hamiltonian | J_max, ΔE_z (20–300 MHz) [assumed] |
| Residual floor | Depolarising, set so the total equals Equal1's reported CZ error **at the nominal point** (no double counting). Aer λ = (1 − F_avg)·d/(d − 1), with d = 4 ([Aer docs](https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.noise.depolarizing_error.html)) | Reported F_CZ |

### 8.4 Why the tuner doesn't estimate these parameters

- **t_c:** at Equal1's exchange (J ≈ 2.5–5 MHz, U ≈ 2 meV), t_c ≈ 2–3 µeV. A polarisation-line fit ([DiCarlo et al., PRL 92, 226801](https://arxiv.org/abs/cond-mat/0311308)) constrains t_c only for t_c ≳ 0.5·k_BT_e ≈ 13 µeV at 0.3 K.
- **α:** the thermal linewidth (≈ 3.5·k_BT/α ≈ 0.34 mV) is below the 0.5 mV minimum pitch.
- **∂f/∂ε and ΔE_z:** charge measurements can't see them.

So C2 is a **model-based map over sourced and assumed ranges**, not a tuner capability.

### 8.5 The study and its expected outcome

**Two labelled platform scenarios [design call]** (Equal1 question 5 is still open):

| Scenario | Charge noise | T2*, CZ duration and floor | Status |
|---|---|---|---|
| **S1: Equal1's measured device (Si/SiGe)** | √S_E 0.3–1 µeV/√Hz ([2209.07242](https://arxiv.org/abs/2209.07242)) | T2* 5.9–11.1 µs; 200 ns CZ; floor set to F_CZ = 99.30% (350 mK) ([2412.01920 v3](https://arxiv.org/html/2412.01920v3)) | Calibrated to a published device |
| **S2: 22FDX projection** | √S_E 1.7–6.5 µeV/√Hz (§7.2) | S1's T2*, pulse and floor reused as placeholders | **Projection**, labelled so on every figure |

The O1 statement is made separately for each scenario.

**Map** the CZ error budget (each §8.3 component, and the total) over:
- ε ∈ [−U/2, U/2];
- J_max ∈ [1 MHz, ΔE_z/5];
- ΔE_z ∈ [20, 300] MHz;
- √S_E over its sourced range, with dot-to-dot correlation 0 and 0.5;
- ∂f/∂ε over its assumed range.

Full propagation is used everywhere (0.3 core-hours, [measured basis]). The ZZ formula serves only as a cross-check inside its validity range.

**Two rules are marked on the map:**
- **O0:** cell centre, default barrier;
- **O1:** ε = 0 with J_max = ΔE_z/5.

**Back-of-envelope with the defaults** (pure-ZZ, so valid at small J_max/ΔE_z):
- **Barrier channel:** δJ/J ≈ 0.3%, so infidelity ≈ 4×10⁻⁶, independent of the barrier setting.
- **Detuning channel** at ε = U/2: infidelity ≈ 0.7–1.5×10⁻⁴; negligible at ε = 0.
- **Dephasing** during a 200 ns gate: of order 10⁻³.
- **Pulse error:** ≤ 3.4×10⁻⁶ at J_max ≤ ΔE_z/5.
- **For comparison:** Equal1's measured CZ error is ≈ 7×10⁻³.

**Expected result:**
- Charge noise through J is at most a few percent of the budget.
- The best point is ε = 0 with J at the pulse limit, i.e. rule O1.
- If the map confirms this, the result is the budget figure plus, per scenario: *"O1 is sufficient; the remaining two-qubit error is dephasing and the residual floor"*. In S2 that claim covers only the FD-SOI charge-noise channel.
- If some regions lose ≥ 0.1 percentage points under O1, those regions are the result.

---

## 9. Drift (stretch, C3, first to cut)

- **Injection:** physical, through the persistent telegraph and 1/f processes of §4.3.
- **Monitoring:** every k simulated jobs, a 32×32 reference window (Bobi). It must **contain at least two transition lines** near V\*; a featureless patch can't be cross-correlated.
- **Detection:** 2D cross-correlation shift against the reference, with no ML. The reader checks the charge state.
- **Ground truth for "needs re-tune":** V\* no longer meets the §11.2 success definition.
- **Recovery:** a local re-tune seeded at V\*, compared with a restart at equal success definition and total cost.
- **Reuse:** the same check is the convergence test for a multi-dot run, if that stretch goal happens (§3.4).

---

## 10. Quantum layer: what Qiskit does, and what the course materials give us

Qiskit use is required, so this layer is protected from cuts. The IBM hardware run is the one cuttable part.

### 10.1 Model-based CZ and RB (C2)

| Step | Tool | Course source |
|---|---|---|
| Device Hamiltonian → CZ unitary per noise draw (Hann pulse, exact 2×2 block, time-sliced); cross-checked with Qiskit operators | `SparsePauliOp`, `Operator`, `PauliEvolutionGate` | Unit 4 Lesson 2 |
| Gate fidelity vs ideal CZ | `average_gate_fidelity` | Unit 1 |
| **Pipeline validation first:** StandardRB + InterleavedRB in Aer on *known Markovian* CZ errors (2Q depolarising at 3 strengths, plus one Pauli channel) | `qiskit_aer`, `qiskit_experiments` `StandardRB`, `InterleavedRB` | Units 1, 3 |
| Then quasi-static scenarios: one `NoiseModel` per draw, held for a whole sequence, averaged | Same | Units 1, 3 |
| *(optional, cut early)* Pauli twirling of the coherent ZZ error | Samplomatic `Twirl`, `InjectNoise` | Unit 3 Lesson 3 |

**Acceptance (review R6):**
- **Markovian validation:** IRB must recover the injected average gate error within its reported systematic bounds plus the fit's confidence interval ([qiskit-experiments RB manual](https://qiskit-community.github.io/qiskit-experiments/manuals/verification/randomized_benchmarking.html)).
- **Quasi-static scenarios:** reported descriptively, not as pass/fail. Report the decay curves, single-exponential fit quality, the uncertainty from sampling sequences and noise draws, and the deviation from the single-gate analytic reference. Noise held fixed across a sequence need not decay as a single exponential ([arXiv 1504.05307](https://arxiv.org/abs/1504.05307)).

### 10.2 IBM hardware run (a scheduled demonstration with a fallback)

- **What:** our StandardRB + InterleavedRB code on one native two-qubit gate of an IBM Heron device, through the **Open Plan**: up to 10 min per **rolling 28-day window**, us-east only, set up as in course Lab 0.
- **Record:**
  - the physical pair, the transpiled circuits and the job IDs;
  - timestamps and whether the data can be analysed;
  - a *descriptive* comparison with the backend-reported two-qubit error, with the protocol and timestamp.
- **Why only descriptive:** IBM's published metric includes a single-qubit Clifford layer and may come from an earlier calibration ([IBM QPU information](https://quantum.cloud.ibm.com/docs/en/guides/qpu-information)). A disagreement triggers investigation; it does not fail the run.
- **What this shows:** that our benchmarking code runs end to end on real hardware. It says nothing about spin qubits, and is labelled that way.
- **Schedule:** develop on `FakeTorino`, submit by 13 Nov, use ≤ 3 QPU minutes.
- **Fallback:** the same code on the fake backend, plus any recorded run.

### 10.3 Course content deliberately not used

- **Quantum kernels / QSVM:** no evidence of benefit over a CNN; it would read as quantum for show.
- **QAOA, VQE, SQD:** no job to do. A two-site Hubbard model is solved exactly in microseconds.
- **Layer fidelity / EPLG:** reserved for the multi-cell stretch goal.

### 10.4 Pitch framing from the course

IBM's quantum-centric supercomputing material lists **calibration** among the classical tasks that "remain essential throughout the quantum workflow" (Unit 0, slide 69).

---

## 11. How success is measured (frozen before the test fleet runs)

### 11.1 Primary question

*On unseen simulated 22FDX-style cells, does a fleet- and chip-history-informed warm start reduce certified charge-tuning cost at equal reliability?* It is compared with:
- the same policy started cold;
- conventional use of the same history;
- the best classical tuner.

### 11.2 Success for one cell (all must hold)

1. The tuner declares V\* after a passing certificate (§5.1) and confirmation (§5.2).
2. **QArray fleets:** the evaluator's noiseless (T = 0) occupancy at V\* is (1,1).
   **QDarts fleet:** at V\*, the dominant charge configuration in the thermal state at the fleet temperature is (1,1), with probability ≥ 0.9.
3. **Margin:** ≥ 0.15·P along every bounding transition's normal (for QDarts, measured to the 0.5-probability contours), and ≥ 3σ of projected gate noise.

**Failure** is anything else:
- no declaration within B or within the RF time budget B_t;
- an abstention;
- a declared V\* that fails step 2 or 3. That last case is a **false success**: counted as a failure, charged B in the secondary restricted mean, and reported separately.

Cells whose certificate can't fit in the domain (≈ 0.3%) are recorded. Results are shown for all cells and for reachable cells.

### 11.3 Metrics

| Outcome | Metric |
|---|---|
| **Reliability (primary)** | Fraction of cells succeeding, with 95% CI; paired reliability difference between tuners |
| **Cost (primary)** | **Paired cost ratio** R_X/Y = Σ cost_X / Σ cost_Y in pixels, over the cells where **both** X and Y succeed |
| Cost (secondary, pre-registered) | Restricted mean pixels mean(min(T_success, B)), charging B = 40,000 px per failure; the same ratio in RF time; DC time; query count |
| Cost net of floor | Paired cost minus T★'s, over the same cells |
| Full picture | Success-vs-budget curves (pixels and RF time); median and p90 among successes; failures by type |
| Trust | False-success rate; abstention rate; certificate false-count rate |
| Hierarchy | Cost vs cell position k; **all-10-cell totals per chip**, including cell 1 and failures |
| Runtime | Tuner compute per cell; simulator time |
| C2 | Error-budget map; O1 loss vs map optimum; Markovian RB recovery; quasi-static decay report |
| C3 (stretch) | Detection recall, false alarms per hour, delay, recovery cost |

### 11.4 Gates (thresholds frozen at the tagged commit)

| Gate | Question | Pass criterion |
|---|---|---|
| **G0 Headroom** (end of week 2; sensor-only, on pilot + validation) | Is there avoidable cost to save? | h = 1 − R_T★/ref in pixels. "ref" is whichever cold classical baseline, T2 or T3, has the lower paired cost. RF-time headroom is reported alongside. **Pre-registered branches, decided on pixels:** <br>**h ≥ 30%:** C1 is the headline; G3(c) practical target ≤ 0.8. <br>**10% ≤ h < 30%:** headline = certified tuning + benchmark; C1 is a measured secondary result; G3(c) practical target ≤ 0.9; T6-NN dropped. <br>**h < 10%:** report the headroom; no practical target; build nothing learned beyond T5/T6 shrinkage; put the time into C2 and the external tests. <br>**Pre-pilot estimate: h ≈ 32%** (ideal case, in-distribution fleet, §1.4). That is at the boundary between the top two branches; noise and the real reader decide. The fleet is never made harder or easier to change h |
| **G1 Generator and certificate** | Does the simulator do what we say, and does the certificate hold? | Lattice matches `optimal_Vg` within 1 px. Noise PSD slope within the set value ± 0.1. Certificate tests §5.1 (a) and (c) pass: 100% correct-or-abstain on noiseless cells over each scenario's P range up to P_max; the ambiguity test passes. Persistent-state test passes (§4.3) |
| **G2 Reader** | Can we read scans, and does the certificate survive the real reader? | Transition-mask F1 ≥ 0.9 in-distribution. Certificate false-count rate ≤ 0.5% on noisy validation cells (§5.1 b). Always reported, never hidden: OOD results, QDSD electron-count accuracy, F1 on 50 hand-labelled D-CSD scans |
| **G3 Warm start (C1)**, ID test | Does it save measurement without losing trust? | (a) T6 reliability ≥ 90%, **and** the lower 95% bound of (reliability T6 − T3) ≥ −2 points. <br>(b) False successes ≤ 1% of declared successes (upper 95% bound ≤ 2%). <br>(c) Wafer-bootstrap 95% CI of R_T6/T3 entirely < 1, **and** the point estimate ≤ the practical target of the G0 branch. <br>(d) CI of R_T6/comparator entirely < 1, with reliability non-inferior as in (a). Otherwise it is reported as "no gain over conventional use of the same information". <br>(e) **Never worse on unfamiliar chips (Bobi):** on every OOD fleet, the upper CI bound of R_T6/T3 ≤ 1.05, the point estimate of (reliability T6 − T3) ≥ −2 points, and its lower 95% bound ≥ −5 points. <br>(f) ≥ 75% reliability on each OOD fleet |
| **G3h Hierarchy** | Does chip history add value beyond the fleet? | CI of R_T6/T5 entirely < 1 for cells k ≥ 3 |
| **G4 Error budget (C2)** | Is the Qiskit model sound, and what does it say? | (a) Block propagator vs 4×4 exponential: difference ≤ 10⁻¹². <br>Pure-ZZ formula vs full H, for J_max/ΔE_z ≤ 0.08 and δJ/J ∈ {0.3%, 1%, 2%}: \|Δ − ZZ\| ≤ 0.01·ZZ + 10⁻⁷, where Δ = (1 − F_full(δJ)) − (1 − F_full(0)). Outside that range the full H is the only reference. <br>(b) Aer IRB recovers the injected Markovian errors within systematic bounds plus fit CI. <br>(c) Quasi-static and IBM results are reported descriptively, not as pass/fail. <br>Result: the map and the O1 statement per scenario |
| **G5 Drift** (C3, stretch) | Cheap recovery? | Recall ≥ 90% at ≤ 1 false alarm per simulated hour; recovery ≤ 25% of restart cost at equal success |

### 11.5 Statistics

- **Paired design:** every tuner runs on the same cells with the same pre-drawn noise trajectories (§4.3).
- **Wafer-level cluster bootstrap:** resample *wafers* with replacement, keeping their chips, cells, histories and tuner seeds intact (review R3).
- **OOD comparisons** are paired by underlying cell.
- **Paired cost ratios** use only cells where both tuners succeed. Reliability differences use all cells. Both get wafer-bootstrap CIs, and every report states how many cells were dropped from each ratio.
- **Seeds:** 3 per stochastic tuner on the pilot; up to 5 at final if the pilot's interval widths justify it.
- **Comparator choice:** the primary classical comparator and every threshold are chosen on validation, never on test.
- **Precision:** 90% reliability on 1,000 cells gives a binomial half-width of ≈ 1.9 points before clustering. Clustered widths come from the pilot.

### 11.6 Pre-registration

- **Freeze:** after validation and before the test fleets are generated, tag a commit containing:
  - this document's thresholds and the G0 branch taken;
  - fleet seeds and configuration;
  - all tuners' hyperparameters and the chosen primary comparator;
  - the certificate constants;
  - the analysis script.
- **After the freeze:** results are reported against the tag. Any later change is reported as a deviation.

---

## 12. Compute plan

- **Measured:**
  - QArray: ~10 ms per 32×32 window; rays are cheaper.
  - QDarts: ~0.2 s per window.
  - The tile cache makes repeated queries < 1 ms.
- **Ray-policy runs** take ~10–20 queries, so ≲ 0.2 s per run with reader inference [estimate]. T2's mosaic adds ~0.5 s.
- **BoTorch** is needed only for the optional T-BO.
- **HPC is optional.** The full spread map is the HPC showcase if cluster hours appear.

| Job | Count | Core-hours | Laptop, 14 cores |
|---|---|---:|---:|
| Frozen evaluation: ~10 tuner configs × 3 seeds × 3,000 QArray cells (ID + OOD) | ~90,000 runs | ~5–10 | < 1 h |
| OOD-simulator (QDarts) | ~6,000 runs × ~15 queries | ~1.5–5 | < 1 h |
| Training-fleet tuning logs (T3 over 10,000 cells) | 10,000 runs | ~1 | minutes |
| Coarse spread map: 3 σ_die × 2 hierarchy strengths × 2 noise levels × 1,000 cells × 4 tuners (T2, T3, T3-H, T6) × 3 seeds | ~144,000 runs | ~10–15 | ~1 h |
| Full spread map (optional HPC): 5 σ_die × 3 σ_cell × 3 hierarchy × 3 noise × 2 temperatures × 1,000 × 4 × 3 | ~3.2 M runs | ~200–300 | ~1 day (or ~2 h on a 128-core node) |
| C2 map: 10⁴ points × 10³ draws, exact 2×2 block | — | **0.3 [measured basis]** | minutes |
| Reader training (CPU) | — | ~10–30 | overnight |
| Optional T-BO: 0.05–0.17 s per step × ~50 steps × 3,000 cells × 2 variants × 3 seeds | — | ~15–25 | ~2 h |

Pin backend threads to 1 per worker and parallelise across cells.

---

## 13. Prerequisites, and which we can get ourselves

| # | Prerequisite | Needed for | Can we get it ourselves? | How / status |
|---|---|---|---|---|
| 1 | Main environment (Python 3.12, QArray, Qiskit stack, PyTorch; BoTorch only for T-BO) | Everything | **Yes** | Verified 25 Oct. Lockfile (`uv`) still to commit |
| 2 | QDarts environment | OOD-simulator fleet | **Yes, verified** | Runs on this Mac; wrap as a worker |
| 3 | Git repo with the check scripts | §1.4 evidence, §11.6 freeze | **Yes** | Scripts copied into `checks/` on 25 Oct, with a README. `git init` and the commit are still to do |
| 4 | Sourced device parameters | §7 | **Yes, done** | Low confidence: σ_die, Δ_edge, σ_wafer, cross-coupling, SEB sensitivity |
| 5 | Equal1 device facts | §3 | **Mostly, done** | SEB + double-dot configuration verified against the paper on 25 Oct. Open: swept axes, how dot B loads, back-gate value, which platform Bell-1 uses |
| 6 | Real scans for external tests | §7.6 | **Partly** | QDSD and D-CSD are direct downloads; QFlow 2.0 needs registration (optional). We can also email the authors of [arXiv 2604.13662](https://arxiv.org/abs/2604.13662) |
| 7 | Compute | §12 | **Yes** | Laptop for everything except the full spread map |
| 8 | Real quantum hardware | §10.2 | **Yes** | IBM Open Plan: 10 min per rolling 28 days, us-east instance |
| 9 | Physics sanity review | §8 | **Partly** | Analytic cross-checks done, including the convention fix. Equal1 judges at the pitch |
| 10 | Spin-qubit hardware or Equal1 scans | Sim-to-real | **No** | Ask (§14). Nothing depends on it |
| 11 | R2P capstone or extra IBM access | Optional | **Unknown** | Ask the programme leads |

---

## 14. Questions for Equal1 (most important first)

1. **Layout and axes:**
   - Is our reading of the SEB + double-dot configuration right: SEB between QT0 and QT1, dots between QT1/QT2 and QT2/QA1, with QT2 as the inter-dot barrier?
   - Which gates do you sweep for charge tuning, and how do you compensate the SEB?
2. **Reservoir of the far dot:** does the QT2/QA1 dot load from the drain through QA1, or only via the near dot?
3. **Distributions:**
   - What are the cryogenic distributions across cells, chips and wafers of first-electron voltage, lever arms, E_c and cross-capacitance?
   - How much of that is shared within a chip?
   - Is a chip 29 cells or 35?
4. **Cost today:** how long does charge tuning take per cell today, and which step dominates (Bobi's question)? This tells us whether certification or speed matters more.
5. **Platform:** do Bell-1 qubits run on the 22FDX cells or on the Si/SiGe devices? NMOS or PMOS?
6. **Spins:** how are spins driven in 22FDX, and what is ΔE_z?
7. **Noise:** what are measured √S_E and its exponent in 22FDX?
8. **Exchange:** the t_c(V) and J(V) slopes; residual J; the CZ pulse shape.
9. **Scans:** could you share ~50 raw charge-sensed scans, even anonymised, as a frozen test?
10. **Multi-dot (Bobi):** is there a linear multi-dot array you'd want tuned pair by pair?
11. **Cooldowns:** how much do the electrostatics shift between cooldowns?

---

## 15. Plan

### 15.1 Before the pitch (Tue 27 Oct, idea-only)

- [ ] **Repo:** `git init`; lockfiles for both environments; commit `checks/`.
- [ ] **Update `SPINTUNE-2.md` to match this document:**
  - the (1,1) target with a certificate;
  - "fleet modelled on published 22FDX statistics";
  - electrons and the SEB + double-dot layout;
  - v3 CZ numbers (200 ns; 99.30% / 98.41%), with the trade-press numbers labelled "vendor-reported";
  - the FD-SOI noise range;
  - "pre-registered target", not "≥ 2×";
  - "never worse on unfamiliar chips";
  - "learned from bring-up logs";
  - Qiskit protected;
  - the 6-dot run as a question for Equal1;
  - the report-straight sentence;
  - drop "every tuner step is a fresh simulation" as the HPC argument.
- [ ] **Q&A additions:**
  - *"Isn't charge tuning cheap already?"* — "In pixels, yes, and we measured how cheap. In the ideal case, chip history saves about a fifth and nothing saves more than about a third. Most of that comes from knowing the charge period, so the tuner can scan more coarsely. The rest of the value is a certificate that can't silently miscount, plus a benchmark that measures every tuner's false-success rate."
  - *"Why not BO?"* — "A scalar score can't count electrons, and its per-step overhead is larger than the simulation."
- [ ] **Backup slides only:**
  1. the anchor miscount (8–15% vs 0/600);
  2. the headroom bound (380 / 442 / 563 px: floor / chip history / cold);
  3. the CZ gate from the Hamiltonian.
- [ ] **Rehearse** the §14 questions.

### 15.2 Tracks

| Track | Content |
|---|---|
| A | Simulation, interface, evaluator |
| B | Certificate and baselines |
| C | Reader and external data |
| D | Fleet learning |
| E | Scoring |
| F | Qiskit (protected, off the critical path) |

### 15.3 Tasks (Bobi's format: "Needs" = hard dependencies; "Done" = the check that must pass)

**Track A: simulation, interface, evaluator**
- **A0. Setup.** `git init`, two environments with lockfiles, `checks/` committed, both laptops working.
  - **Done:** every `checks/` script reruns from the repo on both machines, with outputs saved.
- **A1. Fleet generator.** Hierarchical sampler (§7) for both templates; whole-wafer splits; matched OOD variants.
  - **Needs:** A0.
  - **Done:** the same seed gives the same fleet; a 16-cell scan grid per fleet looks visibly different; the lattice matches `optimal_Vg` within 1 px.
- **A2. Session interface.** Windows and rays, ledger, cost model, caps, domain refusal, tile cache, persistent state, common random numbers.
  - **Needs:** A1.
  - **Done:** the ledger equals the sum of billed pixels; the time model passes unit tests; a latched state survives a query boundary, and the reset ablation differs.
- **A3. Evaluator.** `judge()`, the (1,1) polygon, margins, masks, the QDarts dominant-state rule.
  - **Needs:** A1.
  - **Done:** 5 hand-checked cells; masks agree with occupancy changes.
- **A4. QDarts worker.**
  - **Needs:** A2.
  - **Done:** same interface; speed test on 20 cells; OOD-simulator fleet size fixed.

**Track B: certificate and baselines**
- **B1. Certificate, count and declaration** (§5.1–5.2), with the oracle reader first.
  - **Needs:** A2, A3.
  - **Done:** G1 certificate tests (a) and (c).
- **B2. T★ and T3, then T3-M and T3-H.**
  - **Needs:** B1.
  - **Done:** traces written; oracle-assisted cost table on the pilot (the G0 preview).
- **B3. T0 and T2** (mosaic and fit).
  - **Needs:** B1.
  - **Done:** both run end to end on the pilot.

**Track C: reader and external data**
- **C1. Training samples.** Windows and rays with masks from the training fleet, all pitches and noise levels.
  - **Needs:** A3.
  - **Done:** class balance reported; 20 random samples per class eyeballed.
- **C2. Reader** (U-Net-lite, ray head, abstention).
  - **Needs:** C1.
  - **Done:** G2 F1 bar; certificate false-count rate with the real reader on noisy validation cells.
- **C3. External sets.** QDSD electron counts; hand-label 50 D-CSD scans.
  - **Needs:** C2.
  - **Done:** numbers in the results table.

**Track D: fleet learning**
- **D1. Training-fleet tuning logs** (Bobi T7). T3 with the real reader over the training fleet.
  - **Needs:** B2, C2.
  - **Done:** one trace per cell; success and false-success rates reported.
- **D2. Fit the hierarchical prior from verified logs** (Bobi T8), plus the unfiltered-log ablation.
  - **Needs:** D1.
  - **Done:** prior file written; 50% and 90% ellipse coverage on validation within ±5 points.
- **D3. T5 and T6.**
  - **Needs:** D2.
  - **Done:** both beat T3 on 50 validation cells, or the reason is understood (Bobi's T9 rule).

**Track E: scoring**
- **E1. Harness** (Bobi T10): tuners × fleets × seeds; wafer bootstrap; success-vs-budget plots; automatic PASS/FAIL per gate.
  - **Needs:** B2.
  - **Done:** one command regenerates every figure and verdict from saved traces.
- **E2. Validation runs**, comparator selection, thresholds, **freeze tag**.
  - **Needs:** D3, B3, C2.
  - **Done:** tag pushed with the §11.6 contents.
- **E3. Test and OOD runs**: G3, G3h, external tests, oracle-label ablation (Bobi T11).
  - **Needs:** E2, A4, C3.
  - **Done:** results table and the gate slide.
- **E4. Coarse spread map** (the full map only with cluster hours).
  - **Needs:** E2.

**Track F: Qiskit (protected, off the critical path)**
- **F1. CZ Hamiltonian module**: standard convention, Hann pulse, 2×2 block propagator, ZZ cross-check.
  - **Needs:** A0.
  - **Done:** G4(a).
- **F2. Error-budget map**, with O0 and O1.
  - **Needs:** F1.
  - **Done:** the map figure and the O1 statement.
- **F3. Aer RB/IRB**: Markovian validation, then the quasi-static scenarios.
  - **Needs:** F1.
  - **Done:** G4(b) and the descriptive quasi-static report.
- **F4. IBM Open Plan run.**
  - **Needs:** F3 working on `FakeTorino`.
  - **Done:** job IDs, pair, timestamps, analysed data and the descriptive comparison, or the documented fallback.

**Stretch (only after E2):**
- drift (C3, G5);
- T6-NN and T-BO;
- the 6-dot / multi-cell run, if Equal1 confirms the layout;
- QFlow 2.0;
- Samplomatic twirling;
- a dashboard.

### 15.4 Schedule

| Week | Tasks | Gate at the end of the week |
|---|---|---|
| W1 (28 Oct – 3 Nov) | A0–A3, B1, B2 (oracle reader), F1 | G1; oracle-assisted headroom (G0 preview) |
| W2 (4 – 10 Nov) | A4, B3, C1, C2, F2; start C3 | G2; **sensor-only G0, which picks the headline branch** |
| W3 (11 – 17 Nov) | D1–D3, E1, E2; F3; **submit F4 by 13 Nov** | **Freeze tag by 17 Nov** |
| W4 (18 – 24 Nov) | E3, E4, C3; stretch if time | G3, G3h, G4 |
| 25 – 26 Nov | Demo and dry run | — |
| 27 Nov | Final | — |

### 15.5 Critical path

**A1 → A2 → B1 → B2 → D1 → D2 → D3 → E2 → E3.**
- The reader (C1 → C2) joins the path at D1, because the training logs must come from the real reader.
- Track F, B3, A4, C3 and E1 sit off the path. Give them to whoever is blocked.

### 15.6 Cut order, and what is never cut

**Cut in this order:**
1. Drift (C3).
2. The full spread map (keep the coarse one).
3. T6-NN and T-BO.
4. QFlow 2.0.
5. Samplomatic twirling.
6. The IBM hardware run (keep the Aer and `FakeTorino` pipeline).
7. The coarse map, down to one axis.
8. Reduce the OOD-simulator fleet (never remove it).

**Never cut:**
- the interface and evaluator;
- the certificate;
- T★, T2, T3, T3-H, T5, T6;
- G0–G3h, the wafer bootstrap and the freeze;
- the C2 Hamiltonian map with Aer RB validation (the Qiskit requirement).

### 15.7 Demo (27 Nov)

1. A new virtual chip.
2. **The certificate in action:** rays light up. On a wide-period cell, the "shortcut" rule miscounts while SpinTune certifies or abstains.
3. Cells 1–10 tuned in sequence, with the cost counter against the T★ floor, showing whatever was measured.
4. The false-success counter for every tuner.
5. The headroom result with its confidence interval, and the G0 branch taken.
6. The CZ error budget from the Hamiltonian in Qiskit, with Aer RB, plus the IBM run if it happened.
7. The gates slide: pass or fail, including any failures.

### 15.8 Left to the builder

These are free choices, within the rules above:
- ray lengths, ordering and retry logic;
- the reader's architecture details;
- how the hierarchical model is parameterised;
- T2's line-fitting algorithm;
- plotting;
- file formats beyond Appendix A;
- details of mapping parameters into QDarts.

---

## 16. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| **Headroom is marginal.** The ideal-case estimate (h ≈ 32%) sits at the G0 threshold; noise and a real reader may move it either way | **High: it decides the headline** | Pre-registered G0 branches. The certificate and benchmark carry the headline in the lower branches. RF time and query count are reported. Costlier tuning stages are listed for follow-up (§3.4) |
| The paired cost ratio hides a tuner that fails on hard cells | Medium | Reliability non-inferiority is part of every cost claim (G3 a, d, e). The restricted mean and the number of dropped cells are always reported |
| The certificate abstains too often under noise, so reliability < 90% | Medium | Validation-tuned SNR threshold and pitch; the pre-registered depletion-window contingency (§5.1); abstentions reported |
| Our device mapping (SEB + double dot, plane (QT1, QA1)) is wrong | Medium | "Modelled on" wording; question 1 for Equal1; the generic template as a fallback |
| The compensated-sensor assumption hides real costs | Medium | Uncompensated stress scenario, reported |
| Persistent-state simulation is harder or slower than planned | Medium | Fall back to per-query reset, clearly labelled as simplified |
| Sim-to-real gap | High | QDarts fleet, external data, sourced spreads; the honesty slide |
| The hierarchy structure is assumed | Medium | Swept; question 3 for Equal1 |
| σ_die is low-confidence | Medium | Swept 0–150 mV |
| T2 wins on reliability | Low–Medium | Reported. It's expensive in pixels by construction |
| Scope vs 180 h | Medium | Smaller protected core; cut order; sensor-only G0 in week 2 |
| QDarts install or speed problems | Low–Medium | Verified install; lineshape fallback |
| IBM queue or access problems | Low | Submit by 13 Nov; `FakeTorino` fallback |

---

## 17. References

**Equal1 and 22FDX**
- Equal1 Si/SiGe two-qubit processor (cite v3): [arXiv 2412.01920v3](https://arxiv.org/html/2412.01920v3)
- Equal1 22FDX quantum-dot cells: [arXiv 2412.08422v2](https://arxiv.org/html/2412.08422v2) (Figs. 1, 2, 4), [arXiv 2412.08302v1](https://arxiv.org/html/2412.08302v1)
- 22FDX transistor dots, first-electron spread (different group): [arXiv 2310.20434](https://arxiv.org/html/2310.20434)
- 22FDX multi-gate dots (Quobly/CEA): [arXiv 2501.10146](https://arxiv.org/abs/2501.10146)
- Equal1 technology page: [equal1.com/technology](https://www.equal1.com/technology)

**Noise, tunnel coupling, exchange**
- SOI charge noise: [arXiv 2209.01853](https://arxiv.org/abs/2209.01853)
- 22FDX p-type charge noise: [arXiv 2507.21306v1](https://arxiv.org/html/2507.21306v1)
- Si/SiGe charge noise: [arXiv 2209.07242](https://arxiv.org/abs/2209.07242)
- Correlated noise in a Si/SiGe array: [arXiv 2603.03051](https://arxiv.org/html/2603.03051)
- Intel first-electron variability: [arXiv 2307.04812v2](https://arxiv.org/html/2307.04812v2)
- MOS tunnel-coupling slope: [arXiv 2411.13882](https://arxiv.org/abs/2411.13882)
- Exchange slope and CZ: [arXiv 2410.15590v2](https://arxiv.org/html/2410.15590v2)
- Exchange theory: [QTCAD](https://docs.nanoacademic.com/qtcad/theory_spin_fem/exchange/)
- Polarisation-line t_c: DiCarlo et al., [PRL 92, 226801](https://arxiv.org/abs/cond-mat/0311308)

**Simulators, data, autotuning**
- QArray: [arXiv 2404.04994](https://arxiv.org/abs/2404.04994)
- QDarts: [arXiv 2404.02064](https://arxiv.org/abs/2404.02064), [repo](https://github.com/qplai/QDarts)
- Ray-based state identification: Zwolak et al., [PRX Quantum 2, 020335 (2021)](https://arxiv.org/abs/2102.11784)
- BO tuning: Moon et al. 2020, [PMC7438325](https://pmc.ncbi.nlm.nih.gov/articles/PMC7438325/)
- Real-device data: [QDSD](https://doi.org/10.5281/zenodo.11402792), [Delft D-CSD](https://doi.org/10.5281/zenodo.16363472), [QFlow 2.0](https://data.nist.gov/od/id/66492819760D3FF6E05324570681BA721894)
- Data needs of quantum-dot automation: [arXiv 2312.14322](https://arxiv.org/abs/2312.14322)
- FPGA autotuning (orchestration overhead): [arXiv 2509.19537](https://arxiv.org/abs/2509.19537)

**Qiskit, RB, IBM**
- Aer depolarising channel: [docs](https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.noise.depolarizing_error.html)
- qiskit-experiments RB and IRB systematic bounds: [manual](https://qiskit-community.github.io/qiskit-experiments/manuals/verification/randomized_benchmarking.html)
- RB under correlated (non-Markovian) noise: [arXiv 1504.05307](https://arxiv.org/abs/1504.05307)
- IBM plans (Open Plan, 28-day window): [docs](https://quantum.cloud.ibm.com/docs/en/guides/plans-overview); QPU metric definitions: [docs](https://quantum.cloud.ibm.com/docs/en/guides/qpu-information)
- IBM R2P course, Units 0–4: this folder

**Project documents**
- `SpinTune_Design_v2.md`, `FEASIBILITY_REVIEW.md`, `FEASIBILITY_REVIEW_V2.md`, `CROSS_REVIEW.md`, `bobi_resources/SPINTUNE-2.md`, `bobi_resources/PLAN.md`, `checks/README.md`

---

## Appendix A. Interfaces and code layout (adapted from Bobi's `PLAN.md`)

Plain numpy and json, so the two of you can work on separate pieces.

```text
Cell            dict: hidden params (evaluator only), wafer_id, chip_id, cell_index, die_xy, seed
fleet file      fleets/<name>.npz + fleets/<name>.json   (generator params, seeds, split, matched-OOD map)
Session         s = harness.open(cell, scenario)         # persistent noise/latching state + ledger
s.window(center: float[2], pitch, size) -> float32[size, size]        # billed
s.ray(start: float[2], direction: float[2], pitch, n) -> float32[n]   # billed
s.declare(v_star: float[2], evidence) | s.abstain(reason)             # ends the run
evaluator.judge(cell, trace) -> {success, false_success, margin, occupancy}   # after the run only
tuner.run(s, metadata, history) -> trace
trace           runs/<tuner>/<fleet>/<seed>/<cell>.json:
                queries [{type, args, px, t_query, t_cum}], certificate, declaration, totals {px, rf_s, dc_s, n_queries}
history         this tuner's own earlier traces on this chip and wafer (declarations, measured lines, P, abstentions)
log file        logs/<train_fleet>/<tuner>.jsonl   (training-fleet tuning logs + verification flag)
prior file      priors/<name>.json: {fleet_mean[2], cov_wafer, cov_chip, cov_cell, radial_coeff, P_model}
```

Axes are [QT1, QA1] for the primary template and [P1, P2] for the generic one. QT2, BG and QT0 (sensor compensation) are fixed per scenario.

```text
spintune/
  fleet.py       hierarchical sampling, splits, matched OOD variants        (A1)
  device.py      QArray wrapper, QDarts worker, persistent noise/latching    (A2, A4)
  interface.py   Session: window/ray, ledger, cost model, caps, tile cache   (A2)
  evaluator.py   judge(), margins, masks: the only code that reads params    (A3)
  anchor.py      certificate, count, confirmation, declaration (shared)      (B1)
  tuners/        oracle_start.py, random_start.py, scan_fit.py, raynav.py (T3, T3-M, T3-H), spintune.py (T5, T6)
  reader.py      U-Net-lite + ray head + abstain; training                  (C1, C2)
  prior.py       fit hierarchical prior from verified tuning logs            (D2)
  harness.py     tuners × fleets × seeds, wafer bootstrap, gates, plots      (E1)
  qiskit_cz/     hamiltonian.py (2x2 block), budget_map.py, rb_aer.py, ibm_run.py   (F1–F4)
  drift.py       cross-correlation monitor (stretch)
checks/          evidence scripts (§1.4)
fleets/ runs/ logs/ priors/ figs/     generated output, git-ignored
```
