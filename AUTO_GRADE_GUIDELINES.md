# V1 Automatic Grade + Scout Override Guidelines

The first version is intentionally simple. It is a scouting report / information system first, not a final Stuff+ model.

## What is automatic

- Fastball Velocity: Avg Velo only.
- Fastball Life: movement only (IVB + normalized HB).
- Sinker Velocity: Avg Velo only.
- Sinker Life: movement only (IVB + normalized HB).
- Cutter, Slider, Sweeper, Curveball, Changeup, Splitter: Velo + IVB + normalized HB.

## Scout override rule

- Fastball/Sinker Velocity Present stays automatic only.
- Fastball/Sinker Life and every secondary pitch show the automatic grade but allow a manual Present override.
- Leaving Present on `Auto` sends the calculated grade to the report.
- Choosing a 20-80 Present grade sends the scout-entered grade to the report while preserving the auto grade in the calculator for reference.

## What stays manual

- Every Future grade.
- Command / Control.
- Delivery, makeup and observations.
- Floor / Most Likely / Ceiling.
- Impact Statement and Summary.

## 20-80 conversion

The embedded reference table uses this transparent rule:

- Reference mean = 50
- +0.5 guideline SD = 55
- +1.0 guideline SD = 60
- +1.5 guideline SD = 65
- +2.0 guideline SD = 70
- Negative SD movement works the same way toward 45 / 40 / 30.

These are current calibration guidelines, not claimed exact empirical MLB standard deviations.

## Fastball split

Four-Seam Fastball:
- Velocity grade = Avg Velo only.
- Life grade = 80% IVB + 20% normalized HB.

Sinker / Two-Seam:
- Velocity grade = Avg Velo only.
- Life grade = 30% lower-IVB quality + 70% arm-side HB quality.

This mirrors traditional scouting reports that separate fastball velocity from fastball life.

## Horizontal break

Manual HB should be entered exactly as the source reports it. Throws is used internally to normalize TrackMan-style HB so:

- positive normalized HB = arm-side movement
- negative normalized HB = glove-side movement

That lets RHP and LHP compare on one movement axis.

## Current limitation

Changeup and splitter grades are raw-shape grades only in V1. Fastball separation should be added later before treating those models as finished pitch-quality evaluations.
