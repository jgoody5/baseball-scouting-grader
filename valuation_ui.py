"""Shared draft valuation section for both scouting workflows."""
import json

import streamlit as st

from draft_valuation import apply_override, evaluate, load_valuation_config, money_range


def render_valuation(rows, kind, profile):
    prefix = "pv" if kind == "Pitcher" else "hv"
    config = load_valuation_config()
    st.subheader("Draft Valuation")
    st.caption("Your scouting investment range. No asking price or signability assumptions. "
               "Prototype rubric: weights and bands still need calibration against your evaluations.")
    enabled = st.checkbox("Include draft valuation", key=f"{prefix}_enabled")
    if not enabled:
        return None
    if kind == "Pitcher":
        target = st.selectbox("Projected role", ["", "Starter", "Reliever"], key=f"{prefix}_target")
    else:
        positions = ["", *config["hitter_weights"]]
        default = str(profile.get("position", "")).strip().upper()
        target = st.selectbox("Projected defensive position", positions,
                              index=positions.index(default) if default in positions else 0,
                              key=f"{prefix}_target",
                              help="Choose the position you expect him to play, not simply where he was listed.")
    traits = {}
    with st.expander("Size, traits and projection risk", expanded=True):
        st.caption(f"Profile: {profile.get('height') or 'height not entered'} / "
                   f"{profile.get('weight') or 'weight not entered'} lb. "
                   "Height and weight alone do not earn or lose points. Assess how the body fits the projected role.")
        fit = st.selectbox("Physical fit", list(config["physical_adjustments"]), index=1,
                           key=f"{prefix}_fit")
        fit_note = st.text_input("Physical-fit rationale", key=f"{prefix}_fit_note",
                                placeholder="Frame, strength, mobility, or ability to maintain the projected role")
        st.caption("Use traits only for evidence not already reflected in your tool grades. "
                   "Physical fit and traits together are capped at +/-3 index points.")
        for name in ("Athleticism", "Makeup / learning", "Role reliability"):
            traits[name] = st.selectbox(name, list(config["trait_adjustments"]), index=1,
                                        key=f"{prefix}_{name}")
        risk = st.selectbox("Projection risk", list(config["risk_widths"]), index=1,
                            key=f"{prefix}_risk",
                            help="Higher uncertainty widens the valuation range; it does not add upside points.")
    try:
        result = evaluate(rows, kind, target, traits, fit, fit_note, risk, config)
    except (ValueError, TypeError) as exc:
        st.error(f"Valuation input: {exc}")
        return None
    if not result["ready"]:
        st.info("Complete these inputs to calculate value: " + "; ".join(result["missing"]))
        return None
    result["profile"] = dict(profile)
    result["input_grades"] = rows
    c1, c2 = st.columns(2)
    c1.metric("Suggested round range", result["round"])
    c2.metric("Suggested bonus value", money_range(result))
    st.caption(f"Central band: {result['central_band']} | 2026 dollars | "
               "Investment recommendation, not expected draft position or signing bonus.")
    with st.expander("Why this valuation?"):
        st.dataframe(result["components"], hide_index=True, use_container_width=True)
        st.write(f"Tool index {result['base_index']:.1f} + position/role "
                 f"{result['position_role_adjustment']:+.1f} + traits "
                 f"{result['trait_adjustment']:+.1f} = {result['index']:.1f}.")
        st.caption("This index is an internal lookup score, not an overall 20-80 scouting grade.")
        for reason in result["reasons"]:
            st.write("• " + reason)
        st.write(f"Sensitivity range: +/-{result['range_width']} index points. This is not a statistical confidence interval.")
        st.write(config["money_basis"])
        st.markdown(f"[2026 MLB slot-value reference]({config['source']})")
        st.dataframe(config["bands"], hide_index=True, use_container_width=True)
    with st.expander("My final valuation"):
        override = st.checkbox("Override suggested round and bonus range", key=f"{prefix}_override")
        if override:
            a, b = st.columns(2)
            rlo = a.number_input("Earliest round", 1, 20, result["round_low"], key=f"{prefix}_rlo")
            rhi = b.number_input("Latest round", 1, 20, result["round_high"], key=f"{prefix}_rhi")
            blo = a.number_input("Minimum bonus value ($)", min_value=0, value=int(result["bonus_low"]),
                                 step=10000, key=f"{prefix}_blo")
            bhi = b.number_input("Maximum bonus value ($)", min_value=0, value=int(result["bonus_high"]),
                                 step=10000, key=f"{prefix}_bhi")
            reason = st.text_area("Valuation rationale", key=f"{prefix}_override_reason")
            try:
                result = apply_override(result, rlo, rhi, blo, bhi, reason)
            except ValueError as exc:
                st.error(str(exc))
                st.caption("Invalid override: valuation omitted from report until corrected.")
                return None
            st.success(f"Your value: {result['round']} | {money_range(result)}")
    st.download_button("Download Valuation JSON", json.dumps(result, indent=2),
                       file_name=f"{prefix}_draft_valuation.json", mime="application/json", key=f"{prefix}_download")
    return result

