from __future__ import annotations


def normalize_trackman_hb(raw_hb: float, throws: str) -> float:
    """Normalize manual TrackMan-style HB to one scouting-app convention.

    App convention:
      positive = arm-side movement
      negative = glove-side movement

    Current manual-input assumption (based on the convention we chose for the app):
      RHP arm-side HB is positive in the source
      LHP arm-side HB is negative in the source

    Therefore LHP values are sign-flipped internally.

    IMPORTANT: this is a source adapter, not a universal baseball-data rule.
    If a different vendor/source uses another sign convention, write a separate adapter.
    """
    hand = throws.strip().upper()
    if hand in {"R", "RHP"}:
        return float(raw_hb)
    if hand in {"L", "LHP"}:
        return -float(raw_hb)
    raise ValueError("throws must be R/RHP or L/LHP")


def hb_direction(normalized_hb: float, dead_zone: float = 0.5) -> str:
    """Return arm-side, glove-side, or neutral for normalized HB."""
    if normalized_hb > dead_zone:
        return "arm-side"
    if normalized_hb < -dead_zone:
        return "glove-side"
    return "neutral"
