# SpinTune — Design Proposition

**Fleet-learned, fidelity-aware auto-tuning for silicon spin-qubit devices**

| | |
|---|---|
| **Event** | Timișoara HPC Hackathon (InnoWeek 2026) — ideas round 27 Oct 2026, final 27 Nov 2026 at Qiskit Fall Fest |
| **Organisers / judges** | Equal1 (silicon spin-qubit quantum servers), Fsas Technologies |
| **Brief** | "Anything that connects HPC, AI and quantum" |
| **Status** | Design proposition, v1 (25 Oct 2026). No experiment has been run yet. Every target below is a pre-registered hypothesis, not a result. |

---

## 1. The proposition in one paragraph

Silicon spin qubits are made in CMOS fabs, so every chip comes out slightly different. Before a chip can run a single gate, its gate voltages must be tuned until the electrons sit where they should, and then tuned again whenever charge noise makes the device drift. Today this costs hours to days of fridge time per device and is usually done one device at a time, as if nothing had been learned from the previous chip. **SpinTune is an open tuning harness that learns from a simulated fleet of 10⁴ Equal1-style devices to (1) reach the target charge configuration with far fewer measurements than tuning each device from scratch, (2) pick the operating point inside that configuration that maximises predicted two-qubit fidelity under a realistic charge-noise model, and (3) recover from drift with a small local re-tune instead of a full restart.** Every claim is measured against simulator ground truth on held-out virtual devices, with success thresholds fixed before the test runs.

---

## 2. The problem

### 2.1 Why tuning is the bottleneck

- **Tuning cost is dominated by measurement time, not compute.** A fully autonomous pipeline reached Rabi oscillations in 10 of 13 runs, at a mean of 38 h per successful run, mostly spent on slow DC measurements (Schuff et al., 2024). An FPGA-accelerated autotuner sped up stability-diagram acquisition 9.8× but total initialisation only 2.2×, because orchestration became the limit (arXiv 2509.19537).
- **Device-to-device variability grows with manufacturing volume.** CMOS fabrication makes large numbers of nominally identical but individually different devices. The field's own data-needs report calls cross-device transfer "an aspiration that needs validation" and notes there is **no standard success metric** for tuning, so published success rates are not comparable (arXiv 2312.14322).
- **Charge noise moves the device after it is tuned.** Two-level fluctuators (TLFs) switch randomly, shifting the device's charge-stability diagram (CSD). In a 2026 Si/SiGe array study, the noise was correlated between neighbouring qubits and changed between cooldowns (arXiv 2603.03051). Equal1's own device paper names 1/f charge noise as the dominant decoherence source (arXiv 2412.01920).
- **Tuning usually stops at the charge state.** Existing ML tuners aim for "the device is in the right charge configuration". Where *inside* that configuration to operate — which sets how strongly charge noise couples into the qubit — is typically left to a human or a fixed rule.

### 2.2 Why this matters to Equal1 specifically

- Equal1 builds 6-qubit silicon spin-qubit servers (Bell-1; RacQ announced May 2026) on a CMOS process (GlobalFoundries 22FDX validation, 2025).
- In April 2026 Equal1 partnered with Q-CTRL for autonomous tune-up and drift management. That confirms the pain point is real and commercially important.
- Equal1's peer-reviewed two-qubit device reports SPAM-corrected Bell-state fidelity 0.989 at 300 mK and 0.985 at 740 mK, with charge noise as the dominant decoherence source (arXiv 2412.01920). Vendor-reported gate fidelities are 99.4% (1Q) and 98.4% (2Q).

### 2.3 Positioning against Q-CTRL

SpinTune is **not** a replacement for Q-CTRL's Boulder Opal. It is an **open, reproducible fleet benchmark and warm-start layer**: a way to test any tuner across thousands of statistically realistic virtual devices, and a fleet-learned prior that any tuner (including a commercial one) could start from. We make no claim about Q-CTRL's performance, which is not public.

---

## 3. What SpinTune contributes

