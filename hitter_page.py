from __future__ import annotations

import pandas as pd
import streamlit as st

from hitter_grading import (
    grade_game_power_from_projected_hr,
    grade_hit_from_projected_avg,
    grade_raw_power,
    grade_run_from_60,
    grade_run_from_home_to_first,
    resolve_reference_grade,
)
from hitter_report_export import build_hitter_report_pdf
from ui_components import (
    render_page_label,
    render_player_card,
    render_projection_strip,
    render_tool_cards,
)

HITTER_GRADE_OPTIONS = ["-", 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80]
HITTER_OVERRIDE_OPTIONS = ["Auto", 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80]


def _clean_grade(value):
    return None if value in (None, "-") else int(value)


def _val(key: str, default=None):
    return st.session_state.get(key, default)


def _init_hitter_state() -> None:
    st.session_state.setdefault("hitter_impact_statement", "")
    st.session_state.setdefault("hitter_summary", "")


def _observations_snapshot() -> dict:
    return {
        "date": str(_val("hitter_obs_date", "")) if _val("hitter_obs_date", "") else "",
        "games_seen": _val("hitter_games_seen", ""),
        "positions_seen": _val("hitter_positions_seen", ""),
        "swing": _val("hitter_swing_notes", ""),
        "approach": _val("hitter_approach_notes", ""),
        "adjustments": _val("hitter_adjustment_notes", ""),
        "defense": _val("hitter_defense_notes", ""),
        "baserunning": _val("hitter_baserunning_notes", ""),
        "makeup": _val("hitter_makeup_notes", ""),
        "arm_notes": _val("hitter_arm_notes", ""),
    }


def _tool_rows(
    hit_ref,
    raw_ref,
    raw_source,
    game_ref,
    run_ref,
    run_reference_text,
    throw_velo,
) -> list[dict]:
    hit_present = resolve_reference_grade(hit_ref, _val("hit_present_override", "Auto"))
    raw_present = resolve_reference_grade(raw_ref, _val("raw_present_override", "Auto"))
    game_present = resolve_reference_grade(game_ref, _val("game_present_override", "Auto"))
    run_present = resolve_reference_grade(run_ref, _val("run_present_override", "Auto"))

    hit_avg = _val("projected_mlb_avg")
    ev90 = _val("ev90")
    max_ev = _val("max_ev")
    projected_hr = _val("projected_mlb_hr")

    if hit_avg is not None:
        hit_ref_text = f"Projected MLB AVG: {float(hit_avg):.3f}"
    else:
        hit_ref_text = "-"

    if raw_source == "EV90" and ev90 is not None:
        raw_ref_text = f"EV90: {float(ev90):.1f} mph"
    elif raw_source and max_ev is not None:
        raw_ref_text = f"Max EV: {float(max_ev):.1f} mph"
    else:
        raw_ref_text = "-"

    game_ref_text = f"Projected MLB HR: {int(projected_hr)}" if projected_hr is not None else "-"
    arm_ref_text = f"Throw velo: {float(throw_velo):.1f} mph" if throw_velo is not None else "-"

    return [
        {"Tool": "Hit", "Present": hit_present, "Future": _clean_grade(_val("hit_future", "-")) or "-", "Reference": hit_ref_text},
        {"Tool": "Raw Power", "Present": raw_present, "Future": _clean_grade(_val("raw_future", "-")) or "-", "Reference": raw_ref_text},
        {"Tool": "Game Power", "Present": game_present, "Future": _clean_grade(_val("game_future", "-")) or "-", "Reference": game_ref_text},
        {"Tool": "Run", "Present": run_present, "Future": _clean_grade(_val("run_future", "-")) or "-", "Reference": run_reference_text or "-"},
        {"Tool": "Arm", "Present": _clean_grade(_val("arm_present", "-")) or "-", "Future": _clean_grade(_val("arm_future", "-")) or "-", "Reference": arm_ref_text},
        {"Tool": "Field", "Present": _clean_grade(_val("field_present", "-")) or "-", "Future": _clean_grade(_val("field_future", "-")) or "-", "Reference": "-"},
    ]


