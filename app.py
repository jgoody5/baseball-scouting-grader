from __future__ import annotations

import streamlit as st

from hitter_page import render_hitter_page
from pitcher_page import render_pitcher_page
from portfolio_theme import apply_portfolio_theme

st.set_page_config(page_title="Baseball Scouting Grader", page_icon="⚾", layout="wide")

apply_portfolio_theme()

st.title("Baseball Scouting Grader")
st.caption("Pitcher and position-player scouting reports in one workflow.")

player_type = st.radio(
    "Player Type",
    ["Pitcher", "Position Player"],
    horizontal=True,
    label_visibility="collapsed",
    key="player_type_selector",
)

st.divider()

if player_type == "Pitcher":
    render_pitcher_page()
else:
    render_hitter_page()
