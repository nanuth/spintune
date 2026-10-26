# SpinTune v4: Design Document

**A benchmark and a reference tuner for charge tuning of CMOS spin-qubit cells: does chip history make tuning cheaper without more wrong charge declarations?**

| | |
|---|---|
| **Event** | Equal1 × Fsas "Compute the Future", Timișoara HPC Hackathon (InnoWeek 2026). Idea-only pitch Tue 27 Oct 2026; final Fri 27 Nov 2026 at Qiskit Fall Fest |
| **Team** | Duo, 20+ h/week each through November (~180 focused hours). Laptops (Apple M4 Pro, 14 cores) |
| **Judging constraints** | Visible Qiskit use is required. HPC use is optional |
| **Version** | v4, 25 Oct 2026 |
| **Related documents** | Feasibility reviews (`FEASIBILITY_REVIEW*.md`, `CROSS_REVIEW.md`); evidence scripts (`checks/README.md`) |
| **Source of truth** | This document: *what and why*. `bobi_resources/PLAN.md`: the task checklist, to be rebuilt from §15.3. `bobi_resources/SPINTUNE-2.md`: pitch notes, to be updated per §15.1 |
| **Status** | Design. Feasibility checks only (scripts in `checks/`, §1.2). No tuner has been built. Every number from `checks/` is an idealized estimate (noiseless cells, perfect reader, one specified policy), not a result. Every target is a hypothesis, frozen before the test fleet is generated (§11.6) |

Tags used throughout:
- **[measured]**: we ran it; the script is in `checks/`.
- **[sourced]**: published, with a link.
- **[inferred]**: our reading of a source that doesn't state it outright.
- **[assumed]**: our assumption, always swept.
- **[design call]**: a choice made in this document, which the team can override.

---

## 0. Pitch

> Equal1 builds qubits the way the chip industry builds chips: 29–35 quantum-dot cells per chip, many chips per wafer, one commercial 22 nm FD-SOI process. Every cell has to be tuned to a known electron count before it can hold a qubit, and at that scale nobody watches each cell. An unattended tuner has two jobs: spend little instrument time, and rarely declare a cell ready when it isn't, at a rate that is measured rather than assumed.
>
> **SpinTune tests whether chip history can make charge tuning cheaper without increasing wrong charge declarations.**
> - **An explicit evidence rule.** Before declaring a charge state, a tuner must show an empty region of the device with a few rays and one 2D window. Under a stated device model and sensing assumptions, that evidence implies the electron count (§5.1). Outside those assumptions its error rate is measured, not assumed.
> - **History as an input, tested against the obvious alternative.** Earlier cells on the same chip and the logs of earlier chips set where to start and how coarsely to scan. We compare that with the same policy started cold, and with a plain running mean of the chip's earlier results.
>
> We are building a reproducible benchmark with explicit evidence, abstention and measurement accounting on literature-informed simulated fleets, with separate tests on public experimental scans. Any tuner is scored on its declared state, margin, measurement cost, time and wrong-declaration rate. Hardware validation depends on access to suitable device data.

**What we have measured so far** (25 Oct; idealized: noiseless simulated cells, perfect line reader; §1.2):
- **A simple stopping rule miscounts silently.** In a descent along one gate axis at a time, "no transition for 1.5 typical charge periods means the device is empty" declared an occupied point empty on **8–15% of cells**, all with a charge period ≥ 25 mV. The period-bounded rule of §5.1 made **0 errors on 300 devices at each of two start spreads** (one-sided 95% upper bound ≈ 1% per spread). That test covers the descent rule with perfect occupancy readout, not the full evidence rule under noise; that is task B1 (§15.3).
- **Exploratory cost of one specified policy.** Every ray and window is metered; 300 in-distribution cells:

  | Start | Pixels | Queries | RF time |
  |---|---:|---:|---:|
  | At the answer (oracle-start reference T★) | 357 | 5.0 | 0.33 s |
  | Chip history, all 10 cells of a chip including the first | 451 | 5.8 | 0.36 s |
  | Cold (design spec only) | 527 | 8.3 | 0.50 s |

  - Chip history costs **0.86×** the cold start in pixels and **0.73×** in RF time. Starting at the answer costs 0.68× and 0.67×.
  - **Pixels are about 1% of RF time.** Query setup and voltage moves dominate, so the time saving comes from fewer queries and shorter moves, not from coarser scans.
  - Knowing only the start point gives 0.86× in pixels and 0.80× in time; knowing only the charge period gives 0.87× and 0.81×.
  - The numbers depend on the policy. Sizing every ray exactly to the evidence it still needs saves ~4% of pixels but makes the cold start 6% slower; the history/cold ratios barely move (0.86 and 0.72), but the oracle-start headroom in time rises from 33% to 44%.
  - These are estimates for one policy on ideal cells, with history drawn from the assumed fleet structure rather than learned from logs. They are not a floor: another policy could gather the same evidence more cheaply. Noise, latching, reader v1 and simulated training-fleet logs come next (G0, §11.4).
- **Guessing without measuring rarely works.** Setting a cell to the fleet-average voltage lands in the target charge state only **1–6%** of the time under sourced spreads; the chip's earlier cells raise that to 6–12%. Some measurement is always needed; the question is how little.

### If it works: what changes

1. **Wrong declarations become a measured, bounded number.**
   - Every declaration carries its evidence. The wrong-declaration rate is reported over all declarations, split into wrong counts and inadequate margins, with an upper confidence bound.
   - Scale is why this matters: at a true 1% rate, a 29-cell chip has a 25% chance of at least one wrong declaration. We claim "≤ 1%" only if the upper bound is ≤ 1%.
2. **Bring-up logs become an input with a measured value.** We report when chip and wafer history reduce cost and when they don't, including a no-gain result against a running mean, and a break-even map over how much variation cells on a chip share (§12).
3. **The field gets an executable yardstick.** The community's data and benchmarking review asks for datasets, benchmarks and standardisation ([Zwolak et al., npj Quantum Inf. 10, 105 (2024)](https://doi.org/10.1038/s41534-024-00878-x)). Fixed fleets, metered queries and one scoring contract let Equal1 score any tuner, ours or not, against its own device statistics (§2.2).
4. **It runs anywhere**, on a laptop or an on-premises cluster. That's the sovereign, offline angle for Fsas.
5. **A model-based answer to "where should the exchange gate operate, and how much does charge noise matter there?"** A Qiskit model of the CZ gate, built from the device Hamiltonian, composes charge noise, dephasing and pulse error into a two-qubit error budget. It is a sensitivity study, conditional on stated assumptions (§8).

**What it does not claim:**
- It covers charge-state tuning of already-formed dots. In our time model that is ~0.3–0.6 s of instrument time per cell at RF rates. The value is trust and automation at scale, not hours saved.
- It does not prove a hardware tuner correct, establish a universal cost floor, or show savings on Equal1 devices.
- It makes no physical gate-fidelity claim, no quantum-advantage claim, and no claim about any commercial tuner.
- The fleet is *modelled on* published 22FDX statistics. The joint structure that creates the history advantage (how much cells on a chip share) is an assumption until Equal1 data say otherwise (§7.2).
- Everything is simulated until real scans are available (§7.6).

**If it doesn't work, we report it straight.** The headline is chosen by a pre-registered rule once headroom is measured on sensor-only query traces (gate G0, §11.4).
- If little avoidable cost is left, the headline is the benchmark and the measured error/cost trade-off, with the headroom as a finding.
- The Qiskit error budget is a result either way.

---

## 1. Design decisions and evidence

### 1.1 Decisions this document makes [design calls; confirm or override]

