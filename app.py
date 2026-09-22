from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from grading_engine import (
    FASTBALL_SPLIT_TYPES,
    grade_fastball_life,
    grade_fastball_velocity,
    grade_pitch,
    load_baselines,
    load_config,
    resolve_present_grade,
)
from report_export import build_report_pdf

BASELINE_DIR = Path("data/baselines")
BASELINE_PATH = BASELINE_DIR / "mlb_pitch_baselines.csv"
METADATA_PATH = BASELINE_DIR / "baseline_metadata.json"
PITCH_TYPES = [
    "Four-Seam Fastball",
    "Sinker / Two-Seam",
    "Cutter",
    "Slider",
    "Sweeper",
    "Curveball",
    "Changeup",
    "Splitter",
    "Other",
]
GRADE_OPTIONS = ["-", 20, 30, 40, 45, 50, 55, 60, 65, 70, 75, 80]
PRESENT_OVERRIDE_OPTIONS = ["Auto", 20, 30, 40, 45, 50, 55, 60, 65, 70, 75, 80]
AUTO_METRICS = ("velo", "ivb", "hb_normalized")

st.set_page_config(page_title="Pitcher Scouting Grader v4.4.1", page_icon="⚾", layout="wide")


def init_state() -> None:
    st.session_state.setdefault("pitch_count", 2)
    st.session_state.setdefault("pitch_type_0", "Four-Seam Fastball")
    st.session_state.setdefault("pitch_type_1", "Slider")
    st.session_state.setdefault("impact_statement", "")
    st.session_state.setdefault("summary", "")
    st.session_state.setdefault("position", "P")


def val(key: str, default=None):
    return st.session_state.get(key, default)


def clean_grade(value):
    return None if value in (None, "-") else int(value)


def load_metadata() -> dict:
    if not METADATA_PATH.exists():
        return {}
    try:
        return json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def validate_baselines(baselines: pd.DataFrame, config: dict, metadata: dict) -> tuple[bool, str, list[str]]:
    issues: list[str] = []
    if baselines.empty:
        return False, "Embedded grading references are missing.", ["Baseline file is missing or empty."]

    required_cols = {"pitch_type", "metric", "mean", "sd"}
    missing_cols = required_cols.difference(baselines.columns)
    if missing_cols:
        issues.append(f"Missing baseline columns: {', '.join(sorted(missing_cols))}")

    if not missing_cols:
        for pitch_name, rule in config.items():
            if pitch_name == "note":
                continue
            code = rule["code"]
            for metric in AUTO_METRICS:
                hit = baselines[(baselines["pitch_type"] == code) & (baselines["metric"] == metric)]
                if hit.empty:
                    issues.append(f"Missing {code} {metric} reference")
                    continue
                mean = pd.to_numeric(hit.iloc[0]["mean"], errors="coerce")
                sd = pd.to_numeric(hit.iloc[0]["sd"], errors="coerce")
                if pd.isna(mean) or pd.isna(sd) or float(sd) <= 0:
                    issues.append(f"Invalid {code} {metric} mean/SD")

    hb_validation = metadata.get("hb_validation", {}) if metadata else {}
    if hb_validation.get("status") != "passed":
        issues.append("HB normalization validation marker is missing or failed.")

    if issues:
        return False, "Automatic present grades are disabled because the embedded reference table is incomplete.", issues

    model_version = metadata.get("model_version", "v0.1-embedded-guidelines")
    return True, f"Automatic present-grade model loaded: {model_version}", []


def pitch_input_snapshot(i: int) -> dict:
    pitch_type = val(f"pitch_type_{i}", "Four-Seam Fastball" if i == 0 else "Slider")
    return {
        "pitch_type": pitch_type,
        "velo": val(f"velo_{i}"),
        "ivb": val(f"ivb_{i}"),
        "hb": val(f"hb_{i}"),
        "velo_range": val(f"velo_range_{i}", ""),
        "present_override": val(f"present_override_{i}", "Auto"),
        "life_present_override": val(f"life_present_override_{i}", "Auto"),
        "future": val(f"future_{i}", "-"),
        "future_velo": val(f"future_velo_{i}", "-"),
        "future_life": val(f"future_life_{i}", "-"),
    }


