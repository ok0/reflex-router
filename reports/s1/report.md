# S1 go/no-go spike report

## 1 Verdict

Combined cell: **STOP**

- Part A verdict (AC1 on the frozen grid): A_FAIL
- Part B verdict (AC1, base noise, P = 10): B_TIE
- V1 (N0: neither gate beats the best constant by more than 1%): PASS
- V2 (C1: circuit gate not a formula WIN): PASS
- V3 (L1: formula within 2% of oracle cost): PASS
- Validity: valid

Cell text: STOP: Part A fails (AC1) and Part B shows no circuit win.

On these synthetic tests the circuit gate adds nothing over a formula gate in the scenarios where a nonlinear gate could help, and the circuit map does not give distinct, clean outcome regions. This is a negative result. Any cost-saving claim that depends on the circuit gate would need to be dropped, subject to the user's decision.

Limits. A4: the labels are a synthetic proxy; a circuit WIN here is necessary but not sufficient evidence for a benefit on real benchmark traces (that stays with M11). A5: the stimulus mapping form is S1's own fixed-form gain and offset, not the project default (R8 / M9); a different mapping form could change the Part B results.

## 2 Pre-registration

- Frozen rule files (sha256): `spikes/s1/s1_frozen.py` dfb343f672dca9c5623bb6e0a9b2c1df49ea22c83a6bddd1143e978e445db9c2; `spikes/s1/s1_verdict.py` f1da24d117d0e74f91457373b518e924aed107a67445bbe0f5e124487d1a6f01
- Working tree of spikes/s1 at run time: clean
- Deviations: no deviations

## 3 Run setup

- circuit.json sha256 before: 4ca62284d2831f01228e2d0f8a71fdfce78a0b26674cb1bbccf537f487263d91
- circuit.json sha256 after: 4ca62284d2831f01228e2d0f8a71fdfce78a0b26674cb1bbccf537f487263d91
- Identical before and after: yes
- Wall-clock: 508.6 s (target at most 1800 s, within target)
- Env access in spikes/s1: none
- Network attempts: 0
- brian2 imported: no
- Python: 3.14.8 (main, Oct  9 2026, 15:11:09) [Clang 22.1.3 ]
- numpy: 2.5.4; platform: macOS-15.7.7-arm64-arm-64bit-Mach-O
- Repro check against the earlier run (byte-identical):
  - part_a_map.csv: true
  - part_a_stats.json: true
  - part_b_results.csv: true
  - part_b_summary.json: true

## 4 Circuit facts

- Neurons: 1231
- Connections: 10641
- output_gf group size: 2 (types {'DNp01': 2})
- output_parallel group size: 17
- Parallel DN types (10): {'DNg40': 2, 'DNp02': 2, 'DNp03': 1, 'DNp04': 2, 'DNp05': 2, 'DNp06': 2, 'DNp103': 2, 'DNp11': 2, 'DNp35': 1, 'DNpe025': 1}

## 5 Part A map

Grid 64 x 64, log-spaced rates from 1.0 Hz to 1000.0 Hz on both axes. Rows are r_lplc2 (top = highest), columns are r_lc4 (left = lowest). Legend: G gf_first, P parallel_first, T tie, . no_fire.

```
  1000.0 |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
   464.2 |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
   193.1 |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
    80.3 |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
    33.4 |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
    13.9 |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |GGGGGGGGGGGGGGGPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |GGGGGGGGGGGGGGGPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |GGGGGGGGGGGGGGGPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |GGGGGGGGGGGGGGGPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |GGGGGGGGGGGGGGGPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |GGGGGGGGGGGGGGPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
     5.8 |GGGGGGGGGGGGGGPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |GGGGGGGGGGGGGGPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |GGGGGGGGGGGGGPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |GGGGGGGGGGGGGPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |GGGGGGGGGGGGGPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |..........PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |..........PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |..........PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
     2.4 |.........PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |.........PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |.........PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |.........PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |..........PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |.........PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |.........PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
         |.........PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
     1.0 |..........PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP|
```

Part A verdict: A_FAIL

| outcome | count | fraction | regions | largest | largest share |
|---|---:|---:|---:|---:|---:|
| gf_first | 156 | 0.0381 | 1 | 156 | 1.0000 |
| parallel_first | 3827 | 0.9343 | 1 | 3827 | 1.0000 |
| tie | 0 | 0.0000 | 0 | 0 | 0.0000 |
| no_fire | 113 | 0.0276 | 1 | 113 | 1.0000 |

- Boundary length (adjacent pairs with different outcomes): 57
- Max outcome changes on any row or column: 6
- Lines over 2 changes: 1 of 128 (fraction 0.0078)

Supplementary (tie merged into parallel_first; not used for the verdict):

| outcome | count | fraction | regions | largest | largest share |
|---|---:|---:|---:|---:|---:|
| gf_first | 156 | 0.0381 | 1 | 156 | 1.0000 |
| parallel_first | 3827 | 0.9343 | 1 | 3827 | 1.0000 |
| tie | 0 | 0.0000 | 0 | 0 | 0.0000 |
| no_fire | 113 | 0.0276 | 1 | 113 | 1.0000 |

- Boundary length (merged): 57; max changes 6; fraction over 2 0.0078

- Edge saturation: lc4_min ['gf_first', 'no_fire', 'parallel_first'], lc4_max ['parallel_first'], lplc2_min ['no_fire', 'parallel_first'], lplc2_max ['parallel_first'].
- Capped: yes (the outer rows or columns are not all single-outcome)
- Outcome depends on both inputs: yes (rows varying along r_lc4: 23; columns varying along r_lplc2: 15)
- Diagonal (r_lc4 = r_lplc2) outcomes: ..........PPGPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP; GF-first on the diagonal alone: yes (first at 3.73 Hz)
- Determinism spot-check: 20 of 20 re-simulated points match exactly (all match)
- Lookup agreement with direct simulation: 200 of 200 (1.0000)

## 6 Part B setup

Signals (R10): s = Gaussian-copula marginal in [0,1]; L = log-normal (mu log 400, sigma 1) clipped to [log 20, log 20000] and normalised to [0,1]; copula correlation rho = -0.31 between the Gaussian pair; k in {0,1,2} with probabilities (0.5, 0.3, 0.2); b uniform on [0,1]. The same signals are used across scenarios for a given seed.

Measured summary (seed 0, train n = 2000; test n = 20000):

- Train: mean s 0.5016, mean L 0.4330, mean b 0.4924, k proportions ['0.4990', '0.2960', '0.2050'], corr(s, L) -0.2662
- Test: corr(s, L) -0.2933, k proportions ['0.5014', '0.2995', '0.1990']

