import dataclasses
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class ZenodoConfig:
    record: str
    doi: str
    files: tuple[str, ...]


@dataclass(frozen=True)
class AnnotationsConfig:
    repo: str
    tag: str
    path: str


@dataclass(frozen=True)
class ShiuConfig:
    repo: str
    commit: str
    raw_dir: Path
    manifest: Path
    vendor_files: tuple[str, ...]
    reference_files: tuple[str, ...]
    v630_files: tuple[str, ...]


@dataclass(frozen=True)
class ModelInputConfig:
    out_dir: Path


@dataclass(frozen=True)
class StimSet:
    sugar_grn_ids: tuple[int, ...]
    mn9_id: int


@dataclass(frozen=True)
class RegressConfig:
    frequencies_hz: tuple[float, ...]
    n_trials: int
    seed_base: int
    n_proc: int
    work_dir: Path
    golden: Path
    report: Path
    stim_source: str
    v783: StimSet
    v630: StimSet


@dataclass(frozen=True)
class DiscoverConfig:
    work_dir: Path
    out_dir: Path
    candidates_report: Path
    responsive_table: Path
    m2_report: Path
    lc4_cell_type: str
    lplc2_cell_type: str
    expected_lc4: int
    expected_lplc2: int
    rate_hz: float
    n_trials: int
    seed_base: int
    n_proc: int
    min_rate_hz: float
    min_trial_frac: float
    gf_cell_type: str
    prior_cell_types: tuple[str, ...]
    reported_cell_types: tuple[str, ...]
    license_label: str


@dataclass(frozen=True)
class RobustnessConfig:
    grid: Path
    work_dir: Path
    report: Path
    results: Path


DISCOVER_PATH_KEYS: tuple[str, ...] = (
    "work_dir",
    "out_dir",
    "candidates_report",
    "responsive_table",
    "m2_report",
)
DISCOVER_EXEC_KEYS: tuple[str, ...] = ("n_proc",)


@dataclass(frozen=True)
class DiscoveryConfig:
    source: Path
    version: str
    data_dir: Path
    reports_dir: Path
    manifest: Path
    zenodo: ZenodoConfig
    annotations: AnnotationsConfig
    shiu: ShiuConfig | None = None
    model_input: ModelInputConfig | None = None
    regress: RegressConfig | None = None
    discover: DiscoverConfig | None = None
    robustness: RobustnessConfig | None = None


REQUIRED_KEYS: tuple[str, ...] = (
    "data.version",
    "data.data_dir",
    "data.reports_dir",
    "data.manifest",
    "zenodo.record",
    "zenodo.doi",
    "zenodo.files",
    "annotations.repo",
    "annotations.tag",
    "annotations.path",
)

PATH_KEYS: frozenset[str] = frozenset({"data.data_dir", "data.reports_dir", "data.manifest"})

_HEX40 = re.compile(r"[0-9a-f]{40}")


def _lookup(raw: dict[str, Any], dotted: str) -> tuple[bool, Any]:
    node: Any = raw
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return False, None
        node = node[part]
    return True, node


def _resolve(value: str, base: Path) -> Path:
    p = Path(value)
    return p if p.is_absolute() else base / p


def _table(raw: dict[str, Any], dotted: str, path: Path) -> dict[str, Any] | None:
    found, value = _lookup(raw, dotted)
    if not found:
        return None
    if not isinstance(value, dict):
        raise ConfigError(f"section [{dotted}] in {path} must be a table")
    return value


def _need(tbl: dict[str, Any], dotted: str, path: Path) -> Any:
    key = dotted.rsplit(".", 1)[1]
    if key not in tbl:
        raise ConfigError(f"missing required key '{dotted}' in {path}")
    return tbl[key]


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _check_str(value: Any, key: str, path: Path) -> str:
    if not isinstance(value, str):
        raise ConfigError(f"key '{key}' in {path} must be str")
    return value


def _check_int(value: Any, key: str, path: Path) -> int:
    if not _is_int(value):
        raise ConfigError(f"key '{key}' in {path} must be int")
    return value


def _check_str_list(value: Any, key: str, path: Path) -> tuple[str, ...]:
    if not (isinstance(value, list) and value and all(isinstance(x, str) for x in value)):
        raise ConfigError(f"key '{key}' in {path} must be a non-empty list of str")
    return tuple(value)


