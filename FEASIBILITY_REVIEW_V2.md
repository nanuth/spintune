**SpinTune v2 review — 25 October 2026**

V2 addresses most of the previous review at the level of intent and scope. It is substantially more implementable: occupancy is anchored and counted, the reader has an explicit segmentation contract, fidelity optimisation has been removed, query shapes and acquisition costs are specified, and strong classical baselines are present. Several new details still prevent treating the benchmark and its success gates as frozen.

This review leaves the design unchanged. References below point to `SpinTune_Design_v2.md`. I read the complete document, compared it with the earlier review and addendum, inspected the named scratch scripts, reran `cz_check.py` and `cz_pulse_check.py`, and ran an additional fixed-correction Hamiltonian check. No tuner implementation or end-to-end tuning result exists in this workspace yet. Some evidence scripts exist in the temporary scratch directory but have not been copied into the project as promised in §13.

**Original findings: current status**

| Earlier finding | V2 status |
|---|---|
| Absolute occupancy needs context | Correct architectural response; the proposed empty-anchor test and the tracker still have unresolved failure cases (R1–R2) |
| Fidelity optimiser needs unobservable parameters | Addressed by removing that optimiser and separating the model-based study |
| Barrier trade-off is absent from the equations | Addressed; a boundary optimum is now an acceptable result |
| Pixel and compute budgets disagree | Query accounting substantially addressed; scan coverage and time-based failure accounting still need decisions |
| Classifier does not provide segmentation | Addressed in the window-reader contract; ray handling and overlapping transition labels need implementation rules |
| Exchange, noise and verification contract | Improved and partly reproduced; Zeeman normalization, the pure-ZZ approximation, and RB acceptance still need correction (R6) |
| Evidence, units and versioned facts | `T=300`, v3 fidelity references, and explicit evidence statuses are addressed. The pulse scripts exist and reproduce. Project-local scripts, lockfiles, and raw outputs remain pending |
| Scope, topology and realism | Six-dot promise removed and second simulator added. The primary template combines two different published operating modes (R5) |
| Addendum: trivial prior, HPC caching, missing physics baseline | Addressed by wider literature-inspired scenarios, zero-search ablations, caching, and scan-and-fit. The new headroom claim still needs an end-to-end pilot |

**R1 — High: the empty-anchor rule can still silently miscount electrons.**

At [§5.1, line 248](/Users/razvanstrugariu/IdeaProjects/hackathon/SpinTune_Design_v2.md:248), a transition-free distance exceeding 1.5 times the **prior** addition voltage is treated as proof of an empty device. The permitted charge-period range is about 5–40 mV. With prior P=15 mV and actual P=40 mV, a ray starting at 70 mV encounters no transition over its first 22.5 mV, but can still contain two electrons: take loading transitions at 0 and 40 mV. The routine would call 47.5 mV empty. A missed or latched transition can produce the same failure even when the period estimate is otherwise correct.

This is a constructive counterexample to the rule, not a claim that the eventual implementation necessarily behaves this way. It matters because the confirmation then counts from the same incorrect reference, so it is not independent evidence against a whole-electron offset. A second axis does not automatically establish that both dots are empty.

Required change: define anchor evidence using the allowed maximum projected transition gap, calibrated sensor visibility, direction/sign of crossings, and a two-dimensional depletion check. A measured candidate-specific period bound can reduce the cost once reliable. If the safe domain or sensor response cannot establish emptiness, abstain. Add noiseless tests across the full parameter range and noisy missed-line/latching tests. The 100% noiseless pilot target is useful but cannot substitute for specifying the rule. Re-measure T★ after this change; the earlier 1.2–1.5k-pixel estimate was not measured for this stricter protocol.

**R2 — High: the new lattice tracker assumes line indices before anchoring establishes them.**

[§6, lines 286–294](/Users/razvanstrugariu/IdeaProjects/hackathon/SpinTune_Design_v2.md:286) treats each observed crossing as a linear-Gaussian measurement of an absolute reference point and lattice matrix. Before anchoring, the integer lattice index is unknown. A crossing at voltage x can mean `x = v0 + nP` for several different n. Translating v0 by an integer period and shifting n leaves the local observation unchanged. The likelihood over absolute location is therefore generally multimodal. A flat prior across ±300 mV is also not a local Gaussian prior.