def calculate_pitch(i: int, baselines: pd.DataFrame, config: dict, throws: str | None, auto_ready: bool):
    p = pitch_input_snapshot(i)
    if not auto_ready or p["pitch_type"] == "Other" or p["pitch_type"] not in config:
        return None

    if p["pitch_type"] in FASTBALL_SPLIT_TYPES:
        result = {"mode": "fastball_split", "velocity": None, "life": None}
        if p["velo"] is not None:
            try:
                result["velocity"] = grade_fastball_velocity(
                    p["pitch_type"], float(p["velo"]), baselines, config
                )
            except (ValueError, KeyError, TypeError):
                result["velocity"] = None
        if throws and p["ivb"] is not None and p["hb"] is not None:
            try:
                result["life"] = grade_fastball_life(
                    p["pitch_type"], float(p["ivb"]), float(p["hb"]), throws, baselines, config
                )
            except (ValueError, KeyError, TypeError):
                result["life"] = None
        return result

    if not throws or any(p[x] is None for x in ("velo", "ivb", "hb")):
        return None
    try:
        result = grade_pitch(
            pitch_name=p["pitch_type"],
            velo=float(p["velo"]),
            ivb=float(p["ivb"]),
            raw_hb=float(p["hb"]),
            throws=throws,
            baselines=baselines,
            config=config,
        )
        return {"mode": "single", "grade": result}
    except (ValueError, KeyError, TypeError):
        return None


def _velo_display(p: dict) -> str:
    if p["velo_range"]:
        return p["velo_range"].strip()
    if p["velo"] is not None:
        return f"{float(p['velo']):.1f} avg"
    return "-"


def build_grade_rows(baselines: pd.DataFrame, config: dict, throws: str | None, auto_ready: bool) -> list[dict]:
    rows: list[dict] = []
    for i in range(st.session_state.pitch_count):
        p = pitch_input_snapshot(i)
        calc = calculate_pitch(i, baselines, config, throws, auto_ready)
        pitch_type = p["pitch_type"]

        if pitch_type in FASTBALL_SPLIT_TYPES:
            if pitch_type == "Four-Seam Fastball":
                velo_label = "Fastball Velocity"
                life_label = "Fastball Life"
            else:
                velo_label = "Sinker Velocity"
                life_label = "Sinker Life"

            velocity_present = "-"
            life_auto = "-"
            if calc and calc.get("velocity"):
                velocity_present = calc["velocity"]["present_grade"]
            if calc and calc.get("life"):
                life_auto = calc["life"]["present_grade"]
            life_present = resolve_present_grade(life_auto, p["life_present_override"])

            rows.append({
                "Tool": velo_label,
                "Present": velocity_present,
                "Future": clean_grade(p["future_velo"]) or "-",
                "Velo / Range": _velo_display(p),
            })
            rows.append({
                "Tool": life_label,
                "Present": life_present,
                "Future": clean_grade(p["future_life"]) or "-",
                "Velo / Range": "-",
            })
        else:
            auto_present = "-"
            if calc and calc.get("grade"):
                auto_present = calc["grade"]["present_grade"]
            present = resolve_present_grade(auto_present, p["present_override"])
            rows.append({
                "Tool": pitch_type,
                "Present": present,
                "Future": clean_grade(p["future"]) or "-",
                "Velo / Range": _velo_display(p),
            })

    for tool, p_key, f_key in [
        ("Command", "command_present", "command_future"),
        ("Control", "control_present", "control_future"),
    ]:
        rows.append({
            "Tool": tool,
            "Present": clean_grade(val(p_key, "-")) or "-",
            "Future": clean_grade(val(f_key, "-")) or "-",
            "Velo / Range": "-",
        })
    return rows


def observations_snapshot() -> dict:
    return {
        "date": str(val("obs_date", "")) if val("obs_date", "") else "",
        "games_seen": val("games_seen", ""),
        "innings_seen": val("innings_seen", ""),
        "role": val("role_observed", ""),
        "delivery_grade": val("delivery_grade", "-"),
        "arm_action": val("arm_action", ""),
        "arm_angle": val("arm_angle", ""),
        "aggressiveness": val("aggressiveness", "-"),
        "instincts": val("instincts", "-"),
        "poise": val("poise", "-"),
        "makeup": val("on_field_makeup", ""),
        "delivery_notes": val("delivery_notes", ""),
    }


init_state()
config = load_config()
try:
    baselines = load_baselines(BASELINE_PATH)