Scenarios (R11). Base noise uses p as defined; high noise uses p' = 0.5 + 0.5 * (p - 0.5) (pulled halfway to 0.5).

- N0: Null: p = 0.7 for every request, independent of the signals.
- L1: Linear: logit p = 0.5 + 3.0*(s-0.5) + -2.0*(L-0.3) + -0.8*k + 1.5*(b-0.5).
- L2: Monotone saturating: u = 1.0*s + -0.5*L + -0.2*k, p = 0.15 + 0.75*sigmoid(40.0*(u-0.15)).
- X1: Interaction (independent of the circuit): p = 0.85 if s > 0.6 and (L < 0.35 or k = 0), else 0.25.
- X2: Band (independent of the circuit): for k = 0, p = 0.85 if 0.3 < b < 0.7 and s > 0.6; for k >= 1, p = 0.85 if (s > 0.5) XOR (b > 0.5); otherwise 0.25.
- C1: Circuit-native control: p = 0.85 if the circuit map under the C1 mapping (lc4 gains (2.0, -1.0, 0.0, 0.5), lplc2 gains (-1.0, 1.0, 1.0, 0.0), lplc2 offset 1.5, lc4 offset o*) gives gf_first, else 0.25. Expected to favour the circuit; a harness check, not evidence for the hypothesis.

Cost model (R12): accept and correct = 1; accept and wrong = 1 + P; escalate = 5. Expected cost uses true p on the test set. P values (3.0, 10.0, 30.0), base P = 10. At P = 3 accepting the reflex is always cost-optimal (1 + 3 < 5), so every sensible gate converges to always-reflex; P = 3 is a sensitivity check only.

Formula gate (R13): logistic regression with intercept (L2 1e-4 on the weights, Newton-IRLS, at most 100 iterations) on [s, L, k, b]. Threshold chosen on the training set by empirical cost (free) and as the median split of the training scores (matched: top half accepted). Budget = iterations + threshold candidates; maximum over all fits: 2008.

Circuit gate (R14): fixed circuit.json and LIFSimulator (dt 0.1 ms, window 100.0 ms). Mapping on fc = [s, L, k/2, b]: x1 = clip(theta[4] + fc . theta[0:4], 0, 3) for log10 r_lc4 and x2 = clip(theta[9] + fc . theta[5:9], 0, 3) for log10 r_lplc2; accept = gf_first, escalate otherwise, read from the 64 x 64 map (lookup, agreement in section 5). Fit: (1+1)-ES with 8 restarts x 500 evaluations, budget 4000 candidate mappings. Restart 0 starts from the fixed start; the others from uniform random starts. Matched variant: objective penalised unless the accept share is within 2 points of 50%. The mapping is fit on training data only.

Budget comparison: circuit 4000 vs formula maximum 2008; the circuit budget is at least the formula budget.

Flexible learner (R15 ii): numpy MLP, one tanh hidden layer of 16, sigmoid output, BCE with L2 1e-4, full-batch Adam (lr 0.01, betas 0.9/0.999, eps 1e-8), 3000 steps, init N(0, 1/sqrt(fan_in)), on [s, L, k/2, b]. Thresholds are chosen as for the formula gate. The true-p oracle and the best constant policy (always reflex, always escalate) are reference models, not gates under test.

Sizes and seeds: train 2000, test 20000, 20 dataset seeds per scenario and noise level. Labels are Bernoulli draws from p on the training set only; test metrics use true p.

C1 offset rule (frozen): among offsets -3.0 to 3.0 in steps of 0.1, pick the one whose gf_first share on 100000 reference signals is closest to 50%; ties to smaller |o|, then smaller o. Result: o* = -1.9, gf_first share 0.0935, degenerate: yes (V2 is weak in this case).

Nonlinearity flag (R16): set for a scenario when the MLP beats the formula gate by at least 2% relative expected cost at P = 10, base noise.

| scenario | nonlinearity available | expected to be able to win |
|---|---|---|
| N0 | no | no |
| L1 | no | no |
| L2 | no | no |
| X1 | yes | yes, iff the nonlinearity flag is set |
| X2 | yes | yes, iff the nonlinearity flag is set |
| C1 | no | control (expected to favour the circuit) |

## 7 Results

Free variants unless stated; means over seeds. False-reflex is the share of accepted reflexes that are wrong (true p). The oracle and the constants have no fitted threshold and are recorded once under free.

### N0, base noise, P = 3

| model | expected cost | false-reflex | reflex share | decision acc |
|---|---:|---:|---:|---:|
| circuit | 1.9005 | 0.3000 | 0.9998 | 0.9998 |
| formula | 1.9000 | 0.3000 | 1.0000 | 1.0000 |
| mlp | 1.9000 | 0.3000 | 1.0000 | 1.0000 |
| const_reflex | 1.9000 | 0.3000 | 1.0000 | 1.0000 |
| const_escalate | 5.0000 | n/a | 0.0000 | 0.0000 |
| oracle | 1.9000 | 0.3000 | 1.0000 | 1.0000 |

Circuit minus formula: mean diff 0.0005, relative +0.03%, 95% CI [0.0001, 0.0010], raw label tie.

Matched reflex share (each gate refit with the share within 2 points of 50%):

| model | false-reflex | reflex share | circuit fit feasible (seeds) |
|---|---:|---:|---:|
| circuit | 0.3000 | 0.5157 | 20/20 |
| formula | 0.3000 | 0.5028 | n/a |
| mlp | 0.3000 | 0.5004 | n/a |

### N0, base noise, P = 10

| model | expected cost | false-reflex | reflex share | decision acc |
|---|---:|---:|---:|---:|
| circuit | 4.0245 | 0.3000 | 0.9755 | 0.9755 |
| formula | 4.0139 | 0.3000 | 0.9861 | 0.9861 |
| mlp | 4.0438 | 0.3000 | 0.9562 | 0.9562 |
| const_reflex | 4.0000 | 0.3000 | 1.0000 | 1.0000 |
| const_escalate | 5.0000 | n/a | 0.0000 | 0.0000 |
| oracle | 4.0000 | 0.3000 | 1.0000 | 1.0000 |

Circuit minus formula: mean diff 0.0106, relative +0.26%, 95% CI [0.0046, 0.0162], raw label tie.
Effective label (P = 3 and P = 30 sign check, flag applied): tie.

Matched reflex share (each gate refit with the share within 2 points of 50%):

