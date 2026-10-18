import re
import subprocess
import sys
from pathlib import Path

import pytest
from rr_discovery.cli import main
from rr_discovery.config import (
    DISCOVER_PATH_KEYS,
    ConfigError,
    discover_config_dict,
    load_config,
    require_discover,
    require_regress,
)

REPO = Path(__file__).resolve().parents[2]

M1_CONFIG = """\
[data]
version = "v783"
data_dir = "circuit-data/v783/raw"
reports_dir = "circuit-data/v783/reports"
manifest = "discovery/data_manifest.toml"

[zenodo]
record = "10676866"
doi = "10.5281/zenodo.10676866"
files = ["proofread_connections_783.feather", "proofread_root_ids_783.npy"]

[annotations]
repo = "flyconnectome/flywire_annotations"
tag = "v3.2.0"
path = "supplemental_files/Supplemental_file1_neuron_annotations.tsv"
"""

M2_SECTIONS = """\

[shiu]
repo = "philshiu/Drosophila_brain_model"
commit = "91bdd1e7dcf193f3e7ca5a8933497fcef63b7960"
raw_dir = "circuit-data/shiu/raw"
manifest = "discovery/shiu_manifest.toml"
vendor_files = ["LICENSE", "model.py", "utils.py"]
reference_files = ["Completeness_783.csv", "Connectivity_783.parquet"]
v630_files = ["2023_03_23_completeness_630_final.csv", "2023_03_23_connectivity_630_final.parquet"]

[model_input]
out_dir = "circuit-data/v783/model_input"

[regress]
frequencies_hz = [10, 20, 50, 100, 200]
n_trials = 30
seed_base = 783000
n_proc = 4
work_dir = "circuit-data/v783/regress"
golden = "circuit-data/v783/reports/regress_golden.json"
report = "circuit-data/v783/reports/regress_report.md"
stim_source = "Shiu example.ipynb @91bdd1e"
sugar_grn_ids = [101, 102]
mn9_id = 104

[regress.v630]
sugar_grn_ids = [101, 102]
mn9_id = 104
"""

VALID_CONFIG = M1_CONFIG + M2_SECTIONS


def _write_config(tmp_path: Path, drop_key: str | None = None) -> Path:
    kept: list[str] = []
    section = ""
    for line in VALID_CONFIG.splitlines(keepends=True):
        stripped = line.strip()
        if stripped.startswith("["):
            section = stripped.strip("[]")
        elif (
            drop_key is not None
            and "=" in stripped
            and f"{section}.{stripped.split('=', 1)[0].strip()}" == drop_key
        ):
            continue
        kept.append(line)
    p = tmp_path / "discovery.toml"
    p.write_text("".join(kept), encoding="utf-8")
    return p


def _write_m1_config(tmp_path: Path) -> Path:
    p = tmp_path / "discovery.toml"
    p.write_text(M1_CONFIG, encoding="utf-8")
    return p


def test_load_valid_config(tmp_path: Path) -> None:
    p = _write_config(tmp_path)
    cfg = load_config(p, base_dir=tmp_path)
    assert cfg.zenodo.record == "10676866"
    assert cfg.data_dir == tmp_path / "circuit-data/v783/raw"


@pytest.mark.parametrize(
    "key",
    [
        "zenodo.record",
        "annotations.tag",
        "data.data_dir",
        "shiu.commit",
        "model_input.out_dir",
        "regress.n_trials",
        "regress.v630.mn9_id",
    ],
)
def test_missing_key_raises(tmp_path: Path, key: str) -> None:
    p = _write_config(tmp_path, drop_key=key)
    with pytest.raises(ConfigError, match=re.escape(key)):
        load_config(p, base_dir=tmp_path)


def test_cli_missing_key_exit_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    bad = _write_config(tmp_path, drop_key="zenodo.record")
    assert main(["fetch", "--config", str(bad)]) == 2
    assert "missing required key 'zenodo.record'" in capsys.readouterr().err


def test_optional_sections_absent_are_none(tmp_path: Path) -> None:
    p = _write_m1_config(tmp_path)
    cfg = load_config(p, base_dir=tmp_path)
    assert cfg.shiu is None
    assert cfg.model_input is None
    assert cfg.regress is None
    with pytest.raises(ConfigError, match="missing required section \\[regress\\]"):
        require_regress(cfg)


@pytest.mark.parametrize(
    "freqs",
    [
        "[10, 20, 200]",
        "[20, 100, 200]",
        "[10, 100, 50, 200]",
    ],
)
def test_bad_frequencies_rejected(tmp_path: Path, freqs: str) -> None:
    text = VALID_CONFIG.replace(
        "frequencies_hz = [10, 20, 50, 100, 200]", f"frequencies_hz = {freqs}"
    )
    p = tmp_path / "discovery.toml"
    p.write_text(text, encoding="utf-8")
    with pytest.raises(ConfigError, match="regress.frequencies_hz"):
        load_config(p, base_dir=tmp_path)


def test_regress_config_values(tmp_path: Path) -> None:
    p = _write_config(tmp_path)
    cfg = load_config(p, base_dir=tmp_path)
    regress = require_regress(cfg)
    assert regress.frequencies_hz == (10.0, 20.0, 50.0, 100.0, 200.0)
    assert regress.v630.mn9_id == 104
    assert regress.golden == tmp_path / "circuit-data/v783/reports/regress_golden.json"


def test_cli_help_lists_stages(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "fetch" in out
    assert "inspect" in out
    assert "model-input" in out
    assert "shiu-fetch" in out
    assert "regress" in out
    assert "discover" in out


def test_console_script_help() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "rr_discovery.cli", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "fetch" in result.stdout
    assert "inspect" in result.stdout
    assert "model-input" in result.stdout
    assert "shiu-fetch" in result.stdout
    assert "regress" in result.stdout
    assert "discover" in result.stdout


def test_discover_config_values(tmp_path: Path) -> None:
    cfg = load_config(REPO / "discovery/discovery.toml", base_dir=tmp_path)
    dc = require_discover(cfg)
    assert dc.expected_lc4 == 104
    assert dc.expected_lplc2 == 210
    assert dc.rate_hz == 150.0
    assert dc.n_trials == 30
    assert dc.min_rate_hz == 2.0
    assert dc.min_trial_frac == 0.5
    assert dc.prior_cell_types == ("DNp02", "DNp03", "DNp04", "DNp06")
    assert dc.work_dir == tmp_path / "circuit-data/v783/discover"
    d = discover_config_dict(dc)
    assert not (set(d) & set(DISCOVER_PATH_KEYS + ("n_proc",)))


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("min_trial_frac", "1.5"),
        ("min_rate_hz", "0"),
        ("n_trials", "1"),
        ("n_proc", "0"),
    ],
)
def test_discover_config_rejects(tmp_path: Path, key: str, value: str) -> None:
    real = (REPO / "discovery/discovery.toml").read_text(encoding="utf-8")
    head, section = real.split("[discover]", 1)
    section, n = re.subn(rf"^{key} = [^\n#]*", f"{key} = {value}", section, flags=re.MULTILINE)
    assert n == 1
    text = head + "[discover]" + section
    p = tmp_path / "discovery.toml"
    p.write_text(text, encoding="utf-8")
    with pytest.raises(ConfigError, match=key):
        require_discover(load_config(p, base_dir=tmp_path))
