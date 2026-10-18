# ADR-0002: Fit budget for the formula and circuit gates

## Status

Accepted. Recorded after the fact in M10; the decision was fixed by the frozen code `spikes/s1/s1_frozen.py` and `spikes/s1/s1_verdict.py` (sha256 recorded in `reports/s1/preregistration.md`), and is stated in `reports/s1/preregistration.md`.

## Context

S1 R13, R14 and R16 require fairness between the gates: the same inputs, training and test sets, cost function and seeds. The circuit budget must be at least the formula budget.

## Decision

- Formula gate: logistic regression with intercept on [s, L, k, b], L2 1e-4, Newton-IRLS with at most 100 iterations. The threshold is chosen on the training set by empirical cost. Budget = iterations + threshold candidates; the maximum over all fits is 2008.
- Circuit gate: (1+1)-ES, 8 restarts x 500 evaluations = 4000 candidate mappings, sigma0 0.5, decay 0.995. Restart 0 starts from THETA0; the other restarts start from uniform random starts (gain range (-3.0, 3.0), offset range (0.0, 3.0)). Training data only.
- Data: train 2000, test 20000, 20 dataset seeds per scenario and noise level.
- References (not gates under test): MLP with 16 tanh hidden units, 3000 steps; true-p oracle; best constant policy.

## Alternatives

- Equal budgets of the same count. Not required by S1 R14, which sets a lower bound only.
- Larger budget searches. Not pre-registered.

## Consequences

The result holds only under this fit budget (`docs/report.md` item (e)). The circuit budget of 4000 against a formula budget of at most 2008 is stated in `reports/s1/report.md`.
