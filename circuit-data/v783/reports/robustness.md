# Robustness of the v783 LC4/LPLC2 escape circuit (M6)

> Retention numbers in this report are published as measured. M6 sets no retention threshold and gives no pass/fail verdict on the circuit. The PAC2 threshold is set by the Verifier and finalized at Gate 1 (M11).

## Grid and configuration

Grid file: `robustness.toml`

sha256: `5c07af9936c9221edf65582a6f4d56da53005b935420a9420a8125ba0c980bef`

```toml
# M6 robustness grid (R2). Frozen before the first long-run simulation; later edits need a [[deviations]] entry.
[robustness]
schema = 1
seed_origin = 786000        # condition k (0-based, enumeration order) uses seed_base = seed_origin + k * seed_stride
seed_stride = 100           # must be >= [discover].n_trials
time_cap_s = 10800          # 3 h hard cap (R10); CLI --time-cap-s overrides
budget_probe_conditions = 3 # conditions timed before the projection
min_reduced_trials = 15     # R10 step 3 floor
reduced_control_draws = 3   # R10 step 2
chance_draws = 1000         # R13
chance_seed = 791000
shuffle_rounds = 20         # rounds of disjoint-pair edge swaps per shuffle (R12)
left_label = "left"
right_label = "right"

[robustness.families]
rate_hz = [50.0, 100.0, 200.0]                      # R3
w_syn_mult = [0.5, 0.75, 1.5, 2.0]                  # R4
f_poi_mult = [0.5, 0.75, 1.5, 2.0]                  # R4
subsets = ["lc4", "lplc2", "both"]                  # R5
sides = ["left", "right", "bilateral"]              # R5 (both x bilateral = baseline, skipped)
seed_replicates = 5                                 # R6
interaction_groups = ["lc4", "lplc2"]               # R7
interaction_rate_hz = [50.0, 100.0, 200.0]          # R7
random_set_draws = 5                                # R11
shuffle_draws = 5                                   # R12

# [[robustness.deviations]]
# from_sha256 = "<sha256 of the frozen grid file>"
# reason = "<why the grid changed after freezing>"
```

Deviations from the frozen grid:

None.

## Baseline sanity

- source: m5
- spikes sha256: `266d96d337fb0676165a2ec10ee9fc6d62777cc40babc06d302a226353015aea`
- seed base 785000, 30 trials, rate 150.0000 Hz
- responsive neurons 917, core size 917, members 1231, edges 10641
- side counts: lc4 left 54, right 50, unlabeled 0; lplc2 left 108, right 102, unlabeled 0
- GF ids: 720575940622838154, 720575940632499757
- parallel ids: 720575940604954289, 720575940610505006, 720575940611644529, 720575940612203482, 720575940619654053, 720575940620054694, 720575940620468718, 720575940621401222, 720575940622673860, 720575940622996579, 720575940623781127, 720575940626009852, 720575940626901136, 720575940627645514, 720575940628437291, 720575940629757036, 720575940629777018
- parallel cell types: DNg40, DNp02, DNp03, DNp04, DNp05, DNp06, DNp103, DNp11, DNp35, DNpe025
- circuit sha256: `4ca62284d2831f01228e2d0f8a71fdfce78a0b26674cb1bbccf537f487263d91`
- matches the committed M5 circuit: yes

## Retention

| condition | family | status | trials | stimulated | core excluded | retained / reference | core retention | Jaccard | new | Spearman | members | edges | edge Jaccard | GF set equal | parallel set equal |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rate-50hz | rate | completed | 30 | 314 | 0 | 401 / 917 | 0.4373 | 0.4270 | 22 | 0.8004 | 737 | 5080 | 0.4328 | yes | no |
| rate-100hz | rate | completed | 30 | 314 | 0 | 657 / 917 | 0.7165 | 0.7080 | 11 | 0.9475 | 982 | 7788 | 0.6970 | yes | yes |
| rate-200hz | rate | completed | 30 | 314 | 0 | 914 / 917 | 0.9967 | 0.7825 | 251 | 0.9686 | 1479 | 13784 | 0.7633 | yes | yes |
| wsyn-x0.50 | w_syn | completed | 30→15 | 314 | 0 | 345 / 917 | 0.3762 | 0.3706 | 14 | 0.8975 | 673 | 5323 | 0.4473 | yes | no |
| wsyn-x0.75 | w_syn | completed | 30→15 | 314 | 0 | 603 / 917 | 0.6576 | 0.6491 | 12 | 0.9435 | 929 | 7957 | 0.6837 | yes | no |
| wsyn-x1.50 | w_syn | completed | 30→15 | 314 | 0 | 896 / 917 | 0.9771 | 0.2368 | 2867 | 0.8283 | 4077 | 44421 | 0.2237 | yes | yes |
| wsyn-x2.00 | w_syn | completed | 30→15 | 314 | 0 | 863 / 917 | 0.9411 | 0.0532 | 15294 | 0.6122 | 16471 | 268011 | 0.0348 | yes | yes |
| fpoi-x0.50 | f_poi | completed | 30→15 | 314 | 0 | 912 / 917 | 0.9945 | 0.9733 | 20 | 0.9993 | 1246 | 10923 | 0.9664 | yes | yes |
| fpoi-x0.75 | f_poi | completed | 30→15 | 314 | 0 | 910 / 917 | 0.9924 | 0.9764 | 15 | 0.9992 | 1239 | 10893 | 0.9608 | yes | yes |
| fpoi-x1.50 | f_poi | completed | 30→15 | 314 | 0 | 910 / 917 | 0.9924 | 0.9774 | 14 | 0.9996 | 1238 | 10857 | 0.9660 | yes | yes |
| fpoi-x2.00 | f_poi | completed | 30→15 | 314 | 0 | 911 / 917 | 0.9935 | 0.9785 | 14 | 0.9995 | 1239 | 10792 | 0.9712 | yes | yes |
| stim-lc4-left | subset_side | completed | 30→15 | 54 | 0 | 210 / 917 | 0.2290 | 0.2165 | 53 | 0.4655 | 317 | 2120 | 0.1353 | yes | no |
| stim-lc4-right | subset_side | completed | 30→15 | 50 | 0 | 210 / 917 | 0.2290 | 0.2147 | 61 | 0.4251 | 321 | 2134 | 0.1190 | yes | no |
| stim-lc4-bilateral | subset_side | completed | 30→15 | 104 | 0 | 331 / 917 | 0.3610 | 0.3290 | 89 | 0.6386 | 524 | 3718 | 0.2160 | yes | no |
| stim-lplc2-left | subset_side | completed | 30→15 | 108 | 0 | 419 / 917 | 0.4569 | 0.4017 | 126 | 0.5888 | 653 | 5731 | 0.3170 | yes | no |
| stim-lplc2-right | subset_side | completed | 30→15 | 102 | 0 | 455 / 917 | 0.4962 | 0.4483 | 98 | 0.7084 | 655 | 5555 | 0.3339 | yes | no |
| stim-lplc2-bilateral | subset_side | completed | 30→15 | 210 | 0 | 684 / 917 | 0.7459 | 0.6854 | 81 | 0.8626 | 975 | 8248 | 0.6063 | yes | no |
| stim-both-left | subset_side | completed | 30→15 | 162 | 0 | 502 / 917 | 0.5474 | 0.4841 | 120 | 0.6717 | 784 | 6718 | 0.4146 | yes | no |
| stim-both-right | subset_side | completed | 30→15 | 152 | 0 | 547 / 917 | 0.5965 | 0.5454 | 86 | 0.7629 | 785 | 6561 | 0.4198 | yes | no |
| seed-1 | seed | completed | 30→15 | 314 | 0 | 909 / 917 | 0.9913 | 0.9795 | 11 | 0.9995 | 1234 | 10737 | 0.9710 | yes | yes |
| seed-2 | seed | completed | 30→15 | 314 | 0 | 909 / 917 | 0.9913 | 0.9743 | 16 | 0.9992 | 1239 | 10840 | 0.9567 | yes | yes |
| seed-3 | seed | completed | 30→15 | 314 | 0 | 909 / 917 | 0.9913 | 0.9691 | 21 | 0.9995 | 1244 | 10840 | 0.9537 | yes | yes |
| seed-4 | seed | completed | 30→15 | 314 | 0 | 899 / 917 | 0.9804 | 0.9656 | 14 | 0.9994 | 1227 | 10722 | 0.9581 | yes | yes |
| seed-5 | seed | completed | 30→15 | 314 | 0 | 910 / 917 | 0.9924 | 0.9753 | 16 | 0.9994 | 1240 | 10836 | 0.9598 | yes | yes |
| inter-lc4-50hz | interaction | dropped | 30 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| inter-lc4-100hz | interaction | dropped | 30 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| inter-lc4-200hz | interaction | dropped | 30 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| inter-lplc2-50hz | interaction | dropped | 30 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| inter-lplc2-100hz | interaction | dropped | 30 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| inter-lplc2-200hz | interaction | dropped | 30 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| random-1 | random_set | completed | 30→15 | 314 | 0 | 241 / 917 | 0.2628 | 0.0256 | 8492 | 0.1782 | 9047 | 155211 | 0.0056 | no | no |
| random-2 | random_set | completed | 30→15 | 314 | 5 | 236 / 912 | 0.2588 | 0.0258 | 8233 | 0.0585 | 8783 | 151723 | 0.0061 | no | no |
| random-3 | random_set | completed | 30→15 | 314 | 2 | 228 / 915 | 0.2492 | 0.0244 | 8422 | -0.0021 | 8964 | 153943 | 0.0055 | no | no |
| random-4 | random_set | dropped | 30 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| random-5 | random_set | dropped | 30 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| shuffle-1 | shuffle | completed | 30→15 | 314 | 0 | 33 / 917 | 0.0360 | 0.0185 | 868 | 0.1046 | 1215 | 2200 | 0.0002 | no | no |
| shuffle-2 | shuffle | completed | 30→15 | 314 | 0 | 36 / 917 | 0.0393 | 0.0227 | 669 | -0.0967 | 1019 | 1621 | 0.0002 | no | no |
| shuffle-3 | shuffle | completed | 30→15 | 314 | 0 | 31 / 917 | 0.0338 | 0.0206 | 587 | -0.0190 | 932 | 1313 | 0.0002 | no | no |
| shuffle-4 | shuffle | dropped | 30 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| shuffle-5 | shuffle | dropped | 30 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |

Core retention over completed grid conditions ranges from 0.2290 to 0.9967 (median 0.8435); over control conditions from 0.0338 to 0.2628 (median 0.1442); the chance-level mean is 0.0066.

## Chance-level reference

Random sets of 917 neurons drawn from a population of 138941: 1000 draws, seed 791000.

| metric | mean | sd | min | max |
|---|---|---|---|---|
| core retention | 0.0066 | 0.0026 | 0.0000 | 0.0164 |
| Jaccard | 0.0033 | 0.0013 | 0.0000 | 0.0082 |

## Negative controls

### Random sets

| condition | draw | left | right | unlabeled | ids |
|---|---|---|---|---|---|
| random-1 | 1 | 162 | 152 | 0 | 314 |
| random-2 | 2 | 162 | 152 | 0 | 314 |
| random-3 | 3 | 162 | 152 | 0 | 314 |
| random-4 | 4 | 162 | 152 | 0 | 314 |
| random-5 | 5 | 162 | 152 | 0 | 314 |

### Shuffles

| draw | seed | rounds | attempted | accepted | changed edges | self-loops before | self-loops after | in_degree_equal | no_duplicates | no_new_self_loops | out_degree_equal | signs_follow_pre | syn_multiset_equal |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 788900 | 20 | 150919820 | 146698133 | 15091620 | 0 | 0 | yes | yes | yes | yes | yes | yes |
| 2 | 789000 | 20 | 150919820 | 146699989 | 15091616 | 0 | 0 | yes | yes | yes | yes | yes | yes |
| 3 | 789100 | 20 | 150919820 | 146701014 | 15091656 | 0 | 0 | yes | yes | yes | yes | yes | yes |
| 4 | 789200 | 20 | 150919820 | 146698669 | 15091662 | 0 | 0 | yes | yes | yes | yes | yes | yes |
| 5 | 789300 | 20 | 150919820 | 146696126 | 15091629 | 0 | 0 | yes | yes | yes | yes | yes | yes |

## GF identity

| condition | responsive GF ids | equal to baseline | missing GF |
|---|---|---|---|
| rate-50hz | 720575940622838154, 720575940632499757 | yes | none |
| rate-100hz | 720575940622838154, 720575940632499757 | yes | none |
| rate-200hz | 720575940622838154, 720575940632499757 | yes | none |
| wsyn-x0.50 | 720575940622838154, 720575940632499757 | yes | none |
| wsyn-x0.75 | 720575940622838154, 720575940632499757 | yes | none |
| wsyn-x1.50 | 720575940622838154, 720575940632499757 | yes | none |
| wsyn-x2.00 | 720575940622838154, 720575940632499757 | yes | none |
| fpoi-x0.50 | 720575940622838154, 720575940632499757 | yes | none |
| fpoi-x0.75 | 720575940622838154, 720575940632499757 | yes | none |
| fpoi-x1.50 | 720575940622838154, 720575940632499757 | yes | none |
| fpoi-x2.00 | 720575940622838154, 720575940632499757 | yes | none |
| stim-lc4-left | 720575940622838154, 720575940632499757 | yes | none |
| stim-lc4-right | 720575940622838154, 720575940632499757 | yes | none |
| stim-lc4-bilateral | 720575940622838154, 720575940632499757 | yes | none |
| stim-lplc2-left | 720575940622838154, 720575940632499757 | yes | none |
| stim-lplc2-right | 720575940622838154, 720575940632499757 | yes | none |
| stim-lplc2-bilateral | 720575940622838154, 720575940632499757 | yes | none |
| stim-both-left | 720575940622838154, 720575940632499757 | yes | none |
| stim-both-right | 720575940622838154, 720575940632499757 | yes | none |
| seed-1 | 720575940622838154, 720575940632499757 | yes | none |
| seed-2 | 720575940622838154, 720575940632499757 | yes | none |
| seed-3 | 720575940622838154, 720575940632499757 | yes | none |
| seed-4 | 720575940622838154, 720575940632499757 | yes | none |
| seed-5 | 720575940622838154, 720575940632499757 | yes | none |
| random-1 | none | no | 720575940622838154: rate 0.0000 Hz, rel rate 0.0000, rank n/a, trial frac 0.0000; 720575940632499757: rate 0.0000 Hz, rel rate 0.0000, rank n/a, trial frac 0.0000 |
| random-2 | none | no | 720575940622838154: rate 0.2000 Hz, rel rate 0.0006, rank n/a, trial frac 0.2000; 720575940632499757: rate 0.0667 Hz, rel rate 0.0002, rank n/a, trial frac 0.0667 |
| random-3 | none | no | 720575940622838154: rate 0.2667 Hz, rel rate 0.0008, rank n/a, trial frac 0.2667; 720575940632499757: rate 0.4000 Hz, rel rate 0.0012, rank n/a, trial frac 0.4000 |
| shuffle-1 | none | no | 720575940622838154: rate 0.0000 Hz, rel rate 0.0000, rank n/a, trial frac 0.0000; 720575940632499757: rate 0.0000 Hz, rel rate 0.0000, rank n/a, trial frac 0.0000 |
| shuffle-2 | none | no | 720575940622838154: rate 0.0000 Hz, rel rate 0.0000, rank n/a, trial frac 0.0000; 720575940632499757: rate 0.0000 Hz, rel rate 0.0000, rank n/a, trial frac 0.0000 |
| shuffle-3 | none | no | 720575940622838154: rate 0.0000 Hz, rel rate 0.0000, rank n/a, trial frac 0.0000; 720575940632499757: rate 0.0000 Hz, rel rate 0.0000, rank n/a, trial frac 0.0000 |

The GF set equals the baseline set in 24 of 30 completed conditions.

## Parallel identity

