# Evidence Rule Engine

## Rule evaluation
- ONE_TIME: ≥1 matching evidence linked
- ROLLING_WINDOW: ≥1 matching evidence with event_date >= today - window_days
- EXPIRY: valid_until is null OR valid_until >= today
- COUNT_IN_WINDOW: count(evidence within window) >= min_items

## Status
- NOT_STARTED: no evidence linked
- IN_PROGRESS: evidence exists but rule not satisfied (never satisfied yet)
- OVERDUE: was satisfied previously but now outside window/expired
- READY: rule satisfied
- VERIFIED: READY + Verification.VERIFIED
