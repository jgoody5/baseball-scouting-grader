from __future__ import annotations

from html import escape
from typing import Iterable

import streamlit as st

NAVY = "#153A63"
NAVY_DARK = "#0F2A49"
TEXT = "#172033"
MUTED = "#667085"
BORDER = "#D9E0E7"
LIGHT = "#F5F7FA"
LIGHT_BLUE = "#EDF4FB"
WHITE = "#FFFFFF"


def apply_global_styles() -> None:
    st.html("""
        <style>
        :root {
            --navy: #153A63;
            --navy-dark: #0F2A49;
            --text: #172033;
            --muted: #667085;
            --border: #D9E0E7;
            --light: #F5F7FA;
            --light-blue: #EDF4FB;
            --white: #FFFFFF;
        }

        .stApp {
            background:
                radial-gradient(circle at 8% 0%, rgba(21,58,99,.055), transparent 28rem),
                #F8FAFC;
            color: var(--text);
        }

        [data-testid="stAppViewContainer"] > .main {
            background: transparent;
        }

        .block-container {
            max-width: 1180px;
            padding-top: 1.65rem;
            padding-bottom: 3.5rem;
        }

        h1, h2, h3, h4 {
            color: var(--text);
            letter-spacing: -0.02em;
        }

        h2 {
            font-size: 1.55rem !important;
        }

        h3 {
            font-size: 1.05rem !important;
            margin-top: 1.25rem !important;
            margin-bottom: .55rem !important;
        }

        [data-testid="stCaptionContainer"] {
            color: var(--muted);
        }

        /* Inputs */
        [data-baseweb="input"] > div,
        [data-baseweb="select"] > div,
        textarea {
            border-radius: 10px !important;
            border-color: var(--border) !important;
            background: var(--white) !important;
        }

        [data-baseweb="input"] > div:focus-within,
        [data-baseweb="select"] > div:focus-within,
        textarea:focus {
            border-color: #6D8FB3 !important;
            box-shadow: 0 0 0 2px rgba(21,58,99,.08) !important;
        }

        label, [data-testid="stWidgetLabel"] p {
            color: #344054 !important;
            font-weight: 600 !important;
            font-size: .86rem !important;
        }

        /* Buttons */
        .stButton > button,
        .stDownloadButton > button {
            border-radius: 10px !important;
            border: 1px solid var(--border) !important;
            font-weight: 650 !important;
            min-height: 2.65rem;
            transition: transform .12s ease, box-shadow .12s ease, border-color .12s ease;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            border-color: #9CB0C5 !important;
            box-shadow: 0 4px 12px rgba(16,42,73,.08);
            transform: translateY(-1px);
        }

        /* Main player type selector */
        div[role="radiogroup"] {
            gap: .45rem;
            background: #EAF0F6;
            padding: .3rem;
            border-radius: 12px;
            width: fit-content;
            border: 1px solid #D6E0EA;
        }

        div[role="radiogroup"] label {
            background: transparent;
            border-radius: 9px;
            padding: .45rem .9rem !important;
            margin: 0 !important;
            transition: all .15s ease;
        }

        div[role="radiogroup"] label:has(input:checked) {
            background: white;
            box-shadow: 0 2px 7px rgba(15,42,73,.12);
        }

        div[role="radiogroup"] label p {
            font-weight: 700 !important;
            color: var(--navy-dark) !important;
        }

        /* Expanders */
        [data-testid="stExpander"] {
            border: 1px solid var(--border) !important;
            border-radius: 12px !important;
            background: rgba(255,255,255,.78) !important;
            overflow: hidden;
            box-shadow: 0 1px 2px rgba(16,24,40,.025);
        }

        [data-testid="stExpander"] summary {
            font-weight: 700;
            color: var(--navy-dark);
            min-height: 3.1rem;
        }

        [data-testid="stMetric"] {
            background: var(--light);
            border: 1px solid #E3E8EE;
            border-radius: 11px;
            padding: .72rem .85rem;
        }

        /* Native dataframes */
        [data-testid="stDataFrame"] {
            border: 1px solid var(--border);
            border-radius: 11px;
            overflow: hidden;
        }

        hr {
            border-color: #E4E9EF !important;
        }

        .app-shell {
            background: linear-gradient(135deg, #102D4D 0%, #153A63 58%, #1E507F 100%);
            color: white;
            border-radius: 18px;
            padding: 1.35rem 1.55rem 1.3rem;
            box-shadow: 0 14px 35px rgba(15,42,73,.16);
            margin-bottom: 1.15rem;
            position: relative;
            overflow: hidden;
        }

        .app-shell::after {
            content: "";
            position: absolute;
            width: 240px;
            height: 240px;
            border-radius: 999px;
            right: -90px;
            top: -120px;
            background: rgba(255,255,255,.055);
        }

        .app-kicker {
            text-transform: uppercase;
            font-size: .72rem;
            letter-spacing: .12em;
            opacity: .76;
            font-weight: 700;
            margin-bottom: .35rem;
        }

        .app-title {
            font-size: 2rem;
            line-height: 1.08;
            font-weight: 800;
            letter-spacing: -.035em;
            margin: 0;
        }

        .app-subtitle {
            font-size: .94rem;
            opacity: .82;
            margin-top: .48rem;
            max-width: 720px;
        }

        .app-chips {
            display: flex;
            flex-wrap: wrap;
            gap: .45rem;
            margin-top: .85rem;
        }

        .app-chip {
            border: 1px solid rgba(255,255,255,.19);
            background: rgba(255,255,255,.075);
            border-radius: 999px;
            padding: .27rem .58rem;
            font-size: .72rem;
            font-weight: 650;
            letter-spacing: .02em;
        }

        .page-label {
            display: inline-flex;
            align-items: center;
            gap: .45rem;
            color: var(--navy);
            font-weight: 750;
            text-transform: uppercase;
            letter-spacing: .095em;
            font-size: .7rem;
            margin: .35rem 0 .28rem;
        }

        .page-label::before {
            content: "";
            width: .5rem;
            height: .5rem;
            background: var(--navy);
            border-radius: 999px;
        }

        .player-card {
            background: white;
            border: 1px solid var(--border);
            border-radius: 15px;
            padding: 1rem 1.15rem;
            box-shadow: 0 5px 18px rgba(16,42,73,.055);
            margin: .75rem 0 1.05rem;
        }

        .player-name {
            color: var(--text);
            font-size: 1.35rem;
            font-weight: 800;
            letter-spacing: -.025em;
            line-height: 1.15;
        }

        .player-meta {
            color: var(--muted);
            font-size: .83rem;
            margin-top: .3rem;
            display: flex;
            flex-wrap: wrap;
            gap: .45rem;
        }

        .meta-pill {
            background: var(--light);
            border: 1px solid #E6EAF0;
            padding: .22rem .48rem;
            border-radius: 999px;
            white-space: nowrap;
        }

        .projection-strip {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: .65rem;
            margin: .55rem 0 1rem;
        }

        .projection-cell {
            background: white;
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: .68rem .8rem;
        }

        .projection-label {
            color: var(--muted);
            font-size: .7rem;
            text-transform: uppercase;
            letter-spacing: .08em;
            font-weight: 700;
        }

        .projection-value {
            color: var(--navy-dark);
            font-size: 1.4rem;
            line-height: 1.15;
            font-weight: 800;
            margin-top: .18rem;
        }

        .tool-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: .68rem;
            margin: .55rem 0 .9rem;
        }

        .tool-card {
            background: white;
            border: 1px solid var(--border);
            border-radius: 13px;
            padding: .78rem .86rem .72rem;
            box-shadow: 0 2px 8px rgba(16,42,73,.035);
            min-width: 0;
        }

        .tool-card-top {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: .65rem;
        }

        .tool-name {
            font-size: .83rem;
            font-weight: 750;
            color: #344054;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .tool-grade {
            font-size: 1.38rem;
            font-weight: 800;
            color: var(--navy-dark);
            letter-spacing: -.035em;
        }

        .tool-future {
            color: var(--muted);
            font-size: .72rem;
            font-weight: 650;
            margin-top: .08rem;
        }

        .tool-bar {
            height: 5px;
            background: #E9EEF3;
            border-radius: 999px;
            overflow: hidden;
            margin-top: .6rem;
        }

        .tool-bar-fill {
            height: 100%;
            border-radius: inherit;
            background: linear-gradient(90deg, #6886A6, #153A63);
        }

        .tool-ref {
            color: var(--muted);
            font-size: .7rem;
            line-height: 1.3;
            margin-top: .45rem;
            min-height: .9rem;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .note-card {
            border-left: 3px solid var(--navy);
            background: linear-gradient(90deg, var(--light-blue), #F8FAFC);
            border-radius: 0 11px 11px 0;
            padding: .75rem .9rem;
            color: #344054;
            font-size: .84rem;
            margin: .35rem 0 .8rem;
        }

        @media (max-width: 820px) {
            .tool-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
            .projection-strip {
                grid-template-columns: repeat(3, minmax(0, 1fr));
            }
            .app-title {
                font-size: 1.6rem;
            }
        }

        @media (max-width: 520px) {
            .tool-grid,
            .projection-strip {
                grid-template-columns: 1fr;
            }
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }
        }
        </style>
        """)


