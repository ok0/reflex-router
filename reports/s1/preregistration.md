# S1 pre-registration

**Binding pre-registration.** The binding pre-registration of S1 is the committed frozen code `spikes/s1/s1_frozen.py` (parameters, seeds, grid, costs, thresholds) and `spikes/s1/s1_verdict.py` (decision rules) with sha256 `dfb343f672dca9c5623bb6e0a9b2c1df49ea22c83a6bddd1143e978e445db9c2` and `f1da24d117d0e74f91457373b518e924aed107a67445bbe0f5e124487d1a6f01` respectively. The spec text below is the human-readable statement of the same rules.

Deviations: no deviations. Evidence: `run_meta.json` records `"deviations": []` and an empty `git status --porcelain -- spikes/s1` at run time; `report.md` section 2 states "no deviations"; the independent verification (`verification.md`) found no change under `spikes/`, `src/` and `circuit-data/` relative to their state at run time.

Reading notes: the spec text below is reproduced unchanged. The run wrote its outputs to a working directory that is not part of this repository; the published copies are in `reports/s1/`. Where the spec asks for the commit hash that contains the frozen rule (R1, AC2), this publication records the sha256 of the two frozen files instead. Milestone IDs (M6, M7, M11 and others), AC/PAC IDs, `charter` references and `open-issues.md` refer to the project's internal planning documents, which are not published.

---

# Spec: S1 — Go/no-go spike: does the circuit gate add anything over a formula gate?

### Overview
S1 is a non-roadmap spike that tests the project's core hypothesis cheaply before further spend (open-issues.md sections 2 and 3). Part A sweeps the (r_lc4, r_lplc2) stimulus space on the existing `circuit-data/v783/circuit.json` with the existing runtime simulator, to see whether distinct GF-first and parallel-first (or other non-GF-first) regions exist and how clean the boundary is. Part B compares the circuit gate with a formula gate on synthetic labelled signals, in scenarios where a nonlinear gate can plausibly win and where it cannot. A decision rule (GO / REFRAME / STOP) is fixed before any run. It advances charter R7, R8, R12, R35 and principles P1, P5, and informs the M7 decision map and the Gate 1 comparison (M11). The M6 long run stays held.

### Requirements

Common
- R1 (charter R35, P5). Pre-registration: the decision rule (AC1), scenario definitions, parameters, seeds, grid, costs and thresholds in this spec are frozen before the first S1 run. The report records the git commit that contains them. Any later deviation is listed in the report as a deviation, and the verdict is computed from the frozen rule.
- R2. Budget and isolation: the whole spike needs no API keys, no network, no Brian2 and no whole-brain simulation. Total compute is minutes (target at most 30 minutes wall-clock on the developer laptop; report the actual). `circuit.json` and its sha256 are not modified (report the hash before and after). M6 is not started.
- R3. Determinism: every run is seeded; rerunning with the same seeds gives identical numbers in the report.
- R4. Output: the single deliverable is `.ensemble/milestones/S1/report.md`, with raw result tables alongside it in the same directory (machine-readable, e.g. CSV or JSON).

