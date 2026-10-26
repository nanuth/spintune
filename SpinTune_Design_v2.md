# SpinTune v2: Design Document

**Fleet-learned charge tuning for CMOS spin-qubit cells, with an open benchmark to score any tuner**

| | |
|---|---|
| **Event** | Equal1 × Fsas "Compute the Future", Timișoara HPC Hackathon (InnoWeek 2026). Ideas pitch Tue 27 Oct 2026; final Fri 27 Nov 2026 at Qiskit Fall Fest |
| **Team** | Duo, 20+ h/week each through November (~180 focused hours). Laptops (Apple M4 Pro, 14 cores, measured below) |
| **Judging constraints** | Visible Qiskit use is required. HPC use is optional, so the large sweep is the first big item cut if time is short (§15.3) |
| **Version** | v2, 25 Oct 2026. Supersedes `SpinTune_Design_Proposition.md` (v1) for all technical content. `SPINTUNE.md` stays as pitch notes but must be updated to match this document (§15.1) |
| **Inputs** | v1 design; `SPINTUNE.md`; `FEASIBILITY_REVIEW.md` (findings 1–8, addendum A–E); a builder review of this document's first draft (§1.3); the IBM R2P Qiskit course in this folder; literature and simulation checks run 25 Oct (§1.2) |
| **Status** | Design. Small feasibility simulations have been run (§1.2). No tuner has been built. Every target below is a hypothesis, frozen before the test fleet is generated (§11.5) |

Tags used throughout:
- **[measured]**: we ran it.
- **[sourced]**: published, with a link.
- **[assumed]**: our assumption, always swept.
- **[design call]**: a choice made in this document, which the team can override.

---

## 0. Pitch

> Equal1 builds qubits the way the chip industry builds chips: 29–35 quantum-dot cells per chip, many chips per wafer, all from a commercial 22 nm FD-SOI process. But every cell still has to be tuned before it can hold a qubit, and today's tuners mostly start each device from scratch, as if it were the first one ever made.
>
> **SpinTune treats tuning as a fleet problem.** It learns from a simulated fleet of Equal1-style cells. The fleet uses Equal1's published gate layout and sensor, with variation at wafer, chip and cell level calibrated to published 22FDX measurements. It also learns from the cells already tuned on the same chip. A new cell then reaches its target charge state with fewer measurements, and with no silent failures. We ship the whole thing as an open benchmark with a stated success metric, so any tuner (ours, a commercial one, or a lab script) can be scored on the same virtual devices, on-premises, without calibration data ever leaving the site.

**Why the fleet matters [measured, §1.2]:**
- Within one 22FDX chip, first-electron voltages differ by about 22 mV (1–1.5 charge periods). Across a wafer they differ by about 100 mV, several periods [sourced].
- Under these spreads, setting a cell to the fleet-average voltage with no measurements finds the target charge state only **1–6%** of the time, for a charge period of 15–25 mV.
- Using the average of the cells already tuned on the same chip raises that to **6–12%** and shrinks the search region about 3.5× per axis.
- That gap is the information SpinTune learns to exploit.

### If it works: what changes

1. **Tuning cost per cell falls after the first cell on a chip.**
   - Pre-registered target: warm-started cells reach their target at ≥ 90% reliability with ≥ 20% less measurement cost than the same search started cold. They must also beat the best classical tuner.
   - Stretch target: 2× less cost.
   - For a manufacturer adding cells per chip and chips per system, the first stage of bring-up stops costing the same for every cell.
