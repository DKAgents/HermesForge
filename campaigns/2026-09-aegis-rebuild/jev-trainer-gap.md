# JEV trainer gap

Date: 2026-09-27
scripts/gauntlet/jev_ml_predictor.py can fit a logistic model on R > 0.
scripts/gauntlet/jev_prefilter.py imports it.
scripts/gauntlet/jev_threshold_tuner.py says it retrains every 6 hours.
crontab has no jev line. The trainer is not scheduled.
Do not schedule it. The paper book is not a hostile label.
JEV stays the entry model. The trainer stays off the entry path.