| model | false-reflex | reflex share | circuit fit feasible (seeds) |
|---|---:|---:|---:|
| circuit | 0.3000 | 0.5123 | 20/20 |
| formula | 0.3000 | 0.5028 | n/a |
| mlp | 0.3000 | 0.5004 | n/a |

### N0, base noise, P = 30

| model | expected cost | false-reflex | reflex share | decision acc |
|---|---:|---:|---:|---:|
| circuit | 5.0600 | 0.3000 | 0.0120 | 0.9880 |
| formula | 5.0258 | 0.3000 | 0.0052 | 0.9948 |
| mlp | 5.0428 | 0.3000 | 0.0086 | 0.9914 |
| const_reflex | 10.0000 | 0.3000 | 1.0000 | 0.0000 |
| const_escalate | 5.0000 | n/a | 0.0000 | 1.0000 |
| oracle | 5.0000 | n/a | 0.0000 | 1.0000 |

Circuit minus formula: mean diff 0.0343, relative +0.68%, 95% CI [0.0187, 0.0485], raw label tie.

Matched reflex share (each gate refit with the share within 2 points of 50%):

| model | false-reflex | reflex share | circuit fit feasible (seeds) |
|---|---:|---:|---:|
| circuit | 0.3000 | 0.4884 | 20/20 |
| formula | 0.3000 | 0.5028 | n/a |
| mlp | 0.3000 | 0.5004 | n/a |

### N0, high noise, P = 3

| model | expected cost | false-reflex | reflex share | decision acc |
|---|---:|---:|---:|---:|
| circuit | 2.2003 | 0.4000 | 0.9999 | 0.9999 |
| formula | 2.2000 | 0.4000 | 1.0000 | 1.0000 |
| mlp | 2.2000 | 0.4000 | 1.0000 | 1.0000 |
| const_reflex | 2.2000 | 0.4000 | 1.0000 | 1.0000 |
| const_escalate | 5.0000 | n/a | 0.0000 | 0.0000 |
| oracle | 2.2000 | 0.4000 | 1.0000 | 1.0000 |

Circuit minus formula: mean diff 0.0003, relative +0.01%, 95% CI [0.0001, 0.0006], raw label tie.

Matched reflex share (each gate refit with the share within 2 points of 50%):

| model | false-reflex | reflex share | circuit fit feasible (seeds) |
|---|---:|---:|---:|
| circuit | 0.4000 | 0.5195 | 20/20 |
| formula | 0.4000 | 0.5008 | n/a |
| mlp | 0.4000 | 0.5015 | n/a |

### N0, high noise, P = 10

| model | expected cost | false-reflex | reflex share | decision acc |
|---|---:|---:|---:|---:|
| circuit | 5.0000 | 0.4000 | 0.2373 | 0.7627 |
| formula | 5.0000 | 0.4000 | 0.5605 | 0.4395 |
| mlp | 5.0000 | 0.4000 | 0.5390 | 0.4610 |
| const_reflex | 5.0000 | 0.4000 | 1.0000 | 0.0000 |
| const_escalate | 5.0000 | n/a | 0.0000 | 1.0000 |
| oracle | 5.0000 | n/a | 0.0000 | 1.0000 |

Circuit minus formula: mean diff 0.0000, relative +0.00%, 95% CI [0.0000, 0.0000], raw label tie.
Effective label (P = 3 and P = 30 sign check, flag applied): tie.

Matched reflex share (each gate refit with the share within 2 points of 50%):

| model | false-reflex | reflex share | circuit fit feasible (seeds) |
|---|---:|---:|---:|
| circuit | 0.4000 | 0.4959 | 20/20 |
| formula | 0.4000 | 0.5008 | n/a |
| mlp | 0.4000 | 0.5015 | n/a |

### N0, high noise, P = 30

| model | expected cost | false-reflex | reflex share | decision acc |
|---|---:|---:|---:|---:|
| circuit | 5.0644 | 0.4000 | 0.0081 | 0.9919 |
| formula | 5.0072 | 0.4000 | 0.0009 | 0.9991 |
| mlp | 5.0326 | 0.4000 | 0.0041 | 0.9959 |
| const_reflex | 13.0000 | 0.4000 | 1.0000 | 0.0000 |
| const_escalate | 5.0000 | n/a | 0.0000 | 1.0000 |
| oracle | 5.0000 | n/a | 0.0000 | 1.0000 |

Circuit minus formula: mean diff 0.0572, relative +1.14%, 95% CI [0.0483, 0.0665], raw label tie.

Matched reflex share (each gate refit with the share within 2 points of 50%):

| model | false-reflex | reflex share | circuit fit feasible (seeds) |
|---|---:|---:|---:|
| circuit | 0.4000 | 0.4849 | 20/20 |
| formula | 0.4000 | 0.5008 | n/a |
| mlp | 0.4000 | 0.5015 | n/a |

### L1, base noise, P = 3

| model | expected cost | false-reflex | reflex share | decision acc |
|---|---:|---:|---:|---:|
| circuit | 2.6811 | 0.5603 | 0.9999 | 0.9999 |
| formula | 2.6809 | 0.5603 | 1.0000 | 1.0000 |
| mlp | 2.6809 | 0.5603 | 1.0000 | 1.0000 |
| const_reflex | 2.6809 | 0.5603 | 1.0000 | 1.0000 |
| const_escalate | 5.0000 | n/a | 0.0000 | 0.0000 |
| oracle | 2.6809 | 0.5603 | 1.0000 | 1.0000 |

Circuit minus formula: mean diff 0.0002, relative +0.01%, 95% CI [0.0001, 0.0005], raw label tie.

Matched reflex share (each gate refit with the share within 2 points of 50%):

| model | false-reflex | reflex share | circuit fit feasible (seeds) |
|---|---:|---:|---:|
| circuit | 0.4107 | 0.5170 | 20/20 |
| formula | 0.3524 | 0.5028 | n/a |
| mlp | 0.3548 | 0.5032 | n/a |

### L1, base noise, P = 10

| model | expected cost | false-reflex | reflex share | decision acc |
|---|---:|---:|---:|---:|
| circuit | 4.6618 | 0.2384 | 0.2123 | 0.8892 |
| formula | 4.5809 | 0.2420 | 0.2715 | 0.9544 |
| mlp | 4.5891 | 0.2539 | 0.2890 | 0.9425 |
| const_reflex | 6.6029 | 0.5603 | 1.0000 | 0.2967 |
| const_escalate | 5.0000 | n/a | 0.0000 | 0.7033 |
| oracle | 4.5660 | 0.2537 | 0.2967 | 1.0000 |

