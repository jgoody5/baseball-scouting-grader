# Draft valuation prototype

This feature estimates an evaluator's recommended round and signing-bonus
investment range. It does not estimate a player's demand, expected signing
bonus, likelihood of signing, career earnings or surplus value.

## Status and calibration

Version 0.1 is a **proposed, uncalibrated rubric**. All tool weights, positional
adjustments, trait adjustments and grade-to-round mappings are design assumptions,
not learned coefficients, industry consensus, or Jack's confirmed valuation scale.
Review them against completed scouting reports before adopting the suggestions.
The application labels suggestions and scout overrides separately.

Dollar bands are rounded discretionary budgets informed by MLB's 2026 slot
table: https://www.mlb.com/news/mlb-draft-2026-bonus-pool-pick-values
The underlying source is dated July 11, 2026. Source reviewed October 23, 2026.
The official data anchors the money scale, **not** the mapping from tools to rounds.
Rounds 11-20/free-agent budgets are proposed allowances, not official slot values.
Values remain in 2026 dollars even if a player has a later draft class. These are
not spending caps. No asking price, college commitment or signability enters the model.

## Calculation

1. Use explicitly entered Future grades. Do not assume missing projections equal
   Present grades. Require every positively weighted tool.
2. Hitters use projected-position-specific weights. Hit and game power carry the
   offensive value; raw power has only 5% weight to limit counting power twice.
   Catcher/shortstop/center field receive +2 index points, corner outfield -1,
   first base -3 and DH -4. Other positions are neutral.
3. Pitchers combine velocity and life equally into one fastball tool. If both
   fastball and sinker are graded, use the better complete pair. A starter needs
   two distinct secondary pitch types, Command and Control; a reliever needs one.
   Relievers receive -4 index points. A role is an evaluator input, not something
   inferred from height, velocity or a single pitch. Slider and sweeper can still
   be closely related shapes; the evaluator must assess actual arsenal breadth.
4. Athleticism, makeup/learning, role reliability and physical fit contribute at
   most +/-1 each and +/-3 together. Only add traits not already reflected in tool
   projections. Height and weight are retained in the profile/export but never
   produce an automatic size premium or penalty. A non-neutral physical-fit
   assessment requires a rationale about body, movement or role suitability.
5. Look up the resulting continuous index in `valuation_config.json`. The index is
   not an FV grade. Risk expands lookup by 0/2/4 points. A 15+ point present/future
   gap or no paired present grades forces at least 4 points of sensitivity.
   Sensitivity ranges are not statistical confidence intervals. Round/dollar
   envelopes may be broad when adjacent bands are crossed.
6. A scout may replace the final round and dollar ranges with a reason. JSON
   preserves the original suggestion, input grades, profile, and adjustments;
   report PDFs identify whether the displayed value is a suggestion or override.

## Remaining model limitations

- No historical draft outcome validation or comparison by class, age or competition.
- Position and projected-role choices require scouting judgment, especially catcher
  defense, starter durability, and risk of moving down the defensive spectrum.
- Existing automatic tool grades retain their own calibration limitations.
- Overall Floor/Most Likely/Ceiling is not mixed into this model, to avoid counting
  the same evaluation twice. Compare disagreements as part of review.
- No automated eligibility determination or injury/medical inference.

## Next calibration step

Enter 10-20 prior evaluations with independently assigned round/bonus ranges,
including starting pitchers, relievers, premium defenders and bat-first players.
Compare suggestions to those targets, adjust the documented config and reserve
separate examples to check whether changes generalize. Until then, keep the
prototype label and use final scout overrides where appropriate.
