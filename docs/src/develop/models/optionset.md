# OptionSet

A named, multilingual list of options served to `AjaxSelectField` widgets
(and the options endpoints). The data is a plain text table parsed at
runtime.

Module: `aurora.core.models` — `class OptionSet(AdminReverseMixin, NaturalKeyModel, models.Model)`

## Relations

- None (standalone); consumed by fields through the option set name.

## Fields

| Field | Type | Purpose | Optional | Default |
|-------|------|---------|----------|---------|
| `version` | AutoIncVersionField | optimistic locking version | no | — |
| `last_update_date` | DateTimeField | last modification time (`auto_now`) | no | — |
| `name` | CharField(100) | unique name, must match `[a-z0-9-_]` | no | — |
| `description` | CharField(1000) | human readable description | yes | `None` |
| `data` | TextField | raw options data (one row per line) | yes | `None` |
| `separator` | CharField(1) | column separator for the data table | yes | `` |
| `comment` | CharField(1) | line prefix marking comment rows | yes | `#` |
| `columns` | CharField(20) | number of columns (not editable) | yes | `` |
| `pk_col` | IntegerField | zero-based index of the id column | no | `0` |
| `parent_col` | IntegerField | zero-based index of the parent column for hierarchies | no | `-1` |
| `locale` | CharField(5) | default language code | no | `en-us` |
| `languages` | CharField(255) | language code of each column (comma separated) | yes | `-;-;` |

## Notes

- Natural key: `name`.
- `get_data()` parses `data` into `{pk, parent, label}` entries; `clean()`
  validates that the default locale is present in `languages`.
- `clean()` requires `languages` to be comma-separated.