Circuit minus formula: mean diff 0.0809, relative +1.77%, 95% CI [0.0518, 0.1169], raw label tie.
Effective label (P = 3 and P = 30 sign check, flag applied): tie.

Matched reflex share (each gate refit with the share within 2 points of 50%):

| model | false-reflex | reflex share | circuit fit feasible (seeds) |
|---|---:|---:|---:|
| circuit | 0.3733 | 0.4876 | 20/20 |
| formula | 0.3524 | 0.5028 | n/a |
| mlp | 0.3548 | 0.5032 | n/a |

### L1, base noise, P = 30

| model | expected cost | false-reflex | reflex share | decision acc |
|---|---:|---:|---:|---:|
| circuit | 5.0130 | 0.1586 | 0.0269 | 0.9664 |
| formula | 4.9847 | 0.1090 | 0.0437 | 0.9791 |
| mlp | 4.9990 | 0.1191 | 0.0498 | 0.9713 |
| const_reflex | 17.8087 | 0.5603 | 1.0000 | 0.0346 |
| const_escalate | 5.0000 | n/a | 0.0000 | 0.9654 |
| oracle | 4.9684 | 0.1030 | 0.0346 | 1.0000 |

Circuit minus formula: mean diff 0.0282, relative +0.57%, 95% CI [0.0136, 0.0405], raw label tie.

Matched reflex share (each gate refit with the share within 2 points of 50%):

| model | false-reflex | reflex share | circuit fit feasible (seeds) |
|---|---:|---:|---:|
| circuit | 0.3744 | 0.4861 | 20/20 |
| formula | 0.3524 | 0.5028 | n/a |
| mlp | 0.3548 | 0.5032 | n/a |

### L1, high noise, P = 3

| model | expected cost | false-reflex | reflex share | decision acc |
|---|---:|---:|---:|---:|
| circuit | 2.5905 | 0.5301 | 1.0000 | 1.0000 |
| formula | 2.5904 | 0.5301 | 1.0000 | 1.0000 |
| mlp | 2.5904 | 0.5301 | 1.0000 | 1.0000 |
| const_reflex | 2.5904 | 0.5301 | 1.0000 | 1.0000 |
| const_escalate | 5.0000 | n/a | 0.0000 | 0.0000 |
| oracle | 2.5904 | 0.5301 | 1.0000 | 1.0000 |

Circuit minus formula: mean diff 0.0001, relative +0.00%, 95% CI [0.0000, 0.0002], raw label tie.

Matched reflex share (each gate refit with the share within 2 points of 50%):

| model | false-reflex | reflex share | circuit fit feasible (seeds) |
|---|---:|---:|---:|
| circuit | 0.4593 | 0.5175 | 20/20 |
| formula | 0.4273 | 0.5018 | n/a |
| mlp | 0.4317 | 0.5032 | n/a |

### L1, high noise, P = 10

| model | expected cost | false-reflex | reflex share | decision acc |
|---|---:|---:|---:|---:|
| circuit | 4.9630 | 0.3591 | 0.0941 | 0.8654 |
| formula | 4.9220 | 0.3528 | 0.1960 | 0.9341 |
| mlp | 4.9311 | 0.3557 | 0.1868 | 0.9157 |
| const_reflex | 6.3015 | 0.5301 | 1.0000 | 0.1905 |
| const_escalate | 5.0000 | n/a | 0.0000 | 0.8095 |
| oracle | 4.9045 | 0.3499 | 0.1905 | 1.0000 |

Circuit minus formula: mean diff 0.0410, relative +0.83%, 95% CI [0.0287, 0.0531], raw label tie.
Effective label (P = 3 and P = 30 sign check, flag applied): tie.

Matched reflex share (each gate refit with the share within 2 points of 50%):

| model | false-reflex | reflex share | circuit fit feasible (seeds) |
|---|---:|---:|---:|
| circuit | 0.4393 | 0.4833 | 20/20 |
| formula | 0.4273 | 0.5018 | n/a |
| mlp | 0.4317 | 0.5032 | n/a |

### L1, high noise, P = 30

| model | expected cost | false-reflex | reflex share | decision acc |
|---|---:|---:|---:|---:|
| circuit | 5.0439 | 0.3653 | 0.0071 | 0.9929 |
| formula | 5.0183 | 0.2809 | 0.0038 | 0.9962 |
| mlp | 5.0314 | 0.3077 | 0.0059 | 0.9941 |
| const_reflex | 16.9044 | 0.5301 | 1.0000 | 0.0000 |
| const_escalate | 5.0000 | n/a | 0.0000 | 1.0000 |
| oracle | 5.0000 | n/a | 0.0000 | 1.0000 |

Circuit minus formula: mean diff 0.0256, relative +0.51%, 95% CI [0.0080, 0.0403], raw label tie.

Matched reflex share (each gate refit with the share within 2 points of 50%):

| model | false-reflex | reflex share | circuit fit feasible (seeds) |
|---|---:|---:|---:|
| circuit | 0.4503 | 0.4836 | 20/20 |
| formula | 0.4273 | 0.5018 | n/a |
| mlp | 0.4317 | 0.5032 | n/a |

### L2, base noise, P = 3

| model | expected cost | false-reflex | reflex share | decision acc |
|---|---:|---:|---:|---:|
| circuit | 2.4373 | 0.4789 | 0.9998 | 0.9998 |
| formula | 2.4368 | 0.4789 | 1.0000 | 1.0000 |
| mlp | 2.4368 | 0.4789 | 1.0000 | 1.0000 |
| const_reflex | 2.4368 | 0.4789 | 1.0000 | 1.0000 |
| const_escalate | 5.0000 | n/a | 0.0000 | 0.0000 |
| oracle | 2.4368 | 0.4789 | 1.0000 | 1.0000 |

Circuit minus formula: mean diff 0.0006, relative +0.02%, 95% CI [0.0002, 0.0013], raw label tie.

Matched reflex share (each gate refit with the share within 2 points of 50%):

| model | false-reflex | reflex share | circuit fit feasible (seeds) |
|---|---:|---:|---:|
| circuit | 0.1898 | 0.5158 | 20/20 |
| formula | 0.1356 | 0.5019 | n/a |
| mlp | 0.1325 | 0.5021 | n/a |

### L2, base noise, P = 10

| model | expected cost | false-reflex | reflex share | decision acc |
|---|---:|---:|---:|---:|
| circuit | 3.7340 | 0.1222 | 0.4554 | 0.9515 |
| formula | 3.6644 | 0.1250 | 0.4860 | 0.9763 |
| mlp | 3.6497 | 0.1216 | 0.4854 | 0.9832 |
| const_reflex | 5.7892 | 0.4789 | 1.0000 | 0.4850 |
| const_escalate | 5.0000 | n/a | 0.0000 | 0.5150 |
| oracle | 3.6343 | 0.1184 | 0.4850 | 1.0000 |

