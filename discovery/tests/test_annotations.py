from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from rr_discovery import sanity
from rr_discovery.annotations import (
    descending_ids,
    ids_by_cell_type,
    load_annotations,
    near_matches,
    root_id_column,
)


def _frame(col: str = "root_783") -> pd.DataFrame:
    return pd.DataFrame(
        {
            col: [1, 2, 3, 4, 5, 6, 7, 8],
            "cell_type": ["LC4", "LC4", "LPLC2", "DNp01", "DNp02", "lc4", "LC4", None],
            "super_class": [
                "optic",
                "optic",
                "optic",
                "descending",
                "descending",
                "optic",
                "optic",
                "central",
            ],
        }
    )


VALID = np.array([1, 3, 4, 5, 6, 8], dtype=np.int64)


def test_lc4_lookup() -> None:
    ids = ids_by_cell_type(_frame(), "LC4", valid_ids=VALID)
    assert ids.tolist() == [1]
    assert ids.dtype == np.int64


def test_lplc2_lookup() -> None:
    ids = ids_by_cell_type(_frame(), "LPLC2", valid_ids=VALID)
    assert ids.tolist() == [3]
    assert ids.dtype == np.int64


def test_dnp01_lookup() -> None:
    ids = ids_by_cell_type(_frame(), "DNp01", valid_ids=VALID)
    assert ids.tolist() == [4]
    assert ids.dtype == np.int64


def test_descending_lookup() -> None:
    ids = descending_ids(_frame(), valid_ids=VALID)
    assert ids.tolist() == [4, 5]
    assert ids.dtype == np.int64


def test_absent_cell_type_is_empty_int64() -> None:
    ids = ids_by_cell_type(_frame(), "DNp03", valid_ids=VALID)
    assert ids.size == 0
    assert ids.dtype == np.int64


def test_near_matches() -> None:
    assert near_matches(_frame(), "LC4") == ["LC4", "lc4"]


def test_root_id_column_alternative_name() -> None:
    assert root_id_column(_frame(col="root_id")) == "root_id"
    ids = ids_by_cell_type(_frame(col="root_id"), "LC4", valid_ids=VALID)
    assert ids.tolist() == [1]


def test_root_id_column_missing_raises() -> None:
    frame = _frame().rename(columns={"root_783": "something_else"})
    with pytest.raises(KeyError):
        root_id_column(frame)


def test_tsv_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "ann.tsv"
    _frame().to_csv(path, sep="\t", index=False)
    ann = load_annotations(path)
    assert ids_by_cell_type(ann, "LC4", valid_ids=VALID).tolist() == [1]


def test_sanity_rejects_missing_dnp01() -> None:
    with pytest.raises(sanity.SanityError):
        sanity.check_left_dnp01(np.array([1, 2]))


def test_sanity_accepts_known_dnp01() -> None:
    sanity.check_left_dnp01(np.array([sanity.LEFT_DNP01_V783]))
