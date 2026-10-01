from __future__ import annotations

import streamlit as st

from hitter_page import render_hitter_page
from pitcher_page import render_pitcher_page
from ui_components import apply_global_styles, render_app_header

st.set_page_config(
    page_title="Baseball Scouting Grader",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_global_styles()
render_app_header()

player_type = st.radio(
    "Player Type",
    ["Pitcher", "Position Player"],
    horizontal=True,
    label_visibility="collapsed",
    key="player_type_selector",
)

if player_type == "Pitcher":
    render_pitcher_page()
else:
    render_hitter_page()