Circuit minus formula: mean diff 0.0696, relative +1.90%, 95% CI [0.0176, 0.1327], raw label tie.
Effective label (P = 3 and P = 30 sign check, flag applied): tie.

Matched reflex share (each gate refit with the share within 2 points of 50%):

| model | false-reflex | reflex share | circuit fit feasible (seeds) |
|---|---:|---:|---:|
| circuit | 0.1557 | 0.4965 | 20/20 |
| formula | 0.1356 | 0.5019 | n/a |
| mlp | 0.1325 | 0.5021 | n/a |

### L2, base noise, P = 30

| model | expected cost | false-reflex | reflex share | decision acc |
|---|---:|---:|---:|---:|
| circuit | 4.8678 | 0.1072 | 0.1597 | 0.7261 |
| formula | 4.6348 | 0.1027 | 0.4005 | 0.9610 |
| mlp | 4.6505 | 0.1021 | 0.3763 | 0.9405 |
| const_reflex | 15.3675 | 0.4789 | 1.0000 | 0.4226 |
| const_escalate | 5.0000 | n/a | 0.0000 | 0.5774 |
| oracle | 4.6015 | 0.1019 | 0.4226 | 1.0000 |

Circuit minus formula: mean diff 0.2330, relative +5.03%, 95% CI [0.1890, 0.2729], raw label formula_win.

Matched reflex share (each gate refit with the share within 2 points of 50%):

| model | false-reflex | reflex share | circuit fit feasible (seeds) |
|---|---:|---:|---:|
| circuit | 0.1606 | 0.4862 | 20/20 |
| formula | 0.1356 | 0.5019 | n/a |
| mlp | 0.1325 | 0.5021 | n/a |

### L2, high noise, P = 3

| model | expected cost | false-reflex | reflex share | decision acc |
|---|---:|---:|---:|---:|
| circuit | 2.4686 | 0.4895 | 0.9999 | 0.9999 |
| formula | 2.4684 | 0.4895 | 1.0000 | 1.0000 |
| mlp | 2.4684 | 0.4895 | 1.0000 | 1.0000 |
| const_reflex | 2.4684 | 0.4895 | 1.0000 | 1.0000 |
| const_escalate | 5.0000 | n/a | 0.0000 | 0.0000 |
| oracle | 2.4684 | 0.4895 | 1.0000 | 1.0000 |

Circuit minus formula: mean diff 0.0002, relative +0.01%, 95% CI [0.0001, 0.0004], raw label tie.

Matched reflex share (each gate refit with the share within 2 points of 50%):

| model | false-reflex | reflex share | circuit fit feasible (seeds) |
|---|---:|---:|---:|
| circuit | 0.3730 | 0.5140 | 20/20 |
| formula | 0.3240 | 0.5032 | n/a |
| mlp | 0.3210 | 0.5021 | n/a |

### L2, high noise, P = 10

| model | expected cost | false-reflex | reflex share | decision acc |
|---|---:|---:|---:|---:|
| circuit | 4.7098 | 0.3088 | 0.3196 | 0.8303 |
| formula | 4.6017 | 0.3096 | 0.4425 | 0.9430 |
| mlp | 4.5950 | 0.3100 | 0.4516 | 0.9510 |
| const_reflex | 5.8946 | 0.4895 | 1.0000 | 0.4708 |
| const_escalate | 5.0000 | n/a | 0.0000 | 0.5292 |
| oracle | 4.5563 | 0.3058 | 0.4708 | 1.0000 |

Circuit minus formula: mean diff 0.1081, relative +2.35%, 95% CI [0.0716, 0.1430], raw label formula_win.
Effective label (P = 3 and P = 30 sign check, flag applied): formula_win.

Matched reflex share (each gate refit with the share within 2 points of 50%):

| model | false-reflex | reflex share | circuit fit feasible (seeds) |
|---|---:|---:|---:|
| circuit | 0.3378 | 0.4887 | 20/20 |
| formula | 0.3240 | 0.5032 | n/a |
| mlp | 0.3210 | 0.5021 | n/a |

### L2, high noise, P = 30

| model | expected cost | false-reflex | reflex share | decision acc |
|---|---:|---:|---:|---:|
| circuit | 5.0443 | 0.3409 | 0.0076 | 0.9924 |
| formula | 5.0095 | 0.3000 | 0.0019 | 0.9981 |
| mlp | 5.0295 | 0.3002 | 0.0059 | 0.9941 |
| const_reflex | 15.6838 | 0.4895 | 1.0000 | 0.0000 |
| const_escalate | 5.0000 | n/a | 0.0000 | 1.0000 |
| oracle | 5.0000 | n/a | 0.0000 | 1.0000 |

Circuit minus formula: mean diff 0.0348, relative +0.69%, 95% CI [0.0244, 0.0461], raw label tie.

Matched reflex share (each gate refit with the share within 2 points of 50%):

| model | false-reflex | reflex share | circuit fit feasible (seeds) |
|---|---:|---:|---:|
| circuit | 0.3481 | 0.4854 | 20/20 |
| formula | 0.3240 | 0.5032 | n/a |
| mlp | 0.3210 | 0.5021 | n/a |

### X1, base noise, P = 3

| model | expected cost | false-reflex | reflex share | decision acc |
|---|---:|---:|---:|---:|
| circuit | 2.7504 | 0.5834 | 0.9999 | 0.9999 |
| formula | 2.7502 | 0.5834 | 1.0000 | 1.0000 |
| mlp | 2.7502 | 0.5834 | 1.0000 | 1.0000 |
| const_reflex | 2.7502 | 0.5834 | 1.0000 | 1.0000 |
| const_escalate | 5.0000 | n/a | 0.0000 | 0.0000 |
| oracle | 2.7502 | 0.5834 | 1.0000 | 1.0000 |

Circuit minus formula: mean diff 0.0003, relative +0.01%, 95% CI [0.0001, 0.0005], raw label tie.

Matched reflex share (each gate refit with the share within 2 points of 50%):

| model | false-reflex | reflex share | circuit fit feasible (seeds) |
|---|---:|---:|---:|
| circuit | 0.4461 | 0.5170 | 20/20 |
| formula | 0.4202 | 0.5024 | n/a |
| mlp | 0.4192 | 0.5040 | n/a |

### X1, base noise, P = 10

