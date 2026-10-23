"""Historical draft-profile suggestions with an independent final scout value."""
import json
from pathlib import Path

import streamlit as st

from draft_valuation import apply_override, evaluate, load_valuation_config, money_range
from valuation_profiles import render_profile_examples


def _comparables_table(result):
    return [{"Player": r['name'], "Year": r['year'], "Position": r['position'],
             "Draft round": r['round'], "Pick": r['pick'], "Tool grades": str(r['grades']),
             "Pick value (then $)": r['slot_value'], "Actual bonus (then $)": r['signing_bonus'],
             "Grade distance": r['grade_distance'], "Size evidence used": r['size_matched'],
             "Source type": r['source_type'], "Grade source": r['grade_source'],
             "Outcome source": r['outcome_source']} for r in result.get('comparables', [])]


def render_valuation(rows, kind, profile):
    prefix = "pv" if kind == "Pitcher" else "hv"
    config = load_valuation_config()
    st.subheader("Draft Valuation")
    st.caption("Grade-profile comparisons from the 2022-2025 MLB drafts. Your investment value, with a final scout override.")
    if not st.checkbox("Include draft valuation", key=f"{prefix}_enabled"):
        return None
    render_profile_examples(kind, prefix)
    if kind == "Pitcher":
        target = st.selectbox("Projected role", ["", "Starter", "Reliever"], key=f"{prefix}_target")
    else:
        positions = ["", *config["hitter_weights"]]
        default = str(profile.get("position", "")).strip().upper()
        target = st.selectbox("Projected defensive position", positions,
                              index=positions.index(default) if default in positions else 0,
                              key=f"{prefix}_target")
    source_type = st.selectbox("Player background", ['Any','High school','College','Junior college'],
                               key=f"{prefix}_source", help="Prefers peers with the same background. Not a signability input.")
    traits = {}
    with st.expander("Size, traits and projection risk", expanded=False):
        st.caption(f"Profile: {profile.get('height') or 'height not entered'} / "
                   f"{profile.get('weight') or 'weight not entered'} lb. "
                   "Size refines comparison ranking only when draft-time size is explicitly available. No automatic bigger-is-better premium.")
        fit = st.selectbox("Physical fit", list(config["physical_adjustments"]), index=1, key=f"{prefix}_fit")
        fit_note = st.text_input("Physical-fit rationale", key=f"{prefix}_fit_note",
                                placeholder="Frame, strength, mobility, or ability to maintain the projected role")
        st.caption("Traits not already captured by tool grades may adjust the dollar range by up to 9% total. "
                   "That adjustment is an explicit scouting assumption, not a fitted historical coefficient.")
        for name in ("Athleticism", "Makeup / learning", "Role reliability"):
            traits[name] = st.selectbox(name, list(config["trait_adjustments"]), index=1, key=f"{prefix}_{name}")
        risk = st.selectbox("Projection risk", list(config["risk_widths"]), index=1, key=f"{prefix}_risk",
                            help="Widens the historical outcome range; does not add upside points.")
    try:
        result = evaluate(rows, kind, target, traits, fit, fit_note, risk, config,
                          profile=profile, source_type=source_type)
    except (ValueError, TypeError) as exc:
        st.error(f"Valuation input: {exc}")
        return None
    result.update(profile=dict(profile), input_grades=rows)
    if result['ready']:
        c1,c2 = st.columns(2)
        c1.metric("Suggested round range", result['round'])
        c2.metric("Suggested bonus value", money_range(result))
        st.caption(f"{result['profile_label']} | {result['sample_count']} comparisons | "
                   f"{result['reference_year']} dollars | Historical guide, not a prediction.")
    else:
        st.info("No supported suggestion yet: " + "; ".join(result['missing']))
        st.caption("You can still enter your own final round and dollar value below.")
    with st.expander("Why this valuation?"):
        if result.get('ready'):
            st.write("Matched grade profile: " + str(result['features']))
            st.write(f"Comparable pick range: {result['pick_low']}-{result['pick_high']}. "
                     f"{result['slot_sample_count']} peers have published slot values.")
            st.write(result['money_basis'])
            st.caption("The range summarizes similar drafted players; it is not a statistical confidence interval. "
                       "Ranked prospects are overrepresented. Late-round and non-drafted players have limited coverage.")
            for reason in result['reasons']:
                st.write('• '+reason)
        if result.get('comparables'):
            st.dataframe(_comparables_table(result), hide_index=True, use_container_width=True)
        validation_path = Path(__file__).parent / "data/valuation/validation_report.json"
        if validation_path.exists():
            validation = json.loads(validation_path.read_text())["overall"]
            st.caption(f"Leave-one-draft-year-out check: median absolute error {validation['median_absolute_pick_error']:.0f} picks "
                       f"on {validation['supported_rows']} supported ranked/drafted players. Broad guide only; not a calibrated prediction.")
        st.caption("Draft-year tool grades only. Public Power matches Game Power; public Fastball is a proxy "
                   "for the velocity/life average. Separate Raw Power and Command have no direct public counterpart. "
                   "Relief mentions inform comparisons but do not establish a player's eventual role. "
                   "Matching rules still require external validation.")
    with st.expander("My final valuation", expanded=not result['ready']):
        override = st.checkbox("Override suggested round and bonus range", key=f"{prefix}_override")
        if override:
            a,b = st.columns(2)
            rlo = a.number_input("Earliest round", 1, 20, int(result.get('round_low',7)), key=f"{prefix}_rlo")
            rhi = b.number_input("Latest round", 1, 20, int(result.get('round_high',10)), key=f"{prefix}_rhi")
            blo = a.number_input("Minimum bonus value ($)", min_value=0, value=int(result.get('bonus_low') or 0), step=10000, key=f"{prefix}_blo")
            bhi = b.number_input("Maximum bonus value ($)", min_value=0, value=int(result.get('bonus_high') or 0), step=10000, key=f"{prefix}_bhi")
            reason = st.text_area("Valuation rationale", key=f"{prefix}_override_reason")
            try:
                result = apply_override(result,rlo,rhi,blo,bhi,reason)
            except ValueError as exc:
                st.error(str(exc))
                st.caption("Invalid override: valuation omitted from report until corrected.")
                return None
            st.success(f"Your value: {result['round']} | {money_range(result)}")
    if not result.get('ready'):
        return None
    st.download_button("Download Valuation JSON",json.dumps(result,indent=2),
                       file_name=f"{prefix}_draft_valuation.json",mime="application/json",key=f"{prefix}_download")
    return result
