"""Explainable scouting investment rubric, not a trained draft-outcome model."""
from __future__ import annotations

import json
import math
from pathlib import Path


def load_valuation_config():
    return json.loads(Path(__file__).with_name("valuation_config.json").read_text())


def grade(value):
    if value in (None, "", "-", "Auto"):
        return None
    number = float(value)
    if not math.isfinite(number) or not 20 <= number <= 80 or number % 5:
        raise ValueError("Grades must be 20-80 in five-point steps.")
    return number


def _band(score, config):
    return next(b for b in config["bands"] if score >= b["min_score"])


def evaluate(rows, kind, position_or_role, traits=None, physical_fit="Neutral / not assessed",
             physical_note="", risk="Moderate", config=None):
    """Future tools drive value. Present tools describe projection risk only.

    Missing required future grades block estimates. Repeated pitch types cannot
    manufacture arsenal depth. Height/weight are context for an explicit,
    documented physical-fit assessment; no automatic size premium exists.
    """
    config = config or load_valuation_config()
    if kind not in ("Pitcher", "Position Player"):
        raise ValueError("Choose Pitcher or Position Player.")
    if risk not in config["risk_widths"]:
        raise ValueError("Choose a valid projection-risk level.")
    if physical_fit not in config["physical_adjustments"]:
        raise ValueError("Choose a valid physical-fit assessment.")
    if physical_fit != "Neutral / not assessed" and not physical_note.strip():
        return {"ready": False, "missing": ["Physical-fit rationale"]}
    future, present = {}, {}
    for row in rows:
        name = row["Tool"]
        f, p = grade(row.get("Future")), grade(row.get("Present"))
        # A duplicate pitch label represents one pitch type, not another weapon.
        if f is not None and f > future.get(name, 0):
            future[name] = f
            present[name] = p
    reasons = []
    if kind == "Position Player":
        if position_or_role not in config["hitter_weights"]:
            return {"ready": False, "missing": ["Projected defensive position"]}
        weights = {k: v for k, v in config["hitter_weights"][position_or_role].items() if v > 0}
        missing = [f"{name} Future" for name in weights if name not in future]
        if missing:
            return {"ready": False, "missing": missing}
        values = {name: future[name] for name in weights}
        adjustment = config["position_adjustments"][position_or_role]
        reasons.append(f"{position_or_role} positional adjustment: {adjustment:+.1f} index points.")
        reasons.append("Raw power has limited weight to reduce overlap with game power.")
    else:
        if position_or_role not in config["pitcher_weights"]:
            return {"ready": False, "missing": ["Projected pitching role"]}
        weights = config["pitcher_weights"][position_or_role]
        fastballs = []
        for label in ("Fastball", "Sinker"):
            v, life = future.get(label + " Velocity"), future.get(label + " Life")
            if v is not None and life is not None:
                fastballs.append((0.5 * v + 0.5 * life, label))
        secondary_names = {"Cutter", "Slider", "Sweeper", "Curveball", "Changeup", "Splitter"}
        secondary = sorted(((v, k) for k, v in future.items() if k in secondary_names), reverse=True)
        missing = []
        if not fastballs:
            missing.append("Fastball or Sinker Velocity AND Life Future")
        count = 2 if position_or_role == "Starter" else 1
        if len(secondary) < count:
            missing.append(f"{count} distinct secondary pitch Future grade(s)")
        missing += [f"{k} Future" for k in ("Command", "Control") if k not in future]
        if missing:
            return {"ready": False, "missing": missing}
        fb, label = max(fastballs)
        values = {"Fastball": fb, "Best secondary": secondary[0][0],
                  "Command": future["Command"], "Control": future["Control"]}
        if count == 2:
            values["Second secondary"] = secondary[1][0]
        adjustment = config["role_adjustments"][position_or_role]
        reasons.append(f"{label} velocity and life combined once; best secondary: {secondary[0][1]}.")
        reasons.append(f"{position_or_role} role adjustment: {adjustment:+.1f} index points.")
    components = [{"Tool": k, "Future grade": values[k], "Weight": w,
                   "Contribution": round(values[k] * w, 2)} for k, w in weights.items()]
    base = sum(values[k] * w for k, w in weights.items())
    traits = traits or {}
    allowed = {"Athleticism", "Makeup / learning", "Role reliability"}
    if set(traits) - allowed:
        raise ValueError("Unknown valuation trait.")
    trait_points = config["physical_adjustments"][physical_fit]
    for name, assessment in traits.items():
        if assessment not in config["trait_adjustments"]:
            raise ValueError("Unknown trait assessment.")
        delta = config["trait_adjustments"][assessment]
        trait_points += delta
        reasons.append(f"{name}: {assessment} ({delta:+.1f}).")
    reasons.append(f"Physical fit: {physical_fit} ({config['physical_adjustments'][physical_fit]:+.1f}).")
    cap = config["trait_total_cap"]
    trait_points = max(-cap, min(cap, trait_points))
    score = max(20, min(80, base + adjustment + trait_points))
    width = config["risk_widths"][risk]
    gaps = [future[k] - p for k, p in present.items() if p is not None]
    if gaps and max(gaps) >= 15:
        width = max(width, 4)
        reasons.append("A 15+ point present-to-future gap widens the range; no extra projection bonus added.")
    if not gaps:
        width = max(width, 4)
        reasons.append("No paired present grades: wider range for unassessed development distance.")
    low, high = _band(max(20, score - width), config), _band(min(80, score + width), config)
    center = _band(score, config)
    round_low, round_high = high["round_low"], low["round_high"]
    round_text = center["round"] if low == high else f"Rounds {round_low}-{round_high} value"
    if low["min_score"] == 20 and low != high:
        round_text += " / free-agent possibility"
    return {"ready": True, "version": config["version"], "status": config["status"],
            "kind": kind, "projected_position_or_role": position_or_role,
            "index": round(score, 2), "base_index": round(base, 2),
            "position_role_adjustment": adjustment, "trait_adjustment": trait_points,
            "range_width": width, "central_band": center["round"], "round": round_text,
            "round_low": round_low, "round_high": round_high,
            "bonus_low": low["bonus_low"], "bonus_high": high["bonus_high"],
            "reference_year": config["reference_year"], "money_basis": config["money_basis"],
            "source": config["source"], "components": components, "reasons": reasons,
            "physical_note": physical_note, "traits": traits, "risk": risk,
            "basis": "Model suggestion"}