| model | expected cost | false-reflex | reflex share | decision acc |
|---|---:|---:|---:|---:|
| circuit | 4.5332 | 0.1677 | 0.2009 | 0.9114 |
| formula | 4.5871 | 0.2406 | 0.2609 | 0.9034 |
| mlp | 4.3991 | 0.1772 | 0.2700 | 0.9676 |
| const_reflex | 6.8338 | 0.5834 | 1.0000 | 0.2777 |
| const_escalate | 5.0000 | n/a | 0.0000 | 0.7223 |
| oracle | 4.3058 | 0.1500 | 0.2777 | 1.0000 |

Circuit minus formula: mean diff -0.0539, relative -1.18%, 95% CI [-0.0688, -0.0317], raw label tie.
Effective label (P = 3 and P = 30 sign check, flag applied): tie.

Matched reflex share (each gate refit with the share within 2 points of 50%):

| model | false-reflex | reflex share | circuit fit feasible (seeds) |
|---|---:|---:|---:|
| circuit | 0.4215 | 0.4838 | 20/20 |
| formula | 0.4202 | 0.5024 | n/a |
| mlp | 0.4192 | 0.5040 | n/a |

### X1, base noise, P = 30

| model | expected cost | false-reflex | reflex share | decision acc |
|---|---:|---:|---:|---:|
| circuit | 5.0351 | 0.1698 | 0.0476 | 0.9524 |
| formula | 5.0326 | 0.1528 | 0.0449 | 0.9551 |
| mlp | 5.0552 | 0.1505 | 0.1051 | 0.8949 |
| const_reflex | 18.5015 | 0.5834 | 1.0000 | 0.0000 |
| const_escalate | 5.0000 | n/a | 0.0000 | 1.0000 |
| oracle | 5.0000 | n/a | 0.0000 | 1.0000 |

Circuit minus formula: mean diff 0.0025, relative +0.05%, 95% CI [-0.0135, 0.0168], raw label tie.

Matched reflex share (each gate refit with the share within 2 points of 50%):

| model | false-reflex | reflex share | circuit fit feasible (seeds) |
|---|---:|---:|---:|
| circuit | 0.4270 | 0.4869 | 20/20 |
| formula | 0.4202 | 0.5024 | n/a |
| mlp | 0.4192 | 0.5040 | n/a |

### X1, high noise, P = 3

| model | expected cost | false-reflex | reflex share | decision acc |
|---|---:|---:|---:|---:|
| circuit | 2.6254 | 0.5417 | 0.9998 | 0.9998 |
| formula | 2.6251 | 0.5417 | 1.0000 | 1.0000 |
| mlp | 2.6251 | 0.5417 | 1.0000 | 1.0000 |
| const_reflex | 2.6251 | 0.5417 | 1.0000 | 1.0000 |
| const_escalate | 5.0000 | n/a | 0.0000 | 0.0000 |
| oracle | 2.6251 | 0.5417 | 1.0000 | 1.0000 |

Circuit minus formula: mean diff 0.0004, relative +0.01%, 95% CI [0.0001, 0.0007], raw label tie.

Matched reflex share (each gate refit with the share within 2 points of 50%):

| model | false-reflex | reflex share | circuit fit feasible (seeds) |
|---|---:|---:|---:|
| circuit | 0.4831 | 0.5186 | 20/20 |
| formula | 0.4610 | 0.5021 | n/a |
| mlp | 0.4603 | 0.5025 | n/a |

### X1, high noise, P = 10

| model | expected cost | false-reflex | reflex share | decision acc |
|---|---:|---:|---:|---:|
| circuit | 4.9190 | 0.3513 | 0.1290 | 0.8408 |
| formula | 4.9311 | 0.3588 | 0.1959 | 0.8662 |
| mlp | 4.8774 | 0.3440 | 0.2283 | 0.9182 |
| const_reflex | 6.4169 | 0.5417 | 1.0000 | 0.2777 |
| const_escalate | 5.0000 | n/a | 0.0000 | 0.7223 |
| oracle | 4.7917 | 0.3250 | 0.2777 | 1.0000 |

Circuit minus formula: mean diff -0.0121, relative -0.25%, 95% CI [-0.0297, 0.0066], raw label tie.
Effective label (P = 3 and P = 30 sign check, flag applied): tie.

Matched reflex share (each gate refit with the share within 2 points of 50%):

| model | false-reflex | reflex share | circuit fit feasible (seeds) |
|---|---:|---:|---:|
| circuit | 0.4636 | 0.4854 | 20/20 |
| formula | 0.4610 | 0.5021 | n/a |
| mlp | 0.4603 | 0.5025 | n/a |

### X1, high noise, P = 30

| model | expected cost | false-reflex | reflex share | decision acc |
|---|---:|---:|---:|---:|
| circuit | 5.0527 | 0.3833 | 0.0075 | 0.9925 |
| formula | 5.0091 | 0.3250 | 0.0016 | 0.9984 |
| mlp | 5.0387 | 0.3261 | 0.0067 | 0.9933 |
| const_reflex | 17.2508 | 0.5417 | 1.0000 | 0.0000 |
| const_escalate | 5.0000 | n/a | 0.0000 | 1.0000 |
| oracle | 5.0000 | n/a | 0.0000 | 1.0000 |

Circuit minus formula: mean diff 0.0437, relative +0.87%, 95% CI [0.0302, 0.0584], raw label tie.

Matched reflex share (each gate refit with the share within 2 points of 50%):

| model | false-reflex | reflex share | circuit fit feasible (seeds) |
|---|---:|---:|---:|
| circuit | 0.4696 | 0.4830 | 20/20 |
| formula | 0.4610 | 0.5021 | n/a |
| mlp | 0.4603 | 0.5025 | n/a |

### X2, base noise, P = 3

| model | expected cost | false-reflex | reflex share | decision acc |
|---|---:|---:|---:|---:|
| circuit | 2.6567 | 0.5520 | 0.9997 | 0.9997 |
| formula | 2.6561 | 0.5520 | 1.0000 | 1.0000 |
| mlp | 2.6561 | 0.5520 | 1.0000 | 1.0000 |
| const_reflex | 2.6561 | 0.5520 | 1.0000 | 1.0000 |
| const_escalate | 5.0000 | n/a | 0.0000 | 0.0000 |
| oracle | 2.6561 | 0.5520 | 1.0000 | 1.0000 |

Circuit minus formula: mean diff 0.0006, relative +0.02%, 95% CI [0.0002, 0.0011], raw label tie.

Matched reflex share (each gate refit with the share within 2 points of 50%):

