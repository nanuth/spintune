**SpinTune feasibility and measurement review — 25 October 2026**

The charge-tuning benchmark and fleet warm-start experiment are feasible as a focused November project. The complete proposition combines several research problems whose outcomes cannot be promised on this schedule. Success can be measured convincingly in simulation; demonstrating better physical qubits requires additional measurements and hardware evidence.

This review covers `SPINTUNE.md` and `SpinTune_Design_Proposition.md`. The workspace currently contains those two documents, with no implementation, dependency manifest, benchmark script, datasets, or experiment logs. The `python3` interpreter inspected during review cannot import qarray, Qiskit, Aer, PyTorch, BoTorch, or NumPy. That does not establish what might be installed in another environment. No simulator or tuner experiment was run for this review. Arithmetic and model identities below were checked with standard-library Python; external checks use the linked primary sources. **Update:** a follow-up check the same day installed QArray 1.6.0 under Python 3.12 and ran three small simulations. The [addendum](#addendum-measured-checks-with-qarray-25-october-2026) at the end reports them and updates the statements above about installed packages and unrun experiments.

The strongest parts of the proposal are the separation of charge tuning from hardware verification in `SPINTUNE.md`, the metered measurement interface, device-level train/test splits, paired baselines, explicit OOD tests, and willingness to publish negative results. Those are a sound foundation.

**Findings that need resolving before implementation**

1. **High priority: establish what measurements make the target identifiable.** [Design §7.1](/Users/razvanstrugariu/IdeaProjects/hackathon/SpinTune_Design_Proposition.md:191) proposes identifying absolute occupancies such as (1,1) from a local image. Local transition patterns can repeat across charge cells; randomized sensor offsets and couplings further weaken an absolute charge reference. A classifier cannot generally recover electron count from an unreferenced, featureless patch. Specify a measured empty-state reference, transition-counting history, or another calibrated occupancy reference, and include its acquisition cost. If a reference is assumed available, state that prerequisite explicitly. Experimental charge-autotuning work uses an empty-dot boundary to count transitions; that supports this concern rather than proving every local image is ambiguous. [Experimental online charge autotuning](https://pmc.ncbi.nlm.nih.gov/articles/PMC11907638/).

   There is also a task mismatch: [the pitch labels](/Users/razvanstrugariu/IdeaProjects/hackathon/SPINTUNE.md:38) are no-dot/single/double/bad, whereas the design labels are electron occupancies. A preformed two-dot constant-capacitance model does not generate a physical dot-formation classification task. Use occupancy and transition labels for the core benchmark. Map QFlow labels explicitly: its topology labels are not interchangeable with (1,1), although its stored charge arrays may support derived occupancy labels after inspecting their conventions. [QFlow data paper](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0205844).

2. **High priority: the fidelity optimiser lacks a specified observation model.** [Design §6.4](/Users/razvanstrugariu/IdeaProjects/hackathon/SpinTune_Design_Proposition.md:159) and [§7.4](/Users/razvanstrugariu/IdeaProjects/hackathon/SpinTune_Design_Proposition.md:211) require energy-scale lever arms, U, tunnel coupling versus barrier voltage, noise covariance, and spin-frequency sensitivity. A zero-bias CSD and short sensor trace do not generally identify all of these. The simulator already knows them, but the tuner is explicitly forbidden from seeing that ground truth. A fleet prior also cannot identify an independently randomized hidden parameter that has no effect on its observations.

   Before retaining C2, give every fitted parameter a measurement protocol and cost: for example, energy-scale calibration, tunnel-coupling measurements, noise spectroscopy, and a spin-frequency measurement where applicable. Otherwise hold those quantities fixed and disclosed as model assumptions, and describe the result as an operating-point sensitivity study. For the MVP, predict a useful target region and uncertainty directly; recovering a posterior over every capacitance parameter is unnecessary and may be underdetermined. QArray's published model is electrostatic and applies in the weak-tunnel regime. [QArray paper](https://arxiv.org/html/2404.04994v1).

3. **High priority: the stated barrier trade-off is not produced by the equations.** The design uses `tc = t0 exp(kappa Vb)`, and exchange proportional to `tc²`. Under small, additive barrier-voltage noise of fixed RMS amplitude:

   ```text
   d(log J)/dVb = 2 kappa
   sigma_J / J = 2 kappa sigma_Vb
   RMS conditional-phase error = pi × 2 kappa sigma_Vb
   ```

   These are independent of the barrier setting under those assumptions. Larger absolute `dJ/dVb` does not imply larger phase error when the gate duration is shortened to maintain the same nominal phase. Consequently, if the only other barrier-dependent effect is shorter exposure to dephasing, this model can simply prefer the largest allowed barrier setting. Leakage is mentioned in the pitch but has no implemented model in the design. Correlations or voltage-dependent noise could change the conclusion; they must be specified and justified rather than assumed.

   Also, at the symmetric point, a first-order detuning expansion gives zero error while second-order sensitivity remains. Use sampled `J(epsilon + delta_epsilon, Vb + delta_Vb)` or retain the second-order term. Impose the perturbative validity domain and gate-voltage bounds. First compute the oracle optimum over the proposed parameter ranges. If the optimum collapses to a boundary or the symmetric rule, report that finding and avoid spending a week training an optimiser for it.

4. **High priority: reconcile the measurement budget with the compute budget.** [Design §8.1](/Users/razvanstrugariu/IdeaProjects/hackathon/SpinTune_Design_Proposition.md:228) caps each run at 20,000 pixels, while [the compute tables](/Users/razvanstrugariu/IdeaProjects/hackathon/SPINTUNE.md:64) assume 300 measurements per device using timings for full 100×100 maps. Under that cap, before any probes or confirmation:

   | Query shape | Maximum number within 20,000 pixels |
   |---|---:|
   | 100×100 | 2 |
   | 64×64 | 4 |
   | 32×32 | 19 |
   | 16×16 | 78 |

   Three hundred queries require an average of at most 66.7 pixels each. Two 16×16 probe windows already cost 512 pixels before adding the four rays, rather than approximately 500 including them. Fix query dimensions, scan voltage span, resolution, and the cost of every probe, reference, noise trace, confirmation, and failed acquisition. A full-scan navigation baseline has only two moves under the current cap; add the line-scan/edge-navigation heuristic promised by the pitch so the comparison includes a competitive low-cost baseline.

   Pixels are a useful acquisition proxy. They are not a complete estimate of elapsed calibration time. Report both pixel count and `sum(integration + settling + scan setup + transfer + inference + BO overhead)`. At the illustrative integration times, 20,000 pixels represent only 0.2 seconds of RF acquisition or 20 seconds of DC acquisition, before overhead. Do not extrapolate that to an hours-long full bring-up improvement. The literature's complete qubit-tuning pipelines include many additional stages.

5. **High priority: define the classifier-to-tuner contract.** [Design §7.3](/Users/razvanstrugariu/IdeaProjects/hackathon/SpinTune_Design_Proposition.md:204) obtains a transition margin from "the classifier's segmentation", but §7.1 specifies only a class vector. Specify a transition detector or segmentation output, its labels, and how distances are converted to gate-voltage units. Define whether a window's label describes its centre, its dominant region, or the whole window. Choose an explicit acquisition field of view: a small patch without any transitions may provide no search direction. A BO objective that is almost zero everywhere outside the target can also be hard to optimise. Test observability and search geometry with an oracle-assisted development baseline first; label that baseline clearly and exclude it from sensor-only claims.

6. **High priority: repair the physics and validation contract before an Aer demonstration.** The [design exchange expression](/Users/razvanstrugariu/IdeaProjects/hackathon/SpinTune_Design_Proposition.md:163) has a factor of 2, while [the pitch](/Users/razvanstrugariu/IdeaProjects/hackathon/SPINTUNE.md:47) has a factor of 4. Under the cited Hubbard convention, QTCAD gives `J = 4 U tc² / (U² - epsilon²)`. Choose one convention, define energy versus frequency units, and derive gate duration from an explicit effective Hamiltonian. Exchange alone is not an automatically calibrated CZ. [QTCAD exchange theory](https://docs.nanoacademic.com/qtcad/theory_spin_fem/exchange/).

   Aer using the same assumed model as the optimiser is a numerical consistency check. It cannot independently verify that the physical qubit improves. The optimiser must choose voltages and pulse duration using estimated parameters; the evaluator must propagate the resulting pulse using hidden true parameters and independent held-out noise trajectories. Using estimated parameters for both sides hides calibration error. Specify qubit indices for Bell preparation, assert the ideal circuit creates the intended Bell state, and cross-check a simple phase-error case analytically. Keep noise fixed within each quasi-static shot or RB sequence rather than inadvertently drawing independent noise at every gate. Report sensitivity to the physical model separately from Monte Carlo uncertainty.

   A reported total gate error is also not an independently measured residual depolarising floor. Adding a full measured error again alongside explicit charge noise can double-count it. Treat the residual floor as an assumption or calibrate a total error budget. Aer's depolarising parameter is not gate infidelity: for dimension `d`, `F_avg = 1 - lambda(d-1)/d`. For example, F=0.994 on one qubit means lambda=0.012, and F=0.984 on two qubits means lambda≈0.02133. [Aer channel definition](https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.noise.depolarizing_error.html).

7. **High priority: distinguish design intent from evidence and update versioned facts.** [The pitch](/Users/razvanstrugariu/IdeaProjects/hackathon/SPINTUNE.md:63) says a six-dot run is demonstrated and timings were measured with `bench_qarray.py`; neither implementation nor that script is present here. [The design status](/Users/razvanstrugariu/IdeaProjects/hackathon/SpinTune_Design_Proposition.md:10) says no experiment has run. Treat timings as unverified supplied estimates until the script, environment, device configuration, repetitions, and raw results are available. The six-dot example is future work.

   QArray's source defines `T` in **millikelvin**: 0.3 K must be passed as `T=300` in that API. A direct `T=0.3` would describe 0.3 mK. Pin a version and verify the adapter's physical units, including capacitances and energy scales. [QArray source](https://github.com/b-vanstraaten/QArray/blob/main/qarray/DotArrays/ChargeSensedDotArray.py).

   The design's 0.989/0.985 SPAM-corrected Bell fidelities at 300/740 mK occur in the cited paper's **v1**. The current **v3** changes the temperatures to 350/500/750 mK; Table 1 lists corrected Bell fidelities 0.9794/0.9675/0.8192. Cite the intended version and avoid presenting the older figures as current peer-reviewed results. These are Si/SiGe measurements, which do not by themselves calibrate an FD-SOI device fleet. [Equal1 paper v1](https://arxiv.org/html/2412.01920v1), [v3](https://arxiv.org/html/2412.01920v3).

8. **Medium priority: reconcile scope and claims of realism.** The pitch makes charge tuning the MVP, while the design promotes fidelity selection and drift recovery to headline contributions. The pitch describes five nearest-neighbour links in six dots, while the design describes three pairs. Three disjoint pairs and five adjacent links are different experiments. QFlow is training data in the pitch and a frozen domain-shift test in the design; choose a split policy before using it. One train/validation source plus one external test is a clear initial choice.

   G1 tests whether a noise generator reproduces selected statistics, rather than whether the complete fleet is realistic for Equal1. The cited 0.4 correlation is a frequency-dependent cross-spectrum peak for a particular pair near 0.2 Hz, not a universal Pearson correlation target. Define the same statistic, frequency band, geometry, sign/phase, and observation duration. A slow sensor-noise trace cannot by itself validate nanosecond gate-noise behaviour. Treat the Si/SiGe noise study as one literature-inspired scenario and sweep assumptions for FD-SOI. [Correlated-noise study](https://arxiv.org/html/2603.03051v1).

   Both studies and public vendor pages also evolve. The current vendor technology page separates qubit-performance evidence from its commercial-CMOS evidence; preserve that distinction. Q-CTRL's primary announcement confirms the commercial calibration context and offline operation, but does not establish a public integration API or SpinTune's uniqueness. Broad claims that nobody transfers information across devices are too strong given existing cross-device and cross-architecture tuning work. Define the contribution as this reproducible benchmark and evaluated warm-start method. [Equal1 technology](https://www.equal1.com/technology), [Q-CTRL announcement](https://q-ctrl.com/blog/equal1-and-q-ctrl-partner-to-deliver-fully-autonomous-data-center-ready-quantum-computing), [cross-architecture tuning study](https://pmc.ncbi.nlm.nih.gov/articles/PMC11283483/).

   A future six-dot result needs a shared device state, measured virtual-gate calibration, and a final check that all intended charge states coexist after the last pair is tuned. Independent double-dot simulations do not establish this. The pitch's 12–15-qubit Aer limit also needs a simulation-method qualification: at 15 qubits, a dense complex128 statevector occupies 0.5 MiB, while a dense density matrix occupies 16 GiB, before overhead. Those are different scaling limits. Neither establishes the cost of a particular noisy circuit.

**Recommended deliverable and effort**

These are planning estimates for one experienced Python/ML developer working full time, with access to physics review. They are not measured delivery probabilities. Two contributors can overlap model and benchmark work, but interface and scientific decisions remain dependencies.

| Work | Feasibility by 27 November | Indicative focused effort |
|---|---|---|
| Preformed double-dot generator, unit checks, metered interface, evaluator | High | 3–5 working days |
| Occupancy reference, transition reader, random/heuristic/cold-BO baselines | Moderate to high once the observation contract is fixed | 4–6 days |
| Conditional fleet warm start, ablations, ID/OOD evaluation | Moderate; the implementation is feasible, the gain is unknown | 5–7 days |
| Frozen runs, result plots, reproducible demo and documentation | High if scope stays fixed | 3–4 days |
| Simple translation-drift extension | Moderate stretch | 2–3 additional days |
| Full calibrated TLF ensemble, inferred fidelity optimum, RB, six-dot crosstalk | Low as a combined solo commitment | Separate research work; estimate after pilot |

The core is approximately 15–22 focused working days before contingency. Avoid making a five-network ensemble, physical TLF calibration, full parameter-posterior inference, RB, Stim, or six-dot scaling prerequisites for the warm-start result. If an explicit Qiskit component is needed for judging, keep a small, clearly labelled model-based circuit check alongside the charge benchmark.

Use one canonical experiment specification. Implement the measurement interface first, then baselines, then the learned prior. At evaluation time, only that interface exposes measurements; device parameters and noiseless maps stay evaluator-only. Persist device seeds, measurement events, declared outcomes, and per-run costs so all headline plots can be regenerated without rerunning tuning.

**A success definition that can be defended**

The primary question should be: *On unseen, preformed simulated double dots, does a learned fleet warm start reduce charge-tuning acquisition cost while preserving reliability?* This does not yet establish reduced physical bring-up time, better gate fidelity, or production deployment value.

1. Fix the allowed gate domain, starting information, occupancy-reference protocol, scan shapes, noise bandwidth, and budget. Split by complete device identity before generating image crops. Where populations have shared wafer or fabrication parameters, hold out entire groups as an additional transfer test. Keep OOD populations frozen alongside the ID test.
2. Define success using the evaluator's electrostatic charge state at the final declared voltage, plus a specified stability margin. For anisotropic correlated voltage noise, a useful margin is distance to each transition divided by noise projected onto that transition's normal, rather than Euclidean distance divided by an unspecified scalar RMS. Specify the treatment of temperature separately. Record devices with no reachable robust target, and report the full-population outcome as well as any explicitly conditioned feasible-device outcome.
3. Compare random search, a line-scan/transition-navigation heuristic, cold BO, and warm BO. Use the same measurement interface, state reader, domain, stopping rule, and runtime limits. Tune cold BO on validation data too. Charge warm-start probes to its budget; if both methods receive shared initial probes, charge them to both.
4. Add a pooled static starting point, a simple probe/template predictor, and the learned prior without BO as ablations. These show whether gains come from conditional fleet information, an easier initialization distribution, or a complex optimiser that a simple rule could replace.
5. Freeze hypotheses and analysis after development and validation, before final test results. Start with 100 development devices and three stochastic seeds; scale to 1,000 ID test devices, three OOD populations of 1,000 each, and up to five seeds once the pilot justifies it. Repeated seeds quantify algorithm variability and are nested within devices; they do not create thousands of independent chips.

| Outcome | Metric | Proposed interpretation, to freeze after validation |
|---|---|---|
| Reliability | Fraction of all devices with a valid declared stop by B=20,000 pixels | Retain ≥90% observed ID success; publish its 95% CI and the difference from cold BO |
| Measurement saving | Restricted mean cost `C = mean(min(T_success, B))`, assigning B when there is no valid success | Demonstrate an improvement with a paired device-bootstrap CI for `C_warm/C_cold` below 1; choose a practical target such as ≤0.8 in advance |
| Stretch effect size | Same cost metric and complete success-versus-budget curve | Treat the original ≥2× saving as a hypothesis, not an assumed outcome |
| Robustness | Reliability and cost on each frozen OOD population | Retain the proposed ≥75% success target if validated as meaningful; show negative transfer relative to cold BO |
| Trustworthy stopping | Fraction of declared successes that are wrong; abstention coverage and target precision/recall | Set a false-success tolerance before testing; report all runs, including abstentions and early false stops |
| Runtime | Measured simulator and optimiser wall time, plus labelled acquisition-time scenarios | Substantiate computational feasibility and quantify when measurement savings offset BO latency |
| Optional drift | Event recall, false alarms per monitoring window/hour, detection delay, monitoring plus recovery pixels | Compare local recovery and restart under equal horizons, success requirements, and total cost |

`T_success` is the cumulative cost to the first valid declared success; it is infinite when the tuner never declares a valid result. Charging unsuccessful runs B for the restricted metric prevents a method from looking cheap by stopping incorrectly or failing early. Also show actual expenditure, conditional median/p90, and the complete failure counts separately. The area under the success-versus-budget curve carries equivalent restricted-cost information when defined consistently.

At 90% success on 1,000 independent devices, the approximate binomial 95% half-width is 1.9 percentage points. That supports useful reliability estimates but is not a power analysis for a paired cost ratio or OOD effects. Estimate those intervals from the development/validation pilot. Resample devices with all their tuner seeds together for paired comparisons. Do not claim success from a median over successful devices alone; it can hide a worse failure rate. Accuracy and ECE also do not establish safe stopping when the classifier abstains or the class distribution is imbalanced.

G4 should remain exploratory until the observation model and physics issues above are fixed. If retained, evaluate on hidden true parameters and new trajectories; report absolute gain and regret to the oracle. The fraction of an oracle gap is unstable when that gap is nearly zero. G5 additionally needs observable drift: a 32×32 patch entirely inside a charge cell may lack any features for cross-correlation, so select or schedule a reference window containing transitions and account for that choice.

**Compute feasibility and the first decision point**

The arithmetic in the pitch's full-scan table is broadly consistent with its supplied per-map timings. It does not validate those timings, the 300-query assumption, BO fit/acquisition overhead, or linear scaling to 128 cores. Parallelise independent device runs and benchmark total throughput. Control backend thread counts so multiple workers do not each consume every core. A failed or slow tuner also needs a per-device wall-time limit. Do not multiply operating-point rules into acquisition work if they reuse the same already-tuned device.

A 100-device pilot with four methods, three seeds, and the full 20,000-pixel cap uses at most 24 million sensor pixels. A final run on 4,000 devices with four methods and five seeds uses at most 1.6 billion, excluding separate drift/operating-point stages. These are acquisition counts, not CPU-runtime estimates. Two hundred thousand 100×100 float32 images occupy about 8 GB before labels and metadata; stream or chunk data if retaining that training volume. Choose fleet size from learning curves and uncertainty needs instead of treating 10,000 as a requirement for every development run.

Within the next two working days, require a small proof of execution:

- A pinned QArray smoke test with explicit temperature and unit conversions, a known occupancy reference, and 20 visibly varied devices.
- A metered query API and evaluator with a reachable-target check and a deterministic seed replay.
- Random and transition-navigation baselines on approximately 100 development devices; report target hit rate, query sizes, total pixels, and end-to-end runtime.
- An oracle-assisted development experiment that checks whether the search task and measurement geometry are workable without classifier error. Keep those results separate from sensor-only performance.

If these checks pass, proceed to the learned warm start. If even oracle-assisted search cannot find reachable robust targets at the stated budget, revisit the observation design and query policy before training. If the pilot shows that a simple heuristic already solves nearly every device cheaply, strengthen the benchmark using justified variability or report the small remaining headroom; do not manufacture difficulty merely to favour the learned method.

The recommendation is to proceed with C1 and C4, make the first end-to-end cost comparison the next milestone, and require additional evidence before promoting C2 or hardware relevance to a headline result.

---

## Addendum: measured checks with QArray (25 October 2026)

This addendum was written after the review above. QArray 1.6.0 was installed in an isolated Python 3.12 environment on an Apple M4 Pro (14 cores, macOS), and three small simulations were run. They test assumptions that the review above could only reason about. Scripts and raw output are reproduced in section F.

**A. Environment and API**

- QArray 1.6.0 declares `requires_python >=3.10`, but its compiled dependency `qarray-rust-core` 1.3.1 publishes wheels only for CPython 3.10–3.12. On this machine's default Python 3.14, installation fails while building that package from source, because no Rust toolchain is installed. Pin Python 3.12 in the project setup, or document the Rust toolchain requirement.
- `PSBLatching` and `PSBLatchingModel` are both exported, so neither document uses a wrong name.
- The installed source confirms that `T` is in millikelvin (finding 7).
- QArray exports `optimal_Vg` and `compute_optimal_virtual_gate_matrix`. The first returns the gate voltages for a requested charge state from the capacitance model. The evaluator can use it for ground truth, and it makes a strong physics baseline cheap to build (E2).

**B. Simulation timing**

Charge-sensed CSDs from `ChargeSensedDotArray`, Rust backend, white plus telegraph noise, lead/inter-dot latching, `T=300` (0.3 K). Mean of 10 calls after one warm-up, for one device configuration. The single-thread column sets `RAYON_NUM_THREADS=1` and `OMP_NUM_THREADS=1`.

| Dots | Scan | Default threads | Single thread |
|---|---|---:|---:|
| 2 | 100×100 | 47.1 ms | 97.2 ms |
| 2 | 32×32 | 5.5 ms | 9.9 ms |
| 4 | 100×100 | 57.6 ms | 116.4 ms |
| 4 | 32×32 | 6.0 ms | 12.4 ms |

These timings are in the same range as the supplied `SPINTUNE.md` figures (~76 ms and ~130 ms single-threaded), measured on a different machine and configuration. That makes those estimates plausible. It does not replace committing `bench_qarray.py` with its configuration and results. A 32×32 query costs about a tenth of a 100×100 map. A compute table that charges every tuner query as a full map therefore overstates the load about tenfold for window-based tuners.

**C. Charge cells are congruent in the constant-capacitance model**

For one device on a 400×400 grid, the (1,1), (2,2), (3,3), (1,2) and (2,1) regions each cover 3,011–3,023 pixels (0.922–0.926 V² in illustrative units). In this model, every cell with at least one carrier per dot is a translated copy of the others. A window inside or around one such cell therefore looks the same for (1,1) as for (2,2). This confirms finding 1 for the simulator: occupancy can only be identified with context, such as a measured empty-state region or transitions counted from it. Real devices may break this symmetry through orbital and interaction effects that QArray does not model. The benchmark should not rely on that.

**D. A zero-measurement tuner already reaches the target on most devices**

Devices were drawn from the Design §6.2 spreads:
- lever arms ±15%;
- cross-capacitance 0.1–0.4 of the diagonal;
- dot-to-dot coupling ±20%;
- offset charges either absent or uniform over one charge period.

Offset charges were applied as the equivalent gate-voltage shift. "Cell width" is the square root of the (1,1) cell's area. The zero-measurement tuner reads nothing and sets every device to the fleet-mean (1,1) centre. Success here means the evaluator's noiseless state is (1,1), with **no** stability margin, so the required margin would lower these rates somewhat.

| Offset charges | (1,1) centre SD, P1 / P2 (cell widths, 300 devices) | 95% span (cell widths) | Zero-measurement success (400 devices) |
|---|---|---|---|
| None | 0.10 / 0.10 | 0.38 × 0.35 | 100% |
| Uniform over one period | 0.34 / 0.33 | 1.22 × 1.23 | 82% (95% CI ≈ 78–86%) |

Implications:

- Under the current spreads, G3's "≥90% success at B" is close to free. The "≥2× saving versus cold BO" will mostly depend on how large the cold-start domain is. As specified, the comparison would mainly measure those choices rather than the learned prior.
- Make this tuner a mandatory ablation and run it first. It is the "pooled static starting point" in success-definition item 4. Report its cost (zero search pixels plus confirmation) and its success rate alongside every other method.
- Set offset-charge and threshold-voltage spread from evidence: Equal1 data if offered, or published FD-SOI variability. Devices are often several charge periods from nominal, but that needs a source, not an assumption. This follows the review's caution against manufacturing difficulty. Widen the fleet only as far as the evidence supports, and if it stays narrow, report the small remaining headroom.

**E. Additional findings**

1. **The HPC load depends on the implementation.**
   - A device's noiseless map can be computed once at the needed resolution and cached. Each tuner query then reads a sub-array and adds noise, so evaluation cost barely depends on the number of queries.
   - That removes most of the 1,300 core-hours in `SPINTUNE.md` and the 8,300 in Design §9.
   - QArray generates telegraph noise along the scan order, so caching requires generating query noise separately. Specify that noise model.
   - A more durable HPC workload is sweeping the uncertain assumptions (fleet spread, noise, temperature, tunnel-coupling model) to show how the warm-start gain varies with fabrication spread. Design §11 already lists "gain versus spread" as a mitigation; it makes a stronger HPC centrepiece than per-query simulation.
2. **Add a scan-and-fit baseline.** Take one coarse scan, fit transition slopes and spacings to a capacitance model, then call `optimal_Vg` for the target. This is the physics baseline an Equal1 engineer is likely to propose. A constant-capacitance simulator favours it, because the simulator matches its model exactly. Report that caveat rather than omitting the baseline.
3. **The barrier leaves no trace in QArray maps.** QArray has no tunnel coupling, so V_B's effect on t_c cannot be observed in any simulated measurement. This makes finding 2 concrete: in the current stack, t₀ and κ can only be assumed, not estimated.
4. **The six-dot topology is unconfirmed.** The 22FDX validation cited in `SPINTUNE.md` describes cells of up to three dots. [arXiv 2412.01920 v1](https://arxiv.org/abs/2412.01920v1) describes a two-qubit processor in a six-dot SiGe array. Neither establishes that Bell-1 is a six-dot linear chip. Ask Equal1 before building the six-dot extension.
5. **Correct the elevator pitch.** Design §3 says SpinTune "proves it with a Bell state in Qiskit". Under finding 6, a model-based Aer circuit is a consistency check, not proof. Use wording such as "and checks the operating point with a model-based Bell circuit in Qiskit".

**F. Reproduction**

Environment: `uv venv -p 3.12 .venv && uv pip install qarray==1.6.0` (this installs `qarray-rust-core` 1.3.1).

<details>
<summary><code>smoke.py</code>: timing check (section B)</summary>

```python
import time, numpy as np, os
from qarray import ChargeSensedDotArray, WhiteNoise, TelegraphNoise, LatchingModel
def make(n_dots, T, noise=True, latch=True, seed=0):
    rng = np.random.default_rng(seed)
    Cdd = np.zeros((n_dots, n_dots))
    for i in range(n_dots-1): Cdd[i,i+1]=Cdd[i+1,i]=0.1*(1+0.2*rng.uniform(-1,1))
    Cgd = np.eye(n_dots)*(1+0.15*rng.uniform(-1,1,n_dots))
    for i in range(n_dots-1): Cgd[i,i+1]=Cgd[i+1,i]=0.2
    Cgd = np.hstack([Cgd, 0.01*np.ones((n_dots,1))])          # + sensor gate column
    Cds = np.array([[0.02*(1+0.2*rng.uniform(-1,1)) for _ in range(n_dots)]])
    Cgs = np.array([[0.06]*n_dots + [1.0]])
    nm = (WhiteNoise(amplitude=1e-2) + TelegraphNoise(amplitude=5e-4, p01=1e-3, p10=1e-2)) if noise else None
    lm = LatchingModel(n_dots=n_dots, p_leads=0.95*np.ones(n_dots), p_inter=0.99*np.ones((n_dots,n_dots))) if latch else None
    return ChargeSensedDotArray(Cdd=Cdd, Cgd=Cgd, Cds=Cds, Cgs=Cgs, coulomb_peak_width=0.05, T=T,
                                noise_model=nm, latching_model=lm, charge_carrier='e')
for n_dots in (2,4):
    for npx in (100, 32):
        m = make(n_dots, T=300)
        vg = m.gate_voltage_composer.do2d('P1', -2, 8, npx, 'P2', -2, 8, npx)
        m.charge_sensor_open(vg)  # warm-up
        t=time.perf_counter(); R=10
        for _ in range(R): z, n = m.charge_sensor_open(vg)
        dt=(time.perf_counter()-t)/R
        print(f"{n_dots} dots, {npx}x{npx}, T=300 mK, noise+latching: {dt*1e3:7.1f} ms/CSD  (z {z.shape}, n {n.shape})")
```

Run with `python smoke.py` and with `RAYON_NUM_THREADS=1 OMP_NUM_THREADS=1 python smoke.py`.

</details>

<details>
<summary><code>prior_check.py</code>: cell congruence and fleet spread (sections C and D)</summary>

```python
# (A) Are charge cells (1,1), (2,2), (3,3) the same shape?
# (B) How far does the (1,1) centre move across the fleet, in cell widths?
# (C) Zero-measurement baseline: set every device to the fleet-mean (1,1) centre.
import numpy as np
from qarray import DotArray
rng = np.random.default_rng(1)

def device(rng, offsets=True):
    a = 1 + 0.15*rng.uniform(-1, 1, 2)                 # lever arms +-15%
    x = rng.uniform(0.1, 0.4, 2) * a[::-1]             # cross-cap 0.1-0.4 of diagonal
    Cgd = np.array([[a[0], x[0]], [x[1], a[1]]])
    c = 0.1*(1 + 0.2*rng.uniform(-1, 1))               # dot-dot +-20%
    Cdd = np.array([[0, c], [c, 0]])
    m = DotArray(Cdd=Cdd, Cgd=Cgd, charge_carrier='e', T=0)
    q0 = rng.uniform(-0.5, 0.5, 2) if offsets else np.zeros(2)   # offset charge, one period
    shift = -np.linalg.solve(Cgd, q0)                 # offset charge == gate-voltage shift
    return m, shift

def cell_stats(m, shift, lo=-1.5, hi=5.5, N=400):
    vg = m.gate_voltage_composer.do2d('P1', lo, hi, N, 'P2', lo, hi, N)
    n = np.asarray(m.ground_state_open(vg))
    px = ((hi-lo)/N)**2
    out = {}
    for s in [(1,1),(2,2),(3,3),(1,2),(2,1)]:
        mask = (n[...,0]==s[0]) & (n[...,1]==s[1])
        vs = vg[mask]
        out[s] = (mask.sum()*px, vs.mean(0)+shift if len(vs) else None, mask.sum())
    return out

# (A)
m, sh = device(rng, offsets=False)
st = cell_stats(m, sh)
print("(A) cell areas (V^2) for one device:")
for s,(area,c,cnt) in st.items(): print(f"    {s}: area={area:.4f}  pixels={cnt}")

# (B)
for offsets in (False, True):
    centres, widths = [], []
    for _ in range(300):
        m, sh = device(rng, offsets)
        st = cell_stats(m, sh, N=200)
        area, c, _ = st[(1,1)]
        centres.append(c); widths.append(np.sqrt(area))
    centres = np.array(centres); w = np.median(widths)
    sd = centres.std(0); span = np.percentile(centres,97.5,0)-np.percentile(centres,2.5,0)
    print(f"(B) offsets={'uniform 1 period' if offsets else 'none'}: (1,1) cell width ~{w:.2f} V; "
          f"centre SD = {sd[0]/w:.2f} / {sd[1]/w:.2f} cell widths; 95% span = {span[0]/w:.2f} x {span[1]/w:.2f} cell widths")

# (C)
print("(C) zero-measurement 'fleet mean' tuner, success = lands in true (1,1):")
for offsets in (False, True):
    devs = [device(rng, offsets) for _ in range(400)]
    cs = np.array([cell_stats(m, sh, N=200)[(1,1)][1] for m, sh in devs])
    v_mean = cs.mean(0)
    hit = 0
    for (m, sh) in devs:
        n = np.asarray(m.ground_state_open((v_mean - sh)[None, :]))[0]
        hit += int(n[0]==1 and n[1]==1)
    print(f"    offsets={'uniform 1 period' if offsets else 'none'}: {hit/len(devs):.0%} of devices")
```

The absolute capacitances are illustrative: diagonal lever arms are near 1 and dot-to-dot coupling is near 0.1. Results are reported in cell widths, so they depend mainly on the relative spreads. The run uses one RNG seed, noiseless ground states at T=0, and no stability margin.

</details>

<details>
<summary>Raw output</summary>

```text
threads default:
2 dots, 100x100, T=300 mK, noise+latching:    47.1 ms/CSD  (z (100, 100, 1), n (100, 100, 2))
2 dots, 32x32, T=300 mK, noise+latching:     5.5 ms/CSD  (z (32, 32, 1), n (32, 32, 2))
4 dots, 100x100, T=300 mK, noise+latching:    57.6 ms/CSD  (z (100, 100, 1), n (100, 100, 4))
4 dots, 32x32, T=300 mK, noise+latching:     6.0 ms/CSD  (z (32, 32, 1), n (32, 32, 4))
single-thread:
2 dots, 100x100, T=300 mK, noise+latching:    97.2 ms/CSD  (z (100, 100, 1), n (100, 100, 2))
2 dots, 32x32, T=300 mK, noise+latching:     9.9 ms/CSD  (z (32, 32, 1), n (32, 32, 2))
4 dots, 100x100, T=300 mK, noise+latching:   116.4 ms/CSD  (z (100, 100, 1), n (100, 100, 4))
4 dots, 32x32, T=300 mK, noise+latching:    12.4 ms/CSD  (z (32, 32, 1), n (32, 32, 4))

(A) cell areas (V^2) for one device:
    (1, 1): area=0.9258  pixels=3023
    (2, 2): area=0.9221  pixels=3011
    (3, 3): area=0.9258  pixels=3023
    (1, 2): area=0.9233  pixels=3015
    (2, 1): area=0.9258  pixels=3023
(B) offsets=none: (1,1) cell width ~1.03 V; centre SD = 0.10 / 0.10 cell widths; 95% span = 0.38 x 0.35 cell widths
(B) offsets=uniform 1 period: (1,1) cell width ~1.03 V; centre SD = 0.34 / 0.33 cell widths; 95% span = 1.22 x 1.23 cell widths
(C) zero-measurement 'fleet mean' tuner, success = lands in true (1,1):
    offsets=none: 100% of devices
    offsets=uniform 1 period: 82% of devices
```

</details>
