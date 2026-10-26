[SpinTune v5 design](README.md) › 0. Pitch

# 0. Pitch

> Equal1 builds qubits the way the chip industry builds chips: 29–35 quantum-dot cells per chip, many chips per wafer, one commercial 22 nm FD-SOI process. Every cell has to be tuned to a known electron count before it can hold a qubit, and at that scale nobody watches each cell. An unattended tuner has two jobs: spend little instrument time, and rarely declare a cell ready when it isn't, at a rate that is measured rather than assumed.
>
> **SpinTune tests whether chip history can make charge tuning cheaper without increasing wrong charge declarations.**
> - **An explicit evidence rule.** Before declaring a charge state, a tuner must show an empty region of the device with a few rays and one 2D window. Under a stated device model and sensing assumptions, that evidence implies the electron count ([§5.1](05-reading-the-device.md#51-the-anchor-certificate-design-call)). Outside those assumptions its error rate is measured, not assumed.
> - **History as an input, tested against the obvious alternative.** Earlier cells on the same chip and the logs of earlier chips set where to start and how coarsely to scan. We compare that with the same policy started cold, and with a plain running mean of the chip's earlier results.
>
> We are building a reproducible benchmark with explicit evidence, abstention and measurement accounting on literature-informed simulated fleets, with separate tests on public experimental scans. Any tuner is scored on its declared state, margin, measurement cost, time and wrong-declaration rate. Hardware validation depends on access to suitable device data.

**What we have measured so far** (25 Oct; idealized: noiseless simulated cells, perfect line reader; [§1.2](01-design-decisions-and-evidence.md#12-evidence-status-25-oct-2026)):
- **A simple stopping rule miscounts silently.** In a descent along one gate axis at a time, "no transition for 1.5 typical charge periods means the device is empty" declared an occupied point empty on **8–15% of cells**, all with a charge period ≥ 25 mV. The period-bounded rule of [§5.1](05-reading-the-device.md#51-the-anchor-certificate-design-call) made **0 errors on 300 devices at each of two start spreads** (one-sided 95% upper bound ≈ 1% per spread). That test covers the descent rule with perfect occupancy readout, not the full evidence rule under noise; that is task B1 ([§15.3](15-plan.md#153-tasks-needs--hard-dependencies-done--the-check-that-must-pass)).
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
  - These are estimates for one policy on ideal cells, with history drawn from the assumed fleet structure rather than learned from logs. They are not a floor: another policy could gather the same evidence more cheaply. Noise, latching, reader v1 and simulated training-fleet logs come next (G0, [§11.4](11-success-measurement.md#114-gates-thresholds-frozen-at-the-tagged-commit)).
- **Guessing without measuring rarely works.** Setting a cell to the fleet-average voltage lands in the target charge state only **1–6%** of the time under sourced spreads; the chip's earlier cells raise that to 6–12%. Some measurement is always needed; the question is how little.

## If it works: what changes

1. **Wrong declarations become a measured, bounded number.**
   - Every declaration carries its evidence. The wrong-declaration rate is reported over all declarations, split into wrong counts and inadequate margins, with an upper confidence bound.
   - Scale is why this matters: at a true 1% rate, a 29-cell chip has a 25% chance of at least one wrong declaration. We claim "≤ 1%" only if the upper bound is ≤ 1%.
2. **Bring-up logs become an input with a measured value.** We report when chip and wafer history reduce cost and when they don't, including a no-gain result against a running mean, and a break-even map over how much variation cells on a chip share ([§12](12-compute-plan.md)).
3. **The field gets an executable yardstick.** The community's data and benchmarking review asks for datasets, benchmarks and standardisation ([Zwolak et al., npj Quantum Inf. 10, 105 (2024)](https://doi.org/10.1038/s41534-024-00878-x)). Fixed fleets, metered queries and one scoring contract let Equal1 score any tuner, ours or not, against its own device statistics ([§2.2](02-goals-non-goals-anti-goals.md#22-benchmark-scoring-contract-design-call)).
4. **It runs anywhere**, on a laptop or an on-premises cluster. That's the sovereign, offline angle for Fsas.
5. **A model-based answer to "where should the exchange gate operate, and how much does charge noise matter there?"** A Qiskit model of the CZ gate, built from the device Hamiltonian, composes charge noise, dephasing and pulse error into a two-qubit error budget. It is a sensitivity study, conditional on stated assumptions ([§8](08-physics-layer-cz-error-budget.md)).

**What it does not claim:**
- It covers charge-state tuning of already-formed dots. In our time model that is ~0.3–0.6 s of instrument time per cell at RF rates. The value is trust and automation at scale, not hours saved.
- It does not prove a hardware tuner correct, establish a universal cost floor, or show savings on Equal1 devices.
- It makes no physical gate-fidelity claim, no quantum-advantage claim, and no claim about any commercial tuner.
- The fleet is *modelled on* published 22FDX statistics. The joint structure that creates the history advantage (how much cells on a chip share) is an assumption until Equal1 data say otherwise ([§7.2](07-fleet.md#72-parameters-defaults-and-sweep-ranges)).
- Everything is simulated until real scans are available ([§7.6](07-fleet.md#76-external-real-device-data-sourced-none-is-22fdx)).

**If it doesn't work, we report it straight.** The headline is chosen by a pre-registered rule once headroom is measured on sensor-only query traces (gate G0, [§11.4](11-success-measurement.md#114-gates-thresholds-frozen-at-the-tagged-commit)).
- If little avoidable cost is left, the headline is the benchmark and the measured error/cost trade-off, with the headroom as a finding.
- The Qiskit error budget is a result either way.

---

[Index](README.md) · [1. Design decisions and evidence](01-design-decisions-and-evidence.md) →