| # | Contribution | What is new | What already exists (we do not claim it) |
|---|---|---|---|
| C1 | **Fleet-learned warm start** | An amortised estimator trained across 10⁴ simulated devices that turns a few cheap probe measurements into a prior for the tuner, tested on held-out and out-of-distribution device populations | CNN classification of CSDs (Moon et al. 2020; MAViS 2024); Bayesian-optimisation tuning; adaptive measurement (Lennon et al. 2019) |
| C2 | **Fidelity-aware operating point** | After reaching the target charge state, the tuner chooses the detuning and barrier setting that maximise *predicted Bell fidelity* under a calibrated charge-noise model, and verifies it in Qiskit Aer | Symmetric (sweet-spot) exchange operation as a physics principle (Martins et al. 2016; Reed et al. 2016) |
| C3 | **Physics-driven drift loop** | Drift generated by a TLF ensemble, detected from a small 32×32 window, recovered by a local re-tune | Telegraph-noise and latching models in qarray |
| C4 | **Open fleet benchmark** | A reproducible harness: device generator, fixed train/test/OOD fleets, a stated success definition, measurement accounting, and baseline tuners | Individual simulators (qarray, QFlow, QDFlow) |

**Elevator pitch:** *"Every new silicon chip is tuned as if it were the first. SpinTune learns from ten thousand virtual chips, tunes a new one in a fraction of the measurements, then puts it where charge noise hurts least — and proves it with a Bell state in Qiskit."*

---

## 4. Scope

### 4.1 In scope

- **Primary device:** a charge-sensed double quantum dot (2 plungers, 1 inter-dot barrier, 1 sensor), Equal1-style parameters.
- **Stretch device:** a 6-dot linear array (3 pairs), tuned pair by pair with cross-talk.
- **Tuning stage covered:** charge tuning (from random plunger voltages to the (1,1) charge configuration with a safety margin), operating-point selection, and drift recovery.
- **Verification:** a 2-qubit Bell circuit (and optionally 1Q/2Q randomised benchmarking) in Qiskit Aer, with noise derived from the device's tuned operating point.

### 4.2 Out of scope (stated up front)

- **Dot formation and barrier pinch-off.** qarray uses a constant-capacitance model, valid for weak tunnelling, and does not model dot formation, barrier gates or tunnel coupling (qarray paper, arXiv 2404.04994). We start from devices whose dots are already formed. QFlow lite, a Thomas–Fermi simulator that *does* model dot formation, is used only as an out-of-distribution test of the classifier, not as a full coarse-tuning stage.
- **Spin physics inside the CSD simulator.** Exchange, valley splitting and spin readout are not in qarray. The fidelity model in §6 adds them as an explicit, documented layer on top.
- **Any quantum-advantage claim.** The quantum content is the device physics and the verification circuit, not a quantum speed-up.
- **Real hardware**, unless the organisers provide CSDs or device access. If they do, real CSDs are used as a sim-to-real test (§8.4).

---

## 5. System architecture

```text
┌──────────────────────────────────────────────────────────────┐
│ 1. FLEET GENERATOR (HPC, embarrassingly parallel)            │
│   device ~ p(θ): Cdd, Cgd, Cds, Cgs, offsets, T, noise, J-model│
│   qarray ChargeSensedDotArray → CSDs, ground-truth charges   │
│   TLF ensemble → time-correlated gate-voltage noise          │
└───────────────┬──────────────────────────────────────────────┘
                │ train fleet / val fleet / test fleet / OOD fleets
                ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. AI LAYER                                                  │
│   a) State classifier: CNN ensemble on CSD windows,          │
│      calibrated, can abstain                                 │
│   b) Fleet prior: amortised estimator  probes → p(θ | probes)│
│   c) Tuner: Bayesian optimisation seeded by the fleet prior  │
│   d) Operating-point optimiser: maximises predicted fidelity │
└───────────────┬──────────────────────────────────────────────┘
                │ tuned voltages V*, estimated device params θ̂
                ▼
┌──────────────────────────────────────────────────────────────┐
│ 3. QUANTUM VERIFICATION (Qiskit Aer)                         │
│   θ̂, V*, noise model → exchange J, δJ, dephasing             │
│   Monte Carlo over quasi-static noise → Bell circuit         │
│   → Bell fidelity (and optional RB)                          │
└───────────────┬──────────────────────────────────────────────┘
                ▼
┌──────────────────────────────────────────────────────────────┐
│ 4. DRIFT LOOP                                                │
│   every k jobs: 32×32 window → shift score                   │
│   score > threshold → local re-tune from current V*          │
└──────────────────────────────────────────────────────────────┘
```