def render_hitter_page() -> None:
    _init_hitter_state()

    render_page_label("Position Player Evaluation")
    st.header("Position Player")
    st.caption("Build a six-tool report with objective references where they add value and scout judgment everywhere else.")

    st.subheader("Player Profile")
    c1, c2, c3 = st.columns(3)
    with c1:
        name = st.text_input("Name", key="hitter_player_name", placeholder="Player name")
        position = st.text_input("Position", key="hitter_position", placeholder="CF")
    with c2:
        school = st.text_input("School", key="hitter_school", placeholder="Florida")
        draft_class = st.text_input("Draft Class", key="hitter_draft_class", placeholder="2027")
    with c3:
        height = st.text_input("Height", key="hitter_height", placeholder="6'1\"")
        weight = st.number_input("Weight", min_value=0, max_value=400, value=None, step=1, key="hitter_weight", placeholder="195")

    b1, b2, _ = st.columns([1, 1, 4])
    with b1:
        bats = st.selectbox("Bats", ["", "R", "L", "S"], key="hitter_bats")
    with b2:
        throws = st.selectbox("Throws", ["", "R", "L"], key="hitter_throws")

    render_player_card(
        name=name,
        position=position,
        school=school,
        bats=bats,
        throws=throws,
        height=height,
        weight=weight,
        draft_class=draft_class,
    )

    st.subheader("Overall Projection")
    op1, op2, op3 = st.columns(3)
    with op1:
        floor_grade = st.selectbox("Floor", HITTER_GRADE_OPTIONS, key="hitter_overall_floor")
    with op2:
        likely_grade = st.selectbox("Most Likely", HITTER_GRADE_OPTIONS, key="hitter_overall_most_likely")
    with op3:
        ceiling_grade = st.selectbox("Ceiling", HITTER_GRADE_OPTIONS, key="hitter_overall_ceiling")

    ordered = [_clean_grade(floor_grade), _clean_grade(likely_grade), _clean_grade(ceiling_grade)]
    if all(v is not None for v in ordered) and not (ordered[0] <= ordered[1] <= ordered[2]):
        st.warning("Projection check: Floor should usually be <= Most Likely <= Ceiling.")

    render_projection_strip(floor_grade, likely_grade, ceiling_grade)

    st.subheader("Impact Statement")
    st.text_area(
        "Impact Statement",
        key="hitter_impact_statement",
        label_visibility="collapsed",
        placeholder="One- or two-sentence role / impact projection...",
        height=85,
    )

    hit_ref = grade_hit_from_projected_avg(_val("projected_mlb_avg"))
    raw_ref, raw_source = grade_raw_power(_val("ev90"), _val("max_ev"))
    game_ref = grade_game_power_from_projected_hr(_val("projected_mlb_hr"))

    run_method = _val("run_method", "60-Yard")
    run_ref = None
    run_reference_text = "-"
    if run_method == "60-Yard":
        run_time = _val("sixty_time")
        run_ref = grade_run_from_60(run_time)
        if run_time is not None:
            run_reference_text = f"60-Yard: {float(run_time):.2f}s"
    else:
        h1b = _val("home_to_first")
        timed_side = bats if bats in {"R", "L"} else _val("home_to_first_side", "")
        run_ref = grade_run_from_home_to_first(h1b, timed_side)
        if h1b is not None:
            hand_label = timed_side or "timed side required"
            run_reference_text = f"H-1B: {float(h1b):.2f}s ({hand_label})"

    grade_rows = _tool_rows(
        hit_ref,
        raw_ref,
        raw_source,
        game_ref,
        run_ref,
        run_reference_text,
        _val("throw_velo"),
    )
    grade_df = pd.DataFrame(grade_rows)

    st.subheader("Tool Grades")
    render_tool_cards(grade_rows, "Reference")
    with st.expander("Detailed Grade Table", expanded=False):
        st.dataframe(grade_df, hide_index=True, use_container_width=True)

    st.subheader("Summary")
    st.text_area(
        "Summary",
        key="hitter_summary",
        label_visibility="collapsed",
        placeholder="Full position-player scouting summary...",
        height=180,
    )

    st.subheader("Report Export")
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
        pdf_bytes = build_hitter_report_pdf(
            profile=profile,
            impact=st.session_state.hitter_impact_statement,
            grades=grade_rows,
            summary=st.session_state.hitter_summary,
            observations=_observations_snapshot(),
            overall={
                "floor": _clean_grade(floor_grade),
                "most_likely": _clean_grade(likely_grade),
                "ceiling": _clean_grade(ceiling_grade),
            },
        )
        ex1, ex2 = st.columns(2)
        with ex1:
            st.download_button(
                "Download Scouting Report PDF",
                data=pdf_bytes,
                file_name=f"{(name or 'player').strip().replace(' ', '_')}_position_player_scouting_report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        with ex2:
            st.download_button(
                "Download Grade Table CSV",
                data=grade_df.to_csv(index=False).encode("utf-8"),
                file_name=f"{(name or 'player').strip().replace(' ', '_')}_position_player_grades.csv",
                mime="text/csv",
                use_container_width=True,
            )
    except Exception as exc:
        st.warning(f"Export is temporarily unavailable: {exc}")

    with st.expander("Observations", expanded=False):
        o1, o2, o3 = st.columns(3)
        with o1:
            st.date_input("Date", value=None, key="hitter_obs_date")
        with o2:
            st.number_input("Games Seen", min_value=0, value=None, step=1, key="hitter_games_seen")
        with o3:
            st.text_input("Position(s) Seen", key="hitter_positions_seen", placeholder="CF / RF")

        st.markdown("**Hitting**")
        st.text_area("Swing", key="hitter_swing_notes", height=80, placeholder="Path, bat speed, barrel control, load...")
        st.text_area("Approach", key="hitter_approach_notes", height=80, placeholder="Swing decisions, zone awareness, count management...")
        st.text_area("Adjustments", key="hitter_adjustment_notes", height=80, placeholder="Ability to adjust within and between at-bats...")

        st.markdown("**Defense / Baserunning / Makeup**")
        st.text_area("Defense", key="hitter_defense_notes", height=80, placeholder="Hands, feet, range, routes, reads, instincts...")
        st.text_area("Baserunning", key="hitter_baserunning_notes", height=70, placeholder="First step, turns, instincts, aggressiveness...")
        st.text_area("Arm Notes", key="hitter_arm_notes", height=70, placeholder="Strength, carry, accuracy, release...")
        st.text_area("On-Field Makeup", key="hitter_makeup_notes", height=70)

    with st.expander("Hitting / Tools Calculator", expanded=False):
        st.caption(
            "Reference grades are objective benchmarks where appropriate. Present grades can be scout-overridden; "
            "Future grades remain your projection."
        )

        st.markdown("#### Hit")
        h1, h2, h3, h4 = st.columns(4)
        with h1:
            st.number_input("Projected MLB AVG", min_value=0.100, max_value=0.400, value=None, step=0.001, format="%.3f", key="projected_mlb_avg")
        with h2:
            st.metric("Reference Grade", hit_ref if hit_ref is not None else "-")
        with h3:
            st.selectbox("Present Grade", HITTER_OVERRIDE_OPTIONS, key="hit_present_override")
        with h4:
            st.selectbox("Future Grade", HITTER_GRADE_OPTIONS, key="hit_future")
        st.caption("Projected batting average is a reference point only. Swing quality, contact, approach and competition context still matter.")

        st.markdown("#### Raw Power")
        r1, r2, r3, r4, r5 = st.columns(5)
        with r1:
            st.number_input("EV90", value=None, step=0.1, key="ev90")
        with r2:
            st.number_input("Max EV", value=None, step=0.1, key="max_ev")
        with r3:
            st.metric("Reference Grade", raw_ref if raw_ref is not None else "-")
        with r4:
            st.selectbox("Present Grade", HITTER_OVERRIDE_OPTIONS, key="raw_present_override")
        with r5:
            st.selectbox("Future Grade", HITTER_GRADE_OPTIONS, key="raw_future")
        if raw_source:
            st.caption(f"Reference source: {raw_source}. EV90 takes priority when both are entered.")

        st.markdown("#### Game Power")
        g1, g2, g3, g4 = st.columns(4)
        with g1:
            st.number_input("Projected MLB HR", min_value=0, max_value=70, value=None, step=1, key="projected_mlb_hr")
        with g2:
            st.metric("Reference Grade", game_ref if game_ref is not None else "-")
        with g3:
            st.selectbox("Present Grade", HITTER_OVERRIDE_OPTIONS, key="game_present_override")
        with g4:
            st.selectbox("Future Grade", HITTER_GRADE_OPTIONS, key="game_future")

        st.markdown("#### Run")
        method_col, time_col, ref_col, present_col, future_col = st.columns(5)
        with method_col:
            run_method = st.selectbox("Measurement", ["60-Yard", "Home-to-First"], key="run_method")
        if run_method == "60-Yard":
            with time_col:
                st.number_input("60-Yard Time", min_value=5.5, max_value=9.0, value=None, step=0.01, format="%.2f", key="sixty_time")
        else:
            with time_col:
                st.number_input("Home-to-First", min_value=3.5, max_value=5.5, value=None, step=0.01, format="%.2f", key="home_to_first")
                if bats == "S":
                    st.selectbox("Timed From", ["", "R", "L"], key="home_to_first_side")
        with ref_col:
            st.metric("Reference Grade", run_ref if run_ref is not None else "-")
        with present_col:
            st.selectbox("Present Grade", HITTER_OVERRIDE_OPTIONS, key="run_present_override")
        with future_col:
            st.selectbox("Future Grade", HITTER_GRADE_OPTIONS, key="run_future")
        if run_method == "Home-to-First" and bats not in {"R", "L", "S"}:
            st.caption("Choose the hitter's batting side to calculate the home-to-first reference grade.")
        elif run_method == "Home-to-First" and bats == "S" and _val("home_to_first_side", "") not in {"R", "L"}:
            st.caption("For a switch hitter, choose which side the player was timed from.")

        st.markdown("#### Arm")
        a1, a2, a3 = st.columns(3)
        with a1:
            st.number_input("Throw Velo (optional)", value=None, step=0.1, key="throw_velo")
        with a2:
            st.selectbox("Present Grade", HITTER_GRADE_OPTIONS, key="arm_present")
        with a3:
            st.selectbox("Future Grade", HITTER_GRADE_OPTIONS, key="arm_future")
        st.caption("Throw velocity is supporting context. Arm strength/carry, accuracy, release and position remain scout-evaluated.")

        st.markdown("#### Field")
        f1, f2 = st.columns(2)
        with f1:
            st.selectbox("Present Grade", HITTER_GRADE_OPTIONS, key="field_present")
        with f2:
            st.selectbox("Future Grade", HITTER_GRADE_OPTIONS, key="field_future")
        st.caption("Field remains scout-driven in V2. Use the observation notes for hands, feet, range, reads/routes and instincts.")

    st.caption(
        "V2 position-player model: objective measurements provide reference grades where defensible; the evaluator controls "
        "Present overrides and every Future projection."
    )
