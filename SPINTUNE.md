# SpinTune: fleet-learned auto-tuning for silicon spin qubits

Equal1 × Fsas "Compute the Future": pitch Tue 27 Oct, demo Fri 27 Nov. Solo/duo, laptops only. Facts checked 2026-10-25. Anything not confirmed is marked **unverified**.

## Pitch (one line)
> "Equal1 makes qubits like chips, so every chip needs tuning. We learn a **prior from a fleet of 10⁴ simulated FD-SOI devices** so each new chip reaches its target charge state in *fewer measurements* than a cold start, and we ship it as an open benchmark harness that any tuner, Boulder Opal included, can be scored on."

**Why they care:**
- Equal1 partnered with Q-CTRL on exactly this pain point (autonomous calibration), so they've shown it matters.
- CMOS manufacturing means device-to-device variability, so it makes sense to learn across a fleet.
- It runs on-prem and offline, so calibration data never leaves the site. That's the sovereign angle for Fsas.

---

## Verified facts (use ONLY these on slides)
- **Bell-1:** 6 qubits, 0.3 K, self-contained cryocooler, 1600 W, ~200 kg ([TQI, Mar 2025](https://thequantuminsider.com/2025/03/17/equal1-introduces-bell-1-a-rack-mountable-quantum-system-for-hpc-environments/)).
- **Fidelities:** 99.4% 1Q (84 ns) and 98.4% 2Q (72 ns) ([TQI, Dec 2024](https://thequantuminsider.com/2024/12/03/equal1-demonstrates-advances-in-silicon-based-quantum-computing/)).
- **Process:** GlobalFoundries **22FDX FD-SOI**. 29 NMOS/PMOS cells, each a **linear array of ≤ 3 tunnel-coupled dots** plus charge sensors. Tested from 70 mK to 1.2 K ([TQI, Apr 2025](https://thequantuminsider.com/2025/04/17/equal1-announces-successful-validation-of-cmos-process/)).
- **Q-CTRL:** Equal1 integrated Q-CTRL's Boulder Opal Scale Up for autonomous calibration and drift correction, and it runs offline ([QCR, Apr 2026](https://quantumcomputingreport.com/equal1-and-q-ctrl-integrate-autonomous-calibration-for-silicon-quantum-systems/)).
- **QArray** ([paper](https://arxiv.org/html/2404.04994v1), v1.6 installed):
  - It's a constant-capacitance model, with **no tunnel coupling and no spin physics**.
  - It has a temperature `T` for thermal broadening.
  - It ships `WhiteNoise`, `TelegraphNoise`, `LatchingModel` and `PSBLatching`.
  - The paper's "16 dots in < 1 s" figure is a GPU result.
- **Unverified (ask at the pitch):**
  - Electron or hole spins?
  - The per-cell gate stack.
  - The charge-sensing method.
  - Connectivity and mid-circuit measurement.
  - Qiskit or SDK access. Assume Aer until then.

---

## Architecture
1. **HPC: fleet simulator.**
   - QArray generates charge-sensed CSDs for randomised capacitance and lever-arm matrices, with a **back-gate offset as a fleet-level parameter**.
   - It runs at **T = 0.3 K** (kT ≈ 26 µeV, so transitions are blurry), with white, telegraph and latching noise.
   - Out: `float32[N,100,100]` CSDs plus labels `int8[N]` (no-dot / single / double / bad).
2. **AI: fleet-prior tuner (the MVP).**
   - A small CNN classifies the charge state and outputs `float[4]`.
   - A BoTorch BO proposes the next `float[n_gates]`.
   - **Novelty:** the BO prior (mean and lengthscales over gate space) is fitted across the fleet, and every new device is warm-started from it.
   - The gates are parameterised per Equal1 cell (plungers, barriers, global back gate). They get swapped for the real stack once Equal1 shares it.
3. **Verify, in three honest levels:**
   - **(a) Charge level (MVP).** Did the tuner reach the target charge state? In how many measurements, and with what success rate on held-out devices? ⚠ Never feed hand-typed T1/T2/fidelity numbers into Aer and call it verification. That's circular.
   - **(b) Physics bridge (stretch, labelled model-based).**
     - Exchange: **J = 4Ut_c²/(U² − ε²)**, valid for t_c ≪ |U ± ε| ([QTCAD Eq. 9.7](https://docs.nanoacademic.com/qtcad/theory_spin_fem/exchange/)).
     - Detuning noise enters through ∂J/∂ε = 8Ut_c²ε/(U² − ε²)², which is 0 at ε = 0. That's the symmetric point, which cut charge-noise dephasing by >5× in [Reed et al. PRL 2016](https://arxiv.org/pdf/1508.01223) and up to 6× in GaAs in [Martins et al. PRL 2016](https://ar5iv.arxiv.org/html/1511.07336).
     - Barrier noise enters through ∂J/∂t_c = 8Ut_c/(U² − ε²), which is **not** 0 at ε = 0. Since J ∝ t_c², **σ_J/J = 2σ_tc/t_c**.
     - The CZ phase error is **δφ = π·σ_J/J**. Model it as a quasi-static ZZ error in Aer, and measure it with **`qiskit-experiments` StandardRB + InterleavedRB**.
     - Don't reward "landing at ε = 0". That's a coordinate choice. The real output is the device-specific trade-off over `(ε, t_c, t_gate)`: a larger t_c gives a faster gate, but more barrier sensitivity and more leakage.
     - The assumptions are U, σ_ε, σ_tc and the t_c ∝ exp(α·V_B) map (QArray has no t_c). Sweep them all.
     - This only matters if Equal1's 2Q error is charge-noise limited. Ask them.
   - **(c) Hardware (ask Equal1).** Pauli spin blockade (PSB) readout → spectroscopy → Rabi → Ramsey (T2*) → RB. Promise it only if they give access.
4. **Drift loop.** Every k jobs, re-measure a `float32[32,32]` window.
   - **2D cross-correlation** against the reference window gives the shift vector, with no ML.
   - The CNN only confirms the charge state.
   - Re-tune locally if the shift exceeds the threshold.

---

## Feasibility
- **Qubits:** tuning is pairwise. It's demonstrated on one double dot and run across all 5 pairs of a 6-dot chip in simulation, and the demo **shows** the 6-dot run.
- **Compute (measured with `bench_qarray.py`):** QArray 1.6, Rust backend, 100×100 charge-sensed CSD with noise at T = 0.3 K, **single thread**.
  - Timings: **~76 ms for 2 dots, ~130 ms for 4 dots**. Multi-threaded on a 24-thread laptop: ~18 / ~25 ms.
  - Process scaling is *assumed* linear.

| Job | Core-hours | Laptop (8 cores) | 128-core node |
|---|---|---|---|
| Training set: 200k × 2-dot × 0.08 s | 4.4 | ~33 min | ~2 min |
| Fleet evaluation: 10⁴ devices × 300 measurements × 0.13 s | 108 | ~13.5 h | ~51 min |
| **Benchmark harness: 4 tuners × 3 seeds × fleet evaluation** | **1,300** | **~6.8 days** | **~10 h** |

  The harness is the real HPC load. Every tuner step is a fresh simulation, so it's embarrassingly parallel.

- **MVP by 27 Nov:**
  - The headline plot: **measurements-to-tune on held-out devices, cold-start BO vs fleet-prior warm-start BO**.
  - A heuristic baseline (line scans + edge/Hough detection), with random search as the floor.
  - A CNN trained on QArray plus QFlow.
  - Verification level (a).
- **Stretch:** level (b) RB, a drift-injection demo, real Equal1 CSDs, and a dashboard if there's time.
- **Data:**
  - [QFlow lite (NIST)](https://data.nist.gov/od/id/66492819760D3FF6E05324570681BA721894): 1,001 simulated 100×100 maps ([paper](https://arxiv.org/pdf/1809.10018)).
  - QArray-generated data.
  - ⚠ **Both are simulated.** Mitigate with noise models and domain randomisation until Equal1 shares CSDs.
- **Prior work:** CNN state classification has been done (Kalantre 2019, Zwolak 2020), and so has BO tuning ([Moon et al., Nat. Commun. 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7438325/)). Moon reports ~180× faster than random search and a median < 70 min on *their* device. That's their number, not our target. The fleet prior is what's new.

### Scaling to more qubits (estimates)
- **Joint search dies.** A linear array has ~2N+1 gates, so on a 10-value grid 6 qubits gives 10¹³ points and 50 qubits gives 10¹⁰¹.
- **Pairwise local search is linear.** That's N−1 pairs × ~300 measurements, so ~1,500 measurements at 6 qubits and ~14,700 at 50.
- **The catch is crosstalk.** Tuning pair 3–4 detunes pair 2–3. Scaling is linear **only if virtual-gate compensation works**; otherwise it's iterative. The virtual-gate matrix is ~O(N) (nearest and next-nearest neighbours).
- **Simulate a 3–4 dot window per pair,** so the cost per CSD stays flat (measured above).
- **Level (b) is per-pair RB.** Full-chip Aer simulation is out of reach beyond ~12–15 qubits on a laptop.
- **Where it breaks:**
  - 2D arrays, where windows are bigger and crosstalk is denser.
  - Correlated chip-wide drift.
  - A sim-to-real gap that grows with array size.
- **Pitch line:** "At 6 qubits it's 5 local tuning problems. At 50 it's 49."
- ⚠ The 6 → 17 → 50 qubit roadmap is trade-press only. Say "reported", or leave it out.

---

## 15-min pitch outline
1. **(0:00–1:00) Hook:** "CMOS lets Equal1 make qubits like chips. But every chip still needs tuning, and humans don't scale."
2. **(1:00–2:30) Problem:** device variability. Show a QFlow CSD and cite Moon et al. It's solvable, but per-device.
3. **(2:30–4:00) Insight:** a manufacturer has a *fleet*. Learn the prior across 10⁴ virtual FD-SOI devices, then warm-start each chip. Show the cold vs warm plot.
4. **(4:00–6:30) Architecture:**
   - QArray (T = 0.3 K, back gate, noise) `float32[N,100,100]` → CNN `float[4]` → fleet-prior BO `float[n_gates]`.
   - Stretch: `(ε, t_c)` → J, σ_J from σ_ε **and** σ_tc → RB fidelity.
   - Drift: cross-correlation on `float32[32,32]`.
5. **(6:30–8:00) Compute:** the measured table. "Benchmarking tuners across a fleet is an HPC job."
6. **(8:00–9:30) Why Equal1 and Fsas:** on-prem and offline, so the data never leaves the site. It fits a CMOS fleet and complements Boulder Opal as an open harness.
7. **(9:30–11:00) Honesty slide:**
   - Both data sources are simulated, and sim-to-real is the #1 risk.
   - The model is charge-only, so charge tuning ≠ a working qubit.
   - Fidelity comes from a labelled model.
   - No "quantum advantage" claims, and verified specs only.
8. **(11:00–12:30) Plan:**
   - W1: fleet pipeline.
   - W2: CNN plus baselines.
   - W3: **cold vs warm plot (must be done)**.
   - W4: level (b) RB plus the drift demo. The dashboard only if there's time.
9. **(12:30–13:30) Asks:**
   - From Equal1: ~50 real CSDs, the gate stack, and the carrier type.
   - From Fsas/UPT: cluster hours.
   - SDK/Qiskit access.
10. **(13:30–15:00) Q&A.** Use the table below.

---

## Q&A prep

| They'll say | You say |
|---|---|
| "Q-CTRL already does this for us." | "We're not replacing Boulder Opal. We're an open benchmark harness and fleet dataset that any tuner, Boulder Opal included, can be scored on. The fleet prior is what a CMOS manufacturer needs as volumes grow." |
| "Reaching (1,1) is the easy 20%." | "Correct. We scope the MVP to charge-state bring-up, the step that scales with chip count. The qubit ladder (PSB → Rabi → Ramsey → RB) is level (c) and needs your hardware." |
| "CSDs don't show valley splitting." | "Agreed. It's invisible at charge level, which is a reason for level (c)." Don't bluff. |
| "Your MVP is a double dot." | "Pairwise tuning, shown on one pair and run across all 5 pairs of a 6-dot chip in simulation." Then show it. |
| "Beating random search proves nothing." | "Random is the floor. The real baseline is a heuristic line-scan tuner, and the real comparison is cold vs warm BO." |
| "You have zero real data." | "Correct, that's our #1 risk. We use noise models and domain randomisation, and we're asking you for 50 CSDs." |
| "Why ML for drift?" | "We don't use it. Cross-correlation gives the shift directly, and the CNN only checks the charge state." |
| "Where's the Qiskit?" | "Level (b): `qiskit-experiments` StandardRB + InterleavedRB on CZ, with an Aer noise model from σ_J." |
| "Pairs aren't independent." | "Scaling is linear assuming virtual-gate compensation works. Crosstalk makes it iterative, which is the open problem." |
| "Is it compute-heavy really?" | "A single training run, no. Scoring tuners across a 10⁴ fleet is 1,300 core-h, which takes a week on a laptop or 10 h on a node." |

**Don't say:**
- "Server next to the QPU" (training is offline).
- "Qiskit-native".
- "Plugs into Boulder Opal" (you don't know their API).
- "Protects the qubits".
- Anything about Ethos-U65 running our code (unverified).
- A Digital Annealer angle.
- Your own score, or the other ideas.

## Questions to ask them
1. Electron or hole qubits on Bell-1? What's the gate stack per cell, and is the back gate used for tuning?
2. Is charge sensing done with an SET or gate-based dispersive readout? Could you share ~50 raw CSDs?
3. Is the 2Q error budget charge-noise limited?
4. How long does bring-up take per chip today, and which step dominates?
5. Connectivity, mid-circuit measurement, and SDK/Qiskit access?

## Before you walk in
- [x] QArray timing measured (`bench_qarray.py`). Re-run it if you present from a different machine.
- [ ] Slides use only the verified numbers above, with no Gemini-sourced figures.
- [ ] Architecture slide rebuilt: fleet prior → warm-start BO, back gate, T = 0.3 K, two noise channels.
- [ ] Q&A table rehearsed out loud.