**Architectural rule:** the tuner never sees ground truth. It only "measures" through a metered measurement interface that counts every sensor pixel it reads. Ground truth is used only by the evaluator.

### 5.1 Main data types

| Object | Type / shape | Notes |
|---|---|---|
| Device parameters θ | dataclass | Capacitance matrices, offset charges, temperature, noise parameters, J-model parameters, ∂f/∂ε |
| CSD window | `float32[H, W]` | 100×100 full scan, 32×32 drift window, or 1-D rays |
| Ground-truth charge map | `int8[H, W, n_dots]` | Evaluator only |
| Classifier output | `float32[K]` + abstain flag | K classes, see §7.1 |
| Gate voltages | `float64[n_gates]` | 3 gates for a double dot, plus sensor |
| Measurement ledger | `int64` | Pixels read; converted to fridge time at a stated integration time |
| Tuning result | record | V*, success flag, pixels used, wall time, θ̂ |
| Verification result | record | Bell fidelity mean and CI, J, δJ, per-qubit dephasing |

---

## 6. Physics model

This section separates what comes from qarray, what comes from the literature, and what is an assumption. Judges from a spin-qubit company will probe exactly this, so every assumption is visible and swept.

### 6.1 Charge-stability diagrams — from qarray

- `ChargeSensedDotArray(Cdd, Cgd, Cds, Cgs, coulomb_peak_width, T)` produces sensor-signal CSDs and ground-state charge configurations.
- Noise on the sensor: `WhiteNoise` + `TelegraphNoise(p01, p10, amplitude)`. Latching: `LatchingModel`, and `PSBLatchingModel` for the (1,1)→(0,2) Pauli-spin-blockade signature.
- Speed: under 1 s for a 100×100 CSD of a 16-dot array; about 0.1 s for an open 4-dot example on CPU; smaller arrays take milliseconds (arXiv 2404.04994).
- Known limitation: constant couplings, so no curvature of transition lines. This is the main known gap to real data.

### 6.2 Fleet variability — our generator

Each virtual device draws θ from a fleet distribution:

| Parameter | Source of variation | Default spread (assumption, swept) |
|---|---|---|
| Gate-to-dot lever arms (Cgd diagonal) | fabrication | ±15% |
| Cross-capacitance (Cgd off-diagonal) | geometry | 0.1–0.4 of the diagonal |
| Dot-to-dot coupling (Cdd) | geometry | ±20% |
| Sensor couplings (Cds, Cgs) | geometry | ±20% |
| Offset charges | trapped charge | uniform over one charge period |
| Temperature T | operating point | 0.3 K (train); 0.74 K (OOD), matching Equal1's two reported temperatures |
| Sensor noise amplitude | readout chain | ×1 (train); ×3 (OOD) |

### 6.3 Charge noise — TLF ensemble

- Each device carries an ensemble of TLFs placed at random in the plane, at a density of about 3×10¹⁰ cm⁻² (arXiv 2603.03051).
- Each TLF switches with a random rate drawn log-uniformly over several decades, giving a 1/f-like total spectrum. Each couples to each gate-referred dot potential with a strength that falls off with distance.
- **Calibration targets** (gate G1 in §8):
  - spectrum close to 1/f over the measured band;
  - neighbouring-dot noise correlation of about 0.4 at 0.2 Hz, with a correlation length of about 81 nm at a 108 nm pitch (arXiv 2603.03051);
  - absolute amplitude in the range typically reported for Si/SiGe at 1 Hz (to verify against the literature in week 1).