| root_id | cell type | check (ii) |
|---|---|---|
| 720575940604954289 | DNp04 | yes |
| 720575940610505006 | DNp103 | yes |
| 720575940611622826 | DNpe025 | no |
| 720575940611644529 | DNp06 | yes |
| 720575940612203482 | DNp05 | yes |
| 720575940619654053 | DNp02 | yes |
| 720575940620054694 | DNp11 | yes |
| 720575940620468718 | DNp02 | yes |
| 720575940621401222 | DNpe025 | yes |
| 720575940622673860 | DNp06 | yes |
| 720575940622996579 | DNg40 | yes |
| 720575940623276168 | DNp35 | yes |
| 720575940623781127 | DNp103 | yes |
| 720575940626009852 | DNp05 | yes |
| 720575940626901136 | DNg40 | yes |
| 720575940627645514 | DNp03 | yes |
| 720575940628437291 | DNp35 | yes |
| 720575940628884496 | DNp03 | no |
| 720575940629757036 | DNp04 | yes |
| 720575940629777018 | DNp11 | yes |

| condition | parallel set equal | retained / baseline | lost | new neurons | new cell types |
|---|---|---|---|---|---|
| rate-50hz | no | 16 / 17 | 720575940622673860 (DNp06, check (i) no, check (iii) no) | none | none |
| rate-100hz | yes | 17 / 17 | none | none | none |
| rate-200hz | yes | 17 / 17 | none | none | none |
| wsyn-x0.50 | no | 17 / 17 | none | 720575940623276168 | none |
| wsyn-x0.75 | no | 17 / 17 | none | 720575940623276168 | none |
| wsyn-x1.50 | yes | 17 / 17 | none | none | none |
| wsyn-x2.00 | yes | 17 / 17 | none | none | none |
| fpoi-x0.50 | yes | 17 / 17 | none | none | none |
| fpoi-x0.75 | yes | 17 / 17 | none | none | none |
| fpoi-x1.50 | yes | 17 / 17 | none | none | none |
| fpoi-x2.00 | yes | 17 / 17 | none | none | none |
| stim-lc4-left | no | 10 / 17 | 720575940620468718 (DNp02, check (i) no, check (iii) no); 720575940621401222 (DNpe025, check (i) no, check (iii) no); 720575940622673860 (DNp06, check (i) no, check (iii) no); 720575940623781127 (DNp103, check (i) no, check (iii) no); 720575940626009852 (DNp05, check (i) no, check (iii) no); 720575940629757036 (DNp04, check (i) no, check (iii) no); 720575940629777018 (DNp11, check (i) no, check (iii) no) | none | none |
| stim-lc4-right | no | 9 / 17 | 720575940604954289 (DNp04, check (i) no, check (iii) no); 720575940611644529 (DNp06, check (i) no, check (iii) no); 720575940612203482 (DNp05, check (i) no, check (iii) no); 720575940619654053 (DNp02, check (i) no, check (iii) no); 720575940620054694 (DNp11, check (i) no, check (iii) no); 720575940621401222 (DNpe025, check (i) no, check (iii) no); 720575940627645514 (DNp03, check (i) no, check (iii) no); 720575940628437291 (DNp35, check (i) no, check (iii) no) | 720575940623276168 | none |
| stim-lc4-bilateral | no | 14 / 17 | 720575940611644529 (DNp06, check (i) no, check (iii) no); 720575940621401222 (DNpe025, check (i) no, check (iii) no); 720575940622673860 (DNp06, check (i) no, check (iii) no) | none | none |
| stim-lplc2-left | no | 9 / 17 | 720575940619654053 (DNp02, check (i) no, check (iii) no); 720575940620054694 (DNp11, check (i) no, check (iii) no); 720575940620468718 (DNp02, check (i) no, check (iii) no); 720575940621401222 (DNpe025, check (i) no, check (iii) no); 720575940626009852 (DNp05, check (i) no, check (iii) no); 720575940627645514 (DNp03, check (i) no, check (iii) no); 720575940629757036 (DNp04, check (i) no, check (iii) no); 720575940629777018 (DNp11, check (i) no, check (iii) no) | none | none |
| stim-lplc2-right | no | 9 / 17 | 720575940604954289 (DNp04, check (i) no, check (iii) no); 720575940612203482 (DNp05, check (i) no, check (iii) no); 720575940619654053 (DNp02, check (i) no, check (iii) no); 720575940620054694 (DNp11, check (i) no, check (iii) no); 720575940620468718 (DNp02, check (i) no, check (iii) no); 720575940627645514 (DNp03, check (i) no, check (iii) no); 720575940628437291 (DNp35, check (i) no, check (iii) no); 720575940629777018 (DNp11, check (i) no, check (iii) no) | none | none |
| stim-lplc2-bilateral | no | 11 / 17 | 720575940619654053 (DNp02, check (i) no, check (iii) no); 720575940620054694 (DNp11, check (i) no, check (iii) no); 720575940620468718 (DNp02, check (i) no, check (iii) no); 720575940627645514 (DNp03, check (i) no, check (iii) no); 720575940628437291 (DNp35, check (i) no, check (iii) no); 720575940629777018 (DNp11, check (i) no, check (iii) no) | none | none |
| stim-both-left | no | 12 / 17 | 720575940620468718 (DNp02, check (i) no, check (iii) no); 720575940621401222 (DNpe025, check (i) no, check (iii) no); 720575940626009852 (DNp05, check (i) no, check (iii) no); 720575940629757036 (DNp04, check (i) no, check (iii) no); 720575940629777018 (DNp11, check (i) no, check (iii) no) | none | none |
| stim-both-right | no | 11 / 17 | 720575940604954289 (DNp04, check (i) no, check (iii) no); 720575940612203482 (DNp05, check (i) no, check (iii) no); 720575940619654053 (DNp02, check (i) no, check (iii) no); 720575940620054694 (DNp11, check (i) no, check (iii) no); 720575940627645514 (DNp03, check (i) no, check (iii) no); 720575940628437291 (DNp35, check (i) no, check (iii) no) | 720575940623276168 | none |
| seed-1 | yes | 17 / 17 | none | none | none |
| seed-2 | yes | 17 / 17 | none | none | none |
| seed-3 | yes | 17 / 17 | none | none | none |
| seed-4 | yes | 17 / 17 | none | none | none |
| seed-5 | yes | 17 / 17 | none | none | none |
| random-1 | no | 3 / 17 | 720575940604954289 (DNp04, check (i) no, check (iii) no); 720575940610505006 (DNp103, check (i) no, check (iii) no); 720575940611644529 (DNp06, check (i) no, check (iii) no); 720575940619654053 (DNp02, check (i) no, check (iii) no); 720575940620054694 (DNp11, check (i) no, check (iii) no); 720575940621401222 (DNpe025, check (i) no, check (iii) no); 720575940622673860 (DNp06, check (i) no, check (iii) no); 720575940622996579 (DNg40, check (i) no, check (iii) no); 720575940623781127 (DNp103, check (i) no, check (iii) no); 720575940626901136 (DNg40, check (i) no, check (iii) no); 720575940627645514 (DNp03, check (i) no, check (iii) no); 720575940628437291 (DNp35, check (i) no, check (iii) no); 720575940629757036 (DNp04, check (i) no, check (iii) no); 720575940629777018 (DNp11, check (i) no, check (iii) no) | none | none |
| random-2 | no | 4 / 17 | 720575940604954289 (DNp04, check (i) no, check (iii) no); 720575940610505006 (DNp103, check (i) no, check (iii) no); 720575940611644529 (DNp06, check (i) no, check (iii) no); 720575940619654053 (DNp02, check (i) no, check (iii) no); 720575940620054694 (DNp11, check (i) no, check (iii) no); 720575940621401222 (DNpe025, check (i) no, check (iii) no); 720575940622673860 (DNp06, check (i) no, check (iii) no); 720575940622996579 (DNg40, check (i) no, check (iii) no); 720575940623781127 (DNp103, check (i) no, check (iii) no); 720575940626901136 (DNg40, check (i) no, check (iii) no); 720575940628437291 (DNp35, check (i) no, check (iii) no); 720575940629757036 (DNp04, check (i) no, check (iii) no); 720575940629777018 (DNp11, check (i) no, check (iii) no) | none | none |
| random-3 | no | 3 / 17 | 720575940604954289 (DNp04, check (i) no, check (iii) no); 720575940610505006 (DNp103, check (i) no, check (iii) no); 720575940611644529 (DNp06, check (i) no, check (iii) no); 720575940619654053 (DNp02, check (i) no, check (iii) no); 720575940620054694 (DNp11, check (i) no, check (iii) no); 720575940621401222 (DNpe025, check (i) no, check (iii) no); 720575940622673860 (DNp06, check (i) no, check (iii) no); 720575940622996579 (DNg40, check (i) no, check (iii) no); 720575940623781127 (DNp103, check (i) no, check (iii) no); 720575940626901136 (DNg40, check (i) no, check (iii) no); 720575940627645514 (DNp03, check (i) no, check (iii) no); 720575940628437291 (DNp35, check (i) no, check (iii) no); 720575940629757036 (DNp04, check (i) no, check (iii) no); 720575940629777018 (DNp11, check (i) no, check (iii) no) | none | none |
| shuffle-1 | no | 1 / 17 | 720575940604954289 (DNp04, check (i) no, check (iii) no); 720575940610505006 (DNp103, check (i) no, check (iii) no); 720575940612203482 (DNp05, check (i) no, check (iii) no); 720575940619654053 (DNp02, check (i) no, check (iii) no); 720575940620054694 (DNp11, check (i) no, check (iii) no); 720575940620468718 (DNp02, check (i) no, check (iii) no); 720575940621401222 (DNpe025, check (i) no, check (iii) no); 720575940622673860 (DNp06, check (i) no, check (iii) no); 720575940622996579 (DNg40, check (i) no, check (iii) no); 720575940623781127 (DNp103, check (i) no, check (iii) no); 720575940626009852 (DNp05, check (i) no, check (iii) no); 720575940626901136 (DNg40, check (i) no, check (iii) no); 720575940627645514 (DNp03, check (i) no, check (iii) no); 720575940628437291 (DNp35, check (i) no, check (iii) no); 720575940629757036 (DNp04, check (i) no, check (iii) no); 720575940629777018 (DNp11, check (i) no, check (iii) no) | none | none |
| shuffle-2 | no | 1 / 17 | 720575940604954289 (DNp04, check (i) no, check (iii) no); 720575940610505006 (DNp103, check (i) no, check (iii) no); 720575940611644529 (DNp06, check (i) no, check (iii) no); 720575940612203482 (DNp05, check (i) no, check (iii) no); 720575940619654053 (DNp02, check (i) no, check (iii) no); 720575940620054694 (DNp11, check (i) no, check (iii) no); 720575940620468718 (DNp02, check (i) no, check (iii) no); 720575940621401222 (DNpe025, check (i) no, check (iii) no); 720575940622673860 (DNp06, check (i) no, check (iii) no); 720575940622996579 (DNg40, check (i) no, check (iii) no); 720575940623781127 (DNp103, check (i) no, check (iii) no); 720575940626009852 (DNp05, check (i) no, check (iii) no); 720575940626901136 (DNg40, check (i) no, check (iii) no); 720575940627645514 (DNp03, check (i) no, check (iii) no); 720575940629757036 (DNp04, check (i) no, check (iii) no); 720575940629777018 (DNp11, check (i) no, check (iii) no) | none | none |
| shuffle-3 | no | 1 / 17 | 720575940604954289 (DNp04, check (i) no, check (iii) no); 720575940611644529 (DNp06, check (i) no, check (iii) no); 720575940612203482 (DNp05, check (i) no, check (iii) no); 720575940619654053 (DNp02, check (i) no, check (iii) no); 720575940620054694 (DNp11, check (i) no, check (iii) no); 720575940620468718 (DNp02, check (i) no, check (iii) no); 720575940621401222 (DNpe025, check (i) no, check (iii) no); 720575940622673860 (DNp06, check (i) no, check (iii) no); 720575940622996579 (DNg40, check (i) no, check (iii) no); 720575940623781127 (DNp103, check (i) no, check (iii) no); 720575940626009852 (DNp05, check (i) no, check (iii) no); 720575940626901136 (DNg40, check (i) no, check (iii) no); 720575940627645514 (DNp03, check (i) no, check (iii) no); 720575940628437291 (DNp35, check (i) no, check (iii) no); 720575940629757036 (DNp04, check (i) no, check (iii) no); 720575940629777018 (DNp11, check (i) no, check (iii) no) | 720575940623276168 | none |