This creates a possible deadlock: the tracker anchors only after its target posterior becomes tight, while the periodic local measurements cannot resolve the integer ambiguity needed to make that posterior tight. A Laplace approximation can appear confident around an arbitrary charge cell and trigger a false result.

Required change: either anchor before using absolute-lattice observations or explicitly track discrete charge indices alongside continuous lattice parameters, for example with a bounded mixture/particle representation. Specify how inter-dot transitions, line-family ambiguity, and hypothesis pruning are handled. Test two devices with locally identical scans but target centres separated by several charge periods. They must remain ambiguous until a reference measurement resolves the difference.

Also define the query schedule when the requested uncertainty region exceeds the largest permitted 64×64 window. At 4 mV pitch, that window spans only approximately 252 mV, while the domain is 600 mV wide and a nominal 95% target region is roughly 300 mV. T2's "one coarse scan" likewise requires a mosaic or another explicitly billed protocol. These are core search-policy decisions, rather than minor builder choices to leave until after the freeze.

**R3 — High: two test wafers do not support the intended population-level confidence claim.**

The [test fleet has two wafers](/Users/razvanstrugariu/IdeaProjects/hackathon/SpinTune_Design_v2.md:383), while [§11.4](/Users/razvanstrugariu/IdeaProjects/hackathon/SpinTune_Design_v2.md:568) proposes a bootstrap over chips nested in wafers. V2 introduces shared wafer offsets and a shared radial-shift coefficient, so wafer-to-wafer variation is part of the claimed generalization problem.

Resampling chips while holding the two wafers fixed estimates conditional performance on those wafers. Resampling the wafers themselves provides only two independent top-level draws, which gives an unstable estimate of performance across new wafers. The one-wafer pilot cannot estimate that between-wafer variability. Similarly, one wafer per OOD condition confounds the condition with that wafer's random effects.

Required change: sample fewer chips per wafer across substantially more independently generated wafers at the same overall cell budget. Use the pilot to determine a reasonable top-level sample count; do not make a universal claim that one particular number guarantees valid intervals. Bootstrap whole wafer draws, preserving chip histories and tuner seeds. For OOD comparisons, use multiple wafers and matched latent devices where possible, changing only the designated OOD parameter. If retaining two wafers, explicitly limit the headline inference to those sampled wafers and report the uncertainty accordingly.

**R4 — High: the comparison still mixes information access with algorithm quality.**

[T6 receives same-chip history and metadata; T2/T3 receive none](/Users/razvanstrugariu/IdeaProjects/hackathon/SpinTune_Design_v2.md:301). The [risk table](/Users/razvanstrugariu/IdeaProjects/hackathon/SpinTune_Design_v2.md:699) even says T2 cannot use history, but scan-and-fit or transition navigation can start from the empirical-Bayes prediction, use its uncertainty to choose a scan region, and update a conventional model afterward.

The existing comparison can validly measure the benefit of the complete history-informed package against those particular cold baselines. It does not establish that the learned estimator beats a competitive classical tuner with the same information. The required T6-without-estimator ablation helps, but uses the same lattice policy and is not a replacement for a classical search baseline initialized from the same history.

Required change: add a history-informed version of the strongest classical baseline. Run two explicit comparisons: history versus no history within the same policy, and learned versus conventional inference with equal metadata and history access. Select the primary classical comparator on validation, or specify how selecting the minimum of multiple costs is handled in the bootstrap.

Every history must be generated by that tuner's own previous measurements and declarations, including erroneous declarations and abstentions. Do not populate it with evaluator-known correct centres. Report the total cost and success rate for all ten cells, including cold initialization and failed cells, alongside the gain versus cell index. A within-chip gain can be useful even when the learned estimator adds nothing; the claims should distinguish those outcomes.

**R5 — High for Equal1-specific claims: the device template combines transport and SEB-sensing configurations.**