- The same ensemble produces (a) slow drift of the CSD for the drift loop, and (b) quasi-static voltage noise δV on each gate for the fidelity model.

### 6.4 From operating point to fidelity — the layer on top of qarray

Exchange coupling between the two electrons in (1,1) uses the standard Hubbard form:

$$J(\varepsilon, V_B) = \frac{2\,t_c(V_B)^2\,U}{U^2 - \varepsilon^2}, \qquad t_c(V_B) = t_0\, e^{\kappa V_B}$$

- **ε (detuning)** is measured from the centre of the (1,1) cell along the detuning axis. **U** is the detuning distance to the (0,2)/(2,0) transitions. **Both are read directly from the device's qarray geometry.** This is the honest link between the CSD and the qubit.
- **t₀ and κ** (barrier control of tunnel coupling) are **not** in qarray. They are fleet parameters with stated ranges, chosen so that J reaches the MHz range needed for a CZ gate of about 100 ns. Equal1 reports a 72 ns 2Q gate, a vendor claim. These parameters are swept in every result.
- **Noise propagation:**

$$\delta J = \frac{\partial J}{\partial \varepsilon}\,\delta\varepsilon + \frac{\partial J}{\partial V_B}\,\delta V_B$$

  δε and δV_B come from the TLF ensemble through the lever arms. At ε = 0, ∂J/∂ε = 0 — the symmetric operating point (Martins et al. 2016; Reed et al. 2016).
- **CZ gate:** the hold time is set so the nominal conditional phase is π. Quasi-static noise gives a phase error δφ = π·δJ/J.
- **Single-qubit dephasing:** qubit frequencies shift as δf = (∂f/∂ε)·δε. Here ∂f/∂ε is a device parameter (micromagnet-type sensitivity), drawn from a stated range and swept.
- **Floor:** all remaining gate errors are a depolarising floor set to Equal1's reported 99.4% / 98.4%. That puts the simulated device in a realistic fidelity regime.

**Why the optimum is not trivial.** Moving towards a charge transition (larger |ε|) or opening the barrier raises J, so the gate is faster and less exposed to dephasing. But it also raises ∂J/∂ε and ∂J/∂V_B, so the gate is more sensitive to charge noise. The best point depends on the device's U, lever arms, noise amplitude and noise correlations. The tuner has to estimate those from limited measurements.

### 6.5 Verification in Qiskit Aer

1. Sample N quasi-static noise realisations (default N = 1,000) from the device's TLF ensemble.
2. For each, build a Bell circuit (H, then CZ realised as CPhase(π + δφ), then H), with single-qubit phase errors from δf and a depolarising floor.
3. Simulate with Aer density-matrix or statevector.
4. Report the mean Bell-state fidelity with a 95% bootstrap CI.

Optional: 1Q/2Q randomised benchmarking, using the same per-realisation errors.

---

## 7. AI components

### 7.1 State classifier

- **Input:** CSD windows of 32×32 or 64×64 pixels (and 100×100 for baselines).
- **Classes (from qarray ground truth):** (0,0), (1,0), (0,1), **(1,1) target**, higher occupancy, and **unusable** (latching or noise-dominated).
- **Model:** a small CNN ensemble (5 members) for uncertainty. It **abstains** when ensemble disagreement exceeds a threshold tuned on the validation fleet.
- **Calibration:** temperature scaling on the validation fleet. Expected calibration error (ECE) is reported.

### 7.2 Fleet prior (contribution C1)

- **Probes:** a fixed, cheap measurement — for example two 16×16 coarse windows plus 4 one-dimensional rays, about 500 pixels.
- **Amortised estimator:** a small network trained on the train fleet that maps probes to a posterior over the device's key parameters: lever arms, cross-capacitance, offset charges, and therefore the location and shape of the (1,1) cell.
- **Use:** the posterior sets the starting point, search box and kernel hyperparameters of the Bayesian-optimisation tuner. Without the prior, the tuner starts cold.

### 7.3 Tuner

