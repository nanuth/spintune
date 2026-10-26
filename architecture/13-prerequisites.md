[SpinTune v5 design](README.md) › 13. Prerequisites

# 13. Prerequisites, and which we can get ourselves

| # | Prerequisite | Needed for | Can we get it ourselves? | How / status |
|---|---|---|---|---|
| 1 | Main environment (Python 3.12, QArray, Qiskit stack, PyTorch; BoTorch only for T-BO) | Everything | **Yes** | Verified 25 Oct. Lockfile (`uv`) still to commit |
| 2 | QDarts environment | OOD-simulator fleet | **Yes, verified** | Runs on this Mac; wrap as a worker |
| 3 | Git repo with the check scripts | [§1.2](01-design-decisions-and-evidence.md#12-evidence-status-25-oct-2026) evidence, [§11.6](11-success-measurement.md#116-pre-registration) freeze | **Yes** | Scripts copied into `checks/` on 25 Oct, with a README. `git init` and the commit are still to do |
| 4 | Sourced device parameters | [§7](07-fleet.md) | **Yes, done** | Low confidence: σ_die, Δ_edge, σ_wafer, cross-coupling, SEB sensitivity |
| 5 | Equal1 device facts | [§3](03-scope-and-device-template.md) | **Mostly, done** | SEB + double-dot configuration verified against the paper on 25 Oct. Open: swept axes, how dot B loads, back-gate value, which platform Bell-1 uses |
| 6 | Real scans for external tests | [§7.6](07-fleet.md#76-external-real-device-data-sourced-none-is-22fdx) | **Partly** | QDSD (raw files 186 MB) and D-CSD (1.8 GB) are direct downloads; QFlow 2.0 needs registration (optional). Open a few raw files first and map their labels into the reader contract. We can also ask the CEA-Leti authors of [arXiv 2604.13662](https://arxiv.org/abs/2604.13662) |
| 7 | Compute | [§12](12-compute-plan.md) | **Yes** | Laptop for everything except the full spread map |
| 8 | Real quantum hardware | [§10.2](10-quantum-layer-qiskit.md#102-ibm-hardware-run-a-scheduled-demonstration-with-a-fallback) | **Yes** | IBM Open Plan: 10 min per rolling 28 days, us-east instance |
| 9 | Physics sanity review | [§8](08-physics-layer-cz-error-budget.md) | **Partly** | Analytic cross-checks done ([§1.2](01-design-decisions-and-evidence.md#12-evidence-status-25-oct-2026), [§8.2](08-physics-layer-cz-error-budget.md#82-cz-gate-model-measured-checks)). Equal1 judges at the pitch |
| 10 | Equal1 grouped tuning logs, scans and a timing breakdown | Sim-to-real; the fleet hypothesis | **No** | The structured request ([§14](14-questions-for-equal1.md) Q3–Q5). Nothing depends on it |
| 11 | R2P capstone or extra IBM access | Optional | **Unknown** | Ask the programme leads |

---

← [12. Compute plan](12-compute-plan.md) · [Index](README.md) · [14. Questions for Equal1](14-questions-for-equal1.md) →