Tracked cell types (cell: retained / baseline (+ condition minus retained)):

| condition | DNp02 | DNp03 | DNp04 | DNp06 | DNp11 | DNg40 | DNp05 | DNp103 | DNp35 | DNpe025 |
|---|---|---|---|---|---|---|---|---|---|---|
| rate-50hz | 2 / 2 (+0) | 1 / 1 (+0) | 2 / 2 (+0) | 1 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 1 / 1 (+0) | 1 / 1 (+0) |
| rate-100hz | 2 / 2 (+0) | 1 / 1 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 1 / 1 (+0) | 1 / 1 (+0) |
| rate-200hz | 2 / 2 (+0) | 1 / 1 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 1 / 1 (+0) | 1 / 1 (+0) |
| wsyn-x0.50 | 2 / 2 (+0) | 1 / 1 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 1 / 1 (+1) | 1 / 1 (+0) |
| wsyn-x0.75 | 2 / 2 (+0) | 1 / 1 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 1 / 1 (+1) | 1 / 1 (+0) |
| wsyn-x1.50 | 2 / 2 (+0) | 1 / 1 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 1 / 1 (+0) | 1 / 1 (+0) |
| wsyn-x2.00 | 2 / 2 (+0) | 1 / 1 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 1 / 1 (+0) | 1 / 1 (+0) |
| fpoi-x0.50 | 2 / 2 (+0) | 1 / 1 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 1 / 1 (+0) | 1 / 1 (+0) |
| fpoi-x0.75 | 2 / 2 (+0) | 1 / 1 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 1 / 1 (+0) | 1 / 1 (+0) |
| fpoi-x1.50 | 2 / 2 (+0) | 1 / 1 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 1 / 1 (+0) | 1 / 1 (+0) |
| fpoi-x2.00 | 2 / 2 (+0) | 1 / 1 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 1 / 1 (+0) | 1 / 1 (+0) |
| stim-lc4-left | 1 / 2 (+0) | 1 / 1 (+0) | 1 / 2 (+0) | 1 / 2 (+0) | 1 / 2 (+0) | 2 / 2 (+0) | 1 / 2 (+0) | 1 / 2 (+0) | 1 / 1 (+0) | 0 / 1 (+0) |
| stim-lc4-right | 1 / 2 (+0) | 0 / 1 (+0) | 1 / 2 (+0) | 1 / 2 (+0) | 1 / 2 (+0) | 2 / 2 (+0) | 1 / 2 (+0) | 2 / 2 (+0) | 0 / 1 (+1) | 0 / 1 (+0) |
| stim-lc4-bilateral | 2 / 2 (+0) | 1 / 1 (+0) | 2 / 2 (+0) | 0 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 1 / 1 (+0) | 0 / 1 (+0) |
| stim-lplc2-left | 0 / 2 (+0) | 0 / 1 (+0) | 1 / 2 (+0) | 2 / 2 (+0) | 0 / 2 (+0) | 2 / 2 (+0) | 1 / 2 (+0) | 2 / 2 (+0) | 1 / 1 (+0) | 0 / 1 (+0) |
| stim-lplc2-right | 0 / 2 (+0) | 0 / 1 (+0) | 1 / 2 (+0) | 2 / 2 (+0) | 0 / 2 (+0) | 2 / 2 (+0) | 1 / 2 (+0) | 2 / 2 (+0) | 0 / 1 (+0) | 1 / 1 (+0) |
| stim-lplc2-bilateral | 0 / 2 (+0) | 0 / 1 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 0 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 0 / 1 (+0) | 1 / 1 (+0) |
| stim-both-left | 1 / 2 (+0) | 1 / 1 (+0) | 1 / 2 (+0) | 2 / 2 (+0) | 1 / 2 (+0) | 2 / 2 (+0) | 1 / 2 (+0) | 2 / 2 (+0) | 1 / 1 (+0) | 0 / 1 (+0) |
| stim-both-right | 1 / 2 (+0) | 0 / 1 (+0) | 1 / 2 (+0) | 2 / 2 (+0) | 1 / 2 (+0) | 2 / 2 (+0) | 1 / 2 (+0) | 2 / 2 (+0) | 0 / 1 (+1) | 1 / 1 (+0) |
| seed-1 | 2 / 2 (+0) | 1 / 1 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 1 / 1 (+0) | 1 / 1 (+0) |
| seed-2 | 2 / 2 (+0) | 1 / 1 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 1 / 1 (+0) | 1 / 1 (+0) |
| seed-3 | 2 / 2 (+0) | 1 / 1 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 1 / 1 (+0) | 1 / 1 (+0) |
| seed-4 | 2 / 2 (+0) | 1 / 1 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 1 / 1 (+0) | 1 / 1 (+0) |
| seed-5 | 2 / 2 (+0) | 1 / 1 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 2 / 2 (+0) | 1 / 1 (+0) | 1 / 1 (+0) |
| random-1 | 1 / 2 (+0) | 0 / 1 (+0) | 0 / 2 (+0) | 0 / 2 (+0) | 0 / 2 (+0) | 0 / 2 (+0) | 2 / 2 (+0) | 0 / 2 (+0) | 0 / 1 (+0) | 0 / 1 (+0) |
| random-2 | 1 / 2 (+0) | 1 / 1 (+0) | 0 / 2 (+0) | 0 / 2 (+0) | 0 / 2 (+0) | 0 / 2 (+0) | 2 / 2 (+0) | 0 / 2 (+0) | 0 / 1 (+0) | 0 / 1 (+0) |
| random-3 | 1 / 2 (+0) | 0 / 1 (+0) | 0 / 2 (+0) | 0 / 2 (+0) | 0 / 2 (+0) | 0 / 2 (+0) | 2 / 2 (+0) | 0 / 2 (+0) | 0 / 1 (+0) | 0 / 1 (+0) |
| shuffle-1 | 0 / 2 (+0) | 0 / 1 (+0) | 0 / 2 (+0) | 1 / 2 (+0) | 0 / 2 (+0) | 0 / 2 (+0) | 0 / 2 (+0) | 0 / 2 (+0) | 0 / 1 (+0) | 0 / 1 (+0) |
| shuffle-2 | 0 / 2 (+0) | 0 / 1 (+0) | 0 / 2 (+0) | 0 / 2 (+0) | 0 / 2 (+0) | 0 / 2 (+0) | 0 / 2 (+0) | 0 / 2 (+0) | 1 / 1 (+0) | 0 / 1 (+0) |
| shuffle-3 | 0 / 2 (+0) | 0 / 1 (+0) | 0 / 2 (+0) | 0 / 2 (+0) | 0 / 2 (+0) | 0 / 2 (+0) | 0 / 2 (+0) | 1 / 2 (+0) | 0 / 1 (+1) | 0 / 1 (+0) |

