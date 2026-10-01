from __future__ import annotations

from typing import Optional

HITTER_GRADE_STEPS = (20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80)


def _clamp_grade(value: float) -> int:
    value = max(20.0, min(80.0, float(value)))
    return min(HITTER_GRADE_STEPS, key=lambda g: abs(g - value))


def resolve_reference_grade(reference_grade, override):
    """Use the scout-entered present grade when supplied; otherwise use the reference."""
    if override not in (None, "Auto", "-"):
        return int(override)
    if reference_grade in (None, "-"):
        return "-"
    return int(reference_grade)


def grade_hit_from_projected_avg(projected_avg: Optional[float]) -> Optional[int]:
    """Translate a projected MLB batting average into a traditional hit-tool reference grade."""
    if projected_avg is None:
        return None
    avg = float(projected_avg)
    if avg >= .315:
        return 80
    if avg >= .295:
        return 70
    if avg >= .275:
        return 60
    if avg >= .265:
        return 55
    if avg >= .255:
        return 50
    if avg >= .245:
        return 45
    if avg >= .235:
        return 40
    if avg >= .215:
        return 30
    return 20


def grade_raw_power_from_ev90(ev90: Optional[float]) -> Optional[int]:
    """EV90 reference: 104 mph ~= 50, about 5 grade points per mph, capped 20-80."""
    if ev90 is None:
        return None
    score = 50.0 + 5.0 * (float(ev90) - 104.0)
    return _clamp_grade(score)


def grade_raw_power_from_max_ev(max_ev: Optional[float]) -> Optional[int]:
    """Fallback raw-power reference when EV90 is unavailable."""
    if max_ev is None:
        return None
    ev = float(max_ev)
    if ev >= 117:
        return 80
    if ev >= 116:
        return 75
    if ev >= 115:
        return 70
    if ev >= 114:
        return 65
    if ev >= 113:
        return 60
    if ev >= 112:
        return 55
    if ev >= 109:
        return 50
    if ev >= 108:
        return 45
    if ev >= 107:
        return 40
    if ev >= 106:
        return 35
    if ev >= 105:
        return 30
    if ev >= 104:
        return 25
    return 20


def grade_raw_power(ev90: Optional[float], max_ev: Optional[float]) -> tuple[Optional[int], str]:
    """Prefer EV90; use max EV only as a fallback."""
    if ev90 is not None:
        return grade_raw_power_from_ev90(ev90), "EV90"
    if max_ev is not None:
        return grade_raw_power_from_max_ev(max_ev), "Max EV fallback"
    return None, ""


def grade_game_power_from_projected_hr(projected_hr: Optional[int]) -> Optional[int]:
    """Translate projected MLB home-run output into a game-power reference grade."""
    if projected_hr is None:
        return None
    hr = int(projected_hr)
    if hr >= 40:
        return 80
    if hr >= 34:
        return 70
    if hr >= 28:
        return 60
    if hr >= 23:
        return 55
    if hr >= 19:
        return 50
    if hr >= 14:
        return 45
    if hr >= 10:
        return 40
    if hr >= 5:
        return 30
    return 20


def grade_run_from_60(time_seconds: Optional[float]) -> Optional[int]:
    """Traditional 60-yard scouting reference."""
    if time_seconds is None:
        return None
    t = float(time_seconds)
    if t <= 6.3:
        return 80
    if t <= 6.4:
        return 75
    if t <= 6.5:
        return 70
    if t <= 6.6:
        return 65
    if t <= 6.7:
        return 60
    if t <= 6.8:
        return 55
    if t <= 7.0:
        return 50
    if t <= 7.1:
        return 45
    if t <= 7.2:
        return 40
    if t <= 7.3:
        return 35
    if t <= 7.4:
        return 30
    return 20


def grade_run_from_home_to_first(time_seconds: Optional[float], bats: str) -> Optional[int]:
    """Home-to-first reference with handedness adjustment."""
    if time_seconds is None:
        return None
    hand = (bats or "").upper().strip()
    if hand not in {"R", "L"}:
        return None
    baseline = 4.30 if hand == "R" else 4.20
    score = 50.0 + ((baseline - float(time_seconds)) / 0.10) * 10.0
    return _clamp_grade(score)
