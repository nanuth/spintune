[SpinTune v5 design](README.md) › 18. Scaling

# 18. Scaling: more cells, more dots

Added 26 Oct 2026, after v5. It answers "does this scale to more qubits?". Qubits can be added in two ways, and the design treats them differently:
- **More cells:** more cells per chip, more chips, more wafers. This is how Equal1 scales (29–35 cells per chip, [§3.2](03-scope-and-device-template.md#32-what-a-chip-means-here)), and it is what the design is built for.
- **More dots per cell,** tuned as one coupled array. This is out of scope: Equal1's published cells have at most 3 dots, and the 6-dot run is a stretch goal that depends on Equal1 confirming a layout ([§3.4](03-scope-and-device-template.md#34-deferred-and-stretch)).

## 18.1 More cells, chips and wafers

**Cost grows linearly with the number of cells.**
- The unit of tuning is one cell ([§3.2](03-scope-and-device-template.md#32-what-a-chip-means-here)). No tuning run spans two cells.
- Instrument time is ~0.3–0.6 s per cell at RF rates [measured, idealized; [§1.2](01-design-decisions-and-evidence.md#12-evidence-status-25-oct-2026)], so ~10–20 s for a 35-cell chip. Query setup and slews dominate ([§4.2](04-measurement-interface.md#42-cost-model-pixels-are-not-time)), so throughput is set by the number of queries and the command latency, not by pixels.
- **Simulation:** runs are parallelised across wafer × tuner × seed ([§12](12-compute-plan.md)). QArray barely slows from 2 to 4 dots: 9.9 vs 12.4 ms per 32×32 window [measured; [§1.2](01-design-decisions-and-evidence.md#12-evidence-status-25-oct-2026)].

**History gains level off within a few cells.**
- After k earlier cells on a chip, the start-point spread is 22·√(1 + 1/k) mV ([§1.2](01-design-decisions-and-evidence.md#12-evidence-status-25-oct-2026)): 31 mV at k = 1, 25 at k = 3, 23 at k = 9 [computed].
- The cell-level spread σ_cell = 22 mV ([§7.2](07-fleet.md#72-parameters-defaults-and-sweep-ranges)) is a floor. Chip history removes the offsets a cell shares with its die and wafer, not the cell's own.
- So a 29–35-cell chip mostly spreads the cost of its first cells over more cells; it doesn't make later cells cheaper than on a 10-cell fleet chip. The gain as a function of k ([§6.4](06-tuners-and-baselines.md#64-histories-and-tuning-logs)) measures where the curve flattens.

**Trust is the hard part.** Wrong declarations compound over a chip. With a per-declaration rate p and n cells, P(≥ 1 wrong declaration on a chip) = 1 − (1 − p)ⁿ [computed]:

| Cells per chip | Chips with ≥ 1 wrong declaration, at p = 1% | p needed for ≤ 10% of chips | Error-free declarations needed to show that p (one-sided 95%) |
|---|---:|---:|---:|
| 10 (fleet chip) | 9.6% | 1.05% | ~280 |
| 29 (Equal1 paper) | 25% | 0.36% | ~830 |
| 35 (Equal1 website) | 30% | 0.30% | ~1,000 |
| 100 | 63% | 0.105% | ~2,800 |

- **Rule of thumb:** with zero observed errors, the declarations needed grow as ≈ 28 × the cells per chip [computed]. That's cheap in simulation. On hardware it means many independently verified cells ([§14](14-questions-for-equal1.md) Q3–Q4).
- **What the planned fleets can show:**
  - The in-distribution test fleet (~900 declarations, [§11.5](11-success-measurement.md#115-statistics)) bounds p at ≈ 0.33% with zero errors. That keeps ≤ 10% of chips affected at 29 cells (9.2%), but not at 35 (11.0%).
  - The certificate stress set (≥ 3,000 cells, [§7.4](07-fleet.md#74-fleets)) bounds the wrong-anchor rate at 0.1%. That would cover chips of ~100 cells, but for the certificate only, not the whole declaration.
- **The chip-level rate measured on test is for 10-cell chips.** For Equal1's 29–35-cell chips it has to be recomputed from the per-declaration bound, as in the table. It doesn't carry over directly.

**Sequential history limits throughput** (open, not designed).
- Cell k sees only cells 1…k−1, and every tuner uses that order ([§6.4](06-tuners-and-baselines.md#64-histories-and-tuning-logs)). If the instruments can tune several cells at once, a strict order serialises the chip.
- A batched order, where each batch sees all earlier batches, should keep most of the gain, because history levels off after a few cells [inferred]. That is not measured. Whether Equal1 tunes cells in parallel belongs with the [§14](14-questions-for-equal1.md) questions.

## 18.2 More dots per cell

**What carries over:** the per-axis argument of [§5.1](05-reading-the-device.md#51-the-anchor-certificate-design-call). If every dot has a gate next to it and A1–A4 hold, a transition-free stretch ≥ P_max along that gate's axis still shows that dot is empty [inferred]. If dots can be tuned pair by pair, cost per cell grows roughly linearly in the number of dots: one axis ray per dot, plus a confirmation window per pair [inferred].

**What doesn't carry over** with three or more coupled dots:

| What the design relies on | Why it breaks |
|---|---|
| Dot identity from line orientation in one 2D window: dot-A lines steep, dot-B lines shallow ([§5.1](05-reading-the-device.md#51-the-anchor-certificate-design-call) step 4, [§5.2](05-reading-the-device.md#52-confirmation-and-declaration)) | A 2D slice of an N-dot space can show up to N line families, and orientation alone can't name them all. It needs one plane per pair, or virtual gates |
| Each dot unloads within a ray (A3) | The inner dots of a linear array have no reservoir and load only through their neighbours. In a two-dot cell that is a stress scenario ("dot B unloads only via dot A", [§4.3](04-measurement-interface.md#43-simulation-behind-the-interface-design-call)). In a longer array it is the normal case |
| One sensor shows every dot's line (A4) | Dot B's step is already 2–4× smaller than dot A's ([§7.2](07-fleet.md#72-parameters-defaults-and-sweep-ranges)). Dots further from the SEB fail the visibility test, so the tuner abstains. More dots need more sensors |
| Cross-coupling up to x = 0.4 to the next-nearest gate ([§7.2](07-fleet.md#72-parameters-defaults-and-sweep-ranges)) | More dots put more line families across each axis, which shortens the transition-free stretches the rule needs (the reason for the diagonal descent, [§6.1](06-tuners-and-baselines.md#61-the-shared-policy-diagonal-descent-then-axis-rays-design-call)). The descent's required stretch also grows with the number of axes, so more cells hit the domain limit [inferred] |

**Existing plan if Equal1 confirms a multi-dot layout** ([§3.4](03-scope-and-device-template.md#34-deferred-and-stretch)): tune pair by pair with iterative sweeps, at most 5 passes; check convergence with the [§9](09-drift.md) cross-correlation; compare a cold start with a per-position prior on ~20 chips. Nothing beyond that is designed here.

## 18.3 The Qiskit layer

- C2 models one CZ gate on two qubits ([§8](08-physics-layer-cz-error-budget.md)). It says nothing about crosstalk or errors along a chain.
- `LayerFidelity`/EPLG, the natural multi-qubit metric, is installed ([§1.2](01-design-decisions-and-evidence.md#12-evidence-status-25-oct-2026)) and reserved for the multi-cell stretch goal ([§10.3](10-quantum-layer-qiskit.md#103-course-content-deliberately-not-used)).

## 18.4 What we can and can't claim

**Can claim:**
- cost grows linearly with the number of cells;
- the history gain is measured as a function of a cell's position on the chip;
- wrong declarations are bounded per declaration and per chip, and the bound tightens as the test set grows.

**Can't claim:**
- that the method tunes larger coupled arrays;
- that the history gain grows with chip size;
- that the chip-level rate measured on 10-cell fleet chips holds for 29–35-cell chips without recomputing it ([§18.1](#181-more-cells-chips-and-wafers)).

**Pitch answer:** *"It scales the way Equal1 scales: more cells, chips and wafers, with cost linear in cells. What gets harder is trust. At a 1% error rate, a quarter of 29-cell chips have a bad cell, so we measure and bound the rate instead of assuming it. Larger coupled arrays inside one cell are out of scope until you confirm a layout."*

---

← [17. References](17-references.md) · [Index](README.md) · [Appendix A. Interfaces and code layout](appendix-a-interfaces-and-code-layout.md) →
