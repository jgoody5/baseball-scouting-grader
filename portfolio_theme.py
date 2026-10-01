from __future__ import annotations

import streamlit as st


def apply_portfolio_theme() -> None:
    """Apply visual styling only. No app logic, fields, grading, or exports are changed."""
    st.html(
        """
        <style>
        :root {
            --bg: #f6f7f9;
            --panel: #ffffff;
            --text: #172033;
            --muted: #5f697a;
            --navy: #0f2d4f;
            --navy-2: #173d68;
            --line: #dfe4ea;
            --soft: #eef2f6;
        }

        html, body, [class*="css"] {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }

        .stApp {
            background: var(--bg);
            color: var(--text);
        }

        .block-container {
            max-width: 1080px;
            padding-top: 2.1rem;
            padding-bottom: 3.5rem;
        }

        h1 {
            color: var(--navy) !important;
            font-weight: 800 !important;
            letter-spacing: -0.04em !important;
            margin-bottom: .25rem !important;
        }

        h2 {
            color: var(--navy) !important;
            font-weight: 800 !important;
            letter-spacing: -0.025em !important;
        }

        h3 {
            color: var(--text) !important;
            font-weight: 750 !important;
            letter-spacing: -0.015em !important;
            margin-top: 1.45rem !important;
        }

        [data-testid="stCaptionContainer"] {
            color: var(--muted);
        }

        /* Player-type selector */
        div[role="radiogroup"] {
            display: inline-flex;
            gap: 4px;
            padding: 4px;
            background: var(--soft);
            border: 1px solid var(--line);
            border-radius: 10px;
            margin-top: .25rem;
            margin-bottom: .25rem;
        }

        div[role="radiogroup"] label {
            border-radius: 7px;
            padding: .42rem .85rem !important;
            margin: 0 !important;
        }

        div[role="radiogroup"] label:has(input:checked) {
            background: var(--panel);
            box-shadow: 0 1px 4px rgba(15,45,79,.12);
        }

        div[role="radiogroup"] label p {
            color: var(--navy) !important;
            font-weight: 700 !important;
        }

        /* Inputs */
        [data-baseweb="input"] > div,
        [data-baseweb="select"] > div,
        textarea {
            background: var(--panel) !important;
            border-color: var(--line) !important;
            border-radius: 8px !important;
        }

        [data-baseweb="input"] > div:focus-within,
        [data-baseweb="select"] > div:focus-within,
        textarea:focus {
            border-color: #9babbc !important;
            box-shadow: 0 0 0 2px rgba(15,45,79,.07) !important;
        }

        [data-testid="stWidgetLabel"] p,
        label p {
            color: #344054 !important;
            font-weight: 600 !important;
        }

        /* Expanders and metrics */
        [data-testid="stExpander"] {
            background: var(--panel);
            border: 1px solid var(--line) !important;
            border-radius: 10px !important;
            box-shadow: 0 2px 8px rgba(15,45,79,.025);
        }

        [data-testid="stExpander"] summary {
            color: var(--navy);
            font-weight: 700;
        }

        [data-testid="stMetric"] {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 9px;
            padding: .7rem .8rem;
        }

        /* Tables */
        [data-testid="stDataFrame"] {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 9px;
            overflow: hidden;
        }

        /* Buttons */
        .stDownloadButton > button {
            background: var(--navy) !important;
            color: #ffffff !important;
            border: 1px solid var(--navy) !important;
            border-radius: 8px !important;
            font-weight: 700 !important;
        }

        .stDownloadButton > button:hover {
            background: var(--navy-2) !important;
            border-color: var(--navy-2) !important;
        }

        .stButton > button {
            background: var(--panel) !important;
            color: var(--navy) !important;
            border: 1px solid var(--line) !important;
            border-radius: 8px !important;
            font-weight: 700 !important;
        }

        .stButton > button:hover {
            border-color: #bfcbd6 !important;
            box-shadow: 0 4px 12px rgba(15,45,79,.05);
        }

        hr {
            border-color: var(--line) !important;
        }

        /* Alerts */
        [data-testid="stAlert"] {
            border-radius: 9px;
        }

        @media (max-width: 700px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }
        }
        </style>
        """
    )