2. **"Tuned" becomes a measured claim, not a hope.** Every tuner reports how often it declared success wrongly, against a pre-registered ceiling of 1%. When nobody is watching 29 cells × many chips, an unattended tuner that doesn't lie about success is worth more than a fast one.
3. **The fab gets a number to design to.** The "gain versus fabrication spread" map (§12) shows how much device variability the calibration stack can absorb before tuning cost explodes. Process engineers can trade a tighter threshold-voltage spread against calibration time. Fab variability becomes something the system design can quantify.
4. **The field gets a common yardstick.** The community's own data-needs review notes that there is **no standard success metric** for autotuning, so published results can't be compared ([arXiv 2312.14322](https://arxiv.org/abs/2312.14322)). SpinTune's benchmark (fixed fleets, metered measurements, one success definition) lets Equal1 score any vendor's tuner against its own device statistics.
5. **It runs anywhere.** Everything runs on a laptop or an on-prem cluster. That's the sovereign, offline angle for Fsas.
6. **A quantitative answer to "where should the exchange gate operate, and does charge noise matter there?"**
   - A Qiskit simulation of the CZ gate, built from the device Hamiltonian, breaks the two-qubit error budget into charge noise, dephasing, pulse error and the residual floor.
   - If, as our first estimate suggests (§8.5), it says "operate at the symmetric point with the fastest adiabatic pulse and stop", that saves engineering effort.
   - If not, it shows where optimising pays.

**What it does not claim:**
- SpinTune covers charge-state tuning of already-formed dots. At rf-readout rates that's seconds to minutes of measurement per cell, not the hours of full qubit bring-up.
- It makes no claim about physical gate fidelity, no quantum-advantage claim, and no claim about any commercial tuner's performance.
- Everything is simulated until real scans are available (§7.5).

**If it doesn't work, we report it straight.** If the warm start can't beat a classical tuner, because classical search is already near the minimum cost the rules allow, the headline becomes the benchmark plus measured headroom. That is a published answer to the open question of how much cross-device transfer is worth at realistic fabrication spread. The Qiskit error budget is the second result either way.

---

## 1. What changed, and why

### 1.1 Feasibility-review findings → resolutions

| Review finding | Resolution | Where |
|---|---|---|
| **1** Absolute occupancy can't be identified from a local window | Every tuner first finds the empty (0,0) region and counts transitions from it, using a shared, billed anchor routine. The reader outputs transition masks, not absolute-occupancy classes | §5 |
| **2** The fidelity optimiser has no observation model | Shown that t_c and the lever arm can't be measured from charge data in the qubit regime (§8.4). C2 becomes a model-based error-budget study that doesn't depend on tuner estimates. No optimiser is built | §8 |
| **3** The barrier trade-off isn't produced by the equations | Accepted. Sampled second-order noise, a validity domain, an adiabatic pulse, and a pre-computed budget map instead of a trained optimiser | §8.5 |
| **4** Measurement budget vs compute budget | Fixed query shapes and pitches; an exact cost model with overheads; compute rebuilt from measured timings | §4, §12 |
| **5** Classifier-to-tuner contract | Reader outputs, label semantics and margin are specified. One shared lattice-tracking search policy replaces a BO objective that has no way to count electrons. Oracle-assisted development baseline | §5, §6 |
| **6** Physics and validation contract | One exchange convention; CZ from an explicit Hamiltonian with an adiabatic pulse, verified numerically; hidden parameters and fresh noise in the evaluator; floor and Aer λ handled; CPhase error model corrected | §8 |
| **7** Design intent vs evidence; versioned facts | Evidence table; v3 citations; `T` in mK; check scripts committed | §1.2, §13 |
| **8** Scope and realism claims | One scope, set by the 22FDX layout; QFlow used only as an external test; G1 is a sanity check; FD-SOI noise scenario; six-dot redefined and deferred | §3, §7, §11 |
| **A–C** Python pin; timing; congruent cells | Python 3.12 pinned and verified; timings measured; anchor + count | §12, §13, §5 |
| **D** The zero-measurement tuner gets 82% | Fleet rebuilt with sourced, hierarchical spreads in mV (now 1–6%). Headroom gate G0 measured against the cost floor | §7, §11 |
| **E1** HPC load depends on implementation | Lazy tile cache. HPC is redefined as an optional assumption sweep | §4.3, §12 |
| **E2** Scan-and-fit baseline missing | Added as T2 | §6 |
| **E3** The barrier is invisible in QArray | QDarts adopted as a second simulator (finite t_c, non-constant charging energy), verified to run | §3.3 |
| **E4** Six-dot topology unconfirmed | Equal1's published 22FDX cell is the device template; six-dot dropped; multi-cell chip deferred | §3 |
| **E5** Pitch says Qiskit "proves" it | Reworded: Qiskit gives a model-based error budget | §0, §10 |

### 1.2 Evidence status (25 Oct 2026)

| Item | Status | Result |
|---|---|---|
| QArray 1.6.0 + Qiskit 2.6.1 + Aer 0.18.0 + qiskit-experiments 0.14.2 + Samplomatic 0.21.0 on Python 3.12 | **[measured]** installs | All required APIs present: `StandardRB`, `InterleavedRB`, `LayerFidelity`, `PauliEvolutionGate`, `InjectNoise`, `Twirl`, `optimal_Vg` |
| QDarts 1.0.5 on Python 3.12, macOS arm64 | **[measured]** installs and runs, in its own environment (numpy 1.26) | 2-dot + sensor scan: 0.2 s at 32×32, 0.3 s at 64×64. t_c of 5 vs 80 µeV changes the scan by ~15% of the signal range |
| QArray timing (M4 Pro, one thread, noise + latching, T = 300 mK) | **[measured]** | 2 dots: 97 ms per 100×100 map, 9.9 ms per 32×32. 4 dots: 116 / 12.4 ms |
| Charge cells congruent in constant capacitance | **[measured]** | (1,1), (2,2), (3,3) cells: 3,011–3,023 px each |
| Zero-measurement success, v1 spreads | **[measured]** | 82% (offsets uniform over one period), 100% (no offsets) |
| Zero-measurement success, sourced spreads in mV (σ_cell 22 mV, σ_die 74 mV; 40 chips × 10 cells; generic double dot; die offset only) | **[measured]** | P = 15 mV: fleet mean **1%**, earlier-cells mean **6%**. P = 25 mV: **6%** and **12%** |
| CZ from exchange Hamiltonian, quasi-static δJ | **[measured]** | Pure ZZ error, F = 1 − 0.8 sin²(δφ/4), matching simulation to 4 digits. v1's `CPhase(π+δφ)` model overstates infidelity 3× |
| CZ pulse shape | **[measured]** | Square pulses need synchronisation with ΔE_z (1−F = 5.6×10⁻⁴ at J = 5 MHz, ΔE_z = 63 MHz). An earlier "1.00000" was a coincidence of round ΔE_z values. A Hann (sin²) pulse gives 1−F ≤ 1.2×10⁻⁶ for J ≤ 20 MHz at ΔE_z = 63 MHz, with no synchronisation |
| Equal1 device facts (carrier, gate layout, sensing, lever arm, spreads) | **[sourced]** | §3.1, §7.2 |
| Tuners, reader, estimator, benchmark | Not started | — |

The scripts behind every [measured] row are listed in §13 (row 3). They must be committed before the pitch.

### 1.3 Builder-review resolutions (all are design calls)

| Builder question | Resolution |
|---|---|
| Every tuner pays for the anchor and confirmation, so where does saveable cost come from? A classical tuner may already be near that floor | New **oracle-start tuner T★** measures the irreducible floor. **G0** now tests headroom = (best classical cost − floor) / best classical cost. Probes are adaptive, not a fixed 2,304 px. Cost is reported in total and net of the floor. If G0 fails, we report it straight (§0) |
| BO can't count electrons at arbitrary windows | GP-BO is dropped from the core. All search tuners share one **Bayesian lattice-tracking policy** and differ only in their prior. "Cold" (T4) is the same policy with a flat prior. G3 requires beating both T4 and the best classical tuner |
| Which parameters vary at die and wafer level? | Specified in §7.1–7.2: wafer, die and cell levels; shared offsets, lever-arm and cross-capacitance scales; radial edge shift; die position visible as metadata; hierarchy strength swept. T6's default is empirical-Bayes shrinkage; a learned set encoder is optional |
| E_c / α / P inconsistent; mV vs periods | α and E_c are sampled; P = E_c/α is derived (default ≈ 15 mV). All spreads and domains are in mV, as sourced |
| False-success tolerance; margin too small to mean anything | False success ≤ 1% of declared successes (upper 95% bound ≤ 2%). Margin ≥ 0.15 P from every transition (≈ 2.3 mV), and ≥ 3σ of gate noise |
| What limits the fastest valid J? Are §8.4's measurements feasible? | Hann-shaped adiabatic pulse (verified), J ≤ ΔE_z/3. The t_c and α measurements are infeasible in the qubit regime (t_c ≈ 2 µeV; α linewidth ≈ 0.34 mV, sub-pixel). Both are removed from the interface; C2 is a budget map over sourced ranges |

---

## 2. Goals, non-goals, anti-goals

**Goals**
1. **C1 (primary):** a fleet- and same-chip-informed warm start for charge tuning. On held-out simulated cells, at equal reliability and with every measurement billed, it must beat both the same search started cold and the best classical baseline.
2. **C4 (primary deliverable):** an open, reproducible benchmark:
   - device generator;
   - frozen fleets;
   - metered measurement interface;
   - one success definition;
   - baselines, including the oracle-start floor;
   - scripts that regenerate every plot from logs.
3. **C2 (supporting, protected, because Qiskit is required):**
   - a model-based CZ error-budget study in Qiskit, built from the device Hamiltonian, with RB in Aer;
   - plus a real-hardware run that validates our benchmarking code.
4. **C3 (stretch, first to cut):** drift detection and local re-tune.

**Non-goals**
- Dot formation, barrier pinch-off, spin readout, and qubit-level calibration on spins.
- Estimating tunnel coupling, lever arms or spin parameters from measurements (shown infeasible in this regime, §8.4).
- Replacing or integrating with any commercial tuner.
- Real Equal1 hardware. We use it if offered; nothing depends on it.
- Joint tuning of a whole multi-cell chip.

**Anti-goals (a failure even if it technically works)**
- A headline that comes from an easy fleet, a weak baseline, or a generous cold-start box.
- A tuner that looks cheap because it stops early and wrongly. False successes are failures and are reported separately.
- Quantum for show: quantum kernels, QAOA, VQE or SQD with no job to do (§10.3).
- Calling a model-based Aer result "verification" of a physical qubit.
- Unsourced or outdated numbers on slides.

---

## 3. Scope and device template

### 3.1 Device under test **[design call]**

The primary device is an **Equal1-style 22FDX double-dot cell**. A **generic plunger-gate double dot** is kept as a secondary template, for comparison with the autotuning literature and public datasets.

| | Primary: "E1-22FDX-like" cell | Secondary: generic double dot |
|---|---|---|
| Gates | 5 in series: QA0, QT0, QT1, QT2, QA1, plus a global back gate (BG). No plunger gates. Dots form between QT gates; barrier gates and back gate act as plungers [sourced: [2412.08422v2](https://arxiv.org/html/2412.08422v2)] | 2 plungers, 1 inter-dot barrier |
| Charge-tuning plane | (QT0, QT2) at fixed QT1 and BG | (P1, P2) |
| Tunnel-coupling knob | QT1. Published: 350 mV decoupled, 390 mV separating, 420 mV merged [sourced]. Fixed during charge tuning | Barrier gate |
| Sensor | Single-electron box at the array edge, rf reflectometry at 75.5 MHz [sourced] | Charge-sensor dot |
| Carrier | Electrons [sourced: 2412.08422v2, [2412.08302v1](https://arxiv.org/html/2412.08302v1), [equal1.com/technology](https://www.equal1.com/technology)] | Electrons |

This layout is our reading of the published papers, not a confirmed Bell-1 specification. It is the first question for Equal1 (§14).

### 3.2 What "a chip" means here

- Equal1 reports 29 NMOS + PMOS cells per chip (its technology page says 35), each a linear array of at most 3 dots [sourced].
- The **unit of tuning is one cell**. A "chip" in the fleet is a group of 10 cells sharing die-level parameters. A "wafer" is 50 chips sharing wafer-level parameters (§7.1).
- The v1 six-dot linear array is dropped, since it is not a confirmed Equal1 topology. Multi-cell chip tuning is deferred (§3.4).

### 3.3 Simulators

- **QArray 1.6.0** (constant capacitance, Rust backend) [measured].
  - Used for the training fleet and all in-distribution fleets.
  - It is fast and gives analytic ground truth (`optimal_Vg`).
  - Limits: identical charge cells, no tunnel coupling, no dot formation.
- **QDarts 1.0.5**, second simulator ([repo](https://github.com/qplai/QDarts), [arXiv 2404.02064](https://arxiv.org/abs/2404.02064), MIT licence) **[design call]**.
  - **Physics:**
    - finite tunnel coupling in a local Hamiltonian, with an exact thermal state;
    - voltage-dependent tunnel couplings (T_ij = exp(W_ijᵀv + b_ij));
    - non-constant charging energy (per-dot k, realistic 3–5), which breaks the identical-cell symmetry;
    - sensor dots, white noise and Ornstein–Uhlenbeck noise;
    - ground-truth states and polytopes.
  - **Missing:** latching and 1/f noise. We add these behind the interface (§4.3).
  - **Use:** the **OOD-simulator fleet**: train on QArray, test on QDarts, with charge-tuning-regime t_c (tens of µeV, which rounds the triple points). This is our main sim-to-sim stress test.
  - **Constraints [measured]:**
    - ~0.2 s per window, so it suits evaluation, not bulk training;
    - it pins `numpy<2`, `scipy<=1.12`, `cvxpy==1.5.2`, which conflicts with QArray's `numpy==2.2.4`. It runs in its own environment as a **worker process behind the measurement interface**.
- **Considered and not adopted:**
  - **SimCATS 2.0.0:** geometric model with no t_c parameter, and a CC BY-NC-SA licence.
  - **QDFlow 1.0.2:** no tunnel coupling, and orders of magnitude slower. A candidate for a later OOD fleet.
- **Fallback if QDarts misbehaves:** replace the OOD-simulator fleet with QArray plus our own rounded inter-dot lineshape layer (§8.4 formula).

### 3.4 Deferred until after 27 Nov

These are listed so nobody builds them early:
- multi-cell chip tuning with crosstalk (`LayerFidelity`/EPLG would then be the natural chain metric);
- t_c and lever-arm estimation in the charge-qubit regime;
- noise-learning comparisons;
- valley physics;
- real-Equal1 replay.

---

## 4. The measurement interface (the only window onto a device)

**Rule:** tuners never see device parameters, noiseless maps or labels. They act only through this interface, which bills every query. Only the evaluator sees ground truth. The one exception is public metadata: chip ID, cell index and die position (x, y) on the wafer, which a fab always knows.

### 4.1 Query types [design call]

| Query | Shape | Pixels | Use |
|---|---|---:|---|
| `window(center, pitch, size)` | 2D, size ∈ {16, 32, 64} | 256 / 1,024 / 4,096 | Search, confirmation |
| `ray(start, direction, pitch, n=64)` | 1D | 64 | Anchor, line finding |

- **Pitch:** chosen per query from {0.5, 1, 2, 4} mV.
- **Domain:** a fixed box of ±300 mV per axis around the fleet-nominal target, i.e. ±4σ of the total target spread (σ ≈ 77 mV).
- **Domain size:** at 1 mV pitch, a full scan would be ~360,000 px. Coarse-to-fine search is forced, as on real hardware.
- **Budget:** B = 20,000 px per cell, plus a wall-time cap of 120 s per cell for the tuner's own computation [assumed].

### 4.2 Cost model (pixels are not time)

Every query is logged with pixel count and estimated time:

```text
t_query = n_px · t_int + t_setup + n_lines · t_settle + |ΔV| / slew
```

| Term | RF scenario (Equal1-relevant) | DC scenario | Status |
|---|---|---|---|
| t_int per pixel | 10 µs | 1 ms | [assumed], swept |
| t_setup per query | 20 ms | 20 ms | [assumed], swept |
| t_settle per line | 1 ms | 5 ms | [assumed] |
| slew | 1 V/s | 1 V/s | [assumed] |

Results are reported as pixels and as time in both scenarios, plus the tuner's compute time. Charging per-query overhead stops a tuner looking cheap by issuing many tiny windows ([arXiv 2509.19537](https://arxiv.org/abs/2509.19537) found orchestration overhead became the limit).

**Scale check:** at RF rates the whole 20,000-pixel budget is 0.2 s of integration. Savings are per-cell cost and reliability, not hours.

### 4.3 Simulation behind the interface [design call]

- **Lazy tile cache.** Noiseless maps are computed on demand as 64×64 tiles per pitch and memoised per cell.
- **Noise per query.** Noise is generated independently per query: white noise, plus telegraph noise along each query's own time axis, plus 1/f drift (only for the drift stretch goal).
- **Latching** is applied per query.
- The noise model is part of the frozen specification. QDarts runs as a worker process that returns tiles through the same interface.

---

## 5. Reading the device: anchor, count, segment

### 5.1 The occupancy reference

In a constant-capacitance device, a window can't tell (1,1) from (2,2) [measured]. Every tuner therefore runs the same **anchor routine** before it may declare a charge state:
1. From the current best guess, cast rays toward lower voltage on each axis. Electrons leave as voltage falls.
2. Stop when a ray crosses no transition for longer than 1.5 × the prior's addition voltage. That point is in the empty (0,0) region.
3. Count transitions along the path back to the candidate point, separately for dot-L and dot-R lines (by line orientation). Use one extra diagonal ray when orientation is ambiguous.
4. Every ray is billed.

A tuner may reuse an anchor already established on the same cell. A failed anchor (budget hit, or an ambiguous count) means the run can't declare success.

**The cost floor.** The anchor plus the mandatory confirmation (§6) is a cost every tuner pays. The oracle-start tuner T★ (§6) measures it: about 1.2–1.5k px by the reviewer's estimate, to be measured in week 1.

### 5.2 Reader contract

The **reader** is a small CNN with a U-Net-lite encoder-decoder, shared by all tuners.

- **Input:** one window or ray (normalised sensor signal) plus its pitch.
- **Output per pixel:** probabilities for {no transition, dot-L line, dot-R line, inter-dot line}.
- **Abstention:** a confidence map, and an abstain flag when mean confidence along detected lines falls below a validation-tuned threshold.
- **Labels:** from the evaluator's per-pixel occupancy. A pixel is a "dot-L line" if dot L's occupancy changes between it and a neighbour, and so on. A label describes the pixel, not the window.
- **Not the reader's job:** charge state. That comes from anchor + count (§5.1), which is algorithmic and separately testable.
- **Margin at the final point V*:** the minimum over nearby transitions of the distance along that transition's normal. It must be **≥ 0.15 P** (≈ 2.3 mV at P = 15 mV), so the cell is stable against slow drift and telegraph-noise jumps, **and** ≥ 3σ of quasi-static gate noise projected onto the normal (§7.3). The first condition dominates.
- **Training data:** windows from the train fleet only, mixed across pitches and noise levels.

### 5.3 Oracle-assisted development baseline

During development only, each tuner also runs with a **perfect reader** (evaluator-supplied masks). This checks that the search geometry and budget work before reader errors are added. These results are labelled "oracle-assisted" and never mixed with sensor-only results.

---

## 6. Tuners and baselines

All tuners share:
- the interface;
- the reader;
- the anchor routine;
- the domain, budget, time cap and stopping rule.

**Stopping rule:** a tuner may declare success at V* only after a **confirmation**: a 32×32 window at 1 mV pitch centred on V* shows (1,1) by count, with margin satisfied (§5.2). It is billed.

**Shared search policy: Bayesian lattice tracking [design call].** Tuners T4–T6 use the same policy and differ only in what they know before the first query.

1. **State.** Gaussian (Laplace-approximated) posterior over the local lattice:
   - the voltage of the (0,0)→(1,1) reference point;
   - a 2×2 matrix mapping charge-number steps to voltage steps (line directions and spacings).
2. **Update.** Each measured line crossing (from reader masks) is a linear-Gaussian observation on these parameters.
3. **Next query.** A window or ray centred on the predicted (1,1) centre:
   - size chosen to cover the 2σ uncertainty;
   - coarsest pitch that still gives ≥ 4 px per predicted charge period.
4. **Confirm.** Anchor once the posterior is tight enough to place rays, then confirm when σ(target) < 0.1 P.
5. **Builder's choice:** the exact update algebra and window-size schedule, within these rules.

| ID | Tuner | Starting knowledge | What it isolates |
|---|---|---|---|
| T★ | **Oracle start**: placed at the true target, then anchor + confirm | Truth (evaluator) | The irreducible cost floor under the rules |
| T0 | **Random search**: uniform windows | None | Floor of the comparison |
| T1a / T1b | **Zero-search start**: go to the fleet-mean (a) or earlier-cells-mean (b) target, anchor, confirm | Prior means only | What the spec sheet alone gives |
| T2 | **Scan-and-fit**: one coarse scan of the domain's prior 95% region, fit lattice lines (Hough plus least squares) to a capacitance model, compute the target analytically, confirm | None | The physics baseline an Equal1 engineer would propose. Favoured by constant capacitance, which we report |
| T3 | **Transition navigation**: published line-following heuristic from the anchor | None | Competitive classical method |
| T4 | **Lattice tracking, cold**: shared policy, flat prior over the domain | None | The value of the prior (same policy) |
| T5 | **SpinTune-F**: shared policy, fleet prior (with radial term from die position) plus the learned probe estimator | Fleet | C1, fleet information |
| T6 | **SpinTune-H**: T5 plus same-chip history | Fleet + earlier cells on this chip | **Headline:** C1, hierarchical information |

**SpinTune components (T5/T6) [design call]:**
- **Fleet prior:** a Gaussian over target location and lattice parameters, with a radial term in die position, fitted on the train fleet.
- **Same-chip history (T6, default): empirical-Bayes shrinkage.** A hierarchical Gaussian model, fitted on the train fleet, gives the posterior over this chip's shared offset and scales from the confirmed targets and lattice fits of cells 1…k−1.
  - **Optional:** a learned set encoder (DeepSets), only if it beats shrinkage on validation by ≥ 10% cost.
- **Learned probe estimator (the AI component):**
  - **Input:** reader masks of the first coarse window, which the policy takes only when the prior's target σ > 0.5 P. Probes are adaptive, not fixed.
  - **Model:** a small CNN with a heteroscedastic Gaussian head, trained by negative log-likelihood on the train fleet.
  - **Output:** a posterior over target and lattice parameters, which seeds the lattice tracker.
  - **Calibration:** coverage of 50% and 90% ellipses on validation.

**Required ablations:**
- T4 + probe estimator (the estimator without fleet prior);
- T5 without estimator (prior only);
- T6 without estimator (shrinkage only).

These show whether gains come from the prior, the history, or the learned estimator.

**Optional extra baseline (cut early if time is short):** GP-BO (BoTorch) using the lattice tracker's occupancy prediction as its objective.

**Tuning order on a chip:** a fixed random order per chip. Cell k sees only cells 1…k−1. T6's gain is reported as a function of k.

---

## 7. The fleet

### 7.1 Structure **[design call]**

The fleet is hierarchical: **wafer → chip (50 per wafer) → cell (10 per chip)**.

| Level | Shared by | Varies |
|---|---|---|
| Wafer | All cells on the wafer | Common voltage offset (σ_wafer); radial edge-shift amplitude Δ_edge |
| Chip (die) | All cells on the chip | Common-mode offset (both dots) σ_die; lever-arm scale (±5%); cross-capacitance scale (±10%); radial term Δ_edge·(r/R)² from die position |
| Cell | — | Per-dot first-electron offset σ_cell; per-dot lever arms (±10% about the chip scale); cross-capacitance; inter-dot capacitance; E_c |

- **Splits** are by whole wafer: train, validation and test never share a wafer.
- **Hierarchy strength** (the fraction of variance at chip level) is a swept assumption in §12. The headline holds only if it survives sourced values.

### 7.2 Parameters (defaults and sweep ranges)

| Parameter | Default | Sweep | Source / status |
|---|---|---|---|
| Lever arm α, QT gates to dots | 0.27 eV/V | 0.2–0.4 | [sourced] Equal1 22FDX measured ([2412.08302v1](https://arxiv.org/html/2412.08302v1)); Quobly/CEA 22FDX 0.2–0.4 ([2501.10146](https://arxiv.org/abs/2501.10146)) |
| Charging energy E_c | 4 meV | 2–8 meV | [sourced] 2.0–4.5 meV in multi-gate 22FDX dots (2501.10146); 15 ± 4 meV in transistor dots ([2310.20434](https://arxiv.org/html/2310.20434)), outside our cell type |
| Charge period P = E_c/α | ≈ 15 mV (derived) | ≈ 5–40 mV | Derived. Consistent with 25 ± 4 mV measured in transistor dots (2310.20434) |
| σ_cell, per-dot first-electron spread within a chip | 22 mV | 10–40 mV | [sourced] σ = 22 mV in 22FDX (2310.20434); Intel Si/SiGe 61–63 mV ≈ 0.8–1.0 P ([2307.04812v2](https://arxiv.org/html/2307.04812v2)) |
| σ_die, chip-to-chip offset within a wafer (residual after radial term) | 60 mV | 0–150 mV | [sourced, low–medium confidence] room-temperature V_th IQR ≈ 100 mV over ~40 dies on one wafer, total ≈ 74 mV including the radial term (2501.10146) |
| Δ_edge, radial edge shift | 0–60 mV (uniform per wafer) | 0–120 mV | [assumed], motivated by "edge gates systematically shifted" [sourced, qualitative] |
| σ_wafer, wafer-to-wafer offset | 30 mV | 0–80 mV | [assumed] |
| Cross-capacitance | 0.25 of diagonal (cell 0.1–0.4) | 0.1–0.6 | [assumed]; to replace with Equal1 data |
| Inter-dot capacitance | ±20% around nominal | ±10–30% | [assumed] |
| Temperature | 0.3 K (QArray `T=300`) | 0.35 / 0.5 / 0.75 K | Bell-1 runs at 0.3 K; Equal1 measured 350/500/750 mK ([2412.01920 v3](https://arxiv.org/html/2412.01920v3)) |
| Sensor white noise | SNR 10 per pixel at RF t_int | SNR 3–30 | [assumed] |
| Charge noise √S_E at 1 Hz | 4 µeV/√Hz (FD-SOI scenario) | 1.7–6.5 (FD-SOI); 0.3–1 (Si/SiGe) | [sourced] SOI 1.7–6.3 ([2209.01853](https://arxiv.org/abs/2209.01853)); 22FDX p-type median 6.5 ([2507.21306v1](https://arxiv.org/html/2507.21306v1)); Si/SiGe 0.29 ([2209.07242](https://arxiv.org/abs/2209.07242)) |
| Latching | lead p = 0.95, inter-dot p = 0.99 | 0.8–1.0 | [assumed] |

**Headroom check with sourced spreads [measured]:**
- Fleet-mean zero-search success is 1% (P = 15 mV) to 6% (P = 25 mV).
- The earlier-cells mean gives 6–12%.
- This used 400 cells, a generic double dot, and a die offset only. It will be re-run on the full §7.1 generator in week 1 as part of G0.

### 7.3 Charge noise as seen by gates

- Convert energy noise to gate-voltage noise with √S_V = √S_E / α.
- For 1/f noise, the quasi-static variance over [f_low, f_high] is S(1 Hz)·ln(f_high/f_low).
- **Default band:** f_low = 1/(1000 s), f_high = 1/t_gate, so ln ≈ 20.7 at t_gate = 200 ns.
- **Default numbers:** σ_E ≈ 18 µeV and σ_V ≈ 68 µV.
- **Correlation between dots:** 0 and 0.5 are both run [assumed]. The Si/SiGe correlation study ([2603.03051](https://arxiv.org/html/2603.03051)) is one literature scenario, not a calibration target.

### 7.4 Fleets

| Fleet | Size | Purpose |
|---|---|---|
| Pilot / development | 1 wafer subset: 10 chips × 10 cells | Building, debugging, G0 |
| Train | 20 wafers × 50 chips × 10 cells (10,000 cells) | Reader, estimator, priors. Final size set by learning curves |
| Validation | 2 wafers (1,000 cells) | Thresholds and hyperparameters for **all** tuners; calibration |
| **Test (in-distribution)** | 2 wafers (1,000 cells) | **Headline**, run once after the freeze |
| OOD-hot | 1 wafer (500 cells) | 0.75 K |
| OOD-noisy | 1 wafer | √S_E = 6.5 µeV/√Hz, sensor SNR 3 |
| OOD-crosstalk | 1 wafer | Cross-capacitance 0.4–0.6 |
| OOD-wafer | 1 wafer | σ_wafer and Δ_edge ×2 |
| OOD-simulator | 20 chips × 10 (size set by the week-1 speed test) | QDarts: finite t_c, non-constant charging energy |

### 7.5 External real-device test sets [sourced; none is FD-SOI; none has ground-truth t_c]

| Dataset | What it is | Labels | Tests |
|---|---|---|---|
| **QDSD** ([Zenodo 11402792](https://doi.org/10.5281/zenodo.11402792)), CC-BY-4.0, 726 MB | Si-MOS and GaAs stability diagrams (transport current) | **38 single-dot diagrams with transition polylines and electron-count regions 0, 1, 2, 3, 4+** | Anchor + count on real data, the direct test of finding 1 |
| **Delft D-CSD** ([Zenodo 16363472](https://doi.org/10.5281/zenodo.16363472)), CC-BY-4.0, 3.3 GB | 9,849 measured Si/SiGe and Ge/SiGe charge-sensed CSDs | None | Domain-gap check. **We hand-label 50 scans** with transition masks (~4 h) for reader F1 on real charge-sensed data |
| **QFlow 2.0 `exp_small`** ([NIST](https://data.nist.gov/od/id/66492819760D3FF6E05324570681BA721894)), NIST licence, registration, 13.4 GB zip | 756 measured Si/SiGe scans, 30–60 px | Human labels: no dot / single / double | Reader line-family detection. **Optional; cut early** (large download) |

QFlow lite (NIST, simulated) is used only as an external reader test, never for training. Its topology labels are not mapped to (1,1).

---

## 8. Physics layer: the Qiskit CZ error-budget study (C2)

### 8.1 Conventions [design call]

- Energies are in µeV; exchange is reported as J/h in MHz.
- **Exchange:** two-site Hubbard result J = 4 U t_c² / (U² − ε²) ([QTCAD](https://docs.nanoacademic.com/qtcad/theory_spin_fem/exchange/)). ε is measured from the (1,1) cell centre along the detuning axis, and the transitions sit at ε = ±U.
- **Validity:** t_c ≤ 0.1·(U − |ε|) [assumed], gate voltages inside the safe box, and **J ≤ ΔE_z/3** (pulse adiabaticity, §8.2).
- **Barrier control:** t_c = t₀·10^((V_QT1 − V₀)/V_dec).
  - J's slope of 18.4 decades/V is [sourced] ([2410.15590v2](https://arxiv.org/html/2410.15590v2)), i.e. ≈ 109 mV per decade for t_c.
  - Up to 30 decades/V for t_c is [sourced] ([2411.13882](https://arxiv.org/abs/2411.13882)).
  - Sweep V_dec over 33–110 mV per decade.

### 8.2 CZ gate model [measured checks]

```text
H(t) = (J(t)/4)(XX + YY + ZZ) + (ΔE_z/2)(ZI − IZ)        (frequency units)
Hann pulse: J(t) = J_max · sin²(π t / T),   ∫J dt = 1/2  ⇒  T = 1/J_max
single-qubit Z corrections calibrated once at nominal parameters, in the ΔE_z rotating frame
```

**Checks (`cz_check.py`, `cz_pulse_check.py`, Qiskit `Operator` + `average_gate_fidelity`):**
- **Hann pulse:** 1−F ≤ 4×10⁻¹⁰ at J_max = 5 MHz for ΔE_z ∈ {52.5, 63, 112.5} MHz, and 1.2×10⁻⁶ at J_max = 20 MHz, ΔE_z = 63 MHz. No synchronisation needed.
- **Square pulses** need √(J² + ΔE_z²)·t synchronised to the Zeeman splitting. Otherwise 1−F ≈ 2–30×10⁻⁴ at 5–20 MHz. Not used.
- **Quasi-static δJ** gives a **pure ZZ error**, F = 1 − 0.8 sin²(δφ/4) with δφ = π·δJ/J (matches to 4 digits). v1's `CPhase(π + δφ)` overstates the infidelity 3×.
- **Equal1's CZ** is 200 ns with F_CZ = 99.30% at 350 mK and 98.41% at 750 mK (Si/SiGe, [2412.01920 v3](https://arxiv.org/html/2412.01920v3)) [sourced]. That corresponds to J_max ≈ 5 MHz for a Hann pulse, or 2.5 MHz for a square one.

### 8.3 Noise and error-budget components

| Component | Model | Inputs |
|---|---|---|
| Charge noise through J | Per shot or RB sequence, sample one quasi-static (δε_L, δε_R, δV_QT1) from §7.3 and hold it fixed for the whole circuit. Evaluate J(ε + δε, V + δV) exactly, so second order at ε = 0 is kept | §7.3; ε, U, V_dec |
| Single-qubit dephasing during the gate | δf = (∂f/∂ε)·δε, quasi-static, calibrated to T2* = 5.9–11.1 µs [sourced, 2412.01920 v3] | ∂f/∂ε [assumed, micromagnet scenario] |
| Residual coherent pulse error | From the Hann-pulse Hamiltonian | J_max, ΔE_z [assumed 20–300 MHz] |
| Residual floor | Depolarising, set so the total equals Equal1's reported CZ error **at the nominal point** (no double counting). Aer λ = (1 − F_avg)·d/(d − 1), d = 4 ([Aer docs](https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.noise.depolarizing_error.html)) | Reported F_CZ |

### 8.4 Why the tuner doesn't estimate these parameters

- **t_c:** at Equal1's exchange strength (J ≈ 2.5–5 MHz, U ≈ 2 meV), t_c = √(JU/4) ≈ 2–3 µeV. A polarisation-line fit (DiCarlo et al., ⟨n⟩ − N = ½[1 + (ε/Ω)·tanh(Ω/2k_BT_e)], Ω = √(ε² + 4t²), [PRL 92, 226801](https://arxiv.org/abs/cond-mat/0311308)) constrains t only for t ≳ 0.5 k_BT_e ≈ 13 µeV at 0.3 K.
- **α:** the thermal linewidth of a transition (≈ 3.5 k_BT/α ≈ 0.34 mV) is below the 0.5 mV minimum pitch.
- **∂f/∂ε and ΔE_z:** charge measurements can't see them.

So C2 is a **model-based map over sourced and assumed ranges**, not a capability of the tuner. The interface has no t_c or noise-trace queries (§4.1). This is the review's "operating-point sensitivity study" option.

### 8.5 The study and its expected outcome

**Map** the CZ error budget (each §8.3 component, and the total) over:
- ε ∈ [−U/2, U/2];
- J_max ∈ [1 MHz, ΔE_z/3];
- ΔE_z ∈ [20, 300] MHz;
- √S_E ∈ sourced ranges, with dot-to-dot correlation 0 or 0.5;
- ∂f/∂ε over its assumed range.

Two rules are marked on the map:
- **O0:** cell centre, default barrier;
- **O1:** ε = 0 with the fastest valid J.

**Back-of-envelope with the defaults [rough]:**
- **Barrier channel:**
  - δJ/J ≈ 0.3%, so CZ infidelity ≈ 4×10⁻⁶;
  - independent of the barrier setting.
- **Detuning channel** at ε = U/2, U = 2 meV:
  - δJ/J ≈ 1.2–1.7%, so infidelity ≈ 0.7–1.5×10⁻⁴;
  - negligible at ε = 0.
- **Dephasing during a 200 ns gate:** of order 10⁻³, falling as J rises.
- **Pulse error:** < 10⁻⁶ with Hann pulses.
- **Comparison:** Equal1's measured CZ error is ≈ 7×10⁻³.

**Expected result:**
- Charge noise via J is a few percent of the budget at most.
- The best point is ε = 0 with J at the adiabatic limit, which is a boundary set by the assumed ΔE_z. In other words, rule O1.
- If the full map confirms this, the C2 result is the error-budget figure plus the statement *"under sourced FD-SOI noise, rule O1 is sufficient; the remaining two-qubit error is dephasing and the residual floor"*.
- If the map shows regions where O1 loses ≥ 0.1 percentage points to the map's optimum, those regions (and the parameters that cause them) are the result.

---

## 9. Drift (stretch, C3, first to cut)

- **Injection:** telegraph-noise switching events from §7.3, plus slow 1/f drift.
- **Monitoring:** every k simulated jobs, a 32×32 reference window **chosen to contain at least two transition lines** near V*. A featureless patch can't be cross-correlated.
- **Detection:** 2D cross-correlation shift against the reference, with no ML; the reader checks the charge state.
- **Ground truth for "needs re-tune":** V* no longer meets the §11.1 success definition.
- **Recovery:** local re-tune seeded at V*, compared with a restart under the same horizon, success definition and total cost.

---

## 10. Quantum layer: what Qiskit does, and what the course materials give us

Qiskit use is required by the judging, so this layer is protected from cuts.

### 10.1 Model-based CZ and RB (C2)

| Step | Tool | Course source |
|---|---|---|
| Device Hamiltonian → CZ unitary per noise sample (Hann pulse, time-sliced) | `SparsePauliOp`, `PauliEvolutionGate` / `Operator` | Unit 4 Lesson 2 (quantum simulation, Trotterization) |
| Gate fidelity vs ideal CZ; analytic cross-check | `average_gate_fidelity` | Unit 1 |
| Bell state and 2Q InterleavedRB in Aer, noise fixed per sequence (one `NoiseModel` per quasi-static draw, averaged) | `qiskit_aer`, `qiskit_experiments.library.StandardRB`, `InterleavedRB` | Units 1 and 3 |
| *(optional, cut early)* Pauli twirling turns the coherent ZZ error into stochastic Pauli noise | Samplomatic `Twirl`, `InjectNoise`, `PauliLindbladMap` | Unit 3 Lesson 3 |

**Acceptance check:** the IRB-estimated CZ error in Aer must agree with the analytic average infidelity within the RB fit's confidence interval.

### 10.2 Real-hardware pipeline validation (a prerequisite we can get ourselves)

- **What:** run our StandardRB + InterleavedRB code on one CZ pair of an IBM Heron device, through the IBM Quantum Platform **Open Plan** (free, 10 min QPU per month, set up as in course Lab 0).
- **Pass test:** compare the extracted CZ error with the backend's reported error for that pair.
- **What this proves:** that our benchmarking code measures a real two-qubit gate correctly. It says nothing about spin qubits, and is labelled that way on every slide.
- **QPU budget:** ≤ 3 min. Develop against a fake backend first (`FakeTorino`, as in Lab 0).

### 10.3 Course content deliberately not used

- **Quantum kernels / QSVM (Unit 2 L2):** no evidence of benefit over a CNN for images; it would read as quantum for show.
- **QAOA, VQE, SQD/SKQD (Units 2, 4):** no job to do. A two-site Hubbard model is solved exactly in microseconds.
- **Layer fidelity / EPLG:** reserved for the deferred multi-cell extension.

### 10.4 Pitch framing from the course

IBM's quantum-centric supercomputing material lists **calibration** among the classical tasks that "remain essential throughout the quantum workflow" (Activation workshop, Unit 0, slide 69). SpinTune is that kind of HPC + AI calibration workload, for a spin-qubit system.

---

## 11. How success is measured (frozen before the test fleet runs)

### 11.1 Primary question and success definition

**Question:** *On unseen simulated 22FDX-style cells, does a fleet- and same-chip-informed warm start reduce charge-tuning measurement cost while keeping reliability, compared with the same search started cold and with the best classical tuner?*

**Success for one cell, all of which must hold:**
1. The tuner declares V* after a passing confirmation (§6).
2. The evaluator's noiseless (T = 0) occupancy at V* is (1,1).
3. The margin at V* satisfies §5.2: ≥ 0.15 P along every nearby transition normal, and ≥ 3σ projected gate noise.

**Failure** is anything else:
- no declaration within budget or time;
- a failed anchor;
- a declared V* that fails steps 2 or 3. That last case is a **false success**, counted as a failure and reported separately.

Cells with no reachable robust target are recorded. Results are shown for the full population and for reachable cells.

### 11.2 Metrics

| Outcome | Metric |
|---|---|
| Reliability | Fraction of cells succeeding within B = 20,000 px, with 95% CI |
| Cost (headline) | Restricted mean cost C = mean(min(T_success, B)), charging B for every failure. Reported in pixels and in RF/DC time |
| Cost net of floor (secondary) | C − C_T★, so differences in avoidable search are visible |
| Full picture | Success-versus-budget curve; median and p90 cost among successes; failure counts by type |
| Trustworthiness | False-success rate; abstention rate |
| Hierarchy | T6 cost as a function of the cell's position k on the chip |
| Runtime | Tuner compute time per cell; simulator time |
| C2 | Error-budget map; O1 loss vs map optimum; IRB-vs-analytic agreement |
| C3 (stretch) | Detection recall, false alarms per hour, delay, recovery cost vs restart |

### 11.3 Gates (pass/fail; thresholds frozen at the tagged commit)

| Gate | Question | Pass criterion |
|---|---|---|
| **G0 Headroom** (go/no-go, week 1) | Is there avoidable search cost to save? | On validation, (min(C_T2, C_T3) − C_T★) / min(C_T2, C_T3) ≥ 30%. T1a zero-search success is reported (preliminary 1–6%). **If it fails:** report it straight (§0) and keep running T4–T6 for the record. The fleet is never inflated beyond §7.2's sourced ranges |
| **G1 Generator sanity** | Does the simulator do what we say? | Lattice matches `optimal_Vg` within 1 px; noise spectrum slope within the set value ± 0.1; anchor + count correct on 100% of noiseless pilot cells |
| **G2 Reader** | Can we read windows? | Transition-mask F1 ≥ 0.9 in-distribution; anchor + count accuracy ≥ 98%. Always reported, never hidden: OOD results, QDSD electron-count accuracy, F1 on 50 hand-labelled D-CSD scans |
| **G3 Warm start (C1)** | Does it save measurement? | On ID test: (a) T6 reliability ≥ 90%; (b) false-success ≤ 1% of declared successes (upper 95% bound ≤ 2%); (c) paired cluster-bootstrap 95% CI of C_T6/C_T4 entirely < 1, practical target ≤ 0.8, stretch ≤ 0.5; (d) CI of C_T6 / min(C_T2, C_T3) entirely < 1; (e) ≥ 75% reliability on each OOD fleet; (f) negative transfer reported |
| **G3h Hierarchy** | Does same-chip history add value beyond the fleet? | CI of C_T6/C_T5 < 1 for cells k ≥ 3 |
| **G4 Error budget (C2)** | Is the Qiskit model sound, and what does it say? | Hamiltonian vs analytic formula agree to < 1% relative; Aer IRB vs analytic within the fit CI; IBM pipeline run within the CI of the backend-reported error. Result: the map and the O1 statement (§8.5) |
| **G5 Drift (C3, stretch)** | Cheap recovery? | Recall ≥ 90% at ≤ 1 false alarm per simulated hour; recovery ≤ 25% of restart cost at equal success |

### 11.4 Statistics

- **Paired design:** every tuner runs on the same cells, with the same noise seeds per query index.
- **Cluster bootstrap** over chips, nested in wafers. Cells on a chip are correlated. Tuner seeds are nested within cells.
- **Seeds:** 3 per stochastic tuner on the pilot; up to 5 at final if pilot interval widths justify it.
- **Precision:** at 90% reliability on 1,000 cells, the binomial 95% half-width is ≈ 1.9 points before clustering. Clustered intervals are estimated from the pilot.

### 11.5 Pre-registration

- **Freeze:** after validation and before the test fleets are generated, tag a commit containing:
  - this document's thresholds;
  - fleet seeds and config;
  - all tuners' hyperparameters;
  - the analysis script.
- **After the freeze:** test results are reported against that tag. Later changes are reported as deviations.

---

## 12. Compute plan

- **Measured** (§1.2): QArray window ~10 ms single-threaded; QDarts window ~0.2 s. With the tile cache, a repeated query costs < 1 ms.
- **Tuner overhead** (lattice-tracker updates, CNN inference) is to be measured in week 1. Planning estimate ≤ 1 s per run [assumed].
- **HPC is optional.** The sweep below is the HPC showcase if time and cluster hours allow. A coarse laptop version is the default.

| Job | Count | Core-hours (at ~1 s/run) | Laptop, 14 cores | 128-core node |
|---|---|---:|---:|---:|
| Full frozen evaluation: 9 tuners × 3 seeds × 3,200 cells (ID 1,000 + OOD 2,200) | ~86,000 runs | ~25 (+ ~6 for the QDarts fleet) | ~2.5 h | ~15 min |
| Coarse spread map (default): 3 σ_die × 2 hierarchy strengths × 2 noise × 1,000 cells × 4 key tuners (T2, T3, T4, T6) × 3 seeds | ~144,000 runs | ~40 | ~3 h | ~20 min |
| Full spread map (optional HPC): 5 σ_die × 3 σ_cell × 3 hierarchy × 3 noise × 2 temperatures × 1,000 × 4 × 3 | ~3.2 M runs | ~900 | ~3 days | ~7 h |
| C2 error-budget map (~10⁴ parameter points × 1,000 noise draws, 4×4 unitaries) | — | ~1–3 | < 15 min | — |
| Reader + estimator training (CPU) | — | ~10–30 | overnight | < 1 h |

**Threads:** pin backend threads to 1 per worker and parallelise across cells.

---

## 13. Prerequisites, and which we can get ourselves

| # | Prerequisite | Needed for | Can we get it ourselves? | How / status |
|---|---|---|---|---|
| 1 | Python 3.12 environment: qarray 1.6.0, qiskit 2.6.1, qiskit-aer 0.18.0, qiskit-experiments 0.14.2, qiskit-ibm-runtime 0.51.0, samplomatic 0.21.0, PyTorch (BoTorch only for the optional GP-BO baseline) | Everything | **Yes** | Core stack verified 25 Oct; PyTorch to add. Commit a lockfile (`uv`). QArray's Rust core has no wheel for Python ≥ 3.13 |
| 2 | Second environment: Python 3.12 + qdarts 1.0.5 (numpy 1.26, scipy 1.12, cvxpy 1.5.2) | OOD-simulator fleet | **Yes, verified** | Installs and runs on this Mac (builds `ecos` with the Xcode command-line tools). Wrap as a worker process |
| 3 | Git repo with committed check scripts | §1.2 evidence, §11.5 | **Yes** | The folder is not a git repo yet. Scripts to copy from the temporary scratch folder into `checks/`: `smoke.py` (as `bench_qarray.py`), `prior_check.py`, `hier_check.py`, `hier_check2.py`, `cz_check.py`, `cz_pulse_check.py`, `qdarts_check.py` |
| 4 | Sourced device parameters | §7 | **Yes, done** | §7.2. Low-confidence: σ_die, Δ_edge, σ_wafer, cross-capacitance |
| 5 | Equal1 device facts | §3 | **Mostly yes, done** | Electrons; 5 series gates; single-electron box + rf reflectometry; α = 0.27 eV/V. Open: which platform Bell-1 uses; spin drive in 22FDX |
| 6 | Real CSDs for external tests | §7.5 | **Partly, yes** | QDSD and D-CSD (CC-BY, direct download); QFlow 2.0 (NIST registration, optional). We hand-label 50 D-CSD scans. We can also email the authors of the 1,015-CSD FD-SOI segmentation paper ([arXiv 2604.13662](https://arxiv.org/abs/2604.13662)), which lists no data link |
| 7 | Compute | §12 | **Yes for everything except the full map** | M4 Pro laptop. Cluster hours from Fsas/UPT only for the optional full spread map |
| 8 | Real quantum hardware for pipeline validation | §10.2 | **Yes** | IBM Quantum Platform Open Plan (free, 10 min/month); set-up in course Lab 0 |
| 9 | Physics sanity review | §8 | **Partly** | Analytic cross-checks (done for CZ); R2P course advocates for the Qiskit side; Equal1 judges at the pitch |
| 10 | Spin-qubit hardware or Equal1 scans | Sim-to-real | **No** | Ask Equal1 (§14). Nothing depends on it |
| 11 | R2P capstone or extra IBM access | Optional | **Unknown** | The course mentions a team capstone project; ask the programme leads whether SpinTune can count |

---

## 14. Questions for Equal1 (most important first)

1. Do Bell-1 qubits run on the 22FDX cells or on the Si/SiGe devices? NMOS (electrons) or PMOS (holes)? Is our gate template in §3.1 right?
2. Cryogenic distributions across cells, chips and wafers: first-electron voltage, lever arms, E_c, cross-capacitance. How much is shared within a chip? Is the chip 29 cells or 35?
3. How are spins driven in 22FDX (micromagnet, ESR, spin-orbit / valley EDSR)? What is ΔE_z?
4. Measured √S_E at 1 Hz, and its exponent, in 22FDX and Si/SiGe devices.
5. t_c(V_QT) and J(V_QT) slopes; residual J; CZ pulse shape.
6. Could you share ~50 raw charge-sensed scans, even anonymised, as a frozen test?
7. How much do the electrostatics shift between cooldowns?

---

## 15. Plan

### 15.1 Before the pitch (Mon 26 Oct)

- [ ] `git init`; lockfiles for both environments; copy the check scripts into `checks/`; commit.
- [ ] Update `SPINTUNE.md` to match this document:
  - v3 fidelity numbers;
  - electrons and the series-gate layout;
  - FD-SOI noise values;
  - the exchange factor of 4;
  - the CZ ZZ model and Hann pulse;
  - warm-started *lattice tracking* in place of "BoTorch BO";
  - remove "proves it in Qiskit" and the six-dot demo promise.
- [ ] Two evidence slides:
  1. headroom (82% → 1–6%, and 6–12% with chip history);
  2. CZ from the device Hamiltonian (pure ZZ; Hann vs square pulse).
- [ ] Rehearse the §14 questions.

### 15.2 November (duo, 20+ h/week each)

The work splits into two tracks [design call]:
- **A:** fleet generator, interface, evaluator, anchor, T★/T0–T3, statistics.
- **B:** reader, lattice tracker, T4–T6, QDarts worker, Qiskit layer.

| Dates | Track A | Track B | Gates / exit condition |
|---|---|---|---|
| 28 Oct – 3 Nov | Hierarchical fleet generator, interface + ledger + tile cache, evaluator, anchor; **T★ and T3 first** | QDarts worker + speed test; C2 Hamiltonian/Hann code; download QDSD and D-CSD | **G0 measured** (T★ vs T3) on the pilot; G1 |
| 4 – 10 Nov | T0–T2; oracle-assisted runs; statistics code | Reader; hand-label 50 D-CSD scans; lattice tracker; T4 | G2; first baseline cost table |
| 11 – 17 Nov | Validation runs for all tuners; **freeze tag** | Fleet prior, shrinkage (T6), probe estimator (T5); ablations | Pre-registration commit |
| 18 – 22 Nov | Test + OOD runs; external tests | Aer IRB; IBM hardware run; C2 map | G3, G3h, G4 |
| 23 – 24 Nov | Coarse spread map; full map if cluster hours exist | Drift stretch if time | (G5) |
| 25 – 26 Nov | Demo + dry run | Demo + dry run | — |
| 27 Nov | Final | Final | — |

### 15.3 Cut order if time runs short

1. Drift (C3).
2. Full spread map (keep the coarse one).
3. QFlow 2.0 external set.
4. GP-BO extra baseline.
5. Samplomatic twirling demo.
6. T6 set-encoder variant (keep shrinkage).
7. Reduce the OOD-simulator fleet (never remove it).

**Never cut:**
- interface and evaluator;
- T★, T2, T3, T4, T5, T6;
- G0–G3h;
- the Qiskit CZ budget with Aer IRB;
- the IBM hardware pipeline run.

### 15.4 Demo (27 Nov)

1. A new virtual chip.
2. Cell 1 tuned cold; cells 2–10 warm, with the cost counter falling toward the T★ floor.
3. A side-by-side race: T4 vs T6, measured pixels lighting up.
4. The false-success counter.
5. The coarse gain-vs-spread map.
6. The CZ error-budget bar from the Hamiltonian in Qiskit, with the IBM pipeline check.
7. The gates slide: pass/fail, including any failures.

---

## 16. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Classical search (T3) is already near the floor, so G0 fails | High | Measured in week 1 before any learning is built. If it fails, report it straight (§0) |
| Scan-and-fit (T2) wins in a constant-capacitance simulator | High | Expected to some degree; reported. The OOD-simulator fleet tests whether T2's advantage survives non-constant charging and finite t_c. T6's value is its cost after the first cell, which T2 can't use |
| Sim-to-real gap | High | QDarts fleet, external data, sourced spreads; stated on the honesty slide |
| The hierarchy structure (what is shared per chip) is assumed | Medium | Swept in the spread map; ask Equal1 (§14 Q2) |
| σ_die is low-confidence (room-temperature V_th) | Medium | Swept 0–150 mV |
| Tuner compute overhead erases savings at RF rates | Medium | Report compute time; the RF/DC crossover is a result |
| Reader fails on OOD and external scans | Medium | Abstention; reported; anchor + count is separately testable |
| C2 shows "rule O1 is enough" | Expected | That is a result (§8.5) |
| QDarts install or speed problems | Low–Medium | Verified install; lineshape-layer fallback |
| IBM Open Plan queue times | Low | Develop on a fake backend; submit early |

---

## 17. References

**Equal1 and 22FDX**
- Equal1 Si/SiGe two-qubit processor, **cite v3**: [arXiv 2412.01920v3](https://arxiv.org/html/2412.01920v3). v1 numbers (300/740 mK) are superseded
- Equal1 22FDX quantum-dot cells: [arXiv 2412.08422v2](https://arxiv.org/html/2412.08422v2), [arXiv 2412.08302v1](https://arxiv.org/html/2412.08302v1)
- 22FDX transistor dots, first-electron spread: [arXiv 2310.20434](https://arxiv.org/html/2310.20434)
- 22FDX multi-gate dots (Quobly/CEA): [arXiv 2501.10146](https://arxiv.org/abs/2501.10146)
- Equal1 technology page: [equal1.com/technology](https://www.equal1.com/technology)

**Noise, tunnel coupling, exchange**
- SOI charge noise: [arXiv 2209.01853](https://arxiv.org/abs/2209.01853)
- 22FDX p-type charge noise: [arXiv 2507.21306v1](https://arxiv.org/html/2507.21306v1)
- Si/SiGe thin-well charge noise: [arXiv 2209.07242](https://arxiv.org/abs/2209.07242)
- Correlated noise, Si/SiGe array: [arXiv 2603.03051](https://arxiv.org/html/2603.03051)
- Intel first-electron variability: [arXiv 2307.04812v2](https://arxiv.org/html/2307.04812v2)
- MOS tunnel-coupling slope: [arXiv 2411.13882](https://arxiv.org/abs/2411.13882)
- Diraq/imec exchange slope and CZ: [arXiv 2410.15590v2](https://arxiv.org/html/2410.15590v2)
- Exchange theory: [QTCAD](https://docs.nanoacademic.com/qtcad/theory_spin_fem/exchange/)
- Polarisation-line t_c measurement: DiCarlo et al., [PRL 92, 226801 (2004)](https://arxiv.org/abs/cond-mat/0311308)

**Simulators, data, autotuning**
- QArray: [arXiv 2404.04994](https://arxiv.org/abs/2404.04994)
- QDarts: [arXiv 2404.02064](https://arxiv.org/abs/2404.02064), [repo](https://github.com/qplai/QDarts)
- SimCATS: [repo](https://github.com/f-hader/SimCATS) (CC BY-NC-SA)
- QDFlow: [arXiv 2509.13298](https://arxiv.org/abs/2509.13298)
- Real-device data: [QDSD](https://doi.org/10.5281/zenodo.11402792), [Delft D-CSD](https://doi.org/10.5281/zenodo.16363472), [QFlow 2.0](https://data.nist.gov/od/id/66492819760D3FF6E05324570681BA721894)
- Data needs of quantum-dot automation: [arXiv 2312.14322](https://arxiv.org/abs/2312.14322)
- FPGA autotuning: [arXiv 2509.19537](https://arxiv.org/abs/2509.19537)
- Moon et al. 2020: [PMC7438325](https://pmc.ncbi.nlm.nih.gov/articles/PMC7438325/)

**Qiskit**
- Aer depolarising channel: [docs](https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.noise.depolarizing_error.html)
- IBM R2P course, Units 0–4: this folder
