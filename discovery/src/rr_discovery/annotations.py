from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT_ID_COLUMNS: tuple[str, ...] = ("root_783", "root_id")


def load_annotations(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep="\t", low_memory=False)


def root_id_column(ann: pd.DataFrame) -> str:
    for col in ROOT_ID_COLUMNS:
        if col in ann.columns:
            return col
    raise KeyError(
        f"no root-id column; expected one of {ROOT_ID_COLUMNS}, found {list(ann.columns)}"
    )


def load_root_ids(path: Path) -> np.ndarray:
    return np.load(path).astype(np.int64)


def ids_by_cell_type(ann: pd.DataFrame, cell_type: str, *, valid_ids: np.ndarray) -> np.ndarray:
    mask = ann["cell_type"] == cell_type
    ids = ann.loc[mask, root_id_column(ann)].to_numpy().astype(np.int64)
    ids = np.unique(ids)
    return ids[np.isin(ids, valid_ids)]


def descending_ids(ann: pd.DataFrame, *, valid_ids: np.ndarray) -> np.ndarray:
    mask = ann["super_class"] == "descending"
    ids = ann.loc[mask, root_id_column(ann)].to_numpy().astype(np.int64)
    ids = np.unique(ids)
    return ids[np.isin(ids, valid_ids)]


def near_matches(ann: pd.DataFrame, cell_type: str, limit: int = 10) -> list[str]:
    values = {str(v) for v in ann["cell_type"].dropna().unique()}
    needle = cell_type.lower()
    return sorted(v for v in values if needle in v.lower())[:limit]


def _text(row: pd.Series, column: str) -> str:
    if column not in row.index:
        return ""
    value: Any = row[column]
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return ""
    return str(value)


def labels(ann: pd.DataFrame, ids: np.ndarray) -> pd.DataFrame:
    wanted = np.unique(np.asarray(ids, dtype=np.int64))
    roots = ann[root_id_column(ann)].to_numpy().astype(np.int64)
    first = (
        ann.assign(_root=roots)
        .sort_values("_root", kind="stable")
        .drop_duplicates("_root", keep="first")
        .set_index("_root")
    )
    cell_type: list[str] = []
    side: list[str] = []
    for rid in wanted.tolist():
        if rid in first.index:
            row = first.loc[rid]
            cell_type.append(_text(row, "cell_type"))
            side.append(_text(row, "side"))
        else:
            cell_type.append("")
            side.append("")
    return pd.DataFrame({"root_id": wanted, "cell_type": cell_type, "side": side})
