# Baseball Scouting Grader

A pitcher scouting evaluation and report-generation tool built with Streamlit.

## What it does

- Captures player profile, impact statement, scouting observations, command/control, and projection grades.
- Automatically grades objective present pitch traits using embedded reference baselines.
- Separates fastball/sinker velocity from fastball/sinker life.
- Allows scout overrides for shape-based present grades while preserving the automatic grade as a reference.
- Exports a clean one-page scouting report PDF and a CSV grade table.

## Grading philosophy

The current model uses an embedded V1 reference table. A 50 represents the reference mean and each guideline standard deviation corresponds to 10 points on the 20–80 scale. Future grades remain scout-entered projections. See `AUTO_GRADE_GUIDELINES.md` and `DATA_SOURCES.md` for details and limitations.

## Run locally

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

Use `app.py` as the entrypoint. No secrets or external database are required for this version.
