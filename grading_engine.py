from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from hb import normalize_trackman_hb

GRADE_STEPS = (20, 30, 40, 45, 50, 55, 60, 65, 70, 75, 80)
METRICS = ("velo", "ivb", "hb_normalized")
FASTBALL_SPLIT_TYPES = {"Four-Seam Fastball", "Sinker / Two-Seam"}


def _round_grade(score: float) -> int:
    score = max(20.0, min(80.0, float(score)))
    return min(GRADE_STEPS, key=lambda g: abs(g - score))


def resolve_present_grade(auto_grade, override):
    """Return the scout override when present; otherwise the automatic grade."""
    if override not in (None, "Auto", "-"):
        return int(override)
    if auto_grade in (None, "-"):
        return "-"
    return int(auto_grade)


def load_config(path: str | Path = "pitch_grading_config.json") -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_baselines(path: str | Path = "data/baselines/mlb_pitch_baselines.csv") -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    required = {"pitch_type", "metric", "mean", "sd"}
    if not required.issubset(df.columns):
        raise ValueError(f"Baseline file is missing columns: {sorted(required - set(df.columns))}")
    return df


def _lookup_baseline(baselines: pd.DataFrame, pitch_code: str, metric: str) -> tuple[float, float]:
    hit = baselines[(baselines["pitch_type"] == pitch_code) & (baselines["metric"] == metric)]
    if hit.empty:
        raise KeyError(f"No baseline for {pitch_code} / {metric}")
    mean = float(hit.iloc[0]["mean"])
    sd = float(hit.iloc[0]["sd"])
    if not math.isfinite(sd) or sd <= 0:
        raise ValueError(f"Invalid SD for {pitch_code} / {metric}: {sd}")
    return mean, sd


def _quality_z(value: float, mean: float, sd: float, direction: str) -> float:
    z = (float(value) - mean) / sd
    if direction == "high":
        return z
    if direction == "low":
        return -z
    raise ValueError(f"Unknown quality direction: {direction}")


def _component_detail(value: float, mean: float, sd: float, direction: str, weight: float) -> dict[str, Any]:
    raw_z = (float(value) - mean) / sd
    qz = _quality_z(value, mean, sd, direction)
    return {
        "value": float(value),
        "mlb_mean": mean,
        "mlb_sd": sd,
        "raw_z": raw_z,
        "quality_z": qz,
        "weight": float(weight),
        "direction": direction,
        "grade": _round_grade(50.0 + 10.0 * qz),
    }


def grade_fastball_velocity(
    pitch_name: str,
    velo: float,
    baselines: pd.DataFrame,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Grade only fastball velocity on the 20-80 scale.

    Reference mean = 50 and one guideline SD = 10 grade points.
    This grade intentionally ignores pitch shape.
    """
    if config is None:
        config = load_config()
    if pitch_name not in FASTBALL_SPLIT_TYPES:
        raise ValueError(f"{pitch_name} is not configured as a split fastball tool")
    rule = config[pitch_name]
    mean, sd = _lookup_baseline(baselines, rule["code"], "velo")
    detail = _component_detail(float(velo), mean, sd, "high", 1.0)
    return {
        "pitch_name": pitch_name,
        "tool": "velocity",
        "present_grade": detail["grade"],
        "component": detail,
    }


def grade_fastball_life(
    pitch_name: str,
    ivb: float,
    raw_hb: float,
    throws: str,
    baselines: pd.DataFrame,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Grade fastball life from movement only (IVB + normalized HB).

    Four-seam life emphasizes ride/IVB. Sinker life emphasizes arm-side run and
    lower IVB. Velocity is intentionally excluded so the two fastball tools remain
    distinct on the report.
    """
    if config is None:
        config = load_config()
    if pitch_name not in FASTBALL_SPLIT_TYPES:
        raise ValueError(f"{pitch_name} is not configured as a split fastball tool")

    rule = config[pitch_name]
    code = rule["code"]
    normalized_hb = normalize_trackman_hb(float(raw_hb), throws)
    values = {"ivb": float(ivb), "hb_normalized": normalized_hb}
    weights = rule["life_weights"]

    components: dict[str, Any] = {}
    weighted_z = 0.0
    total_weight = 0.0
    for metric in ("ivb", "hb_normalized"):
        mean, sd = _lookup_baseline(baselines, code, metric)
        direction = rule["directions"][metric]
        weight = float(weights[metric])
        detail = _component_detail(values[metric], mean, sd, direction, weight)
        components[metric] = detail
        weighted_z += weight * detail["quality_z"]
        total_weight += weight

    combined_z = weighted_z / total_weight
    return {
        "pitch_name": pitch_name,
        "tool": "life",
        "present_grade": _round_grade(50.0 + 10.0 * combined_z),
        "combined_quality_z": combined_z,
        "normalized_hb": normalized_hb,
        "components": components,
    }


def grade_pitch(
    pitch_name: str,
    velo: float,
    ivb: float,
    raw_hb: float,
    throws: str,
    baselines: pd.DataFrame,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return an automatic present 20-80 grade for a non-fastball pitch.

    This is the simple V1 objective grade. The app does not call this an opinion or
    projection: it is a transparent calculation from Velo, IVB and normalized HB.
    Future grades remain manual scout projections.
    """
    if config is None:
        config = load_config()
    if pitch_name not in config or pitch_name == "note":
        raise KeyError(f"No auto-grade configuration for {pitch_name}")

    rule = config[pitch_name]
    code = rule["code"]
    values = {
        "velo": float(velo),
        "ivb": float(ivb),
        "hb_normalized": normalize_trackman_hb(float(raw_hb), throws),
    }

    components: dict[str, Any] = {}
    weighted_z = 0.0
    total_weight = 0.0

    for metric in METRICS:
        mean, sd = _lookup_baseline(baselines, code, metric)
        direction = rule["directions"][metric]
        weight = float(rule["weights"][metric])
        detail = _component_detail(values[metric], mean, sd, direction, weight)
        components[metric] = detail
        weighted_z += weight * detail["quality_z"]
        total_weight += weight

    if total_weight <= 0:
        raise ValueError("Pitch weights must sum to a positive value")
    combined_z = weighted_z / total_weight
    present = _round_grade(50.0 + 10.0 * combined_z)

    return {
        "pitch_name": pitch_name,
        "pitch_code": code,
        "present_grade": present,
        "suggested_grade": present,  # backwards-compatible alias for older tests/files
        "combined_quality_z": combined_z,
        "normalized_hb": values["hb_normalized"],
        "components": components,
        "warning": rule.get("warning"),
    }
