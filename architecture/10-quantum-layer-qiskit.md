[SpinTune v5 design](README.md) › 10. Quantum layer (Qiskit)

# 10. Quantum layer: what Qiskit does, and what the course materials give us

Qiskit use is required, so this layer is protected from cuts. The IBM hardware run is the one cuttable part.

## 10.1 Model-based CZ and RB (C2)

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

## 10.2 IBM hardware run (a scheduled demonstration with a fallback)

- **What:** our StandardRB + InterleavedRB code on one native two-qubit gate of an IBM Heron device, through the **Open Plan**: up to 10 min per **rolling 28-day window**, us-east only, set up as in course Lab 0.
- **Record:**
  - the physical pair, the transpiled circuits and the job IDs;
  - timestamps and whether the data can be analysed;
  - a *descriptive* comparison with the backend-reported two-qubit error, with the protocol and timestamp.
- **Why only descriptive:** IBM's published metric includes a single-qubit Clifford layer and may come from an earlier calibration ([IBM QPU information](https://quantum.cloud.ibm.com/docs/en/guides/qpu-information)). A disagreement triggers investigation; it does not fail the run.
- **What this shows:** that our benchmarking code runs end to end on real hardware. It says nothing about spin qubits, and is labelled that way.
- **Schedule:** develop on `FakeTorino`, submit by 13 Nov, use ≤ 3 QPU minutes.
- **Fallback:** the same code on the fake backend, plus any recorded run.

## 10.3 Course content deliberately not used

- **Quantum kernels / QSVM:** no evidence of benefit over a CNN; it would read as quantum for show.
- **QAOA, VQE, SQD:** no job to do. A two-site Hubbard model is solved exactly in microseconds.
- **Layer fidelity / EPLG:** reserved for the multi-cell stretch goal.

## 10.4 Pitch framing from the course

IBM's quantum-centric supercomputing material lists **calibration** among the classical tasks that "remain essential throughout the quantum workflow" (Unit 0, slide 69).

---

← [9. Drift](09-drift.md) · [Index](README.md) · [11. How success is measured](11-success-measurement.md) →
