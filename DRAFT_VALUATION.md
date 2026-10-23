# Historical draft valuation guide

Version 0.2 replaces the fixed grade-index-to-round/dollar lookup with historical
MLB Pipeline grade-profile comparisons. It recommends the evaluator's investment
range, not a player's demand or expected signing bonus. Final scout overrides are
available even when historical evidence is insufficient.

## Reference data and provenance

`data/valuation/draft_history.json` records provenance; `draft_records.csv` contains
981 usable draft-grade profiles across
2022-2025, drawn from the top 250 in each year. Of these, 782 were selected in that
year's draft; 683 have a published slot value and 723 have a reported signing bonus.
The table includes numerical grades and factual draft/bio fields, not scouting prose.
The data was retrieved October 23, 2026.

Official archive pages:
- https://www.mlb.com/milb/prospects/2022/draft/
- https://www.mlb.com/milb/prospects/2023/draft/
- https://www.mlb.com/milb/prospects/2024/draft/
- https://www.mlb.com/milb/prospects/2025/draft/

Official draft outcomes (round, pick, assigned slot and bonus):
- https://statsapi.mlb.com/api/v1/draft/2022
- https://statsapi.mlb.com/api/v1/draft/2023
- https://statsapi.mlb.com/api/v1/draft/2024
- https://statsapi.mlb.com/api/v1/draft/2025

2026 dollar-index reference:
https://www.mlb.com/news/mlb-draft-2026-bonus-pool-pick-values

Rebuild using `python scripts/build_draft_history.py`. Temporary source pages are
cached under `tmp/draft_history` (not distributed). Only the bio explicitly titled
"draft" (case-insensitive) is used; later annual prospect reports are excluded.
If a two-way player has multiple grade paragraphs, only the first profile is used.
Nineteen archive entries lacked a usable draft-grade paragraph and were omitted.
Current roster height, weight and current prospect grades are never substituted.

## Grade profiles

`valuation_profiles.py` provides 16 explicitly illustrative grade combinations:
impact/contact/glove-first shortstops, speed/power center fielders, offense/defense
catchers, hit/power first basemen, a corner bat with hit risk, power/balanced/
pitchability starters, a starter with strike risk, and two relief profiles.
These synthetic inputs run through the same historical algorithm; they are not
attributed to real players or assigned hand-written round/dollar outcomes.
The app shows a profile label, matched players, grade vectors, years, rounds,
picks, original slot values and original signing bonuses. Exploring examples does
not edit the active scouting report.

## Matching and ranges

- Use explicit Future tool grades. No missing projection is filled from Present.
- Hitter features: Hit, Game Power (mapped to public Power), Run, Arm and Field.
  Raw Power is omitted from matching because the public data does not split it
  consistently. No defensible DH-only historical proxy is inferred.
- Pitcher features: the best complete fastball velocity/life pair averaged into
  one Fastball proxy; best secondary; second secondary for starters; and Control.
  Public Fastball is a holistic pitch grade, so the velocity/life average is an
  imperfect proxy. Public Control is not relabeled as Command. Command remains
  in the scouting report and the evaluator's role/risk assessment.
- Position, handedness and selected high-school/college/JUCO background influence
  matching. OF/INF archive labels receive an uncertainty penalty; they are not
  silently treated as exact projected defensive positions. Catchers are compared
  only with catcher-labeled profiles. Relief-related words in the draft narrative
  provide a soft role-context preference, not a verified future-role label.
- Grade distances are weighted RMS differences with documented contextual
  penalties. We retain up to 12 nearest unique players, reject grade/context
  distances above 10, and require at least 4 matches. Gaussian similarity weights
  (scale 5 grade points) limit domination by one exact match. These are transparent
  modeling choices, not learned or industry-approved coefficients.
- Height/weight influence the ordering of close comparisons only when both the
  user and the historical draft narrative provide explicit measurements. Size
  distance is symmetric, bounded and lightly weighted; bigger does not imply
  better. Many records lack size (459 explicit heights, 37 explicit weights).
- Round ranges use weighted historical round quantiles. Compensation and
  competitive-balance rounds map to the preceding numbered round for the range;
  exact original labels and overall picks remain visible in the comparable table.
- Dollar ranges use **assigned pick values**, not actual negotiated bonuses.
  Each year's dollars are indexed using the ratio of the 2026 first-pick slot
  ($11,350,600) to that year's first-pick slot. This is a consistent slot-dollar
  index, not a general inflation calculation. Values are rounded outward to $10K.
- At least 4 slot-valued peers and 75% slot coverage are required for an automatic
  dollar suggestion. Otherwise the app says insufficient slot-value evidence;
  actual bonuses are never used to fill missing slots. Late rounds are therefore
  often manual-value cases. Actual bonuses appear only as historical context.
- Lower/moderate/higher risk chooses 25-75%, 15-85% or 10-90% outcome quantiles.
  A 15+ point present/future gap or no paired present grades forces the wider
  range. These are descriptive sensitivity bands, not confidence intervals.
- Athleticism, makeup/learning, role reliability and documented physical fit may
  adjust the dollar range by 3% per point, capped at +/-3 points (+/-9% total).
  These discretionary adjustments are not fitted historical effects. Only add
  evidence not already reflected in tool projections. Round ranges remain the
  observed comparable ranges; there is no invented trait-to-round coefficient.
- The former weighted tool index is retained only as diagnostic JSON context;
  it does not choose rounds or dollars. The obsolete fixed-band table is removed.

## Overrides and exports

Use **My final valuation** to replace both the round and dollar range, with a
rationale. It also works with incomplete grades or unsupported historical profiles.
Ranges must be finite, nonnegative and ordered; draft rounds must be integers
between 1 and 20. Invalid overrides are omitted from report exports until fixed.
The PDF identifies a historical suggestion or scout override. JSON preserves the
original suggestion, comparable evidence, input grades, profile and rationale.

## Validation and limits

`python scripts/validate_draft_history.py` holds out each entire draft year, then
matches it only against other years. The checked-in JSON reports the measured
results; these are outcome comparisons, not career-success validation.

Of 771 eligible ranked/drafted records, 763 had supported comparisons. Median
absolute pick error was 43 picks; the descriptive round range contained the actual
round in 81.7% of supported cases. This is broad guidance, not an exact predictor.

The cohort excludes most lower-ranked/undrafted players and is selected toward
publicly ranked prospects. It cannot estimate a player's probability of being
drafted or a reliable free-agent budget. Historical picks themselves reflect
signability, club strategy, class strength and other factors that this model does
not isolate. No player-demand input is used, but those historical influences are
not magically removed from draft outcomes. Public tool grades differ by evaluator;
position, body and pitcher-role proxies are incomplete. Use the displayed peers
and final scout override when those omissions materially change your valuation.