def _check_int_list(value: Any, key: str, path: Path, *, allow_empty: bool) -> tuple[int, ...]:
    if not (isinstance(value, list) and all(_is_int(x) for x in value)):
        raise ConfigError(f"key '{key}' in {path} must be a list of int")
    if not allow_empty and not value:
        raise ConfigError(f"key '{key}' in {path} must be a non-empty list of int")
    return tuple(value)


def _check_freqs(value: Any, key: str, path: Path) -> tuple[float, ...]:
    if not (
        isinstance(value, list) and value and all(_is_int(x) or isinstance(x, float) for x in value)
    ):
        raise ConfigError(f"key '{key}' in {path} must be a non-empty list of int or float")
    freqs = tuple(float(x) for x in value)
    ok = (
        all(f > 0 for f in freqs)
        and all(a < b for a, b in zip(freqs, freqs[1:], strict=False))
        and freqs[0] == 10.0
        and freqs[-1] == 200.0
        and 100.0 in freqs
    )
    if not ok:
        raise ConfigError(
            "regress.frequencies_hz must be strictly increasing, start at 10, "
            "end at 200 and include 100"
        )
    return freqs


def _load_shiu(raw: dict[str, Any], base: Path, path: Path) -> ShiuConfig | None:
    tbl = _table(raw, "shiu", path)
    if tbl is None:
        return None
    commit = _check_str(_need(tbl, "shiu.commit", path), "shiu.commit", path)
    if not _HEX40.fullmatch(commit):
        raise ConfigError(f"key 'shiu.commit' in {path} must be a 40-character lowercase hex SHA")
    return ShiuConfig(
        repo=_check_str(_need(tbl, "shiu.repo", path), "shiu.repo", path),
        commit=commit,
        raw_dir=_resolve(_check_str(_need(tbl, "shiu.raw_dir", path), "shiu.raw_dir", path), base),
        manifest=_resolve(
            _check_str(_need(tbl, "shiu.manifest", path), "shiu.manifest", path), base
        ),
        vendor_files=_check_str_list(
            _need(tbl, "shiu.vendor_files", path), "shiu.vendor_files", path
        ),
        reference_files=_check_str_list(
            _need(tbl, "shiu.reference_files", path), "shiu.reference_files", path
        ),
        v630_files=_check_str_list(_need(tbl, "shiu.v630_files", path), "shiu.v630_files", path),
    )


def _load_model_input(raw: dict[str, Any], base: Path, path: Path) -> ModelInputConfig | None:
    tbl = _table(raw, "model_input", path)
    if tbl is None:
        return None
    out_dir = _check_str(_need(tbl, "model_input.out_dir", path), "model_input.out_dir", path)
    return ModelInputConfig(out_dir=_resolve(out_dir, base))


def _load_stim(tbl: dict[str, Any], prefix: str, path: Path, *, allow_empty: bool) -> StimSet:
    sugar_key = f"{prefix}.sugar_grn_ids"
    mn9_key = f"{prefix}.mn9_id"
    sugar = _check_int_list(_need(tbl, sugar_key, path), sugar_key, path, allow_empty=allow_empty)
    mn9 = _check_int(_need(tbl, mn9_key, path), mn9_key, path)
    return StimSet(sugar_grn_ids=sugar, mn9_id=mn9)


def _load_regress(raw: dict[str, Any], base: Path, path: Path) -> RegressConfig | None:
    tbl = _table(raw, "regress", path)
    if tbl is None:
        return None
    frequencies = _check_freqs(
        _need(tbl, "regress.frequencies_hz", path), "regress.frequencies_hz", path
    )
    n_trials = _check_int(_need(tbl, "regress.n_trials", path), "regress.n_trials", path)
    if n_trials < 2:
        raise ConfigError(f"regress.n_trials must be >= 2 in {path}")
    seed_base = _check_int(_need(tbl, "regress.seed_base", path), "regress.seed_base", path)
    n_proc = _check_int(_need(tbl, "regress.n_proc", path), "regress.n_proc", path)
    if n_proc == 0:
        raise ConfigError(f"regress.n_proc must not be 0 in {path}")
    work_dir = _check_str(_need(tbl, "regress.work_dir", path), "regress.work_dir", path)
    golden = _check_str(_need(tbl, "regress.golden", path), "regress.golden", path)
    report = _check_str(_need(tbl, "regress.report", path), "regress.report", path)
    stim_source = _check_str(_need(tbl, "regress.stim_source", path), "regress.stim_source", path)
    v783 = _load_stim(tbl, "regress", path, allow_empty=False)
    v630_tbl = _table(raw, "regress.v630", path)
    if v630_tbl is None:
        raise ConfigError(f"missing required key 'regress.v630' in {path}")
    v630 = _load_stim(v630_tbl, "regress.v630", path, allow_empty=True)
    return RegressConfig(
        frequencies_hz=frequencies,
        n_trials=n_trials,
        seed_base=seed_base,
        n_proc=n_proc,
        work_dir=_resolve(work_dir, base),
        golden=_resolve(golden, base),
        report=_resolve(report, base),
        stim_source=stim_source,
        v783=v783,
        v630=v630,
    )


