# Counter

Daily aggregation of collected records per registration, used for dashboards
and the charts views.

Module: `aurora.counters.models` — `class Counter(models.Model)`

## Relations

- **registration** → `Registration` (FK, CASCADE, `related_name="counters"`)

## Fields

| Field | Type | Purpose | Optional | Default |
|-------|------|---------|----------|---------|
| `registration` | ForeignKey(Registration, CASCADE) | the counted registration | no | — |
| `day` | DateField | aggregation day (db-indexed) | yes | `None` |
| `records` | IntegerField | number of records collected that day | yes | `None` |
| `details` | JSONField | per-hour breakdown (`{"hours": {hour: count}}`) | yes | `{}` |

## Notes

- `(registration, day)` is unique; `get_latest_by = "day"`.
- `Counter.objects.collect()` recomputes counters for the active
  registrations from `Record.timestamp` (historical backfill plus today).
- The `hourly` cached property returns the per-hour counts (hours 0-22).
