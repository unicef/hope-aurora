# FormSet

A repeater group: it embeds another `FlexForm` inside a form, so that a
registration can collect several repetitions of the same sub-form (e.g.
multiple household members).

Module: `aurora.core.models` — `class FormSet(AdminReverseMixin, NaturalKeyModel, OrderableModel)`

## Relations

- **parent** → `FlexForm` (FK, CASCADE, `related_name="formsets"`) — the form that embeds the set
- **flex_form** → `FlexForm` (FK, CASCADE) — the embedded sub-form
- **validator** → `Validator` (FK, SET_NULL; only validators with target `formset`)

## Fields

| Field | Type | Purpose | Optional | Default |
|-------|------|---------|----------|---------|
| `version` | AutoIncVersionField | optimistic locking version | no | — |
| `last_update_date` | DateTimeField | last modification time (`auto_now`) | no | — |
| `name` | CharField(255) | formset name, slugified on save | no | — |
| `title` | CharField(300) | display title | yes | `None` |
| `description` | TextField(2000) | help text | yes | `None` |
| `enabled` | BooleanField | include the formset in the form | no | `True` |
| `parent` | ForeignKey(FlexForm, CASCADE) | embedding form | no | — |
| `flex_form` | ForeignKey(FlexForm, CASCADE) | embedded sub-form | no | — |
| `extra` | IntegerField | number of empty forms rendered | no | `0` |
| `max_num` | IntegerField | maximum repetitions | yes | `None` |
| `min_num` | IntegerField | minimum repetitions (required when > 0) | no | `0` |
| `dynamic` | BooleanField | allow adding/removing repetitions client-side | no | `True` |
| `validator` | ForeignKey(Validator, SET_NULL) | formset-level validator | yes | `None` |
| `advanced` | JSONField | widget options (`smart` attrs) | yes | `{}` |

## Notes

- Natural key: `name`; `(parent, flex_form, name)` is unique.
- Default `smart` widget attributes are merged into `advanced` on save.