except Exception as exc:
    baselines = pd.DataFrame()
    st.error(f"Reference table could not be read: {exc}")
metadata = load_metadata()
auto_ready, baseline_status, baseline_issues = validate_baselines(baselines, config, metadata)

st.title("Pitcher Scouting Grader")
st.caption("V1: scouting information in, objective present grades where available, clean report out.")

# PLAYER PROFILE
st.subheader("Player Profile")
c1, c2, c3 = st.columns(3)
with c1:
    name = st.text_input("Name", key="player_name", placeholder="Player name")
    position = st.text_input("Position", key="position", placeholder="P")
with c2:
    school = st.text_input("School", key="school", placeholder="Florida")
    draft_class = st.text_input("Draft Class", key="draft_class", placeholder="2027")
with c3:
    height = st.text_input("Height", key="height", placeholder="6'2\"")
    weight = st.number_input("Weight", min_value=0, max_value=400, value=None, step=1, key="weight", placeholder="210")

b1, b2, _ = st.columns([1, 1, 4])
with b1:
    bats = st.selectbox("Bats", ["", "R", "L", "S"], key="bats")
with b2:
    throws = st.selectbox("Throws *", ["", "R", "L"], key="throws")
st.caption("* Throws is required for movement-based grades so HB can be normalized correctly. Velocity grades do not require handedness.")

# OVERALL PROJECTION
st.subheader("Overall Projection")
op1, op2, op3 = st.columns(3)
with op1:
    floor_grade = st.selectbox("Floor", GRADE_OPTIONS, key="overall_floor")
with op2:
    likely_grade = st.selectbox("Most Likely", GRADE_OPTIONS, key="overall_most_likely")
with op3:
    ceiling_grade = st.selectbox("Ceiling", GRADE_OPTIONS, key="overall_ceiling")

_order_vals = [clean_grade(floor_grade), clean_grade(likely_grade), clean_grade(ceiling_grade)]
if all(v is not None for v in _order_vals) and not (_order_vals[0] <= _order_vals[1] <= _order_vals[2]):
    st.warning("Projection check: Floor should usually be <= Most Likely <= Ceiling.")

# IMPACT
st.subheader("Impact Statement")
st.text_area(
    "Impact Statement",
    key="impact_statement",
    label_visibility="collapsed",
    placeholder="One- or two-sentence projection / impact statement...",
    height=85,
)

# GRADES OUTPUT ONLY
st.subheader("Tool Grades")
grade_rows = build_grade_rows(baselines, config, throws or None, auto_ready)
grade_df = pd.DataFrame(grade_rows)
st.dataframe(grade_df, hide_index=True, use_container_width=True)
if not auto_ready:
    st.caption("Automatic present grades are off. Manual Command/Control and Future grades still export normally.")

# SUMMARY
st.subheader("Summary")
st.text_area(
    "Summary",
    key="summary",
    label_visibility="collapsed",
    placeholder="Full scouting summary...",
    height=180,
)

