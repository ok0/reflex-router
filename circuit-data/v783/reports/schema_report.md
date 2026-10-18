# Schema report — FlyWire v783

## Sources

- Zenodo DOI: 10.5281/zenodo.10676866 (record 10676866)
- Annotations: flyconnectome/flywire_annotations@v3.2.0, path supplemental_files/Supplemental_file1_neuron_annotations.tsv

| File | sha256 |
| --- | --- |
| Supplemental_file1_neuron_annotations.tsv | b214970b55d2fbe0853bba536fdcb9e28730f4eb7ab06f600491df795da683cd |
| proofread_connections_783.feather | 24f960ae3e7d4f8cd30db3b62e99fb5179cc3d1e76d8c155bfb441e9737d3faf |
| proofread_root_ids_783.npy | 7c7b7e818e9232e5ab64793d52ba20574dbe9da3a6509fbc74193b0f259a01be |

## Connection table

- Rows: 16847997

| Column | Type |
| --- | --- |
| pre_pt_root_id | int64 |
| post_pt_root_id | int64 |
| neuropil | string |
| syn_count | int64 |
| gaba_avg | double |
| ach_avg | double |
| glut_avg | double |
| oct_avg | double |
| ser_avg | double |
| da_avg | double |

- Pre-synaptic column: pre_pt_root_id
- Post-synaptic column: post_pt_root_id
- Synapse-count column: syn_count

## Threshold

- Minimum syn_count per row: 1
- Minimum syn_count per (pre, post) pair after summing neuropils: 1
- Pairs < 5: 12391470 (of 15091983)
- Pairs ≤ 10: 14162304 (of 15091983)

**Verdict:** NOT thresholded: minimum syn_count per row is 1

## Neurotransmitter fields

- gaba_avg
- ach_avg
- glut_avg
- oct_avg
- ser_avg
- da_avg

## Per-target input totals

- derivable: yes
- Number of targets: 137090
- Note: sums over proofread connections only.

## Root-ID coverage

| Measure | Count |
| --- | --- |
| Root-ID list size | 139255 |
| Connection-table IDs | 138639 |
| Connection IDs in root list | 138639 |
| Connection IDs not in root list | 0 |
| Annotation IDs | 139248 |
| Annotation root column used | root_id |
| Root list in annotations | 139241 |
| Root list not in annotations | 14 |
| Connection IDs in annotations | 138625 |

## Annotation table

| Column | Type |
| --- | --- |
| supervoxel_id | int64 |
| root_id | int64 |
| pos_x | float64 |
| pos_y | float64 |
| pos_z | float64 |
| soma_x | float64 |
| soma_y | float64 |
| soma_z | float64 |
| nucleus_id | float64 |
| flow | str |
| super_class | str |
| cell_class | str |
| cell_sub_class | str |
| supertype | float64 |
| cell_type | str |
| hemibrain_type | str |
| ito_lee_hemilineage | str |
| hartenstein_hemilineage | str |
| top_nt | str |
| top_nt_conf | float64 |
| known_nt | str |
| known_nt_source | str |
| side | str |
| nerve | str |
| vfb_id | str |
| fbbt_id | str |
| status | str |
| dimorphism | str |
| matching_notes | str |
| fru_dsx | str |
| synonyms | str |

## Cell-type lookups (restricted to root-ID list)

- LC4: 104
- LPLC2: 210
- DNp01: 2
- descending: 1303
- Naming mapping used: exact case-sensitive match

## Sanity check

- left DNp01 present: PASS

## Unresolved

none