def _check_float(value: Any, key: str, path: Path) -> float:
    if not (_is_int(value) or isinstance(value, float)):
        raise ConfigError(f"key '{key}' in {path} must be int or float")
    return float(value)


def _check_str_list_maybe_empty(value: Any, key: str, path: Path) -> tuple[str, ...]:
    if not (isinstance(value, list) and all(isinstance(x, str) for x in value)):
        raise ConfigError(f"key '{key}' in {path} must be a list of str")
    return tuple(value)


def _load_discover(raw: dict[str, Any], base: Path, path: Path) -> DiscoverConfig | None:
    tbl = _table(raw, "discover", path)
    if tbl is None:
        return None

    def need(name: str) -> Any:
        return _need(tbl, f"discover.{name}", path)

    def key(name: str) -> str:
        return f"discover.{name}"

    n_trials = _check_int(need("n_trials"), key("n_trials"), path)
    if n_trials < 2:
        raise ConfigError(f"key '{key('n_trials')}' in {path} must be >= 2")
    n_proc = _check_int(need("n_proc"), key("n_proc"), path)
    if n_proc == 0:
        raise ConfigError(f"key '{key('n_proc')}' in {path} must not be 0")
    rate_hz = _check_float(need("rate_hz"), key("rate_hz"), path)
    if not (0.0 < rate_hz <= 1000.0):
        raise ConfigError(f"key '{key('rate_hz')}' in {path} must satisfy 0 < rate_hz <= 1000")
    min_rate_hz = _check_float(need("min_rate_hz"), key("min_rate_hz"), path)
    if not min_rate_hz > 0.0:
        raise ConfigError(f"key '{key('min_rate_hz')}' in {path} must be > 0")
    min_trial_frac = _check_float(need("min_trial_frac"), key("min_trial_frac"), path)
    if not (0.0 < min_trial_frac <= 1.0):
        raise ConfigError(
            f"key '{key('min_trial_frac')}' in {path} must satisfy 0 < min_trial_frac <= 1"
        )
    expected_lc4 = _check_int(need("expected_lc4"), key("expected_lc4"), path)
    if expected_lc4 < 1:
        raise ConfigError(f"key '{key('expected_lc4')}' in {path} must be >= 1")
    expected_lplc2 = _check_int(need("expected_lplc2"), key("expected_lplc2"), path)
    if expected_lplc2 < 1:
        raise ConfigError(f"key '{key('expected_lplc2')}' in {path} must be >= 1")
    prior = _check_str_list(need("prior_cell_types"), key("prior_cell_types"), path)
    reported = _check_str_list_maybe_empty(
        need("reported_cell_types"), key("reported_cell_types"), path
    )
    return DiscoverConfig(
        work_dir=_resolve(_check_str(need("work_dir"), key("work_dir"), path), base),
        out_dir=_resolve(_check_str(need("out_dir"), key("out_dir"), path), base),
        candidates_report=_resolve(
            _check_str(need("candidates_report"), key("candidates_report"), path), base
        ),
        responsive_table=_resolve(
            _check_str(need("responsive_table"), key("responsive_table"), path), base
        ),
        m2_report=_resolve(_check_str(need("m2_report"), key("m2_report"), path), base),
        lc4_cell_type=_check_str(need("lc4_cell_type"), key("lc4_cell_type"), path),
        lplc2_cell_type=_check_str(need("lplc2_cell_type"), key("lplc2_cell_type"), path),
        expected_lc4=expected_lc4,
        expected_lplc2=expected_lplc2,
        rate_hz=rate_hz,
        n_trials=n_trials,
        seed_base=_check_int(need("seed_base"), key("seed_base"), path),
        n_proc=n_proc,
        min_rate_hz=min_rate_hz,
        min_trial_frac=min_trial_frac,
        gf_cell_type=_check_str(need("gf_cell_type"), key("gf_cell_type"), path),
        prior_cell_types=prior,
        reported_cell_types=reported,
        license_label=_check_str(need("license_label"), key("license_label"), path),
    )


