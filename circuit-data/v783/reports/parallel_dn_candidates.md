# Parallel DN candidates (v783)

Responsive rule (min_rate_hz=2.0, min_trial_frac=0.5): responsive iff mean rate over trials >= min_rate_hz and fired in >= min_trial_frac of trials; applied to non-stimulated neurons; stimulated neurons are inputs

Connection filter: keep edge iff syn_count > 10 or syn_count > 1% of the target's total input synapses (100*syn_count > input_total); totals over all proofread inputs before restriction; counts aggregated per neuron pair across neuropils

Evidence: prior set {DNp02, DNp03, DNp04, DNp06} is LOW evidence (ADR-15); others are data-driven. No candidate is literature-confirmed in M5.

## Giant fiber (DNp01)

| root_id | side | responsive | rate Hz | rel rate | trial frac |
|---|---|---|---|---|---|
| 720575940622838154 | left | yes | 175.833 | 0.5989 | 1.000 |
| 720575940632499757 | right | yes | 195.067 | 0.6644 | 1.000 |

## Candidates

| cell_type | root_id | side | label | evidence | responsive | rate Hz | rel rate | trial frac | LC4 syn raw | LC4 syn kept | LPLC2 syn raw | LPLC2 syn kept | (i) | (ii) | (iii) | role |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DNp02 | 720575940619654053 | left | prior | LOW | yes | 142.100 | 0.4840 | 1.000 | 525 | 331 | 5 | 0 | pass | pass | pass | output_parallel |
| DNp02 | 720575940620468718 | right | prior | LOW | yes | 131.033 | 0.4463 | 1.000 | 476 | 244 | 0 | 0 | pass | pass | pass | output_parallel |
| DNp03 | 720575940627645514 | left | prior | LOW | yes | 89.467 | 0.3047 | 1.000 | 366 | 128 | 11 | 0 | pass | pass | pass | output_parallel |
| DNp03 | 720575940628884496 | right | prior | LOW | no | 0.000 | 0.0000 | 0.000 | 7 | 0 | 0 | 0 | fail | fail | fail | not in circuit |
| DNp04 | 720575940604954289 | left | prior | LOW | yes | 221.767 | 0.7553 | 1.000 | 1064 | 1012 | 607 | 108 | pass | pass | pass | output_parallel |
| DNp04 | 720575940629757036 | right | prior | LOW | yes | 206.267 | 0.7025 | 1.000 | 790 | 688 | 605 | 225 | pass | pass | pass | output_parallel |
| DNp06 | 720575940611644529 | right | prior | LOW | yes | 119.967 | 0.4086 | 1.000 | 105 | 0 | 518 | 137 | pass | pass | pass | output_parallel |
| DNp06 | 720575940622673860 | left | prior | LOW | yes | 112.933 | 0.3847 | 1.000 | 58 | 0 | 485 | 92 | pass | pass | pass | output_parallel |
| DNp11 | 720575940620054694 | left | reported | data-driven | yes | 139.467 | 0.4750 | 1.000 | 570 | 438 | 17 | 0 | pass | pass | pass | output_parallel |
| DNp11 | 720575940629777018 | right | reported | data-driven | yes | 81.267 | 0.2768 | 1.000 | 353 | 220 | 2 | 0 | pass | pass | pass | output_parallel |
| DNa05 | 720575940620534768 | left | data-driven | data-driven | yes | 29.033 | 0.0989 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNa05 | 720575940623062515 | right | data-driven | data-driven | yes | 6.633 | 0.0226 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNa13 | 720575940616286175 | left | data-driven | data-driven | yes | 14.133 | 0.0481 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNa13 | 720575940613408552 | left | data-driven | data-driven | yes | 4.133 | 0.0141 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNa13 | 720575940625502666 | right | data-driven | data-driven | yes | 2.267 | 0.0077 | 0.933 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNae004 | 720575940603591014 | left | data-driven | data-driven | yes | 13.333 | 0.0454 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNae007 | 720575940615043222 | right | data-driven | data-driven | yes | 3.433 | 0.0117 | 1.000 | 0 | 0 | 5 | 0 | pass | fail | pass | inter |
| DNae007 | 720575940630607738 | left | data-driven | data-driven | yes | 2.067 | 0.0070 | 0.867 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNb01 | 720575940630758418 | right | data-driven | data-driven | yes | 27.467 | 0.0936 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNb01 | 720575940625878160 | left | data-driven | data-driven | yes | 14.100 | 0.0480 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNb05 | 720575940629461442 | right | data-driven | data-driven | yes | 52.267 | 0.1780 | 1.000 | 5 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNb05 | 720575940628352850 | left | data-driven | data-driven | yes | 43.500 | 0.1482 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNb09 | 720575940616826380 | left | data-driven | data-driven | yes | 34.767 | 0.1184 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNb09 | 720575940648636292 | right | data-driven | data-driven | yes | 11.200 | 0.0381 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNbe004 | 720575940653310198 | right | data-driven | data-driven | yes | 18.067 | 0.0615 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNbe004 | 720575940627731599 | left | data-driven | data-driven | yes | 5.433 | 0.0185 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNg100 | 720575940640978048 | left | data-driven | data-driven | yes | 2.933 | 0.0100 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNg108 | 720575940632043576 | right | data-driven | data-driven | yes | 64.133 | 0.2184 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNg108 | 720575940627015196 | left | data-driven | data-driven | yes | 50.033 | 0.1704 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNg40 | 720575940626901136 | left | data-driven | data-driven | yes | 150.100 | 0.5112 | 1.000 | 77 | 0 | 427 | 76 | pass | pass | pass | output_parallel |
| DNg40 | 720575940622996579 | right | data-driven | data-driven | yes | 143.433 | 0.4885 | 1.000 | 41 | 0 | 402 | 76 | pass | pass | pass | output_parallel |
| DNg45 | 720575940622486644 | right | data-driven | data-driven | yes | 8.700 | 0.0296 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNg54 | 720575940618514043 | left | data-driven | data-driven | yes | 2.967 | 0.0101 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNg55 | 720575940622010373 | center | data-driven | data-driven | yes | 62.300 | 0.2122 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNg57 | 720575940634617952 | left | data-driven | data-driven | yes | 11.633 | 0.0396 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNg57 | 720575940632634532 | right | data-driven | data-driven | yes | 6.467 | 0.0220 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNg70 | 720575940632524559 | right | data-driven | data-driven | yes | 8.733 | 0.0297 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNg70 | 720575940632407826 | left | data-driven | data-driven | yes | 4.667 | 0.0159 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNg74_a | 720575940633529548 | left | data-driven | data-driven | yes | 55.700 | 0.1897 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNg74_a | 720575940622500172 | right | data-driven | data-driven | yes | 47.633 | 0.1622 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNg74_b | 720575940636656632 | left | data-driven | data-driven | yes | 58.733 | 0.2000 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNg74_b | 720575940627087646 | right | data-driven | data-driven | yes | 53.867 | 0.1835 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNg79 | 720575940627538434 | right | data-driven | data-driven | yes | 2.600 | 0.0089 | 0.933 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNg93 | 720575940613019541 | right | data-driven | data-driven | yes | 34.267 | 0.1167 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNg93 | 720575940626085562 | left | data-driven | data-driven | yes | 28.000 | 0.0954 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNg97 | 720575940620300308 | right | data-driven | data-driven | yes | 8.100 | 0.0276 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNg98 | 720575940623338281 | right | data-driven | data-driven | yes | 48.233 | 0.1643 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNg98 | 720575940630810486 | left | data-driven | data-driven | yes | 28.900 | 0.0984 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNge003 | 720575940622195625 | right | data-driven | data-driven | yes | 4.067 | 0.0139 | 0.967 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNge036 | 720575940632486969 | left | data-driven | data-driven | yes | 29.100 | 0.0991 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNge036 | 720575940627107721 | right | data-driven | data-driven | yes | 22.167 | 0.0755 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNge038 | 720575940637603038 | right | data-driven | data-driven | yes | 49.933 | 0.1701 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNge038 | 720575940621313414 | left | data-driven | data-driven | yes | 10.100 | 0.0344 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNge041 | 720575940629240263 | right | data-driven | data-driven | yes | 2.867 | 0.0098 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNge041 | 720575940622633716 | left | data-driven | data-driven | yes | 2.133 | 0.0073 | 0.933 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNge047 | 720575940614342038 | left | data-driven | data-driven | yes | 12.767 | 0.0435 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNge053 | 720575940638204132 | left | data-driven | data-driven | yes | 102.367 | 0.3487 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNge053 | 720575940630135084 | right | data-driven | data-driven | yes | 91.200 | 0.3106 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNge054 | 720575940622161366 | right | data-driven | data-driven | yes | 32.500 | 0.1107 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNge099 | 720575940631091407 | left | data-driven | data-driven | yes | 65.733 | 0.2239 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNge099 | 720575940628883535 | right | data-driven | data-driven | yes | 54.133 | 0.1844 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNge119 | 720575940619191966 | right | data-driven | data-driven | yes | 119.600 | 0.4074 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNge119 | 720575940610605614 | left | data-driven | data-driven | yes | 106.300 | 0.3621 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNge124 | 720575940626889491 | right | data-driven | data-driven | yes | 21.400 | 0.0729 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNge124 | 720575940624537284 | left | data-driven | data-driven | yes | 12.333 | 0.0420 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNge131 | 720575940621107847 | right | data-driven | data-driven | yes | 21.633 | 0.0737 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNge131 | 720575940617918021 | left | data-driven | data-driven | yes | 5.833 | 0.0199 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNge136 | 720575940633996883 | left | data-driven | data-driven | yes | 25.100 | 0.0855 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNge136 | 720575940610604078 | right | data-driven | data-driven | yes | 10.733 | 0.0366 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNge136 | 720575940606425033 | right | data-driven | data-driven | yes | 2.500 | 0.0085 | 0.900 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNp05 | 720575940612203482 | left | data-driven | data-driven | yes | 115.900 | 0.3948 | 1.000 | 346 | 159 | 32 | 0 | pass | pass | pass | output_parallel |
| DNp05 | 720575940626009852 | right | data-driven | data-driven | yes | 114.400 | 0.3896 | 1.000 | 295 | 128 | 17 | 0 | pass | pass | pass | output_parallel |
| DNp07 | 720575940622550089 | right | data-driven | data-driven | yes | 41.400 | 0.1410 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNp08 | 720575940633170643 | right | data-driven | data-driven | yes | 17.567 | 0.0598 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNp08 | 720575940628498161 | left | data-driven | data-driven | yes | 13.233 | 0.0451 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNp102 | 720575940610199781 | right | data-driven | data-driven | yes | 44.633 | 0.1520 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNp102 | 720575940638637501 | left | data-driven | data-driven | yes | 41.333 | 0.1408 | 1.000 | 3 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNp103 | 720575940623781127 | left | data-driven | data-driven | yes | 202.200 | 0.6887 | 1.000 | 20 | 0 | 1346 | 1069 | pass | pass | pass | output_parallel |
| DNp103 | 720575940610505006 | right | data-driven | data-driven | yes | 192.133 | 0.6544 | 1.000 | 27 | 0 | 1284 | 1021 | pass | pass | pass | output_parallel |
| DNp13 | 720575940625295339 | right | data-driven | data-driven | yes | 6.933 | 0.0236 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNp13 | 720575940619486891 | left | data-driven | data-driven | yes | 5.100 | 0.0174 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNp18 | 720575940618440000 | left | data-driven | data-driven | yes | 15.400 | 0.0525 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNp18 | 720575940627949589 | right | data-driven | data-driven | yes | 7.667 | 0.0261 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNp27 | 720575940628731140 | left | data-driven | data-driven | yes | 7.100 | 0.0242 | 1.000 | 0 | 0 | 2 | 0 | pass | fail | pass | inter |
| DNp29 | 720575940635549620 | right | data-driven | data-driven | yes | 2.467 | 0.0084 | 0.967 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNp31 | 720575940632189900 | left | data-driven | data-driven | yes | 19.667 | 0.0670 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNp31 | 720575940628132745 | right | data-driven | data-driven | yes | 10.700 | 0.0364 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNp34 | 720575940642894628 | left | data-driven | data-driven | yes | 83.067 | 0.2829 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNp34 | 720575940632903737 | right | data-driven | data-driven | yes | 36.700 | 0.1250 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNp35 | 720575940628437291 | left | data-driven | data-driven | yes | 53.900 | 0.1836 | 1.000 | 203 | 13 | 286 | 31 | pass | pass | pass | output_parallel |
| DNp45 | 720575940617280657 | right | data-driven | data-driven | yes | 28.800 | 0.0981 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNp45 | 720575940624426680 | left | data-driven | data-driven | yes | 17.133 | 0.0584 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNp51 | 720575940612682467 | left | data-driven | data-driven | yes | 7.133 | 0.0243 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNp55 | 720575940617245652 | right | data-driven | data-driven | yes | 48.967 | 0.1668 | 1.000 | 0 | 0 | 116 | 0 | pass | fail | pass | inter |
| DNp57 | 720575940646814340 | left | data-driven | data-driven | yes | 5.067 | 0.0173 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNp64 | 720575940629846722 | right | data-driven | data-driven | yes | 6.533 | 0.0223 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNp70 | 720575940618314897 | right | data-driven | data-driven | yes | 135.933 | 0.4630 | 1.000 | 0 | 0 | 38 | 0 | pass | fail | pass | inter |
| DNp70 | 720575940624349993 | left | data-driven | data-driven | yes | 131.600 | 0.4482 | 1.000 | 0 | 0 | 31 | 0 | pass | fail | pass | inter |
| DNp71 | 720575940625673196 | left | data-driven | data-driven | yes | 2.600 | 0.0089 | 1.000 | 0 | 0 | 151 | 0 | pass | fail | pass | inter |
| DNpe014 | 720575940627924227 | left | data-driven | data-driven | yes | 14.133 | 0.0481 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNpe014 | 720575940623153788 | left | data-driven | data-driven | yes | 13.633 | 0.0464 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNpe016 | 720575940614236200 | right | data-driven | data-driven | yes | 71.800 | 0.2446 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNpe016 | 720575940623556755 | left | data-driven | data-driven | yes | 49.733 | 0.1694 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNpe019 | 720575940627620593 | left | data-driven | data-driven | yes | 8.833 | 0.0301 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNpe020 | 720575940624766700 | left | data-driven | data-driven | yes | 42.733 | 0.1455 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNpe020 | 720575940623125628 | right | data-driven | data-driven | yes | 25.633 | 0.0873 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNpe022 | 720575940615798470 | left | data-driven | data-driven | yes | 12.800 | 0.0436 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNpe022 | 720575940632900665 | right | data-driven | data-driven | yes | 2.567 | 0.0087 | 0.967 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNpe024 | 720575940621157645 | right | data-driven | data-driven | yes | 20.433 | 0.0696 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNpe025 | 720575940621401222 | right | data-driven | data-driven | yes | 75.800 | 0.2582 | 1.000 | 6 | 0 | 195 | 37 | pass | pass | pass | output_parallel |
| DNpe025 | 720575940611622826 | left | data-driven | data-driven | yes | 21.933 | 0.0747 | 1.000 | 7 | 0 | 76 | 0 | pass | fail | pass | inter |
| DNpe037 | 720575940635552948 | right | data-driven | data-driven | yes | 17.633 | 0.0601 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNpe040 | 720575940624801771 | left | data-driven | data-driven | yes | 26.067 | 0.0888 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNpe040 | 720575940605702944 | right | data-driven | data-driven | yes | 11.900 | 0.0405 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNpe042 | 720575940619038493 | right | data-driven | data-driven | yes | 108.367 | 0.3691 | 1.000 | 0 | 0 | 51 | 0 | pass | fail | pass | inter |
| DNpe042 | 720575940615092019 | left | data-driven | data-driven | yes | 80.767 | 0.2751 | 1.000 | 0 | 0 | 46 | 0 | pass | fail | pass | inter |
| DNpe045 | 720575940612488341 | right | data-driven | data-driven | yes | 89.333 | 0.3043 | 1.000 | 2 | 0 | 61 | 0 | pass | fail | pass | inter |
| DNpe045 | 720575940637341668 | left | data-driven | data-driven | yes | 84.167 | 0.2867 | 1.000 | 1 | 0 | 24 | 0 | pass | fail | pass | inter |
| DNpe053 | 720575940624402173 | left | data-driven | data-driven | yes | 25.133 | 0.0856 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| DNpe056 | 720575940634458719 | left | data-driven | data-driven | yes | 90.700 | 0.3089 | 1.000 | 0 | 0 | 153 | 0 | pass | fail | pass | inter |
| DNpe056 | 720575940632472850 | right | data-driven | data-driven | yes | 75.033 | 0.2556 | 1.000 | 0 | 0 | 139 | 0 | pass | fail | pass | inter |
| MDN | 720575940610236514 | right | data-driven | data-driven | yes | 18.900 | 0.0644 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| MDN | 720575940631082808 | left | data-driven | data-driven | yes | 16.733 | 0.0570 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| MDN | 720575940640331472 | right | data-driven | data-driven | yes | 10.267 | 0.0350 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |
| MDN | 720575940616026939 | left | data-driven | data-driven | yes | 3.167 | 0.0108 | 1.000 | 0 | 0 | 0 | 0 | pass | fail | pass | inter |

## Absent or failing candidate types


## Result

parallel_output: present

reason: 17 candidate(s) passed ADR-15 checks (i)-(iii)

## Circuit

- by_role.input_lc4: 104
- by_role.input_lplc2: 210
- by_role.inter: 898
- by_role.output_gf: 2
- by_role.output_parallel: 17
- n_edges: 10641
- n_neurons: 1231
- n_no_incoming: 39
- n_no_outgoing: 102
- n_synapses: 367713