| model | false-reflex | reflex share | circuit fit feasible (seeds) |
|---|---:|---:|---:|
| circuit | 0.4323 | 0.5201 | 20/20 |
| formula | 0.4592 | 0.5013 | n/a |
| mlp | 0.3536 | 0.4985 | n/a |

### X2, base noise, P = 10

| model | expected cost | false-reflex | reflex share | decision acc |
|---|---:|---:|---:|---:|
| circuit | 4.8267 | 0.2479 | 0.1204 | 0.7479 |
| formula | 5.0004 | 0.4172 | 0.0162 | 0.6726 |
| mlp | 4.3269 | 0.1873 | 0.3177 | 0.9474 |
| const_reflex | 6.5203 | 0.5520 | 1.0000 | 0.3299 |
| const_escalate | 5.0000 | n/a | 0.0000 | 0.6701 |
| oracle | 4.1751 | 0.1500 | 0.3299 | 1.0000 |

Circuit minus formula: mean diff -0.1737, relative -3.47%, 95% CI [-0.2064, -0.1423], raw label circuit_win.
Effective label (P = 3 and P = 30 sign check, flag applied): tie.

Matched reflex share (each gate refit with the share within 2 points of 50%):

| model | false-reflex | reflex share | circuit fit feasible (seeds) |
|---|---:|---:|---:|
| circuit | 0.4122 | 0.4901 | 20/20 |
| formula | 0.4592 | 0.5013 | n/a |
| mlp | 0.3536 | 0.4985 | n/a |

### X2, base noise, P = 30

| model | expected cost | false-reflex | reflex share | decision acc |
|---|---:|---:|---:|---:|
| circuit | 5.0275 | 0.2009 | 0.0173 | 0.9827 |
| formula | 5.0039 | 0.3166 | 0.0010 | 0.9990 |
| mlp | 5.0570 | 0.1506 | 0.1077 | 0.8923 |
| const_reflex | 17.5609 | 0.5520 | 1.0000 | 0.0000 |
| const_escalate | 5.0000 | n/a | 0.0000 | 1.0000 |
| oracle | 5.0000 | n/a | 0.0000 | 1.0000 |

Circuit minus formula: mean diff 0.0236, relative +0.47%, 95% CI [0.0138, 0.0356], raw label tie.

Matched reflex share (each gate refit with the share within 2 points of 50%):

| model | false-reflex | reflex share | circuit fit feasible (seeds) |
|---|---:|---:|---:|
| circuit | 0.4182 | 0.4838 | 20/20 |
| formula | 0.4592 | 0.5013 | n/a |
| mlp | 0.3536 | 0.4985 | n/a |

### X2, high noise, P = 3

| model | expected cost | false-reflex | reflex share | decision acc |
|---|---:|---:|---:|---:|
| circuit | 2.5783 | 0.5260 | 0.9999 | 0.9999 |
| formula | 2.5780 | 0.5260 | 1.0000 | 1.0000 |
| mlp | 2.5780 | 0.5260 | 1.0000 | 1.0000 |
| const_reflex | 2.5780 | 0.5260 | 1.0000 | 1.0000 |
| const_escalate | 5.0000 | n/a | 0.0000 | 0.0000 |
| oracle | 2.5780 | 0.5260 | 1.0000 | 1.0000 |

Circuit minus formula: mean diff 0.0002, relative +0.01%, 95% CI [0.0001, 0.0004], raw label tie.

Matched reflex share (each gate refit with the share within 2 points of 50%):

| model | false-reflex | reflex share | circuit fit feasible (seeds) |
|---|---:|---:|---:|
| circuit | 0.4796 | 0.5182 | 20/20 |
| formula | 0.4795 | 0.4995 | n/a |
| mlp | 0.4325 | 0.4975 | n/a |

### X2, high noise, P = 10

| model | expected cost | false-reflex | reflex share | decision acc |
|---|---:|---:|---:|---:|
| circuit | 4.9929 | 0.3893 | 0.0593 | 0.7044 |
| formula | 5.0054 | 0.5360 | 0.0075 | 0.6702 |
| mlp | 4.8902 | 0.3502 | 0.2316 | 0.8591 |
| const_reflex | 6.2602 | 0.5260 | 1.0000 | 0.3299 |
| const_escalate | 5.0000 | n/a | 0.0000 | 0.6701 |
| oracle | 4.7525 | 0.3250 | 0.3299 | 1.0000 |

Circuit minus formula: mean diff -0.0124, relative -0.25%, 95% CI [-0.0210, -0.0039], raw label tie.
Effective label (P = 3 and P = 30 sign check, flag applied): tie.

Matched reflex share (each gate refit with the share within 2 points of 50%):

| model | false-reflex | reflex share | circuit fit feasible (seeds) |
|---|---:|---:|---:|
| circuit | 0.4616 | 0.4833 | 20/20 |
| formula | 0.4795 | 0.4995 | n/a |
| mlp | 0.4325 | 0.4975 | n/a |

### X2, high noise, P = 30

| model | expected cost | false-reflex | reflex share | decision acc |
|---|---:|---:|---:|---:|
| circuit | 5.0390 | 0.4028 | 0.0053 | 0.9947 |
| formula | 5.0124 | 0.5201 | 0.0013 | 0.9987 |
| mlp | 5.0299 | 0.3250 | 0.0052 | 0.9948 |
| const_reflex | 16.7805 | 0.5260 | 1.0000 | 0.0000 |
| const_escalate | 5.0000 | n/a | 0.0000 | 1.0000 |
| oracle | 5.0000 | n/a | 0.0000 | 1.0000 |

Circuit minus formula: mean diff 0.0266, relative +0.53%, 95% CI [0.0191, 0.0335], raw label tie.

Matched reflex share (each gate refit with the share within 2 points of 50%):

| model | false-reflex | reflex share | circuit fit feasible (seeds) |
|---|---:|---:|---:|
| circuit | 0.4682 | 0.4808 | 20/20 |
| formula | 0.4795 | 0.4995 | n/a |
| mlp | 0.4325 | 0.4975 | n/a |

### C1, base noise, P = 3

| model | expected cost | false-reflex | reflex share | decision acc |
|---|---:|---:|---:|---:|
| circuit | 3.0834 | 0.6944 | 0.9999 | 0.9999 |
| formula | 3.0833 | 0.6944 | 1.0000 | 1.0000 |
| mlp | 3.0833 | 0.6944 | 1.0000 | 1.0000 |
| const_reflex | 3.0833 | 0.6944 | 1.0000 | 1.0000 |
| const_escalate | 5.0000 | n/a | 0.0000 | 0.0000 |
| oracle | 3.0833 | 0.6944 | 1.0000 | 1.0000 |