# EXPORT
profile = {
    "name": name,
    "position": position,
    "bats": bats,
    "throws": throws,
    "school": school,
    "height": height,
    "weight": weight,
    "draft_class": draft_class,
}
try:
    pdf_bytes = build_report_pdf(
        profile=profile,
        impact=st.session_state.impact_statement,
        grades=grade_rows,
        summary=st.session_state.summary,
        observations=observations_snapshot(),
        overall={
            "floor": clean_grade(floor_grade),
            "most_likely": clean_grade(likely_grade),
            "ceiling": clean_grade(ceiling_grade),
        },
    )
    ex1, ex2 = st.columns(2)
    with ex1:
        st.download_button(
            "Download Scouting Report PDF",
            data=pdf_bytes,
            file_name=f"{(name or 'player').strip().replace(' ', '_')}_scouting_report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    with ex2:
        st.download_button(
            "Download Grade Table CSV",
            data=grade_df.to_csv(index=False).encode("utf-8"),
            file_name=f"{(name or 'player').strip().replace(' ', '_')}_grades.csv",
            mime="text/csv",
            use_container_width=True,
        )
except Exception as exc:
    st.warning(f"Export is temporarily unavailable: {exc}")

# OBSERVATIONS
with st.expander("Observations", expanded=False):
    o1, o2, o3, o4 = st.columns(4)
    with o1:
        st.date_input("Date", value=None, key="obs_date")
    with o2:
        st.number_input("Games Seen", min_value=0, value=None, step=1, key="games_seen")
    with o3:
        st.number_input("Innings Seen", min_value=0.0, value=None, step=0.1, key="innings_seen")
    with o4:
        st.selectbox("Role Observed", ["", "Starter", "Reliever", "Multi-Inning Relief", "Opener", "Other"], key="role_observed")

    d1, d2, d3 = st.columns(3)
    with d1:
        st.selectbox("Delivery Grade", GRADE_OPTIONS, key="delivery_grade")
    with d2:
        st.selectbox("Arm Action", ["", "Short", "Average", "Long", "Other"], key="arm_action")
    with d3:
        st.selectbox("Arm Angle", ["", "Overhand", "High 3/4", "3/4", "Low 3/4", "Sidearm", "Submarine"], key="arm_angle")

    m1, m2, m3 = st.columns(3)
    with m1:
        st.selectbox("Aggressiveness", GRADE_OPTIONS, key="aggressiveness")
    with m2:
        st.selectbox("Instincts", GRADE_OPTIONS, key="instincts")
    with m3:
        st.selectbox("Poise", GRADE_OPTIONS, key="poise")

    st.text_area("On-Field Makeup", key="on_field_makeup", height=90)
    st.text_area("Delivery / Arm Action Notes", key="delivery_notes", height=90)

# ARSENAL INPUT / AUTO PRESENT GRADING
with st.expander("Arsenal / Pitch Calculator", expanded=False):
    if auto_ready:
        st.success(baseline_status)
    else:
        st.error(baseline_status)
        if baseline_issues:
            st.caption("Safety check: " + "; ".join(baseline_issues[:4]))

    st.caption(
        "Objective auto grades remain visible as a reference. Fastball/Sinker Velocity stays automatic only; "
        "shape-based Present grades can be overridden by the scout. Future grades remain your projection."
    )

    for i in range(st.session_state.pitch_count):
        st.markdown(f"#### Pitch {i + 1}")
        p1, p2 = st.columns([1.2, 2])
        with p1:
            default_type = "Four-Seam Fastball" if i == 0 else "Slider"
            if f"pitch_type_{i}" not in st.session_state:
                st.session_state[f"pitch_type_{i}"] = default_type
            pitch_type = st.selectbox("Pitch Type", PITCH_TYPES, key=f"pitch_type_{i}")
        with p2:
            a, b, c = st.columns(3)
            with a:
                st.number_input("Avg Velo", value=None, step=0.1, key=f"velo_{i}")
            with b:
                st.number_input("IVB", value=None, step=0.1, key=f"ivb_{i}")
            with c:
                st.number_input("HB", value=None, step=0.1, key=f"hb_{i}")

        calc = calculate_pitch(i, baselines, config, throws or None, auto_ready)

        if pitch_type in FASTBALL_SPLIT_TYPES:
            velocity_grade = calc.get("velocity") if calc else None
            life_grade = calc.get("life") if calc else None

            st.markdown("**Velocity**")
            vg1, vg2 = st.columns(2)
            with vg1:
                st.metric("Present - Auto", velocity_grade["present_grade"] if velocity_grade else "-")
            with vg2:
                st.selectbox("Future", GRADE_OPTIONS, key=f"future_velo_{i}")

            st.markdown("**Life / Shape**")
            lg1, lg2, lg3 = st.columns(3)
            with lg1:
                st.metric("Auto Grade", life_grade["present_grade"] if life_grade else "-")
            with lg2:
                st.selectbox(
                    "Present Grade",
                    PRESENT_OVERRIDE_OPTIONS,
                    key=f"life_present_override_{i}",
                    help="Leave on Auto to use the calculated life grade in the report, or choose your own 20-80 grade.",
                )
            with lg3:
                st.selectbox("Future Grade", GRADE_OPTIONS, key=f"future_life_{i}")
        else:
            g1, g2, g3 = st.columns(3)
            single = calc.get("grade") if calc else None
            with g1:
                st.metric("Auto Grade", single["present_grade"] if single else "-")
            with g2:
                st.selectbox(
                    "Present Grade",
                    PRESENT_OVERRIDE_OPTIONS,
                    key=f"present_override_{i}",
                    help="Leave on Auto to use the calculated grade in the report, or choose your own 20-80 grade.",
                )
            with g3:
                st.selectbox("Future Grade", GRADE_OPTIONS, key=f"future_{i}")

        with st.expander("Grade Details / Advanced Metrics", expanded=False):
            st.text_input("Velo Range (optional)", key=f"velo_range_{i}", placeholder="94-97")
            adv1, adv2, adv3 = st.columns(3)
            with adv1:
                st.number_input("Max Velo", value=None, step=0.1, key=f"max_velo_{i}")
            with adv2:
                st.number_input("Extension", value=None, step=0.1, key=f"extension_{i}")
            with adv3:
                st.number_input("VAA", value=None, step=0.1, key=f"vaa_{i}")

            pretty = {"velo": "Velo", "ivb": "IVB", "hb_normalized": "HB"}
            if pitch_type in FASTBALL_SPLIT_TYPES:
                if calc and calc.get("velocity"):
                    d = calc["velocity"]["component"]
                    st.markdown("**Velocity grade**")
                    st.dataframe(pd.DataFrame([{
                        "Metric": "Avg Velo",
                        "Player": round(d["value"], 2),
                        "Reference Mean": round(d["mlb_mean"], 2),
                        "Guideline SD": round(d["mlb_sd"], 2),
                        "Quality SD": round(d["quality_z"], 2),
                        "Grade": d["grade"],
                    }]), hide_index=True, use_container_width=True)
                if calc and calc.get("life"):
                    st.markdown("**Life grade**")
                    rows = []
                    for metric, detail in calc["life"]["components"].items():
                        rows.append({
                            "Metric": pretty[metric],
                            "Player": round(detail["value"], 2),
                            "Reference Mean": round(detail["mlb_mean"], 2),
                            "Guideline SD": round(detail["mlb_sd"], 2),
                            "Quality SD": round(detail["quality_z"], 2),
                            "Weight": f"{detail['weight']:.0%}",
                        })
                    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
                    st.caption(f"Normalized HB: {calc['life']['normalized_hb']:+.1f}\"")
                if not calc or (not calc.get("velocity") and not calc.get("life")):
                    st.caption("Enter Avg Velo for the velocity grade. Enter Throws + IVB + HB for the life grade.")
            else:
                if calc and calc.get("grade"):
                    rows = []
                    for metric, detail in calc["grade"]["components"].items():
                        rows.append({
                            "Metric": pretty[metric],
                            "Player": round(detail["value"], 2),
                            "Reference Mean": round(detail["mlb_mean"], 2),
                            "Guideline SD": round(detail["mlb_sd"], 2),
                            "Quality SD": round(detail["quality_z"], 2),
                            "Weight": f"{detail['weight']:.0%}",
                        })
                    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
                    if calc["grade"].get("warning"):
                        st.warning(calc["grade"]["warning"])
                else:
                    st.caption("Enter Throws + Avg Velo + IVB + HB to calculate the present grade.")

        st.divider()

    buttons = st.columns([1, 1, 3])
    with buttons[0]:
        if st.button("+ Add Pitch", use_container_width=True):
            if st.session_state.pitch_count < 8:
                st.session_state.pitch_count += 1
                st.rerun()
    with buttons[1]:
        if st.session_state.pitch_count > 2 and st.button("Remove Last", use_container_width=True):
            idx = st.session_state.pitch_count - 1
            prefixes = [
                "pitch_type", "velo", "ivb", "hb", "velo_range", "present_override", "life_present_override",
                "future", "future_velo", "future_life", "max_velo", "extension", "vaa",
            ]
            for prefix in prefixes:
                st.session_state.pop(f"{prefix}_{idx}", None)
            st.session_state.pitch_count -= 1
            st.rerun()

    st.markdown("#### Command / Control")
    cc1, cc2, cc3, cc4 = st.columns(4)
    with cc1:
        st.selectbox("Command - Present", GRADE_OPTIONS, key="command_present")
    with cc2:
        st.selectbox("Command - Future", GRADE_OPTIONS, key="command_future")
    with cc3:
        st.selectbox("Control - Present", GRADE_OPTIONS, key="control_present")
    with cc4:
        st.selectbox("Control - Future", GRADE_OPTIONS, key="control_future")

st.caption(
    "v4.4.1 V1 model: objective auto grades provide a reference; shape-based Present grades can be scout-overridden. "
    "Velocity Present grades stay automatic, while Future, Command/Control, Overall Projection and observations remain scout-entered."
)
