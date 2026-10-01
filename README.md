# Baseball Scouting Grader

A Streamlit scouting evaluation and report-generation tool for pitchers and position players.

## V2 structure

The app now begins with a Player Type selector:

- **Pitcher** — preserves the existing V1 pitcher workflow and grading logic.
- **Position Player** — adds a six-tool scouting workflow with Hit, Raw Power, Game Power, Run, Arm and Field.

## Position-player grading philosophy

V2 uses objective measurements as reference points where the benchmark is defensible, while preserving scout judgment.

- **Hit:** projected MLB batting average -> reference grade, with Present override and manual Future.
- **Raw Power:** EV90 preferred; Max EV fallback -> reference grade, with Present override and manual Future.
- **Game Power:** projected MLB HR total -> reference grade, with Present override and manual Future.
- **Run:** 60-yard or handedness-adjusted home-to-first -> reference grade, with Present override and manual Future.
- **Arm:** scout-graded; optional throwing velocity is supporting context only.
- **Field:** scout-graded.

The exported hitter report mirrors the pitcher report: profile, overall projection, impact statement, tool grades, summary and observations.

## Pitcher workflow

The pitcher side is intentionally unchanged from V1. It retains embedded pitch baselines, automatic fastball/sinker velocity grading, automatic shape references, scout overrides for shape-based Present grades, manual Future grades, Command/Control and the existing one-page PDF export.

## Run locally

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

No secrets or external database are required.
