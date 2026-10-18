# ADR-0003: S1 decision rules

## Status

Accepted. Recorded after the fact in M10; the decision was fixed by the frozen code `spikes/s1/s1_frozen.py` and `spikes/s1/s1_verdict.py` (sha256 recorded in `reports/s1/preregistration.md`), and is stated in `reports/s1/preregistration.md`.

## Context

S1 R1, R17 and R18 and AC1 require the rules to be fixed before the first run, and the verdict to be computed mechanically.

## Decision

Rules copied from `docs/report.md` section 3.2 (bullets "Part A rule", "Statistics", "Validity", "Combined table") and the cost model:

- Part A rule: A_PASS needs gf_first and parallel_first each to cover at least 5% of the grid, each with one connected region holding at least 80% of its points, and fewer than 20% of rows and columns with more than 2 outcome changes.
- Statistics: paired per-seed difference circuit minus formula, 95% bootstrap CI over seeds with 10,000 resamples. Circuit WIN if the mean relative difference is at most -2% and the CI upper bound is below 0; formula WIN if at least +2% and the CI lower bound is above 0; otherwise TIE. The verdict uses P = 10 base noise, with the sign retained at P = 3 and P = 30.
- Validity: V1 (N0: no gate beats the best constant by more than 1%), V2 (C1: circuit gate not a formula WIN), V3 (L1: formula within 2% of the oracle).
- Cost model: accept and correct = 1; accept and wrong = 1 + P; escalate = 5; P = 3, 10, 30, with base P = 10.
- Grid: 64 x 64 log-spaced, 1 Hz to 1000 Hz; dt 0.1 ms; window 100.0 ms.

Part A verdicts, from `reports/s1/preregistration.md` AC1:

- A_PARTIAL: gf_first covers at least 5% and a distinct non-GF-first outcome exists but fails one or more of the other A_PASS conditions; or the parallel group is absent, so only gf_first versus no_fire is available, but both cover at least 5% and are each one connected region.
- A_FAIL: anything else (for example no_fire on more than 95% of points, only one outcome present, or fragmented outcomes).

Part B verdicts, from `reports/s1/preregistration.md` AC1:

- B_WIN: circuit WIN in at least one of X1 or X2 (with the nonlinearity flag set), and no formula WIN in L1 or L2.
- B_LOSE: formula WIN in at least one of X1, X2, L1, L2, and no circuit WIN in X1 or X2.
- B_TIE: all of L1, L2, X1, X2 are TIE.
- B_MIXED: circuit WIN in X1 or X2 and formula WIN in L1 or L2.

Combined verdicts, from `reports/s1/preregistration.md` AC1:

- GO: A_PASS and B_WIN. GO (conditional, an ADR-5 revision is required to be filed) for A_PARTIAL and B_WIN.
- REFRAME: B_TIE or B_LOSE with A_PASS or A_PARTIAL; or B_MIXED with any Part A verdict; or A_FAIL with B_WIN; or circuit wins only in C1.
- STOP: A_FAIL with B_TIE or B_LOSE.
- INVALID (R18) overrides all cells when V1, V2 or V3 fails.

## Alternatives

- Post-hoc thresholds. Rejected by S1 R1: any change is a deviation.

## Consequences

The frozen verdict is STOP (A_FAIL, B_TIE), per `reports/s1/part_a_stats.json` and `reports/s1/part_b_summary.json`. No benefit established under these settings. `docs/report.md` item (b) discusses the 5% coverage reading.