## Persistence

Persistence of a neuron is the fraction of completed non-control conditions in which the neuron was not stimulated and was responsive. The denominator counts only the conditions in which the neuron was not stimulated. Bins are cumulative.

Completed non-control conditions: 24.

| bin | all | input_lc4 | inter | not in baseline circuit | output_gf | output_parallel |
|---|---|---|---|---|---|---|
| 100% | 37 | 0 | 32 | 0 | 2 | 3 |
| >=90% | 128 | 0 | 121 | 0 | 2 | 5 |
| >=75% | 493 | 0 | 474 | 0 | 2 | 17 |
| >=50% | 911 | 0 | 881 | 11 | 2 | 17 |

| root_id | role | responsive / eligible | per family |
|---|---|---|---|
| 720575940602120928 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940602483424 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940603591014 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940603942828 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940603981536 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940604088288 | inter | 24 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940604434092 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940604470240 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940604569824 | inter | 24 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940604722278 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 2 / 4 |
| 720575940604938342 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940604954289 | output_parallel | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940605074278 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940605095346 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940605218220 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940605367473 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940605702944 | inter | 16 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940605829065 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940606149321 | inter | 24 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940606218528 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940606425033 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940606428850 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940606598758 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940606852018 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940607262219 | inter | 14 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940607774044 | inter | 22 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 4 / 4 |
| 720575940607800242 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940607889244 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940607915698 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940607982345 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940608083780 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940608118283 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940608120587 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 4 / 4 |
| 720575940608144732 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940608287497 | inter | 22 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 4 / 4 |
| 720575940608336514 | inter | 21 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940608343620 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940608368818 | inter | 14 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940608431625 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940608451420 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940608545219 | inter | 24 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940608566979 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 4 / 4 |
| 720575940608661955 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 4 / 4 |
| 720575940608845124 | inter | 16 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940609032824 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940609037432 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940609180718 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940609234130 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 3 / 4 |
| 720575940609365828 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940609423299 | inter | 19 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940609513841 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940609592270 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 2 / 4 |
| 720575940609600523 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940609675785 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940609961841 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940609996773 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940610063918 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940610199781 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940610236514 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 2 / 4 |
| 720575940610256370 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940610346163 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940610375214 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 3 / 4 |
| 720575940610412773 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940610432120 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940610484906 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940610504750 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940610505006 | output_parallel | 24 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940610515651 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940610549060 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940610604078 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940610605614 | inter | 24 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940610734449 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940610739918 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940611008409 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940611085274 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940611091012 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940611167842 | inter | 22 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 3 / 4 |
| 720575940611207922 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940611347123 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940611426161 | inter | 14 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940611499673 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940611509939 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940611596517 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 3 / 4 |
| 720575940611602552 | inter | 22 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 4 / 4 |
| 720575940611621166 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940611622826 | inter | 17 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940611633010 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940611638258 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940611644529 | output_parallel | 22 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 4 / 4 |
| 720575940611666898 | inter | 13 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 0 / 4 |
| 720575940611746418 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940611788714 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940611788970 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940611885461 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940611928930 | inter | 15 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 3 / 4 |
| 720575940611934706 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940611956946 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940611961878 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940612001489 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940612014120 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940612033253 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 2 / 4 |
| 720575940612203482 | output_parallel | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940612488341 | inter | 24 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940612508053 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 1 / 4 |
| 720575940612537061 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 3 / 4 |
| 720575940612612094 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940612682467 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940612710883 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940612752611 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 4 / 4 |
| 720575940612819367 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940612840982 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940612943539 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 3 / 4 |
| 720575940612990321 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940613019541 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940613025331 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940613154582 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 3 / 4 |
| 720575940613235865 | inter | 20 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 3 / 4 |
| 720575940613408552 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 2 / 4 |
| 720575940613436327 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940613491826 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940613511987 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940613639538 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940613668266 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940613681314 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 3 / 4 |
| 720575940613729022 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940613764817 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940613783277 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 4 / 4 |
| 720575940613824370 | inter | 16 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940613867938 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 1 / 4 |
| 720575940613891442 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940614009542 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940614009553 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940614058719 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940614079715 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940614175742 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940614207894 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 4 / 4 |
| 720575940614236200 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940614311746 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940614342038 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 2 / 4 |
| 720575940614367338 | inter | 13 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940614370610 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940614374034 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 2 / 4 |
| 720575940614380455 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940614434302 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940614441834 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 4 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940614492397 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 4 / 4 |
| 720575940614614495 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940614710509 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940614734754 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940614775592 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940614819926 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940614821661 | inter | 17 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 3 / 4 |
| 720575940614849832 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940614941992 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940614958120 | inter | 14 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940614979634 | inter | 18 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 2 / 4 |
| 720575940615028143 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940615043222 | inter | 17 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940615092019 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940615168985 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940615171003 | inter | 19 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940615205427 | inter | 17 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940615255603 | inter | 15 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940615391638 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940615408490 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940615429118 | inter | 22 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 3 / 4 |
| 720575940615526978 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940615528678 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940615635037 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940615723314 | inter | 17 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940615755147 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 4 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940615757162 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940615786897 | inter | 14 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940615798470 | inter | 15 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940615905373 | inter | 16 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940615924667 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940615928251 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 2 / 4 |
| 720575940615954070 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940615970015 | inter | 20 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 3 / 4 |
| 720575940616026939 | inter | 13 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 1 / 4 |
| 720575940616035990 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940616067701 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940616138123 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940616159773 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940616178026 | inter | 16 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940616194610 | inter | 15 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940616198715 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940616286175 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 3 / 4 |
| 720575940616313942 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940616392849 | inter | 16 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940616664550 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940616670016 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940616736198 | inter | 17 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 3 / 4 |
| 720575940616736230 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 4 / 4 |
| 720575940616766169 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940616783833 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940616807897 | inter | 17 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940616826380 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 4 / 4 |
| 720575940616865025 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940616907678 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 2 / 4 |
| 720575940616951739 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940616984588 | inter | 20 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 3 / 4 |
| 720575940616996364 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940617013554 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 4 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940617019442 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940617019846 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940617054237 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940617089241 | inter | 20 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940617097684 | inter | 17 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 2 / 4 |
| 720575940617098385 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 3 / 4 |
| 720575940617190361 | inter | 21 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 4 / 4 |
| 720575940617245652 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940617280657 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940617316326 | inter | 16 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940617318301 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940617398557 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 4 / 4 |
| 720575940617437697 | inter | 19 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940617442561 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940617444130 | inter | 24 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940617499205 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940617636981 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940617720577 | inter | 15 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 1 / 4 |
| 720575940617912267 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940617918021 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940617948445 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 3 / 4 |
| 720575940618028125 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940618058048 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 1 / 4 |
| 720575940618131928 | inter | 19 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 2 / 4 |
| 720575940618153105 | inter | 14 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940618156689 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940618157110 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 3 / 4 |
| 720575940618165393 | inter | 24 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940618189227 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940618243009 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 3 / 4 |
| 720575940618273241 | inter | 22 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 4 / 4 |
| 720575940618314897 | inter | 24 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940618330041 | inter | 22 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 4 / 4 |
| 720575940618340057 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940618366843 | inter | 22 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 4 / 4 |
| 720575940618380667 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 4 / 4 |
| 720575940618396609 | inter | 13 / 24 | f_poi 3 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 1 / 4 |
| 720575940618432185 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940618440000 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 3 / 4 |
| 720575940618460857 | inter | 16 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940618514043 | inter | 13 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 0 / 4 |
| 720575940618521273 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940618522433 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940618603009 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940618668198 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940618709158 | input_lc4 | 2 / 5 | f_poi 0 / 0; rate 0 / 0; seed 0 / 0; subset_side 2 / 5; w_syn 0 / 0 |
| 720575940618731284 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940618769153 | inter | 22 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 4 / 4 |
| 720575940618845531 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940618886710 | inter | 17 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940618902488 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 4 / 4 |
| 720575940618932763 | inter | 22 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 4 / 4 |
| 720575940618965553 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940618987600 | inter | 18 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 4 / 4 |
| 720575940619038493 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940619046469 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940619075920 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940619076918 | inter | 14 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940619097905 | inter | 24 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940619119963 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940619191966 | inter | 24 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940619263323 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940619264193 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940619317441 | inter | 16 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940619397542 | input_lc4 | 1 / 5 | f_poi 0 / 0; rate 0 / 0; seed 0 / 0; subset_side 1 / 5; w_syn 0 / 0 |
| 720575940619435655 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940619486891 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940619592768 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 4 / 4 |
| 720575940619601488 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940619654053 | output_parallel | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940619676224 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940619682368 | inter | 14 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940619688688 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940619709972 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940619731334 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 4 / 4 |
| 720575940619813057 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940619822784 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940619864047 | inter | 19 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940619977118 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940619991862 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940620001360 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940620020315 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 4 / 4 |
| 720575940620054637 | inter | 14 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940620054694 | output_parallel | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940620058209 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940620119279 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940620123631 | inter | 19 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940620124143 | inter | 17 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 2 / 4 |
| 720575940620156209 | inter | 22 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 3 / 4 |
| 720575940620157093 | inter | 13 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940620165541 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940620167706 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940620170119 | inter | 16 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 2 / 4 |
| 720575940620173737 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940620241573 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 2 / 4 |
| 720575940620300308 | inter | 16 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 2 / 4 |
| 720575940620320902 | inter | 22 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 4 / 4 |
| 720575940620321728 | inter | 22 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 4 / 4 |
| 720575940620330545 | inter | 22 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 4 / 4 |
| 720575940620381575 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940620468718 | output_parallel | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940620474278 | inter | 13 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940620534768 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940620537153 | inter | 24 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940620556966 | inter | 24 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940620571953 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 4 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940620657857 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940620706776 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940620708109 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940620723126 | inter | 22 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 4 / 4 |
| 720575940620745200 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940620771521 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940620813989 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940620835327 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 3 / 4 |
| 720575940620849157 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940620943969 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940620988276 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940621018977 | inter | 17 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940621052848 | inter | 16 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940621067204 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940621107847 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940621157645 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940621164532 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 4 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940621277790 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940621301274 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940621305024 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940621313414 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940621319924 | inter | 19 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940621333509 | inter | 19 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940621354736 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940621364872 | inter | 9 / 24 | f_poi 3 / 4; rate 1 / 3; seed 3 / 5; subset_side 2 / 8; w_syn 0 / 4 |
| 720575940621365236 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940621371045 | inter | 24 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940621393172 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 3 / 4 |
| 720575940621401222 | output_parallel | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940621422319 | inter | 22 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 4 / 4 |
| 720575940621543194 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940621544944 | inter | 10 / 24 | f_poi 3 / 4; rate 1 / 3; seed 4 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940621573056 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940621602139 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940621640170 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940621640363 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 3 / 4 |
| 720575940621689727 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940621726698 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940621752001 | inter | 22 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 4 / 4 |
| 720575940621814911 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940621819227 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940621819630 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 2 / 4 |
| 720575940621820404 | inter | 22 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 4 / 4 |
| 720575940621929641 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940621976097 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 3 / 4 |
| 720575940622007472 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940622010373 | inter | 22 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940622053185 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940622055777 | inter | 16 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940622057057 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 2 / 4 |
| 720575940622140481 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940622160705 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 2 / 4 |
| 720575940622161366 | inter | 19 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940622186305 | inter | 24 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940622195625 | inter | 11 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 0 / 4 |
| 720575940622238934 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940622266061 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 2 / 4 |
| 720575940622304243 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940622324991 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940622335331 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940622339113 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940622366814 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940622388318 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940622459588 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940622473292 | inter | 22 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940622486644 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940622500172 | inter | 22 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 4 / 4 |
| 720575940622523508 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940622525729 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940622550089 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940622611711 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940622633716 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 4 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940622669567 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940622673860 | output_parallel | 21 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 4 / 4 |
| 720575940622680724 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940622681889 | inter | 17 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940622786380 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940622838154 | output_gf | 24 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940622859021 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940622860617 | inter | 19 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940622932164 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940622932487 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940622945037 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 2 / 4 |
| 720575940622972259 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940622975624 | inter | 4 / 24 | f_poi 0 / 4; rate 1 / 3; seed 1 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940622996579 | output_parallel | 24 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940622998627 | inter | 24 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940623016709 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 3 / 4 |
| 720575940623025413 | inter | 22 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 3 / 4 |
| 720575940623054333 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940623062515 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940623072013 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 3 / 4 |
| 720575940623124467 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 1 / 4 |
| 720575940623125628 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940623148109 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940623153788 | inter | 13 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940623203805 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940623338281 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940623432918 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 2 / 4 |
| 720575940623433725 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940623455239 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940623491369 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940623556755 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940623560413 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 3 / 4 |
| 720575940623579063 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940623608361 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940623636957 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940623702345 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940623713168 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940623718119 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 4 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940623781127 | output_parallel | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940623784596 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940623806157 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940623860458 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940623868391 | inter | 13 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940623878891 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940623953900 | inter | 20 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940623957173 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940623983859 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 3 / 4 |
| 720575940624028855 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 4 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940624038438 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940624047615 | inter | 8 / 24 | f_poi 2 / 4; rate 1 / 3; seed 3 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940624068028 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940624145191 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940624192549 | inter | 13 / 24 | f_poi 3 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940624231143 | inter | 23 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940624231719 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940624299534 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 4 / 4 |
| 720575940624336647 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940624349993 | inter | 24 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940624358152 | inter | 22 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 4 / 4 |
| 720575940624373898 | inter | 7 / 24 | f_poi 1 / 4; rate 1 / 3; seed 3 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940624377224 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940624402173 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 2 / 4 |
| 720575940624426680 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940624434323 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 3 / 4 |
| 720575940624439498 | inter | 18 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940624452902 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 4 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940624508563 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940624526925 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940624533956 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940624537284 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 3 / 4 |
| 720575940624676861 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940624710653 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 2 / 4 |
| 720575940624735463 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940624739929 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940624743946 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940624758361 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940624766700 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940624801771 | inter | 17 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 3 / 4 |
| 720575940624846517 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940624864585 | inter | 11 / 24 | f_poi 4 / 4; rate 1 / 3; seed 3 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940624915128 | inter | 7 / 24 | f_poi 2 / 4; rate 1 / 3; seed 1 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940624945333 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940624951847 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 2 / 4 |
| 720575940624972523 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940624991527 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 3 / 4 |
| 720575940624996894 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940624996901 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940625017783 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940625132797 | inter | 24 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940625194558 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940625214183 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940625295339 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940625323620 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940625347657 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940625357547 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940625371155 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940625388873 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940625502666 | inter | 15 / 24 | f_poi 4 / 4; rate 2 / 3; seed 2 / 5; subset_side 4 / 8; w_syn 3 / 4 |
| 720575940625508610 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940625518736 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940625525740 | inter | 20 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 3 / 4 |
| 720575940625531236 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940625556668 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940625656980 | inter | 19 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 4 / 4 |
| 720575940625673196 | inter | 17 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940625827358 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 4 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940625871408 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940625878160 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940625894799 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940625904414 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940625923965 | inter | 15 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 3 / 4 |
| 720575940625952755 | inter | 15 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 3 / 4 |
| 720575940625972867 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940625987571 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940626009852 | output_parallel | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940626013315 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940626022074 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940626039996 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 3 / 4 |
| 720575940626044942 | inter | 22 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 4 / 4 |
| 720575940626046919 | inter | 19 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940626052540 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940626085562 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940626125331 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940626138701 | inter | 24 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940626214275 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940626228057 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940626243614 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940626252053 | inter | 16 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940626255637 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940626308697 | inter | 15 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940626309562 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940626408454 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940626436126 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940626482813 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940626510169 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940626528252 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 3 / 4 |
| 720575940626575997 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940626577425 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940626583056 | inter | 20 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940626630693 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940626663953 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940626677097 | inter | 17 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940626688772 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 2 / 4 |
| 720575940626726458 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940626741379 | inter | 19 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940626751294 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940626774863 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940626783065 | inter | 24 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940626818085 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940626861104 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940626887198 | inter | 22 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 4 / 4 |
| 720575940626889491 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940626901136 | output_parallel | 24 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940626933647 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940626943518 | inter | 14 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940626952847 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940626960536 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940626961241 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940627015196 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940627053861 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 3 / 4 |
| 720575940627068772 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940627069712 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 3 / 4 |
| 720575940627076106 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 3 / 4 |
| 720575940627083397 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940627087646 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940627096068 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940627096957 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 2 / 4 |
| 720575940627107721 | inter | 20 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 3 / 4 |
| 720575940627126866 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940627206842 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940627249338 | inter | 14 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940627249850 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940627253604 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940627293540 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940627357457 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940627371326 | inter | 10 / 24 | f_poi 3 / 4; rate 1 / 3; seed 4 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940627384851 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940627405058 | inter | 24 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940627410451 | inter | 11 / 24 | f_poi 4 / 4; rate 0 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 0 / 4 |
| 720575940627439592 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940627447272 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940627469041 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940627484181 | inter | 19 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940627495452 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940627510012 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940627538434 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940627607812 | inter | 19 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940627620593 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940627638037 | inter | 17 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940627645514 | output_parallel | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940627702293 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940627715870 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 2 / 4 |
| 720575940627723657 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940627731599 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940627796298 | inter | 24 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940627803241 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940627850618 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940627852563 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940627866856 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940627888144 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 2 / 4 |
| 720575940627910010 | inter | 17 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940627924227 | inter | 13 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940627949589 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 3 / 4 |
| 720575940627996285 | inter | 19 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 3 / 4 |
| 720575940628102652 | inter | 24 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940628120744 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940628132745 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 3 / 4 |
| 720575940628145257 | inter | 11 / 24 | f_poi 2 / 4; rate 1 / 3; seed 4 / 5; subset_side 3 / 8; w_syn 1 / 4 |
| 720575940628154364 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 2 / 4 |
| 720575940628169219 | inter | 22 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 4 / 4 |
| 720575940628192220 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940628197392 | inter | 13 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940628236169 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 3 / 4 |
| 720575940628251146 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 4 / 4 |
| 720575940628255621 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940628258577 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940628314667 | inter | 14 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 3 / 4 |
| 720575940628336134 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940628339611 | inter | 11 / 24 | f_poi 4 / 4; rate 1 / 3; seed 4 / 5; subset_side 1 / 8; w_syn 1 / 4 |
| 720575940628342282 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940628346634 | inter | 24 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940628352850 | inter | 22 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 3 / 4 |
| 720575940628355856 | inter | 11 / 24 | f_poi 4 / 4; rate 1 / 3; seed 3 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940628403791 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940628437291 | output_parallel | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 4 / 4 |
| 720575940628459011 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940628463468 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940628498161 | inter | 14 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940628522540 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 2 / 4 |
| 720575940628523113 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 3 / 4 |
| 720575940628537852 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940628538732 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940628579066 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940628582929 | inter | 21 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 4 / 4 |
| 720575940628641127 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940628646160 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940628659650 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 3 / 4 |
| 720575940628678991 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940628702935 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940628709653 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940628716821 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940628731140 | inter | 14 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940628779898 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940628793621 | inter | 22 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 4 / 4 |
| 720575940628883535 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940628956636 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940628998659 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940629008439 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940629072762 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940629125996 | inter | 15 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 3 / 4 |
| 720575940629144906 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940629164842 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940629177655 | inter | 20 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940629179722 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940629179900 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940629192975 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940629229020 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940629240263 | inter | 16 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 2 / 4 |
| 720575940629245903 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940629249783 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940629254647 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940629289472 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940629310970 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940629320010 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940629358321 | inter | 24 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940629361346 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940629414987 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940629426025 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940629437545 | inter | 19 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 4 / 4 |
| 720575940629461442 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 3 / 4 |
| 720575940629464305 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 3 / 4 |
| 720575940629488682 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940629488902 | inter | 20 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 3 / 4 |
| 720575940629489414 | inter | 18 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 2 / 4 |
| 720575940629513478 | inter | 24 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940629517049 | inter | 16 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940629524483 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 0 / 4 |
| 720575940629525882 | inter | 15 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 3 / 4 |
| 720575940629539628 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940629545883 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940629591793 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940629602871 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940629609457 | inter | 22 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 4 / 4 |
| 720575940629637163 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940629677112 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940629757036 | output_parallel | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940629766615 | inter | 22 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940629777018 | output_parallel | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940629846722 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 1 / 4 |
| 720575940629853739 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 3 / 4 |
| 720575940629859115 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940629920056 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940630029307 | inter | 11 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 1 / 4 |
| 720575940630072364 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940630133110 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 2 / 4 |
| 720575940630135084 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940630216263 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940630291671 | inter | 22 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 4 / 4 |
| 720575940630318533 | inter | 22 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 4 / 4 |
| 720575940630385000 | inter | 15 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 3 / 4 |
| 720575940630463908 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940630559908 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 1 / 4 |
| 720575940630574396 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940630607738 | inter | 7 / 24 | f_poi 2 / 4; rate 1 / 3; seed 0 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940630637330 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940630657271 | inter | 21 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 2 / 4 |
| 720575940630708498 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940630733884 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 1 / 4 |
| 720575940630745148 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940630758418 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 3 / 4 |
| 720575940630773560 | inter | 17 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940630810486 | inter | 19 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940630815545 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940630927104 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940631082808 | inter | 14 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940631091407 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940631131436 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940631176151 | inter | 22 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 4 / 4 |
| 720575940631200327 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940631267655 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940631269935 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940631283471 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940631283512 | inter | 22 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 4 / 4 |
| 720575940631293202 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940631299602 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 2 / 4 |
| 720575940631306041 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940631319311 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940631335528 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940631383400 | inter | 20 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940631463272 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940631579929 | inter | 19 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 4 / 4 |
| 720575940631617017 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 3 / 4 |
| 720575940631625979 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940631638521 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940631642937 | inter | 16 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940631663052 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940631670615 | inter | 15 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940631693610 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940631698340 | inter | 18 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 2 / 4 |
| 720575940631770593 | inter | 13 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940631842360 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 4 / 4 |
| 720575940631857548 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940631947095 | inter | 15 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940631999685 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940632042148 | inter | 19 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940632043576 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940632059309 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 2 / 4 |
| 720575940632179148 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940632189900 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940632197969 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940632211015 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940632316205 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940632381536 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940632387353 | inter | 14 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940632407826 | inter | 13 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940632427112 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940632469290 | inter | 24 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940632472850 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940632486969 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 3 / 4 |
| 720575940632495135 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 4 / 4 |
| 720575940632499757 | output_gf | 24 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940632524559 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940632527683 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 3 / 4 |
| 720575940632548665 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 1 / 4 |
| 720575940632557664 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940632634532 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940632704173 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940632777320 | inter | 22 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 4 / 4 |
| 720575940632804435 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 3 / 4 |
| 720575940632807193 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 4 / 5; subset_side 2 / 8; w_syn 1 / 4 |
| 720575940632900665 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940632903737 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940633166617 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940633170643 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 2 / 4 |
| 720575940633176749 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940633315263 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 4 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940633350812 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940633366754 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940633429331 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 2 / 4 |
| 720575940633471583 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 1 / 4 |
| 720575940633498524 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940633529548 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940633560089 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940633572004 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940633612492 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 2 / 4 |
| 720575940633631396 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 3 / 4 |
| 720575940633746515 | inter | 19 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940633763411 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 2 / 4 |
| 720575940633774361 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940633796252 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 3 / 4 |
| 720575940633893401 | inter | 22 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 4 / 4 |
| 720575940633901395 | inter | 19 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940633903897 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 2 / 4 |
| 720575940633915309 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940633995949 | inter | 20 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940633996444 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940633996883 | inter | 17 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 3 / 4 |
| 720575940634062803 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 3 / 4 |
| 720575940634158175 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940634165646 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940634172267 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 4 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940634317724 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940634356587 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940634458719 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940634528864 | inter | 22 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 3 / 4 |
| 720575940634571383 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940634612194 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940634617952 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940634638562 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 1 / 4 |
| 720575940634646753 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940634660833 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940634676916 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940634748385 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 3 / 4 |
| 720575940634763877 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940634823449 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940634874266 | inter | 20 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940634895514 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 3 / 4 |
| 720575940634903800 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940635028591 | inter | 22 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940635069547 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940635089945 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940635116569 | inter | 10 / 24 | f_poi 2 / 4; rate 1 / 3; seed 4 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940635119723 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 4 / 4 |
| 720575940635202204 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940635211115 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940635211768 | inter | 24 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940635549620 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940635552948 | inter | 17 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940635774071 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940635837887 | inter | 7 / 24 | f_poi 1 / 4; rate 1 / 3; seed 3 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940635859354 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940635967886 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940635968398 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940636151871 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940636160319 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940636280809 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940636396400 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 3 / 4 |
| 720575940636533574 | inter | 20 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940636561754 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940636573108 | inter | 16 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940636574644 | inter | 21 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 3 / 4 |
| 720575940636656632 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940636700272 | inter | 15 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940636704357 | inter | 22 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 4 / 4 |
| 720575940636807652 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940636832879 | inter | 23 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940636844870 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940637071849 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 4 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940637085503 | inter | 20 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940637209822 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940637258985 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940637341668 | inter | 24 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940637603038 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940637635305 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 3 / 4 |
| 720575940637718912 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940637826118 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940637834301 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940637952624 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940638049136 | inter | 22 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 4 / 4 |
| 720575940638051696 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940638204132 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940638231861 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940638360798 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940638603709 | inter | 20 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940638637501 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940638642776 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940638668878 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940638715251 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940638897315 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 1 / 4 |
| 720575940638900713 | inter | 24 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940638910040 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 4 / 4 |
| 720575940639123544 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940639128646 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940639193577 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940639352483 | inter | 18 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940639417728 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940639900213 | inter | 20 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940640111568 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940640172221 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940640249296 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940640331472 | inter | 15 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940640332110 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 3 / 4 |
| 720575940640485109 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940640714192 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940640834211 | inter | 24 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940640868184 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940640926627 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940640978048 | inter | 17 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 2 / 4 |
| 720575940640978421 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 2 / 4 |
| 720575940641096144 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940641188304 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940641216976 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940641220853 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940641282267 | inter | 24 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 8 / 8; w_syn 4 / 4 |
| 720575940641363957 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940641464309 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 3 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940641706184 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 3 / 4 |
| 720575940641797773 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940642884000 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 3 / 4 |
| 720575940642894628 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940643118733 | inter | 20 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940643290272 | inter | 16 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 1 / 4 |
| 720575940643754862 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940643826212 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940644184087 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940644300323 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 1 / 4 |
| 720575940644306592 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940644447511 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 6 / 8; w_syn 3 / 4 |
| 720575940644465568 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940644639342 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 1 / 4 |
| 720575940644775534 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 2 / 4 |
| 720575940644791918 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940645360663 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940645404695 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940645697828 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 3 / 4 |
| 720575940645742884 | inter | 19 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940645761844 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940646414132 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940646419747 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940646814340 | inter | 16 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940647010356 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940647061556 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940647253795 | inter | 12 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 0 / 8; w_syn 2 / 4 |
| 720575940647586681 | inter | 17 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940647663748 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 2 / 8; w_syn 2 / 4 |
| 720575940647882548 | inter | 18 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 4 / 4 |
| 720575940647966260 | inter | 23 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 7 / 8; w_syn 4 / 4 |
| 720575940648636292 | inter | 19 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 4 / 8; w_syn 3 / 4 |
| 720575940651804918 | inter | 20 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 3 / 4 |
| 720575940651833078 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |
| 720575940653213174 | inter | 13 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 2 / 4 |
| 720575940653310198 | inter | 14 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 1 / 8; w_syn 3 / 4 |
| 720575940653703841 | inter | 16 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940654008737 | inter | 18 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940655000737 | inter | 17 / 24 | f_poi 4 / 4; rate 2 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 3 / 4 |
| 720575940659613569 | inter | 15 / 24 | f_poi 4 / 4; rate 1 / 3; seed 5 / 5; subset_side 3 / 8; w_syn 2 / 4 |
| 720575940660051073 | inter | 21 / 24 | f_poi 4 / 4; rate 3 / 3; seed 5 / 5; subset_side 5 / 8; w_syn 4 / 4 |