- Bayesian optimisation (BoTorch or scikit-optimize) over plunger voltages.
- Objective: classifier probability of (1,1) times a margin term (distance to the nearest transition, from the classifier's segmentation).
- Each proposal triggers a small window measurement. Every pixel is billed to the ledger.
- Stops when the classifier confirms (1,1) with margin, or when the budget runs out.

### 7.4 Operating-point optimiser (contribution C2)

- Within the confirmed (1,1) cell, it estimates U, lever arms and local noise amplitude from a short noise-trace measurement (also billed), then maximises predicted Bell fidelity over (ε, V_B) using the §6.4 model.
- This is compared with an **oracle** that knows the true θ, which gives the upper bound.

### 7.5 Drift detector (contribution C3)

- Every k simulated jobs, read a 32×32 window around V*.
- **Shift score:** the classifier's change in state probabilities plus image cross-correlation offset against the reference window.
- If the score passes a threshold, run a local re-tune: BO in a small box around V*, seeded with the last estimate.

---

## 8. How success is measured

### 8.1 Definitions (fixed before any test run)

- **Tuning success:** the final voltage point V* lies in the ground-truth (1,1) region of the *noiseless* simulator, at least m_min away from the nearest charge transition. m_min is set to 3× the RMS gate-voltage noise of that device.
- **Measurement cost:** the number of sensor pixels read, including probes and noise traces. It is also reported in fridge time, at a stated integration time per pixel (e.g. 10 µs RF reflectometry and 1 ms DC, both shown).
- **Budget:** a hard cap of B = 20,000 pixels per device (two full 100×100 scans). Every tuner is compared at the same cap and along a full success-versus-budget curve.
- **Fleets:**

| Fleet | Size | Purpose |
|---|---|---|
| Train | 10,000 devices | Fit the classifier and the fleet prior |
| Validation | 1,000 devices | Thresholds, hyperparameters, calibration |
| Test (in-distribution) | 1,000 devices | The headline result. Touched once. |
| OOD-hot | 1,000 devices | 0.74 K instead of 0.3 K (Equal1's two reported temperatures) |
| OOD-noisy | 1,000 devices | 3× sensor noise and 3× TLF density |
| OOD-crosstalk | 1,000 devices | Cross-capacitance ×1.5 beyond the training range |
| QFlow lite | 1,001 maps | Classifier domain-shift test only |

- **Pre-registration:** thresholds, fleet seeds and baselines are committed to the repository (tagged commit) *before* the test fleet is generated. Results are reported against that commit.

### 8.2 Baselines

| ID | Tuner | Why it is there |
|---|---|---|
| T0 | Random search with the same classifier | Floor; the comparison Moon et al. report their ~180× against |
| T1 | Full-scan navigation: repeated 100×100 scans plus classifier plus a rule-based step | Represents the common "scan everything" practice |
| T2 | Cold Bayesian optimisation (identical to SpinTune, without the fleet prior) | **The baseline that isolates contribution C1** |
| T3 | SpinTune (fleet prior + BO) | Proposed |

| ID | Operating point | Why it is there |
|---|---|---|
| O0 | Geometric centre of the (1,1) cell, default barrier | Common manual rule |
| O1 | Symmetric point ε = 0, barrier set for a fixed target J | Physics-informed rule |
| O2 | SpinTune fidelity-aware point (estimated θ̂) | Proposed |
| O* | Oracle point (true θ) | Upper bound |

### 8.3 Success gates

Each gate is pass/fail on its own. Gates 1–3 give a defensible project even if 4 and 5 fail.

| Gate | Question | Metric | Pass criterion (pre-registered) |
|---|---|---|---|
| **G1 Calibrate** | Is the virtual fleet realistic? | TLF spectrum slope; neighbour correlation; sensor SNR | Spectral slope within 1/f ± 0.3 over the band; correlation 0.4 ± 0.1 at the stated geometry |
| **G2 Classify** | Can we read the device? | Accuracy, macro-F1, ECE on test; the same on OOD fleets and QFlow lite | ≥ 95% accuracy and ECE ≤ 0.05 in-distribution; OOD drop reported, never hidden |
| **G3 Tune (C1)** | Does the fleet prior save measurements? | Success rate at B; median and 90th-percentile pixels to success; area under the success-vs-budget curve | T3 ≥ 90% success at B **and** median pixels ≤ 0.5× T2 (a ≥2× saving); T3 ≥ 75% success on each OOD fleet |
| **G4 Operate (C2)** | Does fidelity-aware tuning help? | Mean Aer Bell fidelity at the tuned point; fraction of the O0→O* gap closed | O2 beats O0 and O1 with a paired-bootstrap 95% CI excluding zero, **and** closes ≥ 50% of the O0→O* gap |
| **G5 Drift (C3)** | Can we recover cheaply? | Detection precision and recall on injected TLF events; pixels to recover | Recall ≥ 90% at ≤ 5% false alarms; local re-tune uses ≤ 25% of from-scratch pixels at equal success |

**Statistics:**
- Every tuner and operating point runs on the same devices (paired design).
- 95% CIs come from bootstrap over devices; 5 seeds for stochastic tuners.
- Distributions are reported (median, p90, failures), not only means.
- Failures are logged and shown in the final presentation.

### 8.4 If real data becomes available

If Equal1 or the organisers provide real CSDs, they become a frozen sim-to-real test:
- classifier accuracy on expert-labelled real windows;
- the T3-versus-T2 pixel ratio on replayed real scans.

No gate depends on this.

### 8.5 What counts as a negative result

- **G3 fails:** the fleet prior does not beat cold BO. That is a useful finding about cross-device transfer, and we report it.
- **G4 fails:** the symmetric-point rule is already near-optimal under realistic noise. That is also a finding, and it tells hardware teams that rule O1 is enough.
- In both cases the open fleet benchmark (C4) still stands as a deliverable.

---

## 9. Where HPC, AI and quantum each do real work

| Pillar | Real job | How we show it |
|---|---|---|
| **HPC** | Generating 10⁴+ device fleets, Monte Carlo noise ensembles, and evaluating 4 tuners × 4 operating rules × 5 fleets × 5 seeds × 1,000 devices | A strong-scaling plot of devices evaluated per hour against cores, from a laptop to a cluster node |
| **AI** | Calibrated CSD classifier, amortised fleet prior, Bayesian-optimisation tuner, drift detector | Gates G2, G3, G5 |
| **Quantum** | The device physics (exchange, charge-noise dephasing) and Bell-state verification in Qiskit Aer, in Equal1's own fidelity regime | Gate G4 and a fidelity-versus-operating-point map per device |

**HPC budget (upper bound, assuming 1 s per CSD; double dots are much faster):**

| Job | Count | Core-hours | Laptop (8 cores) | 128-core node |
|---|---|---|---|---|
| Classifier training set | 200k windows | 56 | ~7 h | ~26 min |
| Tuner evaluation | 1,000 devices × 300 measurements | 83 | ~10 h | ~39 min |
| Full evaluation matrix | ×(4 tuners × 5 fleets × 5 seeds) | ~8,300 | impractical | ~65 h, or minutes on many nodes |

The first two rows are the partner's original estimates. Real timings are measured on day 1, and the double-dot case is expected to be far below 1 s per CSD.

---

## 10. Demo for the final (27 Nov)

1. **"Cold chip":** a new virtual device from the held-out fleet, shown as a blank CSD.
2. **Race:** cold BO (T2) and SpinTune (T3) tune side by side. Measured pixels light up live, and a counter shows fridge time.
3. **"Where to stand":** a heat map of predicted Bell fidelity across the (1,1) cell, with the O0, O1, O2 and oracle points marked.
4. **Qiskit moment:** run the Bell circuit in Aer at O0 and at O2 and show both fidelities with CIs.
5. **Drift:** inject a TLF switch, watch the CSD shift, see detection and a small local re-tune.
6. **Results slide:** gates G1–G5, pass or fail, including any failures.

---

## 11. Risks and mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| "Q-CTRL already does this for Equal1" | High | Position as an open benchmark and warm-start layer. Lead with C1 and C2, not the CNN. |
| Sim-to-real gap (qarray has straight transition lines and no barrier physics) | High | State it up front; OOD fleets; QFlow lite domain-shift test; real CSDs if offered |
| The fidelity layer's t₀, κ and ∂f/∂ε are assumptions | High | Sweep them; report results as maps over assumptions; separate qarray-derived quantities (U, ε, lever arms) from assumed ones |
| The fleet prior gives little gain because devices are too similar | Medium | Fleet spread is a swept variable; show the gain versus spread. Too-similar fleets are a finding, not a failure. |
| G4 is trivially won by the symmetric rule | Medium | O1 is an explicit baseline; G4 requires beating O1 too, and closing the oracle gap |
| Judges call the quantum part "light" | Medium | G4 makes quantum the objective of tuning, not an add-on. Optional November module: a stabiliser/decoder study using the same noise model (Stim). |
| qarray installation or API problems | Low | Day-1 smoke test; pin versions; fallback to a minimal constant-interaction implementation for double dots |
| Equal1 hardware access is not offered | Low | Nothing depends on it; ask the organisers anyway |

---

## 12. Prepared answers to likely judge questions

- **"Q-CTRL already does this. Why you?"** — We don't replace a commercial tuner. We provide the open fleet benchmark that lets anyone measure tuners on thousands of statistically realistic devices, and a fleet-learned prior that any tuner can start from. Our second contribution, fidelity-aware operating points, is about *where* to operate, not just reaching the charge state.
- **"Your simulator isn't real."** — Correct, and we say so. qarray is a constant-capacitance model. We calibrate the noise to published 2026 measurements (gate G1), test on shifted populations and on a different simulator (QFlow lite), and every assumed parameter is swept.
- **"Where is the quantum?"** — The tuning objective is a quantum quantity: Bell fidelity under charge noise, evaluated in Qiskit Aer in Equal1's reported fidelity regime. The physics of exchange and charge noise is the core of the second contribution.
- **"Why HPC for 6 qubits?"** — The device is small; the population is not. Statistically valid claims need thousands of devices × seeds × fleets × tuners. We show a scaling plot.
- **"What if the prior doesn't help?"** — Then we have shown, on a public benchmark, how much cross-device transfer is worth at a given fabrication spread. That is the open question the field's own data paper names.

---

## 13. Plan

### 13.1 Before the ideas pitch (Sun 25 – Tue 27 Oct, 13:00)

| When | Goal | Exit condition |
|---|---|---|
| **Sun afternoon** | Install qarray; build a double-dot fleet generator; time CSD generation; render 20 example CSDs from different devices | Measured seconds per CSD; a slide showing fleet variability |
| **Sun evening** | Random-search baseline using a ground-truth oracle classifier (skip the CNN for now) | First success-versus-pixels curve on 100 devices |
| **Mon** | Cold BO versus random on the same 100 devices; Bell circuit in Aer at two operating points using the §6.4 model | Two plots: tuning cost curve and fidelity-versus-ε |
| **Tue morning** | 15-minute pitch | Problem, contributions C1–C3, success gates, early plots, November plan |

The pitch shows the gates and early plots, not claimed results. A CNN and the fleet prior are not needed for Tuesday.

### 13.2 November roadmap

| Dates | Milestone | Gates |
|---|---|---|
| 28 Oct – 3 Nov | TLF ensemble and calibration; fleet generator with OOD fleets; pre-registration commit | G1 |
| 4 – 10 Nov | CNN ensemble with calibration and abstention; measurement ledger | G2 |
| 11 – 17 Nov | Fleet prior and BO tuner; full T0–T3 comparison | G3 |
| 18 – 22 Nov | Fidelity-aware operating point; Aer verification; drift loop | G4, G5 |
| 23 – 25 Nov | HPC scaling runs; full evaluation matrix; stretch: 6-dot array | — |
| 26 Nov | Demo polish and dry run | — |
| 27 Nov | Final at Qiskit Fall Fest | — |

### 13.3 Suggested repository layout

```text
spintune/
├── fleet/            # device sampler, qarray wrapper, TLF ensemble
├── measure/          # metered measurement interface and ledger
├── models/           # CNN ensemble, calibration, fleet-prior estimator
├── tuners/           # random, full-scan, cold BO, SpinTune
├── operate/          # J-model, operating-point optimiser, oracle
├── verify/           # Qiskit Aer Bell circuit and RB, Monte Carlo
├── drift/            # drift injection, detector, local re-tune
├── eval/             # gates G1–G5, statistics, plots
├── configs/          # fleet definitions, pre-registered thresholds
└── hpc/              # Slurm / multiprocessing launchers, scaling runs
```

---

## 14. Open questions for the organisers

1. Is Equal1 hardware (Bell-1 or RacQ) reachable during the hackathon, and through which software stack? No public evidence of Qiskit support was found.
2. Could Equal1 share any anonymised real charge-stability diagrams, even a few dozen, as a test set?
3. How does the judging rubric weight the quantum component against scientific rigour?
4. What HPC resources (node type, core-hours) will finalists get?

---

## 15. References

**Simulators and data**
- QArray: GPU-accelerated constant-capacitance simulator — [arXiv 2404.04994](https://arxiv.org/abs/2404.04994) · [docs](https://qarray.readthedocs.io/en/latest/introduction.html) · [noise and latching models](https://qarray.readthedocs.io/en/latest/advanced_functionality.html)
- QFlow lite dataset (NIST) — [data.nist.gov](https://data.nist.gov/od/id/66492819760D3FF6E05324570681BA721894) · [paper](https://arxiv.org/abs/1809.10018)
- QDFlow simulator — [arXiv 2509.13298](https://arxiv.org/abs/2509.13298)

**Auto-tuning**
- Moon et al., ML tuning faster than human experts, Nat. Commun. 2020 — [PMC7438325](https://pmc.ncbi.nlm.nih.gov/articles/PMC7438325/)
- Lennon et al., Efficiently measuring a quantum device using machine learning, npj QI 2019 — [arXiv 1810.10042](https://arxiv.org/abs/1810.10042)
- Schuff et al., fully autonomous tuning to Rabi oscillations, 2024 — [PDF](https://zumbuhllab.unibas.ch/fileadmin/user_upload/zumbuhllab/Publications/2024/SchuffCarballido_2402.03931.pdf)
- MAViS, virtualisation of a 10-dot array — [arXiv 2411.12516](https://arxiv.org/abs/2411.12516)
- FPGA-accelerated autotuning — [arXiv 2509.19537](https://arxiv.org/abs/2509.19537)
- Data needs and challenges of quantum-dot automation — [arXiv 2312.14322](https://arxiv.org/abs/2312.14322)

**Spin-qubit physics and noise**
- Equal1 Si/SiGe two-qubit processor (Bell fidelity, charge noise) — [arXiv 2412.01920](https://arxiv.org/abs/2412.01920)
- Correlated charge noise in a Si/SiGe array and QEC impact — [arXiv 2603.03051](https://arxiv.org/abs/2603.03051)
- Localising dominant TLFs from cross-spectra — [arXiv 2505.05875](https://arxiv.org/abs/2505.05875)
- Martins et al., noise suppression using symmetric exchange gates, PRL 116, 116801 (2016)
- Reed et al., reduced sensitivity to charge noise via symmetric operation, PRL 116, 110402 (2016)

**Industry context**
- Equal1 × Q-CTRL autonomous calibration — [Quantum Computing Report](https://quantumcomputingreport.com/equal1-and-q-ctrl-integrate-autonomous-calibration-for-silicon-quantum-systems/)
- Equal1 Bell-1 launch — [Equal1](https://www.equal1.com/insights/equal1-launches-bell-1-the-first-quantum-system-purpose-built-for-the-hpc-era)

---

*Evidence status: design document only. The physics layer in §6.4 adds documented assumptions on top of qarray. All gate thresholds are pre-registration proposals and should be reviewed by the team before the test fleet is generated.*