def money_range(result):
    return f"${result['bonus_low']:,.0f} - ${result['bonus_high']:,.0f}"


def apply_override(result, round_low, round_high, bonus_low, bonus_high, reason):
    if not result.get("ready"):
        raise ValueError("Complete the scouting inputs before overriding.")
    nums = (round_low, round_high, bonus_low, bonus_high)
    if not all(math.isfinite(float(n)) for n in nums):
        raise ValueError("Override values must be finite.")
    if not (1 <= round_low <= round_high <= 20) or any(int(n) != n for n in (round_low, round_high)):
        raise ValueError("Round range must be ordered whole numbers from 1 to 20.")
    if not (0 <= bonus_low <= bonus_high):
        raise ValueError("Bonus range must be nonnegative and ordered.")
    if not reason.strip():
        raise ValueError("Add a reason for your valuation override.")
    return {**result, "model_suggestion": result, "round_low": int(round_low),
            "round_high": int(round_high), "round": f"Rounds {int(round_low)}-{int(round_high)} value",
            "bonus_low": float(bonus_low), "bonus_high": float(bonus_high),
            "basis": "Scout override", "override_reason": reason.strip()}

def valuation_report_text(valuation):
    if not valuation or not valuation.get("ready"):
        return ""
    text = (f"{valuation['round']} | {money_range(valuation)} | {valuation['basis']} | "
            f"{valuation['reference_year']} USD. Prototype scouting investment rubric; not a market prediction.")
    if valuation.get("override_reason"):
        text += " Rationale: " + valuation["override_reason"]
    return text
