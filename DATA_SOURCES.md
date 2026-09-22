# Data / Model Notes - v4.4.1

V1 uses a fixed embedded reference table so the app is reliable offline and does not depend on Baseball Savant returning a particular CSV format.

The table is MLB-centered and contains reference means plus explicit guideline spread parameters for Velo, IVB and normalized HB by pitch type. It is a transparent calibration model, not a claim that every spread value is an exact empirical MLB standard deviation.

The purpose of V1 is to standardize objective pitch inputs and scouting report output. The reference table can be replaced later by a fully validated multi-year MLB/MiLB distribution without changing the report workflow.

HB convention inside the app:
- positive normalized HB = arm-side
- negative normalized HB = glove-side

Manual TrackMan-style HB is normalized using pitcher handedness before grading.