Part A: decision map on the real circuit
- R5 (charter R7, R8). Report circuit facts that bound the gate: neuron count, the sizes of the `output_gf` and `output_parallel` groups, and the parallel DN types present. If there is no parallel group, say so, and treat the non-GF-first outcomes as `no_fire` plus any distinct output the simulator reports.
- R6. Sweep (r_lc4, r_lplc2) over a log-spaced grid of at least 25 x 25 points. The range is documented and must be wide enough to reach the circuit's saturation on both axes (stated as: the outermost rows and columns show a single stable outcome, or the report says the range was capped and why). Use the circuit's existing simulation window and time step. Record outcome per point (`gf_first`, `parallel_first`, `no_fire`, plus the simulator's no-parallel-group variants) and first-spike time(s).
- R7. Report: the fraction of grid points per outcome (including `no_fire`); for each outcome the number of connected regions (4-neighbour) and the size of the largest; the boundary length (count of adjacent grid pairs with different outcomes); and a cleanliness figure, namely the maximum number of outcome changes along any single row or column (monotone ordering of outcomes means at most 2 changes) and the fraction of rows/columns exceeding 2 changes.
- R8. Report whether outcome depends on both inputs (not only on one axis) and whether stimulating along the diagonal (r_lc4 = r_lplc2 raised together, a proxy for urgency) alone yields GF-first, without any other evidence (the M7 "urgency alone" concern).
- R9. A spot-check of determinism: at least 20 randomly chosen grid points are re-simulated and match exactly.

Part B: offline gate comparison on synthetic data
- R10. Signals (all free signals from flow.md variant B): cache similarity s in [0,1], request length L (log-normal, then normalised to [0,1]), risk class k in {0,1,2} (probabilities 0.5/0.3/0.2), latency budget b in [0,1] (uniform; tighter = smaller). The signal distributions, including correlations (s and L correlated at about -0.3), are documented and the same across scenarios.
- R11. Label: y = 1 if the reflex answer is correct (agrees with the deliberate answer), else 0. Labels are Bernoulli draws from a scenario-specific true probability p(signals). Scenarios (each with base label noise, plus a high-noise variant where p is pulled halfway towards 0.5):
  - N0 Null: p is a constant (0.7), independent of the signals. Neither gate may beat the best constant policy.
  - L1 Linear: logit p is a linear function of (s, L, k, b). Formula gate should tie or win.
  - L2 Monotone saturating: p is a monotone sigmoid of a single linear score, but with a steep step near one cut (nearly threshold-like). Formula should tie.
  - X1 Interaction (independent nonlinear): p is high only if s is high AND (L is short OR k = 0); otherwise low. Not generated from the circuit.
  - X2 Non-monotone / band (independent nonlinear): p is high when s is high and b is in a middle band (not too tight, not too generous), and low outside it; XOR-like on (s>0.5) vs (b>0.5) for k >= 1. Not generated from the circuit.
  - C1 Circuit-native (positive control): p derives from the circuit's own decision map (R6) applied to a fixed signal-to-stimulus mapping that differs from the one the fitting procedure starts from, plus label noise. This case is expected to favour the circuit and is reported as a harness sanity check, not as evidence for the hypothesis.
- R12. Costs (per request, in abstract units, documented): reflex accepted and correct = 1; reflex accepted and wrong = 1 + P (false-reflex penalty); escalated to deliberate = 5. Base P = 10; sensitivity runs at P = 3 and P = 30. Metric definitions: expected cost per request (primary); false-reflex rate (accepted-reflex requests that are wrong, per accepted reflex, reported first per P6); reflex share (fraction accepted); accuracy of the accept/escalate decision against the cost-optimal oracle decision implied by the true p.
- R13. Formula gate (charter R12): score = w . [s, L, k, b] + bias; accept reflex if score > threshold (bias and threshold are one degree of freedom, so only weights and one threshold are fit). Fit on the training set to minimise empirical expected cost (P-aware). Documented fitting procedure (for example logistic regression for weights, then threshold chosen on the training set by cost), same cross-fitted training data as the circuit gate.
- R14. Circuit gate: the fixed `circuit.json` and runtime simulator. Only the signal-to-stimulus mapping is fit (charter P3, A3): a fixed-form mapping with per-signal gain and offset (documented before the run) to (r_lc4, r_lplc2), with accept = GF-first and escalate = otherwise (parallel_first or no_fire). The circuit gate gets a fitting budget (number of candidate mappings evaluated and number of random restarts) at least equal to the formula gate's parameter-evaluation budget, and the report states both. The mapping search is run on training data only. Using the Part A map as a lookup for speed is permitted if agreement with direct simulation on at least 200 random points is reported.
- R15. Reference models (not gates under test; they show whether any nonlinearity is available per scenario): (i) the true-p oracle policy; (ii) one flexible nonlinear learner on the same inputs (for example gradient-boosted trees or a small MLP, the choice documented), fit on the same training data with a documented fixed hyperparameter setting; (iii) the best constant policy (always escalate, always reflex).
- R16. Fairness: both gates see exactly the same inputs, the same training and test sets, the same cost function and the same number of dataset seeds. Training size 2,000 and test size 20,000 per seed; 20 dataset seeds per scenario; the circuit gate's multi-restart seeds are fixed. A scenario is flagged "nonlinearity available" when the flexible learner (R15 ii) beats the formula gate by at least 2% relative expected cost in that scenario at base noise. Only "nonlinearity available" scenarios among X1 and X2 can count towards a circuit win. The report states, per scenario, whether the circuit was expected to be able to win.
- R17. Statistics: per scenario, report the paired per-seed difference in expected cost (circuit minus formula), the mean as a percentage of the formula cost, and a 95% bootstrap CI over seeds (at least 10,000 resamples). Define: circuit WIN if the mean relative difference is at most -2% and the CI upper bound is below 0; formula WIN if at least +2% and the CI lower bound is above 0; otherwise TIE. Also report false-reflex rate and reflex share for each gate, and false-reflex at matched reflex share (each gate refit with the reflex share constrained to within 2 points of 50%).
- R18. Harness validity checks (reported, evaluated before the verdict): V1: in N0 neither gate beats the best constant policy by more than 1% relative cost (otherwise suspect leakage). V2: in C1 the circuit gate is not a formula WIN (otherwise the fitting of the circuit gate is suspect: the harness cannot recover a circuit-generated rule). V3: in L1 the formula gate is within 2% of the oracle policy's cost excess (formula fitting works). If V1, V2 or V3 fails, the verdict is INVALID: fix the harness and rerun, with the rerun recorded as a deviation (R1). No verdict is issued from an INVALID run.

### Assumptions
- A1. Part A and Part B thresholds below (5%, 2%, 25 x 25, 20 seeds) are the Planner's choices; they are frozen by R1 and are the user's to override before the first run.
- A2. The existing runtime simulator and circuit loader are usable as-is for the sweep. If the circuit never fires anywhere in the sweep (all `no_fire`) this is a valid Part A finding (A-FAIL), not a defect to fix inside S1.
- A3. Synthetic cost units are abstract; absolute values are not claims about real pricing. Only comparisons between gates are interpreted.
- A4. Synthetic labels are a proxy. A circuit WIN here is necessary but not sufficient evidence for a benefit on real benchmark traces (that stays with M11); a TIE or LOSE is informative because the synthetic scenarios include cases built to favour nonlinear gates.
- A5. The stimulus mapping form for Part B is S1's own choice (fixed-form gain/offset), not the final project default (R8 / M9). The report notes that a different mapping form could change Part B results.
- A6. The verdict is a recommendation; the user makes the final go/no-go decision, including on the P-A race question.

### Out of Scope
- Whole-brain simulation, M6 robustness run, Brian2 validation of the runtime simulator (M7 criterion 1), any use of API keys, real LLM calls, real benchmark data.
- Changing `circuit.json`, the loader, the simulator or the charter/blueprint/roadmap (applying GO/REFRAME/STOP consequences, including the race demotion P-A, is a separate step after the verdict).
- Encoder design for production, calibration loop behaviour over time, latency overhead of the gate (R11), cascade or race cost accounting.
- Choosing a parallel DN set or evidence labelling (M5 / M19 work).

### Acceptance Criteria
AC1. Pre-registered decision rule (frozen before any run, per R1). Part A verdict, from R6-R8, evaluated on the frozen grid:
  - A-PASS: `gf_first` and a distinct non-GF-first firing outcome (`parallel_first`) each cover at least 5% of grid points, each has one connected region holding at least 80% of its points, and fewer than 20% of rows/columns have more than 2 outcome changes.
  - A-PARTIAL: `gf_first` covers at least 5% and a distinct non-GF-first outcome exists but fails one or more of the other A-PASS conditions, or the parallel group is absent so only `gf_first` versus `no_fire` is available but both cover at least 5% and are each one connected region.
  - A-FAIL: anything else (for example `no_fire` on more than 95% of points, or only one outcome present, or fragmented outcomes).
  Part B verdict, from R17 and the "nonlinearity available" flag (R16), at P = 10 base noise, with the sign of the result retained at P = 3 and P = 30:
  - B-WIN: circuit WIN in at least one of X1 or X2 (with the flag set), and no formula WIN in L1 or L2 (a formula WIN there means the circuit loses where nonlinearity cannot help, which is evidence against, not neutral).
  - B-LOSE: formula WIN in at least one of X1, X2, L1, L2, and no circuit WIN in X1 or X2.
  - B-TIE: all of L1, L2, X1, X2 are TIE.
  - B-MIXED: circuit WIN in X1 or X2 and formula WIN in L1 or L2.
  Combined verdict (INVALID per R18 overrides everything):
  - GO: A-PASS and B-WIN. Also GO (conditional, an ADR-5 revision is required to be filed) for A-PARTIAL and B-WIN.
  - REFRAME: B-TIE or B-LOSE with A-PASS or A-PARTIAL; or B-MIXED with any Part A verdict; or A-FAIL with B-WIN (win is not trusted without a two-sided decision); or circuit wins only in C1.
  - STOP: A-FAIL with B-TIE or B-LOSE.
  The report applies this table mechanically and states the cell reached. A reframe or stop consequence for the project goal (cost-saving claim dropped, negative result published per P5) is proposed in the report but not applied.
AC2. (R1) The report cites the commit hash containing this frozen rule and states "no deviations" or lists each deviation with reason; a deviation that changes thresholds or scenarios makes the verdict non-binding until the user confirms.
AC3. (R2, R3) The report shows the circuit.json sha256 before and after (identical), the actual wall-clock time, the environment (no keys, no network, no Brian2 imports), and rerunning the sweep and Part B comparison with the same seeds reproduces the report tables exactly.
AC4. (R5) The report lists circuit neuron count, `output_gf` and `output_parallel` group sizes and parallel DN types, or states the parallel group is absent.
AC5. (R6, R7) The report contains the decision map (image or table) over at least 25 x 25 points, with per-outcome fractions including `no_fire`, region counts and largest-region sizes, boundary length, and the row/column outcome-change statistics.
AC6. (R8, R9) The report states whether the outcome depends on both inputs, whether the diagonal alone yields GF-first, and that the determinism spot-check of at least 20 points matched.
AC7. (R10-R12) The report documents the signal distributions, all six scenarios with their p(signals) definitions, the high-noise variants, and the cost model with P = 3, 10, 30.
AC8. (R13-R16) The report documents both fitting procedures, the circuit gate's mapping form and fitting budget versus the formula gate's, the reference models, sample sizes, seed counts, and the "nonlinearity available" flag per scenario.
AC9. (R17) A results table per scenario and P value lists, for circuit, formula, flexible learner, constants and oracle: expected cost, false-reflex rate, reflex share, decision accuracy, the paired difference with its 95% bootstrap CI, the WIN/TIE label, and the matched-reflex-share false-reflex rates.
AC10. (R18) The report shows the V1, V2, V3 checks as pass/fail; the verdict is INVALID if any fails, otherwise the AC1 table cell is reported as GO, REFRAME or STOP, with a plain-language paragraph on what the result means for the circuit's usefulness over a formula gate and a note of the A4 and A5 limits.