1. **Target:** the (1,1) charge state, established by the §5.1 evidence and the count. A "double-dot regime" window label is not the target: 73–91% of random 32×32 windows already qualify [measured].
2. **Research question:** *when* does information from previously tuned cells reduce acquisition cost without increasing wrong declarations (§2)? A no-gain result is a valid outcome.
3. **Search policy:** one policy shared by every search tuner: a diagonal descent, then one ray per axis through the candidate empty point (§6.1). Not a lattice tracker (it can't resolve whole-electron offsets before anchoring), and not BoTorch.
4. **An evidence rule, not a proof:** the §5.1 certificate implies the count only under its stated assumptions. Under noise and stress its error rate is measured and reported in three categories: wrong anchor, wrong count, inadequate margin.
5. **Headline branches are pre-registered** on headroom measured from sensor-only query traces (G0), with practical targets set relative to that headroom.
6. **Device template:** the paper's SEB + double-dot configuration, tuning plane (QT1, QA1).
7. **Queries:** rays of 8–64 samples and windows of 16, 32 or 64 px square (§4.1). The shared policy rounds each ray up to 16, 32 or 64 samples, because that makes the cold baseline fastest [measured].
   - **Shared-policy settings** (query sizing, ordering, retries) are tuned on validation to minimise T3's all-cell RF time, and every tuner then uses the same values. That keeps the cold baseline as strong as possible.
8. **Reader:** a signal-processing reader first. A CNN replaces it only if it beats it on validation (§5.3).
9. **Budget B = 40,000 px** per cell, about one full-domain coarse mosaic plus a confirmation: the manual fallback a failed autotune triggers.
10. **Cost metrics:**
    - **Acquisition:** the paired pixel ratio over cells where both tuners succeed. It is conditional on joint success, so it is always shown with the four joint success/failure counts.
    - **Operational:** the all-cell elapsed cost, including tuner compute and a frozen fallback charge for every failure (§11.3).
    - **Speed claims use RF time, never pixels.** Pixels are ~1% of RF time [measured].
11. **Trust claims:** "≤ 1% wrong declarations" is stated only if the one-sided 95% upper bound is ≤ 1%. Otherwise the wording is "observed X%, upper bound Y%".
12. **Success is judged on the nominal device** at V\*, with a margin. Success over a post-declaration hold in the noisy, latched device is reported beside it (§11.2).
13. **Latching is a relaxation rate in instrument time**, not a per-pixel probability (§4.3).
14. **Charge period in the in-distribution fleets:** P ≈ 15 mV ± 17% per cell. The design tolerance of 7.5–30 mV sets **P_max = 30 mV**. The 5–40 mV range is a separate "wide-period" scenario.
15. **C2 runs two labelled scenarios** (Equal1's measured Si/SiGe device; a 22FDX projection) and composes noise channels instead of adding infidelities (§8.3).
16. **RF is simulated; DC is only a re-costing** of the same query log.
17. **Scope:** planning caps per track adding up to 180 h, including 20 h of contingency (§15.2). If a track doesn't fit, its promise shrinks before the contingency is spent.
18. **6-dot run:** a stretch goal, conditional on Equal1 confirming such a layout.

### 1.2 Evidence status (25 Oct 2026)

| Item | Status | Result |
|---|---|---|
| Main environment: QArray 1.6.0, Qiskit 2.6.1, Aer 0.18.0, qiskit-experiments 0.14.2, Samplomatic 0.21.0, Python 3.12 | **[measured]** installs | `StandardRB`, `InterleavedRB`, `LayerFidelity`, `PauliEvolutionGate`, `InjectNoise`, `Twirl`, `optimal_Vg` present |
| QDarts 1.0.5, own environment (numpy 1.26) | **[measured]** runs | 2 dots + sensor: 0.2 s at 32×32, 0.3 s at 64×64. t_c of 5 vs 80 µeV changes the scan by ~15% of the signal range |
| QArray timing (one thread, noise and latching, T = 300 mK) | **[measured]** | 2 dots: 97 ms per 100×100, 9.9 ms per 32×32. 4 dots: 116 / 12.4 ms |
| Charge cells are congruent in constant capacitance | **[measured]** | (1,1), (2,2), (3,3): 3,011–3,023 px each, so a window alone can't give the count |
| Zero-measurement success | **[measured]** | Narrow spreads (lever arms ±15%, offsets within one charge period): 82–100%. Sourced spreads (σ_cell 22 mV, die 74 mV): fleet mean **1–6%**, earlier-cells mean **6–12%**, for P = 15–25 mV |
| **Stopping rules on noiseless cells** | **[measured]** `anchor_check.py`: 300 QArray devices, P ~ U[5, 40] mV, each started at two spreads (22 and 77 mV); perfect occupancy readout; a descent along one axis at a time, stopping rule only | A fixed 22.5 mV rule (1.5 × the typical 15 mV period) declared an occupied point empty on **24/300** and **45/300** devices, all with P ≥ 25 mV. The period-bounded rule (L = 65 mV): **0/300 at each spread** (one-sided 95% bound ≈ 1% each, assuming independence). Not covered: visibility, signs, the 2D window, noise, latching, sensor transitions |
| **Policy cost, idealized** | **[measured]** `headroom_v4.py`: noiseless QArray, perfect reader, the §6.1 policy with every ray and window metered (rays rounded up to 16/32/64 samples and shrunk to fit the ±300 mV domain; integer pixels; confirmation per §5.2; billed retries), RF time per §4.2. History beliefs are drawn around the truth with the §7.2 spreads (start sd 22·√(1+1/k) mV, period 13%·√(1+1/k) after k earlier cells), not fitted from logs | **In-distribution:** T★ 357 px / 5.0 queries / 0.33 s; T3 cold 527 / 8.3 / 0.50 s; T3-M 528 px / 0.50 s; chip history (10-cell chips, cell 1 included) 451 / 5.8 / 0.36 s. History/cold **0.86 in pixels, 0.73 in time**; oracle-start headroom **32% in pixels, 33% in time**. Start knowledge alone 0.86 / 0.80; period knowledge alone 0.87 / 0.81. **Wide-period:** T★ 555, T3 757, history 652 px; history/cold 0.86 / 0.69; headroom 27% / 40%. 0 wrong anchors in 3,600 runs (300 cells × 6 tuner configurations × 2 fleets); ≤ 5/300 abstentions per tuner, from the domain limit |
| Pixels vs time | **[measured]** same script | Pixel integration is **about 1% of RF time** (1.1% and 1.3% for T3; up to 1.6% across tuners and fleets). Setup, settling and DC slew are the rest |
| Descent direction | **[measured]** `headroom_v4.py --axis-descent` | Descending one axis at a time stalls while the other dot is still occupied: its lines cross the axis every P/x (42 mV in a traced cell, below L = 49 mV). T3 then abstained on **19%** (in-distribution) and **22%** (wide) of cells, and cost 1.1–1.2× the pixels and 1.9× the time of the diagonal descent, which abstained on 0–1% |
| Ray sizes | **[measured]** `headroom_v4.py --need-sized` | Rays sized exactly to the missing evidence (8–64 samples) instead of rounded to 16/32/64: −4% pixels, but T3 is 6% (in-distribution) and 12% (wide) slower, with 3–5 more queries per cell. T★ is 11% faster, so the time headroom rises to 44% / 47%. History/cold ratios: 0.86 px, 0.72 / 0.67 time |
| Shortcut under the shared policy | **[measured]** `headroom_v4.py --stop-length 22.5` | With the 1.5-period length (22.5 mV) everywhere: 0/300 wrong anchors in-distribution, **4/300 for T3 and 1/300 for T3-M** in the wide fleet, for 8–10% lower cost. The descent's extra P_lo and the measured period partly protect it. A first point on the cost–risk curve (§6.3 f) |
| "Double-dot regime" as a target | **[measured]** `regime_check.py` | 73–91% of random 32×32 windows already qualify |
| BoTorch overhead (3D, GP refit + qLogEI) | **[measured]** `bo_overhead.py` | 0.05–0.17 s per step at 50–300 observations |
| **Hann CZ pulse, standard convention** | **[measured]** `cz_v3_check.py`, `cz_v3_scan.py` | The nominal error oscillates with J_max/ΔE_z (e.g. 4×10⁻⁵ at 0.32, 2×10⁻⁶ at 0.33). Worst case up to a given ratio: ≤ 1×10⁻⁶ up to 0.15; ≤ 3.4×10⁻⁶ up to 0.21; ≤ 1×10⁻⁴ up to 0.35. **Design limit: J_max ≤ ΔE_z/5** |
| **Pure-ZZ formula vs full Hamiltonian** (local corrections fixed at nominal) | **[measured]** | Excess infidelity over 0.8 sin²(πδJ/4J) ≈ **1.15·(J_max/ΔE_z)²**: 0.03% at 0.017, 0.5–0.7% at 0.07–0.08, 2.9% at 0.16, 12–19% at 0.32. Agreement within 1% needs J_max/ΔE_z ≤ 0.09 |
| C2 propagation cost | **[measured]** | The exact 2×2 odd-block propagator matches 4×4 `expm` to 7×10⁻¹⁵. 1,000 draws × 2,000 slices take 0.12 s per map point, so **10⁴ points ≈ 0.3 core-hours**, vs ≈ 27 with a 4×4 `expm` per draw |
| CZ quasi-static error is pure ZZ; a `CPhase(π + δφ)` error model is 3× too pessimistic | **[measured]** | Holds within the validity range above |
| Equal1 22FDX cell configurations | **[sourced]**, verified against [2412.08422v2](https://arxiv.org/html/2412.08422v2) | Transport: dots QT0/QT1 and QT1/QT2, QT1 the barrier. **SEB + double dot (Fig. 4c,f): SEB between QT0 and QT1, double dot between QT1, QT2 and QA1**; barriers under QT2 and QA1; data at 700 mK; rf reflectometry at 75.5 MHz. In Fig. 4(c) the double-dot response is "overlaid with another set of transitions due to the SEB", and "further analysis is needed to understand each transition in detail" |
| External datasets | **[sourced]** Zenodo records and READMEs | **QDSD:** only single-dot diagrams are labelled; values are measured current; the interpolated CSV set (127 MB) loses information, the raw files are 186 MB. **D-CSD:** 9,850 diagrams selected with a clean/noisy classifier; raw HDF5 holds voltages and values; the default loader resizes to 128×128; no charge-count labels; 1.8 GB |
| RF/FPGA timing in practice | **[sourced]** [Roux et al., IEEE TQE (2026)](https://doi.org/10.1109/TQE.2026.3670353) | A 9.8× faster measurement gave a 2.2× faster total initialization, limited by Python execution. ~27 ms latency per command; stepped DC slews of 0.04–0.39 V/s; 0.5–16.6 ms integration per point |
| IBM Quantum Open Plan | **[sourced]** 25 Oct ([plans](https://quantum.cloud.ibm.com/docs/en/guides/plans-overview)) | Up to **10 min per rolling 28-day window**, us-east only. A promotion offers +180 min over 12 months (as of 16 Mar 2026) |
| Tuners, reader, benchmark | Not started | — |

All scripts are in `checks/` (see `checks/README.md`). They still need to be committed (§15.1).

---

## 2. Goals, non-goals, anti-goals

**Goals**
1. **C1, the research question:** *when does information from previously tuned cells reduce acquisition cost without increasing wrong charge declarations?*
   - **Test:** on unseen simulated cells, the shared policy with chip and wafer history (T6) against the same policy started cold (T3), and against a plain running mean of the same history (T3-H).
   - **Break-even map:** the gain or loss as a function of how much variation cells on a chip share and how predictable the charge period is (§12), including where history stops paying.
   - **Ablation:** knowledge of the start point vs knowledge of the period.
   - Whether C1 is the headline is set by G0 (§11.4).
2. **C4, the benchmark (deliverable either way):**
   - the device generator and frozen fleets;
   - the metered interface with persistent device state;
   - a scoring contract that any tuner can use (§2.2);
   - the evidence rule and one success definition;
   - the baselines, including the oracle-start reference T★;
   - scripts that regenerate every figure from logs.
3. **Trust:** the wrong-declaration rate, with abstention and an upper bound, is a primary metric for every tuner.
4. **C2 (protected, because Qiskit is required):**
   - a model-based CZ error budget built from the device Hamiltonian, presented as a sensitivity study;
   - an Aer RB pipeline validated on known channels;
   - an IBM hardware run, as a scheduled demonstration with a fallback.
5. **C3 (stretch, first to cut):** drift detection and local re-tune.

**The protected outcome:** one correctly metered, sensor-only run that reaches and verifies (1,1), followed by an honest comparison against conventional history reuse. Everything else is built around it.

**Non-goals**
- Dot formation, barrier pinch-off, spin readout, and qubit-level calibration on spins.
- Estimating tunnel coupling, lever arms or spin parameters from charge data. This is infeasible in this regime (§8.4).
- Joint tuning of a multi-cell chip or a 6-dot array (§3.4).
- BO-based search (optional comparator only).
- Replacing or integrating with any commercial tuner.
- Real Equal1 hardware. We use it if offered; nothing depends on it.

**Anti-goals (a failure even if it technically works)**
- A headline that comes from an easy fleet, a weak baseline, a generous cold-start box, or a cost metric or budget picked after seeing results.
- A tuner that looks cheap because it stops early and wrongly. Wrong declarations are failures.
- Evaluator ground truth leaking into anything a tuner can see, including its history.
- Calling an idealized policy estimate a floor, or a pixel ratio a time saving.
- Claiming "≤ 1%" or "no silent failures" from an observed rate or from zero observed errors.
- Quantum for show (§10.3), or calling a model-based Aer result "verification" of a physical qubit.
- Unsourced or outdated numbers on slides.

### 2.1 Related work, and what is new here

| Element | Existing evidence | What SpinTune adds |
|---|---|---|
| Ray measurements | Ray-based state identification and tuning, validated experimentally ([Zwolak et al., PRX Quantum 2, 020335 (2021)](https://doi.org/10.1103/PRXQuantum.2.020335)) | A specific evidence protocol, and a fair accounting of its cost |
| Uncertainty-aware charge tuning | Online single-dot tuning into the one-electron regime using neural-network uncertainty; 95% success over 20 runs ([Yon et al., Nano Lett. 25, 3717 (2025)](https://doi.org/10.1021/acs.nanolett.4c04889)) | Wrong-declaration risk, measured across explicit device shifts |
| FD-SOI line segmentation and target selection | CEA-Leti 300 mm FD-SOI: 1,015 experimental diagrams, nine geometries, seven wafers, 80.0% offline tuning success ([Samaha et al., arXiv 2604.13662 (2026)](https://arxiv.org/abs/2604.13662)) | Sequential acquisition, history reuse and a reproducible comparison. Their 80% is offline, on a different process, task and sensor, so it is not comparable with a synthetic target |
| Autonomous spin-qubit tuning | A full sequence from a grounded device to Rabi oscillations, Ge/Si nanowire ([Schuff et al., Nature Electronics (2026)](https://doi.org/10.1038/s41928-025-01562-4)) | A narrow, well-measured charge-tuning component that could fit into such a workflow |
| RF/FPGA acceleration | 9.8× faster measurement gave 2.2× faster total initialization, limited by Python execution ([Roux et al., IEEE TQE (2026)](https://doi.org/10.1109/TQE.2026.3670353)) | Time accounted per query, so pixel savings aren't mistaken for time savings |
| Hierarchical fleet prior | Empirical Bayes and shrinkage are standard methods | Evidence on when chip and wafer history helps, hurts, or adds nothing |
| Open benchmark | The community has asked for datasets, benchmarking and standardisation ([Zwolak et al., npj Quantum Inf. 10, 105 (2024)](https://doi.org/10.1038/s41534-024-00878-x)) | An executable protocol that scores independent tuners and reports their failures |

### 2.2 Benchmark scoring contract [design call]

- **Outcome scoring is separate from our policy.** A tuner is scored on what it declares and what it spent, not on whether it used our evidence rule:
  - the declared V\*, or an abstention with a reason;
  - the evaluator's verdict: count, margin, nominal success and hold success (§11.2);
  - cost: pixels, queries, RF time, compute;
  - risk: wrong declarations over all declarations, with bounds (§11.5).
- **Tuners that use our interface** run through the metered session directly.
- **External tuners** plug in through an adapter that maps each scan they request onto billed windows or rays at the nearest allowed pitch and size. Their own evidence, in whatever form, is logged but not required.
- **Constrained-protocol results**, meaning comparisons that require the §5.1 evidence, are labelled as such.
- **The value of the evidence rule is measured at comparable risk.** The benchmark includes credible heuristics with and without extra verification:
  - T2's scan-and-fit, with its native count (T2-N) and with the §5.1 evidence (T2);
  - the shared policy with its stopping length swept from a 1.5-period shortcut to the full L (T3-L).

  The rule's value is the cost difference at matched wrong-declaration rate (§6.3 f), not its win over a known-broken shortcut.

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
| Sensor | The SEB, next to QT1. Sweeping QT1 detunes the sensor strongly, so the interface models a **compensated** sensor by default (virtual compensation on QT0). An uncompensated sensor is a stress scenario. Equal1's Fig. 4(c) shows the double-dot response overlaid with SEB transitions, so residual SEB transitions are a second stress scenario (§5.1 b) | Compensation [assumed] |
| Sensor sensitivity | Dot A, adjacent to the SEB, gives larger steps than dot B. Ratio 2–4 [assumed], swept. This matters for the certificate's visibility test | [assumed] |
| Reservoirs | The SEB is tunnel-coupled to the source; dot A loads through the QT1 barrier [inferred]. How dot B loads (from the drain through QA1, or only via dot A) isn't stated. Its lead transitions are modelled as prone to latching | [assumed]; question 2 (§14) |
| Carrier | Electrons | [sourced] 2412.08422v2, [2412.08302v1](https://arxiv.org/html/2412.08302v1), [equal1.com/technology](https://www.equal1.com/technology) |
| Published operating data | V_QT1 = 350 / 390 / 420 mV for decoupled / separating / merged dots (transport configuration, where QT1 is the barrier). Data at 700 mK (Figs. 2, 4) and 70 mK (Fig. 3). Lever arm 0.27 eV/V | [sourced]; which gate the lever arm refers to in this configuration is [assumed] |

**Why not the transport configuration?**
- In transport, the dots sit between QT0/QT1 and QT1/QT2 with QT1 as the barrier.
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
  - **Physics:** finite tunnel coupling, an exact thermal state, voltage-dependent tunnel couplings, and non-constant charging energy (which breaks the identical-cell symmetry). It is an equilibrium simulator: white and slow sensor noise, but no dynamics.
  - **Use:** the OOD-simulator fleet.
  - **How it runs:** in its own environment, as a worker process behind the same interface. Latching and 1/f noise are added in our wrapper (§4.3).
- **Fallback if QDarts misbehaves:** QArray plus our own rounded inter-dot lineshape layer.
- **Not adopted:**
  - SimCATS: no t_c parameter, and a non-commercial licence.
  - QDFlow: no tunnel coupling, and much slower.

### 3.4 Deferred and stretch

Listed so nobody builds them early:
- **6-dot / multi-cell run.** Equal1's published cells are linear arrays of at most 3 dots (§3.2). Build it only if Equal1 confirms a linear multi-dot layout to tune pair by pair. If so, use iterative sweeps, a 5-pass cap, convergence by cross-correlation (§9), and cold vs per-position prior on ~20 chips. `LayerFidelity`/EPLG would then be the natural chain metric.
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
| `ray(start, direction, pitch, n)` | 1D, 8 ≤ n ≤ 64 | n | Descent, certificate, measuring the period |

- **Pitch:** one of {0.5, 1, 2, 4} mV per query. The largest window, and the longest ray at 4 mV, span 256 mV.
- **Ray length:** chosen by the tuner for each query, 8–64 samples. The shared policy sizes each ray for the transition-free length still missing plus one period, rounds it up to 16, 32 or 64 samples, and shrinks it to the largest of those that fits above the domain floor (§6.1). Samples acquired after the evidence is complete are billed and unused.
  - Rays sized exactly to the evidence save ~4% of pixels but cost the cold baseline 6–12% more RF time, through 3–5 extra queries per cell [measured]. Under the rule in §1.1 (make T3 fastest), the rounded sizes win.
- **Domain:** [−300, +300] mV per axis around the design-nominal target.
  - Queries that would leave it are refused (logged, not billed).
  - A descent never goes below the point where the certificate would no longer fit; if it would have to, the tuner abstains.
  - In the idealized estimate, 0–1.7% of cells abstain for this reason, depending on the tuner [measured].
- **Mosaic:** larger regions are covered by tiling 64×64 windows, each billed.
  - The full domain at 4 mV is a 3×3 mosaic: **36,864 px**.
- **Budget:** **B = 40,000 px** per cell.
  - That's a full-domain coarse mosaic plus a certificate and a confirmation: the manual fallback a failed autotune triggers [design call].
  - At a much larger budget, such as 300 32×32 windows (307,200 px), nothing fails, so reliability would tell us nothing.
  - A run that exceeds B is a failure.
  - B is also the fallback charge in the all-cell cost (§11.3).
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
| t_setup per query | 20 ms | 20 ms | [assumed], swept 5 / 20 / 50 ms |
| t_settle per line | 1 ms | 5 ms | [assumed] |
| DC slew | 1 V/s | 1 V/s | [assumed], swept 0.4 / 1 / 10 V/s |

**What dominates** [measured, idealized]: pixel integration is about 1% of a ray-policy run's RF time (up to 1.6%). Query setup and DC slew are most of the rest; one extra query costs as much time as ~2,000 pixels. So:
- the pixel count measures acquisition, and it is reproducible;
- time savings come from fewer queries and shorter moves;
- every "faster" claim uses RF time, shows its sensitivity to t_setup and slew, and is checked against Equal1's own time breakdown when available (§14 Q5).

Published practice brackets these defaults. An RF/FPGA autotuning study measured ~27 ms latency per command, stepped DC slews of 0.04–0.39 V/s and 0.5–16.6 ms integration per point ([Roux et al., IEEE TQE (2026)](https://doi.org/10.1109/TQE.2026.3670353)) [sourced]. Our 20 ms setup is consistent with that; our 1 V/s slew and 10 µs pixels are optimistic.

- **One simulation, two costings:**
  - Every run is simulated once, in the RF scenario. Per-pixel SNR, telegraph switching and latching are all defined at the RF pixel rate and in RF instrument time.
  - DC time is a re-costing of the same query log, not a separate run. It is not a prediction of DC tuning reliability.
- **Elapsed time** = RF instrument time + measured tuner compute (single thread, reference laptop). The operational metric uses it (§11.3).
- **Time budget B_t (RF):** 1.25 × the RF time of a full-domain mosaic plus a certificate and a confirmation, i.e. T2's whole protocol.
  - The harness computes it once from the frozen constants and freezes it. That's ≈ 5 s with the defaults.
  - A run that exceeds B_t is a failure.
  - The DC equivalent (≈ 54 s) is used only for the DC re-costing.
- **Frozen fallback:** a run that fails or abstains is charged T2's protocol on top of what it spent: B px and B_t/1.25 of RF time.
- **Reported:** pixels, RF time, elapsed time, DC re-costing, query count, total slew distance, tuner compute.

### 4.3 Simulation behind the interface [design call]

- **Deterministic part:** a lazy tile cache. Noiseless occupancy and sensor maps are computed on demand per pitch and stored per cell.
- **Persistent stochastic state:** for each cell session, telegraph fluctuators, 1/f drift and latched occupancy carry over between queries. They are drawn along the actual acquisition path (raster or ray order) in simulated instrument time. Queries are simulated in the order they are issued.
- **Evolution between samples:** noise processes and latched states evolve during every interval of instrument time: pixel integration, query setup, line settling, slews and tuner compute (charged at its measured duration).
- **Noise parameters (defaults [assumed], swept):**
  - **White noise:** SNR = (dot-A step height) / (per-pixel noise σ) = 10 at the RF pixel time. Dot-B steps are smaller by the SEB sensitivity ratio (§7.2).
  - **Telegraph noise:** 2 fluctuators per dot. Each shifts that dot's lines by 0.05–0.2·P, with switching rates log-uniform over 1–100 Hz in instrument time. A shift can exceed the 0.15·P declaration margin, so hold success (§11.2) can fall below nominal success; the gap is measured, not hidden.
  - **Latching as relaxation:** a charge transition that has become energetically allowed happens within an interval Δt with probability 1 − exp(−Γ·Δt). Γ is set per transition type (lead A, lead B, inter-dot; §7.2) and may depend on detuning. At the RF pixel time, the defaults equal per-pixel probabilities of 0.95 / 0.85 / 0.99.
    - At the default rates a latched state relaxes within microseconds, so latching shows up only within a sweep, as lines displaced along the scan direction. Every gap between queries (≥ 1 ms) clears it.
    - The model is phenomenological. A **partition test** runs one 64-sample path as 1, 2, 4 and 8 queries, with setup, settling and slew set to zero, and checks that the latched-state statistics agree within sampling error.
    - **Slow-lead stress values** (§5.1 b): Γ_B = 10³, 10² and 10 s⁻¹, and Γ_B = 0 ("dot B unloads only via dot A"). Only these survive a query boundary, which needs Γ ≲ 10³ s⁻¹ against a 64-sample ray of 0.64 ms.
  - **SEB background transitions (stress scenario):** the sensor's own charge transitions appear as extra steps of either sign along each axis, with residual compensation error of 0–20%. Equal1's Fig. 4(c) shows the double-dot response overlaid with such transitions (§1.2).
- **Common random numbers:** only exogenous randomness is shared between tuners. That means white-noise samples, telegraph switching times and 1/f trajectories indexed by instrument time, plus the uniform draws used for latching decisions on a fixed time grid. Latched occupancy itself is not shared, because different tuners drive the device through different states.
- **Ablation:** "per-query reset", labelled as a simplified scenario. The persistent run is the reference.
- **QDarts** runs as a worker that returns noiseless tiles; the wrapper adds the stochastic parts. QDarts is an equilibrium simulator (it has white and slow sensor noise but no dynamics), so the OOD-simulator fleet tests the physics, not our noise and latching wrapper.

Code-level interfaces: Appendix A.

---

## 5. Reading the device: certificate, count, confirm

### 5.1 The anchor certificate [design call]

A window alone can't tell (1,1) from (2,2) [measured]. Every tuner must therefore show evidence of an **empty (0,0) region** before it may declare a charge state.

**What "certificate" means here.** It is an evidence rule: a fixed list of measurements that must all pass. Under assumptions A1–A4 below, passing it implies that the anchor is empty. Real devices can break those assumptions, so outside the noiseless model its error rate is measured, not guaranteed. An SNR threshold does not by itself bound that error rate.

**Constants (frozen with the fleet spec):**
- **P_max:** the upper end of the design tolerance for the addition voltage along a swept-gate axis. It is part of each scenario's spec.
  - **30 mV** for the in-distribution and OOD QArray fleets (design nominal 15 mV, tolerance ×/÷ 2).
  - **40 mV** for the wide-period scenario.
  - For QDarts, computed from its generator, including the larger first addition energy.
  - The OOD-spec fleet (§7.4) tests what happens when real devices exceed P_max.
- **r_m,max = 0.3:** the largest shift of one dot's lines when the other dot gains an electron, as a fraction of P.
- **L = 1.25 · (1 + r_m,max) · P_max:** the required transition-free length. That's **49 mV** at P_max = 30 mV and 65 mV at 40 mV.

**The evidence for a candidate empty point v0 (every ray billed; all must hold):**
1. **Axis rays.** For each axis (−QT1 and −QA1), a ray through v0 whose samples show a transition-free stretch of length ≥ L that contains v0, ending in a visible crossing above v0.
   - A ray cast upward from v0 − L·e to the first crossing satisfies this. So does a descent along that axis, if v0 lies in its final free stretch.
   - The crossing is the visibility check: it shows that the sensor responds on this ray.
2. **Diagonal ray.** The stretch from v0 down to v0 − √2·L along (1, 1)/√2 is transition-free. The §6.1 diagonal descent provides it, because v0 is placed √2·L above the point where the descent stopped, inside its free stretch. This is redundancy against one missed line.
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
6. **Validity at v0.** Every ray in the evidence must pass through v0. A ray cast before a later move no longer counts.

**Count:**
- The target (1,1) cell is the region reached from v0 by crossing dot A's first line once and dot B's once, in the addition direction, and no other line.
- Dot identity comes from orientation in the 2D confirmation window.
- Inter-dot lines on a ray count as transitions: they reset the transition-free stretch.
- No hypothesis tracking is needed, because nothing about absolute charge numbers is inferred before the certificate.

**Noiseless argument** (a written statement, separate from any Monte Carlo):
- **Assumptions:**
  - **A1. Electrostatics:** constant capacitance. At fixed occupancy each dot's electrochemical potential is linear in the gate voltages, and lowering a swept gate raises every dot's potential.
  - **A2. Period bound:** along each swept axis, at fixed occupancy of the other dot, every addition voltage of the dot next to that gate, including the first, is ≤ P_max.
  - **A3. Equilibrium:** along each ray, the occupancy is the ground state. There is no latching, and thermal broadening is below one pitch.
  - **A4. Detection:** the reader reports every occupancy change along a ray and nothing else. The sensor response is visible and correctly signed, and the sensor has no transitions of its own.
- **Claim:** if v0 lies in a transition-free stretch of length ≥ P_max along −QT1, dot A is empty at v0. If it lies in one along −QA1, dot B is empty. Together, v0 is (0,0).
- **Argument (dot A; dot B is the same):**
  - On a transition-free stretch the occupancy (n_A, n_B) is constant (A3, A4). Suppose n_A ≥ 1 on it.
  - At the stretch's upper end c, the n_A-th electron is bound, μ_A(n_A) ≤ 0, and the next one is not, μ_A(n_A + 1) > 0.
  - Moving down the −QT1 axis raises μ_A at the rate set by that gate's lever arm (A1). So the n_A-th electron leaves within one addition voltage, (μ_A(n_A+1) − μ_A(n_A))/α ≤ P_max (A2), below c.
  - That transition lies inside the stretch, a contradiction.
  - Any other transition that happens first (dot B unloading through cross-coupling, or an inter-dot transfer) also lies inside the stretch, so it is also a contradiction.
  - So n_A = 0 everywhere on the stretch, including at v0.
- **Margins:** the argument needs only P_max, because the other dot's occupancy is constant on a transition-free stretch. The rule uses L = 1.25·(1 + r_m,max)·P_max anyway: the 1.25 covers pitch quantisation and uncertainty in P_max, and (1 + r_m,max) covers devices outside constant capacitance (QDarts, real cells), where the spacing can shift with the other dot's occupancy. Whether a shorter L is safe under noise is measured by the T3-L sweep (§6.3 f), not assumed.
- **What breaks it:**
  - a period above P_max (A2; the OOD-spec fleet);
  - a dot that can't unload within the ray, for example dot B if it loads only through dot A (A3);
  - a missed or invented line from weak dot-B response, sensor detuning, compensation error or SEB background transitions (A4).

  Two rays can miss the same line for the same reason. The diagonal adds redundancy, not independence.

**Evidence so far:**
- On noiseless QArray devices with perfect occupancy readout, a descent along one axis at a time with the period-bounded length made 0 errors on 300 devices at each of two start spreads (P = 5–40 mV, L = 65 mV). With a fixed 22.5 mV length it failed on 8–15% [measured].
- In the metered estimate of the adopted policy, there were 0 wrong anchors in 3,600 runs (300 cells × 6 tuner configurations × 2 fleets). With the 22.5 mV length, T3 made 4/300 wrong anchors in the wide fleet [measured].
- Neither test covers the full evidence rule under noise. Claims about its error rate wait for B1 (§15.3).

**Pre-registered contingency:** if the ray-only certificate's wrong-anchor rate on the nominal-noise set exceeds 0.5%, a depletion window below v0 is added: 16×16 at 4 mV (256 px, spanning 64 mV ≥ L at P_max = 30 mV), or 32×32 at 4 mV in the wide-period scenario. This is decided before the freeze.

**Required tests (part of G1 and G2):**
- **(a) Noiseless, through the metered session:** the whole evidence rule (descent, axis rays, signs, 2D visibility, domain refusal, declaration), across the scenario's full P range up to P_max and the full cross-coupling range. Every cell is either counted correctly or abstains.
- **(b) Noisy and stress.** These run on ≥ 3,000 noisy cells from validation-type wafers, never test wafers, so that zero errors gives a one-sided 95% bound of 0.1%.
  - **Nominal noise:** sensor SNR 5–30, telegraph noise, latching at the §7.2 rates. Bar: observed wrong-anchor rate ≤ 0.5%, with its upper bound reported.
  - **Stress scenarios, reported without a bar:**
    - **low SNR:** SNR 3, where dot-B steps are about 1σ per pixel;
    - **correlated missed transitions:** a dot-B step suppressed on both its axis ray and the diagonal (sensor on a flat part of the SEB peak);
    - **persistent latching:** the dot-B lead rate lowered until unloading takes longer than a ray (Γ_B = 10³, 10², 10 s⁻¹), plus Γ_B = 0, "dot B unloads only via dot A" (§4.3);
    - **SEB background transitions** overlaid on the dot response, with 0–20% compensation error;
    - **sensor detuning** that changes the step size along a ray, including a sign flip past the Coulomb peak;
    - **out-of-spec periods** (OOD-spec).
  - **Reported separately for every scenario:** wrong anchors (v0 not (0,0)); wrong final counts (V\* not in (1,1)); correct counts with inadequate margin. The last two are wrong declarations (§11.2).
- **(c) Ambiguity test:**
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
- **Margin:** **≥ 0.15·P_est** along each bounding line's normal, **and** ≥ 3σ of quasi-static gate noise projected onto that normal (§7.3). The margin is geometric, on the nominal device; telegraph shifts can exceed it, which hold success measures (§11.2).
- **Retries** are allowed and billed.
- **Outcome:** the tuner either declares V\* or abstains with a reason.

### 5.3 Reader contract [design call]

**Reader v1 is signal processing**, shared by all tuners. A small CNN (U-Net-lite with a 1D ray head) replaces it only if, on validation, the CNN lowers the wrong-anchor rate, or the abstention rate at an equal wrong-anchor rate, by a margin fixed before training (default 25% relative). The choice is frozen at the end of week 2, before the training-fleet logs are generated (D1), and recorded in the tag.

- **Rays (v1):** a matched-filter step detector. It takes the difference of means over n samples on each side and thresholds it against the noise floor measured on the ray's own flat stretches.
- **Windows (v1):** gradient and structure-tensor orientation separate steep (dot A) from shallow (dot B) lines. Hough plus least squares fits the bounding lines. Inter-dot lines are the short segments joining the two families.
- **Output contract** (the same for v1 and the CNN):
  - **Input:** a normalised window or ray, plus its pitch.
  - **Per pixel, windows (multi-label):** dot-A line, dot-B line, inter-dot line. Pixels where two families meet, such as triple points, carry both labels.
  - **Per sample, rays:** transition or none, plus step amplitude and sign.
    - Ray transitions are given a dot only provisionally, by step height and spacing, and only to estimate P (§6.1).
    - The 2D window is the authority on which dot a line belongs to.
  - **Window-level head:** {no transitions, lines present, bad}. The "bad" class (low SNR, latching artefact) feeds abstention.
  - **Abstention:** a confidence map, plus an abstain flag when confidence along the detected lines falls below a threshold tuned on validation.
- **Labels from the evaluator** (to score both readers and to train the CNN):
  - **QArray:** a pixel is a dot-A line if dot A's occupancy changes between it and a neighbour, and so on.
  - **QDarts:** a pixel is labelled where the *dominant* charge configuration changes. Pixels where no configuration reaches probability 0.9 are marked as a transition zone. Line positions are the 0.5-probability contours.
- **Not the reader's job:** the charge count. That comes from the certificate and count, which are algorithmic and tested separately.
- **CNN training data:** windows and rays from the training fleet only, mixed across pitches and noise levels.

### 5.4 Oracle-assisted development mode

- During development, each tuner also runs with a perfect reader (masks supplied by the evaluator). This tests the search geometry and the budget before reader errors are added.
- These results are labelled "oracle-assisted" and are never mixed with sensor-only results.

---

## 6. Tuners and baselines

### 6.1 The shared policy: diagonal descent, then axis rays [design call]

Every search tuner except T2 runs this policy. They differ only in what they know before the first query:
- a start point s;
- a belief about the charge period, summarised by a point estimate P̂ and its 5th percentile P_lo.

Every tuner also knows the scenario's design spec, including P_max, because the evidence rule needs it.

1. **Measure the period first, but only if it pays.**
   - The test: would a known period allow a coarser pitch than P_lo does, i.e. is pitch(P_lo) < pitch(0.9·P̂)?
   - If so, first cast one 64-sample ray centred on s along +QT1, at the finest pitch spanning ≥ 2·P_max: 1 mV when P_max ≤ 32 mV, otherwise 2 mV.
   - If that ray shows ≥ 2 same-dot crossings, P is measured, and P_lo becomes 0.9 × the measured value.
2. **Pitch.** Use the largest allowed pitch ≤ P_lo/3, which gives ≥ 3 samples per period.
3. **Descend** along −(1, 1)/√2 from s until the stretch since the last transition is ≥ √2·L + P_lo.
   - Each query is sized for the free length still missing plus one period, rounded up to 16, 32 or 64 samples, and shrunk to the largest of those that fits above the domain floor.
   - The descent never goes below the point where the certificate would leave the domain. If it would have to, the tuner abstains.
   - **Why diagonal:** descending one axis at a time stalls while the other dot is still occupied, because that dot's lines cross the axis every P/x, which can be shorter than L. In the idealized estimate that made T3 abstain on 19–22% of cells, against 0–1% for the diagonal descent [measured].
4. **Certify** (§5.1) at v0 = the descent's stopping point + √2·L along (1, 1)/√2. v0 sits inside the free stretch, so the descent itself is the diagonal ray through v0.
   - Cast one ray per axis from v0 − L·e upward to the first crossing, plus 2 samples.
   - If either ray shows a transition below v0, restart the descent from v0 − L·e.
   - If P is still unknown, cast one 64-sample ray above the first dot-A line to measure it.
5. **Confirm** with the §5.2 window at the corner plus the estimated half-periods. Retry (billed) if the fitted period differs from the estimate by more than 20%.
6. **Declare V\* or abstain.**

This is the policy simulated in `checks/headroom_v4.py` with a perfect reader (§1.2). It is one reasonable way to collect the §5.1 evidence, not the cheapest possible. T★'s cost is a reference for this policy, not a floor.

The prior **never** sets absolute charge numbers. It only chooses s, the query sizes and the pitch.

**Tuning:** query sizing beyond the rules above, ordering and retry logic are tuned on validation to minimise T3's all-cell RF time (§1.1), and every tuner uses the same values. Pixels are reported for that same policy.

### 6.2 Tuners

| ID | Tuner | Starting knowledge | What it isolates |
|---|---|---|---|
| T★ | **Oracle start:** the shared policy from the true (1,1) centre, with the true P | Truth (evaluator) | **Oracle-start reference:** what this policy's evidence costs when the start is perfect. It is not a lower bound for other policies |
| T0 | **Random start:** the shared policy from a uniformly random point in the domain, with the design-spec period belief (as T3) | No start knowledge; the design spec only for P and P_max | What a search costs without a start point |
| T2 | **Scan-and-fit:** 3×3 mosaic at 4 mV (36,864 px); fit lines with reader v1's Hough + least squares; compute the target from the fitted lines; then the §5.1 evidence and confirmation. A simple fitter, not a research project | Design spec only | The physics baseline an Equal1 engineer would propose, and a validation comparator. Expensive in pixels, strong on reliability |
| T2-N | **T2 with its native count:** counts lines from the mosaic's empty corner and declares, without the §5.1 rays | Design spec only | A credible heuristic without the extra verification (§6.3 f) |
| T3 | **Ray navigation, cold:** the shared policy with only the **design spec**: s = design-nominal target (the domain centre), P̂ = 15 mV, P_lo = 7.5 mV (the tolerance's lower end). Its period belief allows only a 2 mV pitch, so it measures P first | Design spec | Competitive classical method, in the spirit of ray-based state identification ([Zwolak et al., PRX Quantum 2, 020335 (2021)](https://arxiv.org/abs/2102.11784)) |
| T3-M | **Fleet-mean start:** T3 with s = the fleet-mean target and P̂, P_lo from the fleet's period distribution (all from training logs) | Fleet mean and spread | "What do fleet statistics alone give?" With the default Δ_nom = 0 it differs from T3 only through the P belief, so it is expected to be about equal [measured, idealized: 1.00× in pixels in-distribution, 0.94× in the wide fleet]. It differs more in the Δ_nom sweep |
| T3-H | **Conventional history:** T3 with s = the running mean of its *own earlier declared* V\* on this chip. For a chip's first cell, s = the running mean over this wafer's earlier chips; with no history at all, the design spec. P̂ = the median of its own earlier measured periods and P_lo their 5th percentile, or the T3-M belief while fewer than 3 exist | Own chip and wafer history | The strongest classical use of the same information as T6 |
| T3-L(ℓ) | **Stopping-length sweep:** T3 with the transition-free length L replaced by ℓ ∈ {1.5·P_nom, 0.5·L, 0.75·L, L} everywhere: the descent stretch (√2·ℓ + P_lo), the axis rays and the diagonal | Design spec | The cost–risk curve: what a shorter stopping rule saves, and what it costs in wrong declarations (§6.3 f) |
| T5 | **SpinTune-F:** the shared policy with s and the period belief from the fleet prior (hierarchical empirical Bayes, fitted from training logs, with a radial term from die position) | Fleet | Value of a learned fleet prior |
| T6 | **SpinTune-H:** T5 plus this chip's and this wafer's own earlier traces, combined by hierarchical shrinkage into a posterior over the chip's offset, scales and P | Fleet + own history | **Headline candidate** |

**Optional, first to cut:**
- **T6-NN:** a learned set encoder or probe CNN in place of shrinkage. Kept only if it beats T6 on validation by ≥ 10% cost.
- **T-BO:** BoTorch with a prior from tuning logs, as a literature-style comparator. It is not the search policy: a scalar window score can't count electrons, and its per-step overhead (0.05–0.17 s [measured]) exceeds the simulation itself.

**Ablations:**
- T6 with start knowledge only, and with period knowledge only (§6.3 g).
- T6 with the prior fitted on unfiltered logs (§6.4).
- T5 without the radial term.
- Per-query-reset noise (§4.3).

### 6.3 Comparisons (each one answers a different question)

| | Comparison | Question |
|---|---|---|
| (a) | T6 vs T5, and T3-H vs T3 | Does history help, within the same policy? |
| (b) | **T6 vs T3-H** | With equal information, does learned inference beat a conventional running mean? |
| (c) | T5 vs T3, and T3-M vs T3 | What does the fleet prior give, and what does the fleet mean alone give? |
| (d) | T6 vs the **primary classical comparator** | Is it better than the best classical option? The comparator is chosen on validation among {T2, T3, T3-M, T3-H}, as the one with the lowest paired cost among those meeting T6's reliability minus 2 points. It is frozen at the tag. It is never chosen as the minimum on test |
| (e) | Everything vs T★ | How much avoidable cost is left within this policy? |
| (f) | T2 vs T2-N, and the T3-L(ℓ) curve | What does the extra verification cost, at a matched wrong-declaration rate? |
| (g) | T6 with start knowledge only vs period knowledge only | Which part of the history does the work? |

### 6.4 Histories and tuning logs

- **Test-time history:** only *that tuner's own* earlier traces on this chip and wafer. That includes its declarations (right or wrong), the lines and periods it measured, and its abstentions. Never evaluator truth.
- **Tuning order:** fixed and random, set by seed.
  - Chips are tuned in order on their wafer; chip j sees chips 1…j−1.
  - Cells are tuned in order on their chip; cell k sees cells 1…k−1.
  - Every tuner uses the same order.
- **Reported:**
  - totals over all 10 cells per chip, including the cold first cell and any failures;
  - the gain as a function of k.
- **Training logs:** T3 runs with the frozen reader (§5.3) over the training fleet.
  - Each log entry has a downstream-verification flag. In simulation it is the evaluator's judgement; on hardware it has to come from an independent downstream measurement (§14 Q4). This mirrors how a fab learns which bring-ups worked.
  - The prior is fitted on **verified** logs [design call]. An ablation fits it on unfiltered logs.
- **Prior file:**
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
| σ_cell, per-dot first-electron spread within a chip | 22 mV | 10–40 mV | [sourced] σ = 22 mV for the 28 nm devices of a **different group's 1,024-dot 22FDX transistor-dot array**, of which 16 mV is intrinsic ([Thomas et al. 2025](https://doi.org/10.1038/s41928-024-01304-y)); not an Equal1 multi-gate cell. Intel Si/SiGe: 61–63 mV ([2307.04812v2](https://arxiv.org/html/2307.04812v2)) |
| σ_die, chip-to-chip offset (residual after the radial term) | 60 mV | 0–150 mV | [sourced, low–medium confidence] room-temperature threshold-voltage IQR ≈ 100 mV over ~40 dies, pooled over gates and including systematic access-gate shifts (2501.10146) |
| Δ_edge, radial edge shift | 0–60 mV (uniform per wafer) | 0–120 mV | [assumed] |
| σ_wafer | 30 mV | 0–80 mV | [assumed] |
| **Δ_nom**, gap between the design-nominal prediction and the true fleet mean | 0 mV | 0–100 mV | [assumed]. Default 0 is conservative (cold = fleet-mean start) |
| Cross-coupling x (next-nearest gate) | 0.25 (cell 0.1–0.4) | 0.1–0.6 | [assumed] |
| Inter-dot capacitance | ±20% around nominal (r_m ≤ 0.3) | ±10–30% | [assumed] |
| SEB sensitivity, dot A : dot B | 3 | 2–4 | [assumed] |
| Temperature | 0.3 K (QArray `T=300`) | 0.35 / 0.5 / 0.75 K | Bell-1 runs at 0.3 K; Equal1 measured at 350/500/750 mK ([2412.01920 v3](https://arxiv.org/html/2412.01920v3)) |
| Sensor white noise | SNR 10 per pixel at the RF t_int, defined on **dot-A** steps (dot B: 10/3) | SNR 5–30 | [assumed]. Definition in §4.3 |
| Telegraph noise | 2 fluctuators per dot, line shift 0.05–0.2·P, rates 1–100 Hz | Amplitude ×0.5–2 | [assumed]. Can exceed the 0.15·P margin (§11.2) |
| Charge noise √S_E at 1 Hz | 4 µeV/√Hz | 1.7–6.5 µeV/√Hz | [sourced] SOI 1.7–6.3 ([2209.01853](https://arxiv.org/abs/2209.01853)); 22FDX p-type median 6.5 ([2507.21306v1](https://arxiv.org/html/2507.21306v1)) |
| Latching (relaxation rate Γ, §4.3) | Lead A 3.0×10⁵ s⁻¹, lead B 1.9×10⁵ s⁻¹, inter-dot 4.6×10⁵ s⁻¹ (per-pixel 0.95 / 0.85 / 0.99 at 10 µs) | Per-pixel equivalent 0.8–1.0; stress: lead B down to 0.5, and "dot B unloads only via dot A" | [assumed] |

**Joint distributions are the main unknown.** The sources above give plausible ranges for single parameters, measured on other groups' devices: a single-gate transistor-dot array, and room-temperature thresholds pooled over gates. They do not identify Equal1's cryogenic covariance between cells, chips, wafers, periods and target locations. That covariance is what creates the history advantage, so it is swept (§12) and treated as an assumption until Equal1 data exist (§14 Q3).

### 7.3 Charge noise as seen by the gates

- Energy noise converts to gate-voltage noise as √S_V = √S_E/α.
- For 1/f noise, the quasi-static variance is S(1 Hz)·ln(f_high/f_low).
- **Defaults:**
  - f_low = 1/(1000 s) and f_high = 1/t_gate, so the log factor ≈ 22.3 at t_gate = 200 ns;
  - σ_E ≈ 19 µeV and σ_V ≈ 70 µV;
  - dot-to-dot correlation of 0 and 0.5 are both run [assumed].

### 7.4 Fleets

| Fleet | Size | Purpose |
|---|---|---|
| Pilot | 5 wafers × 4 chips × 10 cells (200) | Building, debugging, G0, and sizing the test fleet |
| Train | 50 wafers × 20 chips × 10 cells (10,000) | Reader, tuning logs, priors |
| Validation | 10 wafers × 5 chips × 10 cells (500) | Thresholds, hyperparameters and comparator selection for **all** tuners |
| **Test (in-distribution)** | **20 wafers × 5 chips × 10 cells (1,000)**. The pilot may raise this to at most 40 wafers (sizing rule in §11.5) | **Headline**, run once after the freeze |
| OOD-hot / OOD-noisy / OOD-crosstalk | The **same underlying cells** as test wafers 1–10 (500 cells), changing only: 0.75 K / √S_E = 6.5 with SNR 5 / cross-coupling 0.4–0.6. SNR 5 rather than 3: with the 3:1 sensitivity ratio, SNR 3 would put dot B near 1 per pixel | Paired robustness tests |
| Certificate stress set | 60 wafers × 5 chips × 10 cells (3,000), generated like validation; never test | The §5.1 b nominal-noise bar and the stress scenarios |
| OOD-spec (in the trust report; no cost gate) | The same 500 cells, with E_c scaled so that ~10% of cells exceed P_max | What the certificate does when devices fall outside the design tolerance it relies on |
| OOD-wafer | 10 new wafers × 5 × 10, with σ_wafer and Δ_edge ×2 | Fab-level shift |
| OOD-simulator | QDarts, 10 wafers × 2 chips × 10 cells (200); underlying parameters mapped where defined | Finite t_c, non-constant charging energy |

### 7.5 Tuning logs

- Training-fleet logs come from T3 with the frozen reader (§6.4).
- The prior and hierarchy (T5, T6) are fitted only from these logs.
- The generator's parameters are never used for fitting.

### 7.6 External real-device data [sourced; none is 22FDX]

| Dataset | What it is | Labels | What it can test | What it can't |
|---|---|---|---|---|
| **QDSD** ([Zenodo 11402792](https://doi.org/10.5281/zenodo.11402792)), CC-BY-4.0 | Si-MOS and GaAs stability diagrams. The values are measured current. Raw x/y/z files (186 MB) and an interpolated CSV set (127 MB) that loses information | Only single-dot diagrams are labelled (transition lines and charge areas) | A separate single-dot counting experiment: line detection and counting from the empty region, with an observation model adapted to current peaks. Uses the raw files | The two-dot SEB certificate: a current peak is not a sensor step |
| **Delft D-CSD** ([Zenodo 16363472](https://doi.org/10.5281/zenodo.16363472)), CC-BY-4.0 | 9,850 Si/SiGe and Ge/SiGe stability diagrams, selected with a clean/noisy classifier. Raw HDF5 holds voltages and measured values; the default loader resizes to 128×128 (CSD archive 1.8 GB) | Clean/noisy only; no charge counts | Line-detection transfer of the reader on real scans, against our own hand labels; ambiguity analysis | Absolute (1,1) truth, sequential interventions, a fab-level hierarchy |
| **QFlow 2.0 `exp_small`** ([NIST](https://data.nist.gov/od/id/66492819760D3FF6E05324570681BA721894)), registration required | 756 measured scans | No dot / single / double | Optional; first to cut. Test only | — |

**How we use them:**
- Use the raw data, record how each set was selected, and never resize.
- **Labelling is timed before it is promised.** Label 5–10 D-CSD scans first, including ambiguous ones, with the other team member reviewing a subset. Commit to 50 only if that rate fits the external-data cap (§15.2).
- **Static replay is observation evidence only.** A stored scan can't show what the device would have done under a different scan order, dwell time, averaging request or latch state.
- If public data are used to tune preprocessing or thresholds, the test scans are frozen first and never touched.
- QDarts widens the physics tested (tunnel coupling, non-constant charging energy). It is an equilibrium simulator, so it doesn't validate our noise and latching wrapper.

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

The components are **composed as channels**, not added as infidelities.

| Component | Model | Inputs |
|---|---|---|
| Charge noise through J | Per shot or RB sequence, draw one quasi-static (δε_A, δε_B, δV_QT2) from §7.3 and hold it for the whole circuit. Evaluate J exactly, so second order at ε = 0 is kept | §7.3; ε, U, V_dec |
| Single-qubit dephasing during the gate | Quasi-static frequency noise with total σ_f set by T2* = 5.9–11.1 µs [sourced, 2412.01920 v3]. The charge-noise part is (∂f/∂ε)·σ_ε. It must not exceed σ_f; the remainder is attributed to other quasi-static sources | ∂f/∂ε [assumed, micromagnet scenario] |
| Residual coherent pulse error | From the Hann-pulse Hamiltonian | J_max, ΔE_z (20–300 MHz) [assumed] |
| Residual floor | Depolarising, applied last | Derived below |

**Composition:**
- Per noise draw, the charge-noise, dephasing and pulse terms enter one Hamiltonian and are propagated together. Averaging over draws gives the model's channel and its average gate fidelity F_model.
- **Residual floor:** a depolarising channel of strength λ applied after the model channel gives F_total = (1 − λ)·F_model + λ/d, with d = 4. So λ = (F_model − F_CZ)/(F_model − 1/d) reaches Equal1's reported F_CZ at the nominal point. For a perfect model channel this reduces to Aer's λ = (1 − F_CZ)·d/(d − 1) ([Aer docs](https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.noise.depolarizing_error.html)).
- **Rejection rule:** if F_model is already below the reported fidelity, the residual would need negative noise. Such parameter sets are rejected and counted, not clipped.
- **No double counting:** charge noise enters once, through J and through (∂f/∂ε). T2* is the total quasi-static dephasing, not an extra term. Parameter sets with (∂f/∂ε)·σ_ε > σ_f are rejected.
- Matching the floor to one reported fidelity does not identify its physical cause. The floor is labelled as unexplained.

### 8.4 Why the tuner doesn't estimate these parameters

- **t_c:** at Equal1's exchange (J ≈ 2.5–5 MHz, U ≈ 2 meV), t_c ≈ 2–3 µeV. A polarisation-line fit ([DiCarlo et al., PRL 92, 226801](https://arxiv.org/abs/cond-mat/0311308)) constrains t_c only for t_c ≳ 0.5·k_BT_e ≈ 13 µeV at 0.3 K.
- **α:** the thermal linewidth (≈ 3.5·k_BT/α ≈ 0.34 mV) is below the 0.5 mV minimum pitch.
- **∂f/∂ε and ΔE_z:** charge measurements can't see them.

So C2 is a **model-based map over sourced and assumed ranges**, not a tuner capability.

### 8.5 The study and its expected outcome

**Two labelled platform scenarios [design call]** (Equal1 question 7, on the platform, is still open):

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

**Expected result (a sensitivity study, conditional on the model):**
- Charge noise through J is at most a few percent of the budget.
- The best point is ε = 0 with J at the pulse limit, i.e. rule O1. That optimum may mostly reflect the model's assumptions (first-order insensitivity at ε = 0, the imposed pulse limit), so it is stated as conditional on them.
- If the map confirms this, the result is the budget figure plus, per scenario: *"Under these assumptions, O1 is sufficient; the remaining two-qubit error is dephasing and the unexplained floor"*. In S2 that claim covers only the FD-SOI charge-noise channel.
- If some regions lose ≥ 0.1 percentage points under O1, those regions are the result.
- **What C2 does not show:** that the tuner's electron count is right, or that physical gate fidelity improves.

---

## 9. Drift (stretch, C3, first to cut)

- **Injection:** physical, through the persistent telegraph and 1/f processes of §4.3.
- **Monitoring:** every k simulated jobs, a 32×32 reference window. It must **contain at least two transition lines** near V\*; a featureless patch can't be cross-correlated.
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

**Acceptance:**
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

*When does information from previously tuned cells reduce acquisition cost without increasing wrong charge declarations?* On unseen simulated 22FDX-style cells, T6 is compared with:
- the same policy started cold (T3);
- conventional use of the same history (T3-H);
- the best classical tuner (the comparator, §6.3 d).

### 11.2 Success for one cell

**Nominal success (primary; all must hold):**
1. The tuner declares V\*. Whether the §5.1 evidence and §5.2 confirmation were present is recorded as a separate flag, so tuners that don't use them (T2-N, external tuners) are scored on the same terms. For the shared policy they are part of the policy.
2. **QArray fleets:** the noiseless (T = 0) equilibrium occupancy of the nominal device at V\* is (1,1).
   **QDarts fleet:** at V\*, the dominant charge configuration in the thermal state at the fleet temperature is (1,1), with probability ≥ 0.9.
3. **Margin:** ≥ 0.15·P along every bounding transition's normal (for QDarts, measured to the 0.5-probability contours), and ≥ 3σ of projected quasi-static gate noise.

"Nominal" means the device without telegraph shifts, drift or latched state: the operating point a tuner is meant to find.

**Hold success (reported beside it, not gated):** after the declaration, the simulator holds V\* for 1 s of instrument time with every noise process and the latched state running. The cell holds if its actual occupancy is (1,1) for ≥ 99% of that time. Telegraph shifts of up to 0.2·P per fluctuator can exceed the 0.15·P margin, so hold success can be lower than nominal success. The gap is a finding.

**Outcomes:**
- **Success:** nominal success.
- **Wrong declaration:** a declared V\* that fails step 2 (**wrong count**) or only step 3 (**inadequate margin**). Where a wrong anchor (v0 not (0,0)) caused it, that is logged as the cause.
- **Abstention:** the tuner stops with a reason, including the domain limit.
- **Over budget:** no declaration within B or B_t.

Cells whose certificate can't fit in the domain are recorded. Results are shown for all attempted cells and for reachable cells.

### 11.3 Scorecard

| Question | Metric | How it's reported |
|---|---|---|
| Does the tuner work? | **Reliability:** successes / all attempted cells | All cells and reachable cells; 95% CI; failures by cause |
| Can its declarations be trusted? | **Wrong-declaration rate:** wrong declarations / all declarations | Counts by type (wrong count, inadequate margin); abstention rate; exact one-sided 95% upper bound; the chip-level rate (§11.5) |
| Is ≤ 1% established? | The upper bound | "≤ 1%" only if the bound is ≤ 1%; otherwise "observed X%, upper bound Y%" |
| Does it save acquisition? | **Paired pixel ratio** R_X/Y = Σ px_X / Σ px_Y over cells where both succeed | Labelled as conditional on joint success, always with the 2×2 table of joint success/failure counts |
| Does it reduce operational cost? | **All-cell elapsed cost:** RF time plus compute for every attempted cell, plus the frozen fallback (B px, B_t/1.25 s) for each non-success (§4.2) | Also in pixels; the failure-penalised restricted mean; success-vs-budget curves in pixels and RF time |
| Is learning necessary? | T6 vs T3-H (equal information); T6 vs T5 (value of history) | Under the reliability and wrong-declaration constraints of G3 |
| Does it tolerate shift? | Non-inferiority on each tested OOD fleet | The margins and the scenario list. OOD-spec goes into the trust report |
| Does it scale? | Per chip: completion, number of wrong declarations, all-cell cost including cell 1 | Cost vs cell position k |
| Cost above the reference | Paired cost minus T★'s | Within this policy only |
| Runtime | Tuner compute per cell; simulator time | — |
| C2 | Error-budget map; O1 loss vs map optimum; Markovian RB recovery; quasi-static decay report; rejected parameter sets | — |
| C3 (stretch) | Detection recall, false alarms per hour, delay, recovery cost | — |

### 11.4 Gates (thresholds frozen at the tagged commit)

| Gate | Question | Pass criterion |
|---|---|---|
| **G0 Headroom** (end of week 2; sensor-only, on pilot + validation) | Is there avoidable cost to save, within this policy? | Computed from sensor-only query traces: integer queries, the §5.2 confirmation rules, retries, domain checks and complete chip histories. h = 1 − R_T★/ref in pixels, and h_t the same in RF time. "ref" is whichever cold classical baseline, T2 or T3, has the lower paired pixel cost. **Practical targets, relative to the measured headroom:** history must capture at least a third of it, so R_T6/T3 ≤ 1 − h/3 in pixels and ≤ 1 − h_t/3 in RF time. Both are computed from G0 and frozen at the tag. <br>**Pre-registered branches, decided on pixels:** <br>**h ≥ 30%:** C1 is the headline. <br>**10% ≤ h < 30%:** headline = the benchmark and the measured error/cost trade-off; C1 is a measured secondary result; T6-NN dropped. <br>**h < 10%:** report the headroom; no practical target; build nothing learned beyond T5/T6 shrinkage; put the time into C2 and the external tests. <br>**"Faster" wording**, in any branch, also needs h_t ≥ 10% and G3(c′). <br>**Idealized pre-pilot estimate: h ≈ 32%, h_t ≈ 33%** (in-distribution, §1.2), so targets of ≈ 0.89 in both units. The idealized history ratios (0.86 px, 0.73 time) pass, the pixel one narrowly. Noise, reader v1 and simulated training-fleet logs decide. The fleet is never made harder or easier to change h |
| **G1 Generator and certificate** | Does the simulator do what we say, and does the evidence rule hold in the noiseless model? | Lattice matches `optimal_Vg` within 1 px. Noise PSD slope within the set value ± 0.1. Certificate tests §5.1 (a) and (c) pass through the metered session: 100% correct-or-abstain on noiseless cells over each scenario's P range up to P_max; the ambiguity test passes. The persistent-state and latching-partition tests pass (§4.3) |
| **G2 Reader** | Can we read scans, and does the evidence rule survive the frozen reader? | Transition-mask F1 ≥ 0.9 in-distribution. Wrong-anchor rate ≤ 0.5% on the nominal-noise certificate set (§5.1 b), with its upper bound reported. Reported at the final, never hidden: the stress scenarios, OOD results, QDSD single-dot counting, D-CSD line F1 on our hand-labelled scans |
| **G3 Warm start (C1)**, ID test | Does it save measurement without losing trust? | (a) T6 reliability ≥ 90%, **and** the lower 95% bound of (reliability T6 − T3) ≥ −2 points. <br>(b) Wrong declarations: the one-sided 95% upper bound over all T6 declarations ≤ 1%, which establishes "≤ 1%". If only the observed rate is ≤ 1%, G3(b) is "not established" and the report says "observed X%, upper bound Y%". The chip-level rate is reported beside it. <br>(c) Wafer-bootstrap 95% CI of the paired pixel ratio R_T6/T3 entirely < 1, **and** the point estimate ≤ the G0 practical target (1 − h/3). (c′) For speed wording, the same test on the all-cell RF elapsed cost, against 1 − h_t/3. <br>(d) CI of R_T6/comparator entirely < 1, with reliability non-inferior as in (a). Otherwise it is reported as "no gain over conventional use of the same information". <br>(e) **Pre-specified non-inferiority on the tested shifts:** on each OOD fleet (hot, noisy, crosstalk, wafer, simulator), the upper CI bound of R_T6/T3 ≤ 1.05, the point estimate of (reliability T6 − T3) ≥ −2 points, and its lower 95% bound ≥ −5 points. A claim about all five fleets at once uses Bonferroni-adjusted (one-sided 99%) intervals. Missing a bound means "not shown", not "worse", unless the point estimate itself is beyond the margin. <br>(f) ≥ 75% reliability on each OOD fleet |
| **G3h Hierarchy** | Does chip history add value beyond the fleet? | CI of R_T6/T5 entirely < 1 for cells k ≥ 3 |
| **G4 Error budget (C2)** | Is the Qiskit model sound, and what does it say? | (a) Block propagator vs 4×4 exponential: difference ≤ 10⁻¹². <br>Pure-ZZ formula vs full H, for J_max/ΔE_z ≤ 0.08 and δJ/J ∈ {0.3%, 1%, 2%}: \|Δ − ZZ\| ≤ 0.01·ZZ + 10⁻⁷, where Δ = (1 − F_full(δJ)) − (1 − F_full(0)). Outside that range the full H is the only reference. <br>(b) Aer IRB recovers the injected Markovian errors within systematic bounds plus fit CI. <br>(c) Quasi-static and IBM results are reported descriptively, not as pass/fail. <br>Rejected parameter sets (negative residual, dephasing over budget) are counted and reported. <br>Result: the map and the O1 statement per scenario |
| **G5 Drift** (C3, stretch) | Cheap recovery? | Recall ≥ 90% at ≤ 1 false alarm per simulated hour; recovery ≤ 25% of restart cost at equal success |

### 11.5 Statistics

- **Paired design:** every tuner runs on the same cells with the same exogenous noise (§4.3).
- **The unit of inference is the wafer.** Cost ratios, reliability and their differences use a wafer-level cluster bootstrap: resample wafers with replacement, keeping their chips, cells, histories and tuner seeds intact. Repeated tuner seeds do not add independent devices.
- **Rare events need their own bound.** A bootstrap can't bound a rate with zero observed events, because every replicate is zero. So wrong-declaration rates use:
  - the exact (Clopper–Pearson) one-sided 95% upper bound over declarations, labelled "assumes independent declarations";
  - the same bound over chips for the fraction of chips with ≥ 1 wrong declaration, which doesn't assume independence within a chip.
  - With 900 declarations, 0 / 1 / 3 / 4 errors give bounds of 0.33% / 0.53% / 0.86% / 1.01%. With 100 chips and none affected, the chip-level bound is 3.0%.
- **OOD comparisons** are paired by underlying cell.
- **Paired cost ratios** use only cells where both tuners succeed; every report states the dropped cells and the 2×2 joint counts. Reliability differences use all cells.
- **Multiple scenarios:** per-scenario intervals are unadjusted 95%. Any "on all scenarios" claim uses Bonferroni across the scenarios it names.
- **Seeds:** 3 per stochastic tuner on the pilot; up to 5 at final if the pilot's interval widths justify it.
- **Comparator choice:** the primary classical comparator and every threshold are chosen on validation, never on test.
- **Sizing the test fleet:** the pilot sizes it for all three claims, not only the cost ratio. The targets are a CI half-width ≤ 0.05 on R_T6/T3, ≤ 2 points on the reliability difference, and ≥ 300 declarations (so that zero errors gives a bound ≤ 1%). 90% reliability on 1,000 cells gives a binomial half-width of ≈ 1.9 points before clustering; clustered widths come from the pilot. The cap is 40 test wafers.

### 11.6 Pre-registration

- **Freeze:** after validation and before the test fleets are generated, tag a commit containing:
  - this document's thresholds and the G0 branch taken;
  - fleet seeds and configuration;
  - all tuners' hyperparameters, query-sizing parameters and the chosen primary comparator;
  - the reader choice (v1 or CNN) and the certificate constants;
  - the timing and fallback constants;
  - the analysis script.
- **After the freeze:** results are reported against the tag. Any later change is reported as a deviation.

---

## 12. Compute plan

- **Measured:**
  - QArray: ~10 ms per 32×32 window; rays are cheaper.
  - QDarts: ~0.2 s per window.
  - The tile cache makes repeated queries < 1 ms.
- **Ray-policy runs** take ~4–9 queries in the idealized estimate (§1.2), so ≲ 0.2 s per run with reader inference [estimate]. T2's mosaic adds ~0.5 s.
- **BoTorch** is needed only for the optional T-BO.
- **HPC is optional.** The full spread map is the HPC showcase if cluster hours appear.

| Job | Count | Core-hours | Laptop, 14 cores |
|---|---|---:|---:|
| Frozen evaluation: ~18 tuner configs (including T3-L and the ablations) × 3 seeds × 3,500 QArray cells (ID + OOD + OOD-spec) | ~189,000 runs | ~10–20 | ~1–1.5 h |
| Certificate stress set (§5.1 b): ≥ 3,000 cells × ~6 scenarios, shared policy | ~18,000 runs | ~1–2 | minutes |
| OOD-simulator (QDarts) | ~6,000 runs × ~10 queries | ~1.5–5 | < 1 h |
| Training-fleet tuning logs (T3 over 10,000 cells) | 10,000 runs | ~1 | minutes |
| Coarse spread map (the break-even map): 3 σ_die × 2 hierarchy strengths × 2 period-predictability levels (cell-level P spread 5% and 13%) × 2 noise levels × 1,000 cells × 4 tuners (T2, T3, T3-H, T6) × 3 seeds | ~288,000 runs | ~20–30 | ~2 h |
| Full spread map (optional HPC): 5 σ_die × 3 σ_cell × 3 hierarchy × 3 period predictability × 3 noise × 2 temperatures × 1,000 × 4 × 3 | ~9.7 M runs | ~600–900 | ~3 days (or ~6 h on a 128-core node) |
| C2 map: 10⁴ points × 10³ draws, exact 2×2 block | — | **0.3 [measured basis]** | minutes |
| CNN reader training (optional, CPU) | — | ~10–30 | overnight |
| Optional T-BO: 0.05–0.17 s per step × ~50 steps × 3,000 cells × 2 variants × 3 seeds | — | ~13–43 | ~1–3 h |

**Parallelism:** pin backend threads to 1 per worker. Parallelise across independent sessions (wafer × tuner × seed). Within a wafer, chips and cells run in order, because each tuner's history is sequential.

---

## 13. Prerequisites, and which we can get ourselves

| # | Prerequisite | Needed for | Can we get it ourselves? | How / status |
|---|---|---|---|---|
| 1 | Main environment (Python 3.12, QArray, Qiskit stack, PyTorch; BoTorch only for T-BO) | Everything | **Yes** | Verified 25 Oct. Lockfile (`uv`) still to commit |
| 2 | QDarts environment | OOD-simulator fleet | **Yes, verified** | Runs on this Mac; wrap as a worker |
| 3 | Git repo with the check scripts | §1.2 evidence, §11.6 freeze | **Yes** | Scripts copied into `checks/` on 25 Oct, with a README. `git init` and the commit are still to do |
| 4 | Sourced device parameters | §7 | **Yes, done** | Low confidence: σ_die, Δ_edge, σ_wafer, cross-coupling, SEB sensitivity |
| 5 | Equal1 device facts | §3 | **Mostly, done** | SEB + double-dot configuration verified against the paper on 25 Oct. Open: swept axes, how dot B loads, back-gate value, which platform Bell-1 uses |
| 6 | Real scans for external tests | §7.6 | **Partly** | QDSD (raw files 186 MB) and D-CSD (1.8 GB) are direct downloads; QFlow 2.0 needs registration (optional). Open a few raw files first and map their labels into the reader contract. We can also ask the CEA-Leti authors of [arXiv 2604.13662](https://arxiv.org/abs/2604.13662) |
| 7 | Compute | §12 | **Yes** | Laptop for everything except the full spread map |
| 8 | Real quantum hardware | §10.2 | **Yes** | IBM Open Plan: 10 min per rolling 28 days, us-east instance |
| 9 | Physics sanity review | §8 | **Partly** | Analytic cross-checks done (§1.2, §8.2). Equal1 judges at the pitch |
| 10 | Equal1 grouped tuning logs, scans and a timing breakdown | Sim-to-real; the fleet hypothesis | **No** | The structured request (§14 Q3–Q5). Nothing depends on it |
| 11 | R2P capstone or extra IBM access | Optional | **Unknown** | Ask the programme leads |

---

## 14. Questions for Equal1 (most important first)

1. **Layout and axes:**
   - Is our reading of the SEB + double-dot configuration right: SEB between QT0 and QT1, dots between QT1/QT2 and QT2/QA1, with QT2 as the inter-dot barrier?
   - Which gates do you sweep for charge tuning, and how do you compensate the SEB?
2. **Reservoir of the far dot:** does the QT2/QA1 dot load from the drain through QA1, or only via the near dot?
3. **Data, as a structured request.** For an initial sample spread over **at least 5 chips, with repeated same-design cells**, could you share:
   - the raw sensor signal with its voltage axes, gate identities and fixed biases;
   - sensor compensation settings;
   - acquisition order, integration time and timestamps;
   - cell, chip, wafer and cooldown IDs;
   - measured charge periods and verified target locations;
   - unsuccessful attempts, not only successes?

   That would allow an exploratory look at within-chip predictability. It would not establish a rare-error ceiling or generalisation across wafers.
4. **Verification:** which independent downstream measurement tells you that a charge-tuned cell was right? Our tuning logs assume such a flag (§6.4).
5. **Cost today, broken down:** per cell, how much time goes to setup, settling, slewing, integration and analysis? That decides whether fewer pixels or fewer queries matter.
6. **Distributions:**
   - What are the cryogenic distributions across cells, chips and wafers of first-electron voltage, lever arms, E_c and cross-capacitance?
   - How much of that is shared within a chip?
   - Is a chip 29 cells or 35?
7. **Platform:** do Bell-1 qubits run on the 22FDX cells or on the Si/SiGe devices? NMOS or PMOS?
8. **Spins:** how are spins driven in 22FDX, and what is ΔE_z?
9. **Noise:** what are measured √S_E and its exponent in 22FDX?
10. **Exchange:** the t_c(V) and J(V) slopes; residual J; the CZ pulse shape.
11. **Multi-dot:** is there a linear multi-dot array you'd want tuned pair by pair?
12. **Cooldowns:** how much do the electrostatics shift between cooldowns?

---

## 15. Plan

### 15.1 Before the pitch (Tue 27 Oct, idea-only)

- [ ] **Repo:** `git init`; lockfiles for both environments; commit `checks/`.
- [ ] **Update `SPINTUNE-2.md` to match this document:**
  - the §0 pitch: "SpinTune tests whether chip history can make charge tuning cheaper without increasing wrong charge declarations";
  - none of "proves its answer", "never lies", "holds across all devices", "floor" or "nothing can save more";
  - the (1,1) target, with the §5.1 evidence rule and its assumptions;
  - "fleet modelled on published 22FDX statistics; the within-chip structure is an assumption";
  - electrons and the SEB + double-dot layout;
  - the CZ numbers from arXiv 2412.01920v3 (200 ns; 99.30% / 98.41%), with the trade-press numbers labelled "vendor-reported";
  - the FD-SOI noise range;
  - "pre-registered target", not "≥ 2×";
  - "non-inferiority on the tested shifts", not "never worse";
  - "learned from bring-up logs";
  - Qiskit protected;
  - the 6-dot run as a question for Equal1;
  - the report-straight sentence;
  - drop "every tuner step is a fresh simulation" as the HPC argument.
- [ ] **Comparison slide:** the §2.1 table, including the CEA-Leti 2026 FD-SOI paper.
- [ ] **Q&A additions:**
  - *"Isn't charge tuning cheap already?"* — "Yes, and we measured how cheap, for one policy on ideal cells: about half a second per cell at RF rates, and pixels are about 1% of that. Chip history cut pixels by about 14% and time by about 27%, mostly by needing fewer queries. The value is a measured wrong-declaration rate and a benchmark that reports it for every tuner."
  - *"Is the certificate a proof?"* — "Only under stated assumptions: a bounded charge period, equilibrium occupancy, and a sensor that shows every line. Real devices can break each one, so we measure its error rate under noise, latching and sensor artefacts, and report the upper bound."
  - *"How is this different from the CEA-Leti FD-SOI work?"* — "They segment single diagrams offline, with 80% success on their own process. We test sequential acquisition with metered cost and history reuse. The numbers aren't comparable."
  - *"Why not BO?"* — "A scalar score can't count electrons, and its per-step overhead is larger than the simulation."
- [ ] **Backup slides only:**
  1. the stopping-rule miscount (8–15% in a one-axis descent, vs 0/300 per start spread with the period-bounded length; 4/300 for the shortcut under the shared policy, wide fleet; all noiseless);
  2. the idealized cost table (pixels, queries and time; §0);
  3. the CZ gate from the Hamiltonian.
- [ ] **Hand Equal1 the structured data request** (§14 Q3–Q5) at the pitch.
- [ ] **Rehearse** the §14 questions.

### 15.2 Tracks and hour caps [design call]

| Track | Content | Cap |
|---|---|---:|
| A | Simulation, interface, evaluator (A4, the QDarts worker, counts against Track R's external cap) | 30 h |
| B | Evidence rule and baselines (B1 ≈ 12 h, B2–B4 ≈ 13 h) | 25 h |
| R | Reader v1 (15 h); QDarts and external data, a small study (15 h) | 30 h |
| D | Fleet learning | 15 h |
| E | Scoring and statistics | 25 h |
| F | Qiskit (protected, off the critical path) | 20 h |
| — | Presentation and reproduction | 15 h |
| — | Contingency | 20 h |
| | **Total** | **180 h** |

These are planning caps, not measured estimates. If a track won't fit its cap, shrink what it promises before spending the contingency.

### 15.3 Tasks ("Needs" = hard dependencies; "Done" = the check that must pass)

**Track A: simulation, interface, evaluator**
- **A0. Setup.** `git init`, two environments with lockfiles, `checks/` committed, both laptops working.
  - **Done:** every `checks/` script reruns from the repo on both machines, with outputs saved.
- **A1. Fleet generator.** Hierarchical sampler (§7) for both templates; whole-wafer splits; matched OOD variants.
  - **Needs:** A0.
  - **Done:** the same seed gives the same fleet; a 16-cell scan grid per fleet looks visibly different; the lattice matches `optimal_Vg` within 1 px.
- **A2. Session interface.** Windows and rays, ledger, cost model, caps, domain refusal, tile cache, persistent state, latching as relaxation, common random numbers.
  - **Needs:** A1.
  - **Done:**
    - the ledger equals the sum of billed pixels, and the time model passes unit tests;
    - a latched state survives a query boundary, and the reset ablation differs;
    - the latching partition test passes (§4.3);
    - only exogenous noise is shared between tuners.
- **A3. Evaluator.** `judge()`: nominal success, hold success, wrong count vs inadequate margin, wrong anchor; the (1,1) polygon, masks, the QDarts dominant-state rule.
  - **Needs:** A1.
  - **Done:** 5 hand-checked cells; masks agree with occupancy changes.
- **A4. QDarts worker.**
  - **Needs:** A2.
  - **Done:** same interface; speed test on 20 cells; OOD-simulator fleet size fixed.

**Track B: evidence rule and baselines**
- **B1. The whole evidence rule through the metered session** (§5.1–5.2): diagonal descent, axis rays, sign calibration, 2D visibility, domain refusal, count and declaration. First with the oracle reader, then with reader v1. Write up the noiseless argument as a one-page note with its assumptions.
  - **Needs:** A2, A3.
  - **Done:** G1 certificate tests (a) and (c). Until B1 is done, slides quote only the noiseless descent result.
- **B2. T★ and T3, then T3-M and T3-H, with reader v1.**
  - **Needs:** B1, R1.
  - **Done:** **the first sensor-only end-to-end comparison**: T★, T3 and T3-H on the pilot, reaching and verifying (1,1), with pixels, queries and RF time. This is the week-1 objective.
- **B3. T0, T2 (simple mosaic fit), T2-N, and the T3-L(ℓ) sweep.**
  - **Needs:** B1.
  - **Done:** all run end to end on the pilot; the cost–risk curve on validation.
- **B4. Certificate stress set** (§5.1 b, §7.4) with reader v1: the nominal-noise set and the stress scenarios.
  - **Needs:** B1, R1, and A2 complete (persistent noise and latching).
  - **Done:** the wrong-anchor rate on the nominal-noise set with its upper bound (feeds G2 and the reader choice); the stress-scenario table in three error categories.

**Track R: reader and external data**
- **R1. Reader v1** (signal processing: ray step detector, window orientation + Hough, abstention; §5.3).
  - **Needs:** A3.
  - **Done:** F1 on validation windows and rays; wrong-anchor rate with v1 on noisy validation cells.
- **R2. CNN reader (optional).** Training samples from the training fleet; U-Net-lite + ray head.
  - **Needs:** R1.
  - **Done:** kept only if it beats v1 by the §5.3 margin on validation; otherwise dropped, and the reason recorded.
- **R3. External data.** Open a few raw QDSD and D-CSD files and map their labels into the reader contract. Run the QDSD single-dot counting experiment. Time 5–10 D-CSD labels (with a second review on a subset), then decide whether to label 50.
  - **Needs:** R1.
  - **Done:** numbers in the results table, labelling rate recorded, within the 15 h cap (shared with A4).

**Track D: fleet learning**
- **D1. Training-fleet tuning logs.** T3 with the frozen reader over the training fleet.
  - **Needs:** B2, and the reader choice frozen at the end of week 2 (R1, or R2 if kept).
  - **Done:** one trace per cell; success and wrong-declaration rates reported.
- **D2. Fit the hierarchical prior from verified logs**, plus the unfiltered-log ablation.
  - **Needs:** D1.
  - **Done:** prior file written; 50% and 90% ellipse coverage on validation within ±5 points.
- **D3. T5 and T6**, plus the start-only and period-only ablations.
  - **Needs:** D2.
  - **Done:** both beat T3 on 50 validation cells, or the reason is understood.

**Track E: scoring and statistics**
- **E1. Harness:** tuners × fleets × seeds; wafer bootstrap; Clopper–Pearson bounds over declarations and over chips; joint 2×2 counts; all-cell cost with the fallback; success-vs-budget plots; automatic PASS/FAIL per gate.
  - **Needs:** B2.
  - **Done:** one command regenerates every figure and verdict from saved traces.
- **E2. Validation runs**, the certificate stress set, comparator selection, thresholds, **freeze tag**.
  - **Needs:** E1, D3, B3, B4.
  - **Done:** tag pushed with the §11.6 contents.
- **E3. Test and OOD runs**: G3, G3h, external tests, oracle-assisted ablation.
  - **Needs:** E2, A4, R3.
  - **Done:** results table and the gate slide.
- **E4. Coarse spread map**, i.e. the break-even map (the full map only with cluster hours).
  - **Needs:** E2.

**Track F: Qiskit (protected, off the critical path)**
- **F1. CZ Hamiltonian module**: standard convention, Hann pulse, 2×2 block propagator, ZZ cross-check.
  - **Needs:** A0.
  - **Done:** G4(a).
- **F2. Error-budget map** with composed channels, rejection counts, O0 and O1.
  - **Needs:** F1.
  - **Done:** the map figure and the conditional O1 statement.
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
| W1 (28 Oct – 3 Nov) | A0, A1, A2 core (ledger, cost model, domain, tile cache, white noise), A3, B1, R1 minimal (ray step detector, window line fit), B2 | G1 except the persistent-state tests; **the first sensor-only, metered end-to-end comparison (T★, T3, T3-H) with reader v1** |
| W2 (4 – 10 Nov) | A2 rest (telegraph, 1/f, latching, common random numbers, partition test), A4, B3, B4, R1 complete (abstention, "bad" class), R2 (optional), start R3, F1, F2 | Rest of G1; G2; **sensor-only G0: does history add value in pixels and in time, and are wrong declarations controlled?** The branch is chosen and **the reader is frozen** |
| W3 (11 – 17 Nov) | D1, D2, D3, E1, E2; F3; **submit F4 by 13 Nov** | **Freeze tag by 17 Nov** |
| W4 (18 – 24 Nov) | E3, E4, R3; presentation; stretch if time | G3, G3h, G4 |
| 25 – 26 Nov | Demo and dry run | — |
| 27 Nov | Final | — |

Planned load is about 40 h a week (two people × 20 h) in W1–W3, with W4 lighter to leave room for the presentation. The 20 h contingency covers overruns; if it runs out, cut in the §15.6 order.

### 15.5 Critical path

**A1 → A2 → B1 → B2 → B4 → reader freeze → D1 → D2 → D3 → E2 → E3.**
- Reader v1 (R1) joins the path at B2, because the week-1 comparison is sensor-only.
- The harness (E1) must be finished before E2: comparator selection and the frozen analysis script use it.
- The CNN (R2) is off the path. Track F, B3, A4 and R3 sit off the path too. Give them to whoever is blocked.

### 15.6 Cut order, and what is never cut

**Cut in this order:**
1. Drift (C3).
2. The full spread map (keep the coarse one).
3. T6-NN and T-BO.
4. The CNN reader (keep v1).
5. QFlow 2.0.
6. Samplomatic twirling.
7. The IBM hardware run (keep the Aer and `FakeTorino` pipeline).
8. D-CSD labels beyond the timed first batch.
9. The coarse map, down to one axis.
10. Reduce the OOD-simulator fleet (never remove it).

**Never cut:**
- the interface and evaluator;
- the evidence rule and reader v1;
- T★, T2 (simple fitter), T3, T3-H, T5, T6;
- G0–G3h, the wafer bootstrap, the rare-event bounds and the freeze;
- the C2 Hamiltonian map with Aer RB validation (the Qiskit requirement).

**Must not displace the protected outcome** (§2): the IBM hardware run, a dashboard, drift, the 6-dot run, a neural set encoder, the large map.

### 15.7 Demo (27 Nov)

1. A new virtual chip.
2. **The evidence rule in action:** rays light up. On a wide-period cell where it happens (4/300 for T3 in the idealized wide fleet), the 1.5-period shortcut miscounts while the full rule certifies or abstains.
3. Cells 1–10 tuned in sequence, with pixel and time counters against the T★ reference, showing whatever was measured.
4. The wrong-declaration counter for every tuner, with upper bounds.
5. The headroom result with its confidence interval, and the G0 branch taken.
6. The CZ error budget from the Hamiltonian in Qiskit, with Aer RB, plus the IBM run if it happened.
7. The gates slide: pass or fail, including any failures.

### 15.8 Left to the builder

These are free choices, within the rules above:
- query sizing and ordering within §6.1, and retry logic;
- reader v1's filter details, and the CNN's architecture;
- how the hierarchical model is parameterised;
- T2's line-fitting algorithm, kept simple;
- plotting;
- file formats beyond Appendix A;
- details of mapping parameters into QDarts.

---

## 16. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| **Headroom is marginal.** The idealized estimate (h ≈ 32% in pixels) sits near the 30% line, and the idealized history ratio (0.86) only narrowly meets its relative target (≈ 0.89); noise, reader v1 and simulated training-fleet logs may move both | **High: it decides the headline** | Pre-registered G0 branches on sensor-only traces. The benchmark and the error/cost trade-off carry the headline in the lower branches. Costlier tuning stages are listed for follow-up (§3.4) |
| **Pixel savings don't become time savings.** Pixels are ~1% of RF time | **High for practical value** | Time metered per query; "faster" needs h_t and G3(c′); sensitivity to setup and slew; Equal1's own time breakdown (§14 Q5) |
| **The history advantage is an artefact of the assumed joint distributions** | **High** | The break-even map over shared variation and period predictability; T3-H as the no-learning baseline; the structured data request (§14 Q3) |
| **The evidence rule fails under real sensing** (SEB background transitions, detuning, latching) | **High** | The §5.1 b stress tests; three error categories; the depletion-window contingency; abstention |
| The paired cost ratio hides tuners that fail on different cells | Medium | The 2×2 joint counts; all-cell cost with the fallback; reliability non-inferiority in every cost claim |
| Too few declarations to bound a rare error rate | Medium | Clopper–Pearson bounds; a certificate stress set of ≥ 3,000 cells; "observed X%, upper bound Y%" wording |
| The evidence rule abstains too often under noise, so reliability < 90% | Medium | Validation-tuned SNR threshold and pitch; the pre-registered depletion-window contingency (§5.1); abstentions reported |
| Our device mapping (SEB + double dot, plane (QT1, QA1)) is wrong | Medium | "Modelled on" wording; question 1 for Equal1; the generic template as a fallback |
| The compensated-sensor assumption hides real costs | Medium | Uncompensated and SEB-background stress scenarios, reported |
| Persistent-state simulation is harder or slower than planned | Medium | Fall back to per-query reset, clearly labelled as simplified |
| Sim-to-real gap | High | QDarts fleet, external data, sourced spreads; the honesty slide |
| σ_die is low-confidence | Medium | Swept 0–150 mV |
| T2 wins on reliability | Low–Medium | Reported. It's expensive in pixels by construction |
| **Scope vs 180 h** | **High** | Hour caps (§15.2); the protected outcome first; reader v1 before any CNN; cut order |
| QDarts install or speed problems | Low–Medium | Verified install; lineshape fallback |
| IBM queue or access problems | Low | Submit by 13 Nov; `FakeTorino` fallback |

---

## 17. References

**Equal1 and 22FDX**
- Equal1 Si/SiGe two-qubit processor: [arXiv 2412.01920v3](https://arxiv.org/html/2412.01920v3)
- Equal1 22FDX quantum-dot cells: Amitonov et al., [arXiv 2412.08422v2](https://arxiv.org/html/2412.08422v2) (Figs. 1, 2, 4); [arXiv 2412.08302v1](https://arxiv.org/html/2412.08302v1)
- 22FDX transistor dots, first-electron spread (different group): Thomas et al., Nature Electronics 8, 75 (2025), [doi:10.1038/s41928-024-01304-y](https://doi.org/10.1038/s41928-024-01304-y), [arXiv 2310.20434](https://arxiv.org/html/2310.20434)
- 22FDX multi-gate dots (Quobly / CEA-Leti): Elbaz et al., [arXiv 2501.10146](https://arxiv.org/abs/2501.10146)
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

**Autotuning and related work**
- Ray-based state identification: Zwolak et al., PRX Quantum 2, 020335 (2021), [doi:10.1103/PRXQuantum.2.020335](https://doi.org/10.1103/PRXQuantum.2.020335), [arXiv 2102.11784](https://arxiv.org/abs/2102.11784)
- Online neural-network charge autotuning: Yon et al., Nano Lett. 25, 3717 (2025), [doi:10.1021/acs.nanolett.4c04889](https://doi.org/10.1021/acs.nanolett.4c04889), [arXiv 2409.20320](https://arxiv.org/abs/2409.20320)
- CEA-Leti 300 mm FD-SOI charge-state tuning by segmentation: Samaha et al., [arXiv 2604.13662](https://arxiv.org/abs/2604.13662) (2026)
- Fully autonomous spin-qubit tuning: Schuff et al., Nature Electronics (2026), [doi:10.1038/s41928-025-01562-4](https://doi.org/10.1038/s41928-025-01562-4), [arXiv 2402.03931](https://arxiv.org/abs/2402.03931)
- RF/FPGA autotuning and its time breakdown: Roux et al., IEEE Trans. Quantum Eng. (2026), [doi:10.1109/TQE.2026.3670353](https://doi.org/10.1109/TQE.2026.3670353), [arXiv 2509.19537](https://arxiv.org/abs/2509.19537)
- BO tuning: Moon et al. 2020, [PMC7438325](https://pmc.ncbi.nlm.nih.gov/articles/PMC7438325/)
- Data needs and benchmarking: Zwolak et al., npj Quantum Inf. 10, 105 (2024), [doi:10.1038/s41534-024-00878-x](https://doi.org/10.1038/s41534-024-00878-x), [arXiv 2312.14322](https://arxiv.org/abs/2312.14322)

**Simulators and data**
- QArray: [arXiv 2404.04994](https://arxiv.org/abs/2404.04994)
- QDarts: Krzywda et al., SciPost Phys. Codebases 43 (2025), [doi:10.21468/SciPostPhysCodeb.43](https://doi.org/10.21468/SciPostPhysCodeb.43), [arXiv 2404.02064](https://arxiv.org/abs/2404.02064), [repo](https://github.com/qplai/QDarts)
- QDSD: Yon et al., [Zenodo 11402792](https://doi.org/10.5281/zenodo.11402792); Delft D-CSD: de Snoo et al., [Zenodo 16363472](https://doi.org/10.5281/zenodo.16363472); [QFlow 2.0](https://data.nist.gov/od/id/66492819760D3FF6E05324570681BA721894)

**Qiskit, RB, IBM**
- Aer depolarising channel: [docs](https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.noise.depolarizing_error.html)
- qiskit-experiments RB and IRB systematic bounds: [manual](https://qiskit-community.github.io/qiskit-experiments/manuals/verification/randomized_benchmarking.html)
- RB under correlated (non-Markovian) noise: [arXiv 1504.05307](https://arxiv.org/abs/1504.05307)
- IBM plans (Open Plan, 28-day window): [docs](https://quantum.cloud.ibm.com/docs/en/guides/plans-overview); QPU metric definitions: [docs](https://quantum.cloud.ibm.com/docs/en/guides/qpu-information)
- IBM R2P course, Units 0–4: this folder

**Project documents**
- `bobi_resources/SPINTUNE-2.md`, `bobi_resources/PLAN.md`, `checks/README.md`

---

## Appendix A. Interfaces and code layout

Plain numpy and json, so the two of you can work on separate pieces.

```text
Cell            dict: hidden params (evaluator only), wafer_id, chip_id, cell_index, die_xy, seed
fleet file      fleets/<name>.npz + fleets/<name>.json   (generator params, seeds, split, matched-OOD map)
Session         s = harness.open(cell, scenario)         # persistent noise/latching state + ledger
s.window(center: float[2], pitch, size) -> float32[size, size]        # billed
s.ray(start: float[2], direction: float[2], pitch, n) -> float32[n]   # billed; 8 <= n <= 64
s.declare(v_star: float[2], evidence) | s.abstain(reason)             # ends the run
evaluator.judge(cell, trace) -> {outcome: success|wrong_count|inadequate_margin|abstain|over_budget,
                                 hold_success, wrong_anchor, margin, occupancy}   # after the run only
tuner.run(s, metadata, history) -> trace
trace           runs/<tuner>/<fleet>/<seed>/<cell>.json:
                queries [{type, args, px, t_query, t_cum}], certificate, declaration,
                totals {px, rf_s, elapsed_s, dc_s, n_queries, slew_mV, compute_s}
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
  tuners/        oracle_start.py, random_start.py, scan_fit.py (T2, T2-N), raynav.py (T3, T3-M, T3-H, T3-L), spintune.py (T5, T6)
  reader.py      v1 signal processing; optional U-Net-lite + ray head      (R1, R2)
  prior.py       fit hierarchical prior from verified tuning logs            (D2)
  harness.py     tuners × fleets × seeds, wafer bootstrap, gates, plots      (E1)
  qiskit_cz/     hamiltonian.py (2x2 block), budget_map.py, rb_aer.py, ibm_run.py   (F1–F4)
  drift.py       cross-correlation monitor (stretch)
checks/          evidence scripts (§1.2)
fleets/ runs/ logs/ priors/ figs/     generated output, git-ignored
```
