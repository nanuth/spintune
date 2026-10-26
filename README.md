# SpinTune

**A benchmark and a reference tuner for charge tuning of CMOS spin-qubit cells. The question it tests: does chip history make tuning cheaper without more wrong charge declarations?**

Built for the Equal1 × Fsas "Compute the Future" hackathon (Timișoara HPC Hackathon, InnoWeek 2026). Idea pitch on Tue 27 Oct 2026, final demo on Fri 27 Nov 2026 at Qiskit Fall Fest.

> **Status: design stage.** No tuner has been built yet. The repo holds the design, its reviews and the feasibility scripts. Every number from `checks/` is an idealized estimate (noiseless simulated cells, a perfect reader, one specified policy), not a result.

## The idea

Equal1 builds qubits the way the chip industry builds chips: 29–35 quantum-dot cells per chip, many chips per wafer, one commercial 22 nm FD-SOI process. Every cell has to be tuned to a known electron count before it can hold a qubit, and at that scale nobody watches each cell. An unattended tuner has two jobs:

1. Spend little instrument time.
2. Rarely declare a cell ready when it isn't, at a rate that is measured rather than assumed.

SpinTune tests whether history (earlier cells on the same chip, and logs from earlier chips) can cut tuning cost without raising the wrong-declaration rate. It does this with:

- **An explicit evidence rule.** Before declaring a charge state, a tuner must show an empty region of the device with a few rays and one 2D window.
- **A reproducible benchmark.** Fixed simulated fleets, metered measurement queries and one scoring contract, so any tuner can be scored on its declared state, margin, cost, time and wrong-declaration rate.
- **A Qiskit CZ error-budget study.** A model of the two-qubit gate built from the device Hamiltonian, composing charge noise, dephasing and pulse error.

The full pitch, scope, non-claims and plan are in [`SpinTune_Design_v5.md`](SpinTune_Design_v5.md).

## Where to start

| If you want… | Read |
|---|---|
| The current design | [`SpinTune_Design_v5.md`](SpinTune_Design_v5.md) |
| The original pitch notes, Q&A prep and questions for Equal1 | [`SPINTUNE.md`](SPINTUNE.md) |
| The scripts behind every *[measured]* claim | [`checks/README.md`](checks/README.md) |
| The implementation checklist | [`bobi_resources/PLAN.md`](bobi_resources/PLAN.md) |

## Repository layout

```
.
├── SPINTUNE.md                       Original pitch notes
├── SpinTune_Design_Proposition.md    First design
├── SpinTune_Design_v2.md … v5.md     Design iterations (v5 is current)
├── FEASIBILITY_REVIEW.md             Review of the proposition
├── FEASIBILITY_REVIEW_V2.md          Review of v2
├── FEASIBILITY_REVIEW_V3.md          Review of v3
├── CROSS_REVIEW.md                   Teammate's plan vs the v2 design
├── bobi_resources/
│   ├── PLAN.md                       Implementation checklist
│   └── SPINTUNE-2.md                 Revised pitch notes
└── checks/                           Feasibility scripts (see checks/README.md)
```

Each design version supersedes the one before it and responds to the review in between. The v5 header lists its changes from v4.

## Running the checks

The scripts are quick feasibility checks, not product code. They need:

- **Python 3.12** with `qarray==1.6.0`, `qiskit==2.6.1`, `qiskit-aer==0.18.0`, `qiskit-experiments==0.14.2`, `torch` and `botorch`. QArray's Rust core has no wheel for Python 3.13 or later.
- **For `qdarts_check.py` only:** a separate Python 3.12 environment with `qdarts==1.0.5`, which pins `numpy<2`, `scipy<=1.12` and `cvxpy==1.5.2`.

Example, the main tuning-cost estimate (about 30 s on 14 cores):

```bash
cd checks
python headroom_v4.py anchor_check.py
```

[`checks/README.md`](checks/README.md) lists every script, what it shows, its flags and which design section it supports.

## What this does not claim

- It covers charge-state tuning of already-formed dots, not a working qubit.
- It does not prove a hardware tuner correct, establish a universal cost floor, or show savings on Equal1 devices.
- It makes no physical gate-fidelity claim, no quantum-advantage claim, and no claim about any commercial tuner.
- Everything is simulated until real device scans are available.