[§3.1](/Users/razvanstrugariu/IdeaProjects/hackathon/SpinTune_Design_v2.md:150) combines the QT0/QT2 tuning plane and QT1 inter-dot barrier with an edge SEB. In the cited paper's **transport** configuration, the two dots lie between QT0/QT1 and QT1/QT2. In its **SEB plus double-dot** configuration, the SEB occupies QT0/QT1, while the sensed dots occupy QT1/QT2 and QT2/QA1. The shared barrier for those sensed dots is QT2. These layouts cannot simply be combined into one sourced template. [Equal1 paper, Fig. 2 and Fig. 4](https://arxiv.org/html/2412.08422v2).

Required change: draw the reservoirs, sensor, dots, and active/fixed gates for one chosen operating mode, and derive the two-dimensional tuning plane and capacitance matrices for that mode. Until confirmed, describe the generator as inspired by the published devices. A sensor-dot model can be a useful proxy, but its transfer function and visibility assumptions need to be identified as such. A second simulator does not independently validate an incorrectly mapped device geometry.

The 22 mV first-electron spread is a relevant measurement in a different group's 22FDX transistor-dot array, not a direct Equal1 multi-gate-cell calibration. The design already labels some hierarchy parameters as uncertain; the opening pitch should use the same qualification rather than saying the entire hierarchical fleet is calibrated to Equal1's published statistics. [22FDX variability study](https://arxiv.org/html/2310.20434).

**R6 — High for G4: the quantum acceptance tests require equivalences that are not generally valid.**

There are three separate issues:

- **Hamiltonian convention:** [§8.2](/Users/razvanstrugariu/IdeaProjects/hackathon/SpinTune_Design_v2.md:417) uses `(DeltaEz/2)(ZI−IZ)`. This has odd-state Zeeman energies ±DeltaEz, so their splitting is **2 DeltaEz**. The square-pulse oscillation frequency is therefore `sqrt(J² + 4 DeltaEz²)`, rather than the `sqrt(J² + DeltaEz²)` stated nearby. If DeltaEz means the physical qubit-frequency difference, the Hamiltonian coefficient should be DeltaEz/4. The scratch pulse script uses the former coefficient, so it reproduces the numbers but does not resolve the definition. Fix the convention and rerun the adiabatic-limit and pulse checks.
- **Pure-ZZ is an approximation:** the fixed local corrections do not generally remove noise-dependent single-qubit phases induced by finite exchange relative to the Zeeman difference. I reproduced the nominal pulse claims, then kept corrections fixed at the nominal point while changing J. At Jmax=20 MHz, DeltaEz=63 MHz and deltaJ/J=1%, the full stated Hamiltonian gives infidelity about **5.2031e−5**, versus **4.9347e−5** for the pure-ZZ formula. Even subtracting the nominal pulse infidelity of approximately 1.2458e−6 leaves about a **2.9%** discrepancy. A <1% relative criterion on infidelity therefore fails within the allowed range; if the criterion instead applies to fidelity near one, it is too loose to validate this error budget. Treat the ZZ formula as a large-gradient check with a stated validity range, and evaluate the full channel elsewhere. Use an absolute tolerance near zero error as well as a relative tolerance.
- **RB estimates and backend properties are not universal ground truth:** [§10.1–10.2](/Users/razvanstrugariu/IdeaProjects/hackathon/SpinTune_Design_v2.md:500) and G4 demand IRB agreement with analytic average infidelity and with the backend-reported error within a fitted CI. Quasi-static noise held across a sequence can produce decay behaviour that a single exponential does not capture. IRB also has systematic error bounds beyond a fit's statistical CI. IBM documents that its published two-qubit metric includes a single-qubit Clifford layer; it can additionally come from an earlier characterization time. It is not necessarily the isolated CZ quantity estimated by this experiment. [Correlated-noise RB analysis](https://arxiv.org/abs/1504.05307), [Qiskit IRB systematic bounds](https://qiskit-community.github.io/qiskit-experiments/manuals/verification/randomized_benchmarking.html), [IBM metric definitions](https://quantum.cloud.ibm.com/docs/en/guides/qpu-information).

Required change: validate the pipeline first on known Markovian simulated channels, including systematic bounds and fit diagnostics. For quasi-static scenarios, report decay curves, model fit quality, sequence/noise-sampling uncertainty, and deviations from the single-gate analytic reference as a result. For IBM, verify the native operation, physical pair, transpilation, job execution, and analysable data; compare with backend properties descriptively with the protocol and timestamp recorded. A disagreement should trigger investigation rather than automatically invalidate the implementation.

Keep an external IBM run as a scheduled demonstration with a fallback; it should not be a non-cuttable scientific prerequisite for the simulation result. Open access currently exists, but actual service access, queueing, and hardware drift are external dependencies. The allowance is up to 10 minutes per **28-day rolling window**, rather than a calendar month. [IBM plans](https://quantum.cloud.ibm.com/docs/en/guides/plans-overview).

**R7 — Medium: time-correlated and finite-tunnelling evaluation needs explicit semantics.**

[§4.3](/Users/razvanstrugariu/IdeaProjects/hackathon/SpinTune_Design_v2.md:235) resets noise and latching for every query. That is a possible synthetic task definition, but arbitrary segmentation of a physical scan into small requests should not silently reset a charge trap or latched occupancy. Otherwise algorithms can benefit from query boundaries rather than better tuning. Preserve physical simulator state across queries where the process is intended to persist, or label the reset model as a simplified scenario and add a persistent-state stress test. Keep noiseless tile caching separate from state-dependent effects.

For the QDarts fleet, define whether (1,1) success means an electrostatic reference cell, a dominant charge sector, or a specified charge-sector probability. Finite tunnel coupling can mix integer-charge configurations even at zero temperature. Reusing a strict integer equality on a thermal expectation would not implement the same task. Similarly, define consistent transition labels where the signal is rounded.

Specify a cumulative time model and a time cap for failure-penalized RF/DC comparisons. The primary pixel metric `min(T_success, B_pixels)` is well-defined. It cannot be converted into restricted mean seconds using one fixed per-pixel coefficient once setup, slew and line overhead depend on query history. Report actual time separately, or use a prespecified time-budget metric with failed runs charged that time budget.

**R8 — Medium: the protected scope remains large for 180 hours.**

The plan now protects a new lattice policy, reader, learned estimator, hierarchy inference, multiple baselines, two simulation environments, OOD tests, external annotations, a full quantum map, Aer IRB, and an IBM run. A small empirical-Bayes model is a useful simplification, but the unresolved tracker and anchor are central research work. The first sensor-only cost comparison should be a milestone in week 1–2, before committing to every protected branch.

The C2 timing estimate also assumes a computational shortcut that is not stated. Ten thousand points × one thousand noise draws gives ten million propagations. The check script uses 2,000 time slices per Hann pulse. Repeating that construction for every draw would require twenty billion small matrix exponentials; the proposed 1–3 core-hour budget needs benchmarking. Use vectorized analytic approximations over the map, validate selected regions with full propagation, or precompute and interpolate propagators with an error bound.

Protect the measurement interface, trusted reference, T★/strong classical baseline, cold/history-informed comparison, and frozen analysis. A minimal, labelled Qiskit Hamiltonian study can satisfy the required quantum component while the core result is established. Schedule IBM early and allow a documented fallback. Retain the larger map, estimator complexity, and secondary analyses only when a first end-to-end comparison leaves time for them.

**Evidence reproduced in this review**

The existing temporary `cz_pulse_check.py` reproduces Hann nominal infidelities approximately 4.7e−11, 3.7e−10, and 8.2e−11 at Jmax=5 MHz for its three Zeeman values, and approximately 1.2e−6 at Jmax=20 MHz, DeltaEz=63 MHz. The existing `cz_check.py` also reproduces the small-J/large-gradient distinction between pure-ZZ and CPhase errors. These are real checks of those particular conventions and points, rather than evidence that G4 holds across the full map.

The additional check used the same Hamiltonian, 2,000 midpoint time slices, nominal local-Z calibration, and fixed corrections under perturbed exchange. Its script is at `/private/tmp/spintune_v2_review_checks.py`. The repository should retain its own final version of these checks, environments, and outputs before using them in slides.

**Recommended decision**

Proceed with implementation after fixing R1–R4 in the experiment specification. Resolve the primary device mapping before claiming Equal1-specific fidelity of the simulator, and rewrite G4 before using it as a pass/fail gate. V2 supports a credible, measurable project; it does not yet establish that the warm start saves cost, that the headroom is sufficient, or that the stated confidence gates are attainable.