Circuit minus formula: mean diff 0.0001, relative +0.00%, 95% CI [0.0000, 0.0002], raw label tie.

Matched reflex share (each gate refit with the share within 2 points of 50%):

| model | false-reflex | reflex share | circuit fit feasible (seeds) |
|---|---:|---:|---:|
| circuit | 0.6478 | 0.5191 | 20/20 |
| formula | 0.6393 | 0.5022 | n/a |
| mlp | 0.6386 | 0.4991 | n/a |

### C1, base noise, P = 10

| model | expected cost | false-reflex | reflex share | decision acc |
|---|---:|---:|---:|---:|
| circuit | 4.8256 | 0.1721 | 0.0755 | 0.9781 |
| formula | 4.8479 | 0.2173 | 0.0827 | 0.9718 |
| mlp | 4.8018 | 0.1842 | 0.0921 | 0.9888 |
| const_reflex | 7.9442 | 0.6944 | 1.0000 | 0.0926 |
| const_escalate | 5.0000 | n/a | 0.0000 | 0.9074 |
| oracle | 4.7684 | 0.1500 | 0.0926 | 1.0000 |

Circuit minus formula: mean diff -0.0223, relative -0.46%, 95% CI [-0.0453, 0.0033], raw label tie.
Effective label (P = 3 and P = 30 sign check, flag applied): tie.

Matched reflex share (each gate refit with the share within 2 points of 50%):

| model | false-reflex | reflex share | circuit fit feasible (seeds) |
|---|---:|---:|---:|
| circuit | 0.6360 | 0.4773 | 20/20 |
| formula | 0.6393 | 0.5022 | n/a |
| mlp | 0.6386 | 0.4991 | n/a |

### C1, base noise, P = 30

| model | expected cost | false-reflex | reflex share | decision acc |
|---|---:|---:|---:|---:|
| circuit | 5.0227 | 0.2095 | 0.0150 | 0.9850 |
| formula | 5.0186 | 0.2067 | 0.0153 | 0.9847 |
| mlp | 5.0155 | 0.1693 | 0.0225 | 0.9775 |
| const_reflex | 21.8325 | 0.6944 | 1.0000 | 0.0000 |
| const_escalate | 5.0000 | n/a | 0.0000 | 1.0000 |
| oracle | 5.0000 | n/a | 0.0000 | 1.0000 |

Circuit minus formula: mean diff 0.0041, relative +0.08%, 95% CI [-0.0129, 0.0210], raw label tie.

Matched reflex share (each gate refit with the share within 2 points of 50%):

| model | false-reflex | reflex share | circuit fit feasible (seeds) |
|---|---:|---:|---:|
| circuit | 0.6388 | 0.4798 | 20/20 |
| formula | 0.6393 | 0.5022 | n/a |
| mlp | 0.6386 | 0.4991 | n/a |

### C1, high noise, P = 3

| model | expected cost | false-reflex | reflex share | decision acc |
|---|---:|---:|---:|---:|
| circuit | 2.7919 | 0.5972 | 0.9999 | 0.9999 |
| formula | 2.7916 | 0.5972 | 1.0000 | 1.0000 |
| mlp | 2.7916 | 0.5972 | 1.0000 | 1.0000 |
| const_reflex | 2.7916 | 0.5972 | 1.0000 | 1.0000 |
| const_escalate | 5.0000 | n/a | 0.0000 | 0.0000 |
| oracle | 2.7916 | 0.5972 | 1.0000 | 1.0000 |

Circuit minus formula: mean diff 0.0003, relative +0.01%, 95% CI [0.0001, 0.0005], raw label tie.

Matched reflex share (each gate refit with the share within 2 points of 50%):

| model | false-reflex | reflex share | circuit fit feasible (seeds) |
|---|---:|---:|---:|
| circuit | 0.5784 | 0.5145 | 20/20 |
| formula | 0.5695 | 0.5005 | n/a |
| mlp | 0.5694 | 0.4992 | n/a |

### C1, high noise, P = 10

| model | expected cost | false-reflex | reflex share | decision acc |
|---|---:|---:|---:|---:|
| circuit | 4.9901 | 0.3766 | 0.0379 | 0.9329 |
| formula | 4.9831 | 0.3782 | 0.0612 | 0.9493 |
| mlp | 4.9699 | 0.3555 | 0.0728 | 0.9639 |
| const_reflex | 6.9721 | 0.5972 | 1.0000 | 0.0926 |
| const_escalate | 5.0000 | n/a | 0.0000 | 0.9074 |
| oracle | 4.9305 | 0.3250 | 0.0926 | 1.0000 |

Circuit minus formula: mean diff 0.0070, relative +0.14%, 95% CI [-0.0055, 0.0186], raw label tie.
Effective label (P = 3 and P = 30 sign check, flag applied): tie.

Matched reflex share (each gate refit with the share within 2 points of 50%):

| model | false-reflex | reflex share | circuit fit feasible (seeds) |
|---|---:|---:|---:|
| circuit | 0.5750 | 0.4831 | 20/20 |
| formula | 0.5695 | 0.5005 | n/a |
| mlp | 0.5694 | 0.4992 | n/a |

### C1, high noise, P = 30

| model | expected cost | false-reflex | reflex share | decision acc |
|---|---:|---:|---:|---:|
| circuit | 5.0383 | 0.4934 | 0.0039 | 0.9961 |
| formula | 5.0124 | 0.4035 | 0.0018 | 0.9982 |
| mlp | 5.0234 | 0.3635 | 0.0038 | 0.9962 |
| const_reflex | 18.9163 | 0.5972 | 1.0000 | 0.0000 |
| const_escalate | 5.0000 | n/a | 0.0000 | 1.0000 |
| oracle | 5.0000 | n/a | 0.0000 | 1.0000 |

Circuit minus formula: mean diff 0.0259, relative +0.52%, 95% CI [0.0142, 0.0373], raw label tie.

Matched reflex share (each gate refit with the share within 2 points of 50%):

| model | false-reflex | reflex share | circuit fit feasible (seeds) |
|---|---:|---:|---:|
| circuit | 0.5789 | 0.4784 | 20/20 |
| formula | 0.5695 | 0.5005 | n/a |
| mlp | 0.5694 | 0.4992 | n/a |

## 8 Proposed consequence

Proposed, not applied: drop the cost-saving claim for the circuit gate and publish the negative result (P5); the race demotion (P-A) is a separate step after this verdict.

