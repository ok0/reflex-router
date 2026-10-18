"""Connection filter for member edges (M5, R6/R8). Pure; integer arithmetic."""

import numpy as np
import pandas as pd

SYN_ABS_EXCLUSIVE = 10
INPUT_PCT_EXCLUSIVE = 1

RULE_TEXT = (
    "keep edge iff syn_count > 10 or syn_count > 1% of the target's total input synapses "
    "(100*syn_count > input_total); totals over all proofread inputs before restriction; "
    "counts aggregated per neuron pair across neuropils"
)
CITATION = (
    "Schlegel et al., bioRxiv 2023 abstract (doi 10.1101/2023.06.27.546055); "
    "Nature 634:139-152 (doi 10.1038/s41586-024-07686-5)"
)
CODEX_NOTE = (
    "Codex's default threshold is 5 synapses; this project uses the 10 / 1% rule above "
    "with no deviation"
)


class ConnFilterError(Exception):
    pass


def keep(edges: pd.DataFrame, input_totals: pd.DataFrame) -> np.ndarray:
    if edges.duplicated(subset=["pre", "post"]).any():
        raise ConnFilterError("duplicate (pre, post) pair in edges")
    totals = input_totals.set_index("root_id")["input_total"]
    post = edges["post"].to_numpy(dtype=np.int64)
    looked_up = totals.reindex(post)
    missing_mask = looked_up.isna().to_numpy(dtype=bool)
    if missing_mask.any():
        missing = sorted({int(x) for x in post[missing_mask]})[:10]
        raise ConnFilterError(f"post ids missing from input totals: {missing}")
    total = looked_up.to_numpy(dtype=np.int64)
    syn = edges["syn"].to_numpy(dtype=np.int64)
    return (syn > SYN_ABS_EXCLUSIVE) | (syn * 100 > INPUT_PCT_EXCLUSIVE * total)