def _load_robustness(raw: dict[str, Any], base: Path, path: Path) -> RobustnessConfig | None:
    tbl = _table(raw, "robustness", path)
    if tbl is None:
        return None

    def path_of(name: str) -> Path:
        key = f"robustness.{name}"
        return _resolve(_check_str(_need(tbl, key, path), key, path), base)

    return RobustnessConfig(
        grid=path_of("grid"),
        work_dir=path_of("work_dir"),
        report=path_of("report"),
        results=path_of("results"),
    )


def load_config(path: Path, base_dir: Path | None = None) -> DiscoveryConfig:
    if not path.is_file():
        raise ConfigError(f"config file not found: {path}")
    try:
        with path.open("rb") as fh:
            raw: dict[str, Any] = tomllib.load(fh)
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"invalid TOML in {path}: {e}") from e

    values: dict[str, Any] = {}
    for key in REQUIRED_KEYS:
        found, value = _lookup(raw, key)
        if not found:
            raise ConfigError(f"missing required key '{key}' in {path}")
        if key == "zenodo.files":
            if not (
                isinstance(value, list) and value and all(isinstance(item, str) for item in value)
            ):
                raise ConfigError(f"key '{key}' in {path} must be a non-empty list of str")
            values[key] = tuple(value)
        else:
            if not isinstance(value, str):
                raise ConfigError(f"key '{key}' in {path} must be str")
            values[key] = value

    base = base_dir if base_dir is not None else Path.cwd()
    return DiscoveryConfig(
        source=path,
        version=values["data.version"],
        data_dir=_resolve(values["data.data_dir"], base),
        reports_dir=_resolve(values["data.reports_dir"], base),
        manifest=_resolve(values["data.manifest"], base),
        zenodo=ZenodoConfig(
            record=values["zenodo.record"],
            doi=values["zenodo.doi"],
            files=values["zenodo.files"],
        ),
        annotations=AnnotationsConfig(
            repo=values["annotations.repo"],
            tag=values["annotations.tag"],
            path=values["annotations.path"],
        ),
        shiu=_load_shiu(raw, base, path),
        model_input=_load_model_input(raw, base, path),
        regress=_load_regress(raw, base, path),
        discover=_load_discover(raw, base, path),
        robustness=_load_robustness(raw, base, path),
    )


def with_data_dir(cfg: DiscoveryConfig, data_dir: Path) -> DiscoveryConfig:
    return dataclasses.replace(cfg, data_dir=data_dir)


def discover_config_dict(dc: DiscoverConfig) -> dict[str, Any]:
    excluded = set(DISCOVER_PATH_KEYS) | set(DISCOVER_EXEC_KEYS)
    out: dict[str, Any] = {}
    for f in dataclasses.fields(dc):
        if f.name in excluded:
            continue
        value = getattr(dc, f.name)
        out[f.name] = list(value) if isinstance(value, tuple) else value
    return out


def require_shiu(cfg: DiscoveryConfig) -> ShiuConfig:
    if cfg.shiu is None:
        raise ConfigError(f"missing required section [shiu] in {cfg.source}")
    return cfg.shiu


def require_model_input(cfg: DiscoveryConfig) -> ModelInputConfig:
    if cfg.model_input is None:
        raise ConfigError(f"missing required section [model_input] in {cfg.source}")
    return cfg.model_input


def require_regress(cfg: DiscoveryConfig) -> RegressConfig:
    if cfg.regress is None:
        raise ConfigError(f"missing required section [regress] in {cfg.source}")
    return cfg.regress


def require_discover(cfg: DiscoveryConfig) -> DiscoverConfig:
    if cfg.discover is None:
        raise ConfigError(f"missing required section [discover] in {cfg.source}")
    return cfg.discover


def require_robustness(cfg: DiscoveryConfig) -> RobustnessConfig:
    if cfg.robustness is None:
        raise ConfigError(f"missing required section [robustness] in {cfg.source}")
    return cfg.robustness
