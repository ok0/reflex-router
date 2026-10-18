# S1 independent verification (summary)

Summary of the verification report written for S1 by an independent verifier after the run. It recomputed the results from the published raw files with its own code. Numbers are copied unchanged.

## Result

PASS: all S1 acceptance criteria were satisfied, and the STOP cell follows mechanically from the frozen decision table.

## Independent recomputation

| Item | Method | Result |
|------|--------|--------|
| Part A verdict | Recomputed from `part_a_map.csv` with independent BFS, boundary and line-change code | gf_first 156/4096 = 3.81% < 5% -> A_FAIL |
| Part A map statistics | Same code | Counts G 156 / P 3827 / . 113 / T 0; one region each; boundary 57; max line changes 6; 1 of 128 lines with more than 2 changes. All equal the published statistics |
| Part B labels | Own paired bootstrap (10,000 resamples) on `part_b_results.csv` | X1, X2, L1, L2 effective labels all tie at P = 10 -> B_TIE |
| Combined cell | Spec decision table | A_FAIL + B_TIE = STOP; matches `report.md` section 1 |
| Validity checks | V1-V3 recomputed | V1: circuit 1.0061, formula 1.0035 of best constant (< 1.01); V2: C1 at P = 10 diff -0.46%, tie; V3: formula 4.5809 vs oracle 4.5660 |
| Fit budgets and flags | Report section 6 checked | Budgets circuit 4000 vs formula max 2008; X1, X2 flagged; MLP reference beats formula by 4.1% / 13.5% (recomputed) |
| Pre-registration | `git diff` of `spikes/`, `src/`, `circuit-data/` against the state at run time, and `git status` | Both empty; `run_meta.json` deviations `[]`; report states "no deviations" |
| Run setup | Hashes, environment, repeat run | circuit.json sha256 4ca62284... before, after and at verification; wall clock 508.6 s; network attempts 0; Brian2 not imported; two separate runs `cmp`-identical for all four raw files |
| Project checks at the time | Full test suite, spike tests, lint, type-check | 321 passed, 4 skipped; 12 spike tests passed; lint and type-check clean |

## Sensitivity notes (kept from the verification report)

- Part A is not a harness artifact in structure: outcomes are clean (one region each, 1/128 lines over 2 changes, spot-check and lookup agreement exact). The A_FAIL arises solely from the frozen 5% coverage rule: gf_first is 3.81% (156 cells, needs 205). It is a small corner (grid rows j 12-22, columns i 0-14, i.e. r_lc4 below about 6 Hz and r_lplc2 about 2.4-13.9 Hz) and the low-r_lc4 edge is not saturated (edge outcomes mixed, report says "capped: yes"), so the frozen 1-1000 Hz grid may cut off part of the GF region. The verdict is therefore sensitive to the grid/threshold: at 5% it would be A_PARTIAL -> REFRAME, not STOP. Frozen rule applied correctly, but this is the closest-call input.
- Part B: B_TIE depends on the sign-retention rule (s1_verdict.effective_label). X2 has a raw circuit WIN at P=10 (-3.47%, CI [-0.206,-0.142], recomputed) but the sign flips at P=30 (+0.47%, circuit worse) and is ~0 at P=3, so it is demoted to tie. That reading is faithful to the spec wording and was pre-registered in code, but a looser reading would give B_WIN -> A_FAIL + B_WIN = REFRAME. Even so, the circuit lost to the MLP by a wide margin on X2 (circuit 4.83 vs MLP 4.33 vs oracle 4.18) and X1 is a tie, so the circuit captures a small part of the available nonlinearity.
- Circuit-gate fit/harness: ties are not an issue (tie count 0 on the map). C1 control is degenerate (o* = -1.9, gf share 9.35% vs 50% target), so V2 passing is weak evidence that the circuit fit can recover a circuit-generated rule; N0/V1 and L1/V3 are valid. Circuit gate accepts rarely (reflex share 0.02-0.2 at P=10) because gf_first is a small stimulus region; the 64x64 lookup is exact vs direct simulation (200/200). Fit budget favours the circuit (4000 vs 2008).
- Conclusion: STOP is the correct mechanical outcome of the frozen rules and not a computational artifact, but it is a narrow STOP: it is close to REFRAME on two frozen-rule boundaries (5% coverage, X2 sign retention). Under these settings, no benefit of the circuit gate over the formula gate is established.