def render_app_header() -> None:
    st.html("""
        <div class="app-shell">
            <div class="app-kicker">Baseball Operations • Evaluation</div>
            <div class="app-title">Baseball Scouting Grader</div>
            <div class="app-subtitle">
                Build structured 20–80 evaluations, blend objective measurements with scouting judgment,
                and export a clean professional report.
            </div>
            <div class="app-chips">
                <span class="app-chip">20–80 Scale</span>
                <span class="app-chip">Pitcher + Position Player</span>
                <span class="app-chip">PDF / CSV Export</span>
            </div>
        </div>
        """)


def render_page_label(text: str) -> None:
    st.html(f'<div class="page-label">{escape(text)}</div>')


def render_player_card(
    name: str | None,
    position: str | None,
    school: str | None,
    bats: str | None,
    throws: str | None,
    height: str | None,
    weight,
    draft_class: str | None,
) -> None:
    display_name = escape((name or "Player Profile").strip() or "Player Profile")
    meta = []
    if position:
        meta.append(escape(str(position)))
    if school:
        meta.append(escape(str(school)))
    if bats or throws:
        meta.append(f"B/T {escape(str(bats or '—'))}/{escape(str(throws or '—'))}")
    if height:
        meta.append(escape(str(height)))
    if weight:
        meta.append(f"{escape(str(weight))} lbs")
    if draft_class:
        meta.append(f"Draft {escape(str(draft_class))}")

    pills = "".join(f'<span class="meta-pill">{m}</span>' for m in meta)
    if not pills:
        pills = '<span class="meta-pill">Enter player information above</span>'

    st.markdown(
        f"""
        <div class="player-card">
            <div class="player-name">{display_name}</div>
            <div class="player-meta">{pills}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_projection_strip(floor, likely, ceiling) -> None:
    def grade(v):
        return escape(str(v)) if v not in (None, "", "-") else "—"

    st.markdown(
        f"""
        <div class="projection-strip">
            <div class="projection-cell">
                <div class="projection-label">Floor</div>
                <div class="projection-value">{grade(floor)}</div>
            </div>
            <div class="projection-cell">
                <div class="projection-label">Most Likely</div>
                <div class="projection-value">{grade(likely)}</div>
            </div>
            <div class="projection-cell">
                <div class="projection-label">Ceiling</div>
                <div class="projection-value">{grade(ceiling)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _grade_percent(value) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(100.0, ((numeric - 20.0) / 60.0) * 100.0))


def render_tool_cards(
    rows: Iterable[dict],
    detail_key: str,
) -> None:
    cards = []
    for row in rows:
        tool = escape(str(row.get("Tool", "")))
        present = row.get("Present", "-")
        future = row.get("Future", "-")
        detail = row.get(detail_key, "-")

        present_text = "—" if present in (None, "", "-") else escape(str(present))
        future_text = "—" if future in (None, "", "-") else escape(str(future))
        detail_text = " " if detail in (None, "", "-") else escape(str(detail))
        width = _grade_percent(present)

        cards.append(
            f"""
            <div class="tool-card">
                <div class="tool-card-top">
                    <div>
                        <div class="tool-name">{tool}</div>
                        <div class="tool-future">Future {future_text}</div>
                    </div>
                    <div class="tool-grade">{present_text}</div>
                </div>
                <div class="tool-bar">
                    <div class="tool-bar-fill" style="width:{width:.1f}%"></div>
                </div>
                <div class="tool-ref">{detail_text}</div>
            </div>
            """
        )

    st.html('<div class="tool-grid">' + "".join(cards) + "</div>")


def render_note(text: str) -> None:
    st.html(f'<div class="note-card">{escape(text)}</div>')