## Failed, dropped or reduced conditions

- Step 1: the interaction family (R7) was dropped.
- Step 2: random-set and shuffle controls were cut to 3 draws each.
- Step 3: trials of non-baseline conditions not yet run were cut to 15.
- Dropped: inter-lc4-50hz, inter-lc4-100hz, inter-lc4-200hz, inter-lplc2-50hz, inter-lplc2-100hz, inter-lplc2-200hz, random-4, random-5, shuffle-4, shuffle-5
- Reduced: fpoi-x0.50 to 15 trials
- Reduced: fpoi-x0.75 to 15 trials
- Reduced: fpoi-x1.50 to 15 trials
- Reduced: fpoi-x2.00 to 15 trials
- Reduced: random-1 to 15 trials
- Reduced: random-2 to 15 trials
- Reduced: random-3 to 15 trials
- Reduced: seed-1 to 15 trials
- Reduced: seed-2 to 15 trials
- Reduced: seed-3 to 15 trials
- Reduced: seed-4 to 15 trials
- Reduced: seed-5 to 15 trials
- Reduced: shuffle-1 to 15 trials
- Reduced: shuffle-2 to 15 trials
- Reduced: shuffle-3 to 15 trials
- Reduced: stim-both-left to 15 trials
- Reduced: stim-both-right to 15 trials
- Reduced: stim-lc4-bilateral to 15 trials
- Reduced: stim-lc4-left to 15 trials
- Reduced: stim-lc4-right to 15 trials
- Reduced: stim-lplc2-bilateral to 15 trials
- Reduced: stim-lplc2-left to 15 trials
- Reduced: stim-lplc2-right to 15 trials
- Reduced: wsyn-x0.50 to 15 trials
- Reduced: wsyn-x0.75 to 15 trials
- Reduced: wsyn-x1.50 to 15 trials
- Reduced: wsyn-x2.00 to 15 trials

## Run cost

Per-condition and total wall times are kept out of this file for byte reproducibility; they are in the git-ignored run log discover/robustness/run_log.json and summarized in discovery/README.md next to the pre-run estimate.

