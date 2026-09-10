# Validator

A reusable JavaScript validation script executed client-side with DukPY.
Validators attach to forms, fields, formsets, modules or scripts.

Module: `aurora.core.models` — `class Validator(AdminReverseMixin, NaturalKeyModel)`

## Relations

- **validator_for** ← `Registration.validator` (FK, `related_name="validator_for"`)
- **script_for** ← `Registration.scripts` (M2M, `related_name="script_for"`)
- referenced by `FlexForm.validator`, `FormSet.validator` and `FlexFormField.validator`

## Fields

| Field | Type | Purpose | Optional | Default |
|-------|------|---------|----------|---------|
| `version` | AutoIncVersionField | optimistic locking version | no | — |
| `last_update_date` | DateTimeField | last modification time (`auto_now`) | no | — |
| `label` | CharField(255) | human readable name | no | — |
| `name` | CharField(255) | function name, unique; auto-generated from the label | yes | `None` |
| `code` | TextField | JavaScript code executed by DukPY | yes | `None` |
| `target` | CharField(10) | where the validator applies: `form`, `field`, `formset`, `module`, `handler`, `script` | no | — |
| `trace` | BooleanField | trace invocations on Sentry (debug) | no | `False` |
| `count_errors` | BooleanField | count failures | no | `False` |
| `active` | BooleanField | enable/disable the validator | no | `False` |
| `draft` | BooleanField | draft validators run only for staff users | no | `False` |

## Notes

- Natural key: `name`.
- `validate(value)` runs the script only when `active` (or `draft` for staff).
